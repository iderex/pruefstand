"""The suite that runs anywhere runs with outbound network refused.

Issue #23. The refusal itself is `no_network.py`; this file is where it is put
in force for the run and where it is shown to bite.

Importing this module installs the refusal. Discovery imports every test module
before it runs any test, so the refusal is in force for the whole run whichever
route started it, and a test added tomorrow inherits it without knowing this
file exists. The one route that does not carry it is running a single test
module by name, which is a convenience rather than the gate.

The bite is shown by calling the real thing rather than by inspecting the
patch: an outbound connection, a connection on the second spelling that returns
a code instead of raising, a datagram, and a name lookup. Each is refused, and
the connection is timed, because the failure this issue is about is not a test
that errors but a test that sits there for a minute first.

Deleting the `refuse_outbound()` call below turns nine tests red, including the
one that says the refusal is in force, so the guard cannot be removed quietly.
The same deletion takes the whole run from 2.3 seconds to 69.9 seconds, which is
the second half of what this issue is about arriving as a measurement rather
than as a warning.

This file also carries the register of what an engine reaches on first use.
There is no adapter in this tree, so nothing has been examined and the register
is empty; the check below reds the day an adapter package lands without an
entry, which is what stops an empty register from being read as a finding that
engines reach nothing.
"""

from __future__ import annotations

import socket
import tempfile
import time
import unittest
from pathlib import Path

import no_network

REPO_ROOT = Path(__file__).resolve().parent.parent
ADAPTERS_DIR = "adapters"

# In force for every test in this run, installed at import rather than in a
# setUp, because a setUp runs after discovery has already imported everything
# and a module doing its outbound call at import time would have got out.
no_network.refuse_outbound()

# An address in the range reserved for documentation. Reaching it is refused
# before anything is sent, so nothing here depends on what is or is not routable
# from the machine the suite runs on.
UNREACHABLE = ("203.0.113.1", 80)

# A name in the reserved top-level domain that is guaranteed not to resolve. It
# is here so that the refusal is what stops the call rather than the absence of
# an answer.
UNRESOLVABLE = "pruefstand.invalid"

# What a refused call may take before it is a hang rather than a refusal. The
# refusal does no input or output at all, so this is orders of magnitude above
# what it costs and still far below the tens of seconds an unanswered connection
# takes to give up.
PROMPT_SECONDS = 5.0

# What an engine reaches on first use, one entry per adapter package under
# `adapters/`, keyed by the package directory name.
#
# An entry says what the engine fetched, and how it was made to stop. Where an
# engine was examined and found to reach nothing, the entry says that and names
# the command that showed it, because "examined and found nothing" and "not
# examined" are different statements and only one of them is evidence.
#
# EMPTY IS NOT A FINDING TODAY. There is no adapter package in this tree:
#
#     git ls-files adapters/
#     adapters/README.md
#
# so nothing has been examined and nothing could have been. The check below is
# what makes that state expire rather than persist as an unread note.
FIRST_USE_NETWORK: dict[str, str] = {}


def adapter_packages(root: Path) -> list[str]:
    """Every directory under `adapters/` that is a package."""
    adapters = root / ADAPTERS_DIR
    if not adapters.is_dir():
        return []
    return sorted(
        path.name for path in adapters.iterdir() if (path / "__init__.py").is_file()
    )


def register_violations(root: Path, register: dict[str, str]) -> list[str]:
    """Every way the register and the tree disagree. Empty is the only pass.

    It fails closed in both directions. An adapter with no entry is an engine
    nobody looked at, and an entry naming no adapter is a note about something
    that is no longer here, which is the state a register rots into.
    """
    violations: list[str] = []
    packages = adapter_packages(root)

    for name in packages:
        if name not in register:
            violations.append(
                f"{ADAPTERS_DIR}/{name} is an adapter package and the register "
                f"says nothing about what its engine reaches on first use"
            )

    for name in sorted(register):
        if name not in packages:
            violations.append(
                f"the register carries an entry for {ADAPTERS_DIR}/{name}, and "
                f"there is no adapter package there"
            )

    return sorted(violations)


class TheRefusalIsInForce(unittest.TestCase):
    def test_it_is_installed_for_this_run(self) -> None:
        # Delete the call at the top of this file and this reds. It is the only
        # test here that fails for the guard being absent rather than for the
        # guard being wrong.
        self.assertTrue(no_network.in_force())

    def test_it_reaches_both_halves(self) -> None:
        # Connection and resolution are separate routes out, and a guard that
        # took only one of them would pass every other test in this class.
        replaced = no_network.refused_calls()
        self.assertIn("socket.socket.connect", replaced)
        self.assertIn("socket.getaddrinfo", replaced)

    def test_installing_it_twice_changes_nothing(self) -> None:
        # A second install that wrapped the first would keep a refusal as the
        # original, and there would be no way back to a working socket module.
        self.assertFalse(no_network.refuse_outbound())


class AnOutboundCall(unittest.TestCase):
    def test_a_connection_is_refused(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            with self.assertRaises(no_network.NetworkRefused):
                sock.connect(UNREACHABLE)

    def test_it_is_refused_promptly_rather_than_after_a_wait(self) -> None:
        # The failure this issue names. An outbound call that is not refused
        # does not fail here, it waits, and a suite that waits is a suite people
        # stop running.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            started = time.monotonic()
            with self.assertRaises(no_network.NetworkRefused):
                sock.connect(UNREACHABLE)
            elapsed = time.monotonic() - started
        self.assertLess(elapsed, PROMPT_SECONDS, f"took {elapsed:.3f}s to refuse")

    def test_the_spelling_that_returns_a_code_is_refused_too(self) -> None:
        # The one-character mistake somebody will actually make. `connect_ex`
        # reports failure by returning rather than by raising, so a guard that
        # only covered `connect` would let this one through silently.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            with self.assertRaises(no_network.NetworkRefused):
                sock.connect_ex(UNREACHABLE)

    def test_a_datagram_is_refused(self) -> None:
        # A datagram needs no connection, so every check written around
        # connecting misses it.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            with self.assertRaises(no_network.NetworkRefused):
                sock.sendto(b"x", UNREACHABLE)

    def test_a_connection_over_the_other_internet_family_is_refused(self) -> None:
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        except OSError as error:
            # Said out loud rather than passed over. A machine that cannot make
            # the socket at all has not shown this half of the refusal, and a
            # silent pass here would read as though it had.
            self.skipTest(f"this machine cannot open an AF_INET6 socket: {error}")
        else:
            # THE SOCKET IS USED IN THE BRANCH THAT MADE IT, and the `else` is
            # what says so. Before, `with sock:` stood after the try block and
            # was reachable on paper from the failing path too - correct only
            # because `skipTest` raises, which is a property of unittest the
            # reader has to know and a checker cannot see. CodeQL read it as
            # `sock` possibly used before assignment, the one `error`-severity
            # finding across the fleet on 2026-08-17.
            #
            # Nothing about the behaviour changes. What changes is that the
            # guarantee is in the code rather than in what somebody remembers
            # about skipTest.
            with sock:
                with self.assertRaises(no_network.NetworkRefused):
                    sock.connect(("2001:db8::1", 80, 0, 0))


class NameResolution(unittest.TestCase):
    def test_the_general_lookup_is_refused(self) -> None:
        with self.assertRaises(no_network.NetworkRefused):
            socket.getaddrinfo(UNRESOLVABLE, 80)

    def test_the_older_lookup_is_refused(self) -> None:
        with self.assertRaises(no_network.NetworkRefused):
            socket.gethostbyname(UNRESOLVABLE)

    def test_the_reverse_lookup_is_refused(self) -> None:
        # Reverse resolution sends the address of somebody the suite is not
        # supposed to be talking to, which is the same leak read backwards.
        with self.assertRaises(no_network.NetworkRefused):
            socket.gethostbyaddr(UNREACHABLE[0])


class WhatIsStillAllowed(unittest.TestCase):
    """The near-miss. Without this class a guard that broke the socket module
    outright would pass every refusal above and be indistinguishable from one
    that refuses exactly what it names."""

    def test_an_internet_socket_can_still_be_made_and_closed(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(sock.close)
        self.assertEqual(sock.family, socket.AF_INET)

    def test_the_local_hostname_is_still_readable(self) -> None:
        # It answers from the machine and reaches nowhere, so refusing it would
        # be the guard growing past what it was asked for.
        self.assertTrue(socket.gethostname())

    def test_a_socket_on_another_family_is_passed_through(self) -> None:
        # The branch no platform-independent socket can reach from a test. A
        # guard without the family check would refuse a local socket too, and
        # every other test here would still be green.
        passed: list[object] = []

        def original(_self: object, *args: object) -> str:
            passed.append(args)
            return "passed through"

        refusal = no_network._method_refusal("connect", original)

        class NotAnInternetSocket:
            family = -1

        self.assertEqual(refusal(NotAnInternetSocket(), "somewhere"), "passed through")
        self.assertEqual(passed, [("somewhere",)])


class TheRegisterAndTheTree(unittest.TestCase):
    def test_this_repository_has_no_violations(self) -> None:
        self.assertEqual(register_violations(REPO_ROOT, FIRST_USE_NETWORK), [])

    def test_an_adapter_with_no_entry_is_refused(self) -> None:
        # The trigger that makes the empty register expire. The day an adapter
        # lands, this reds until somebody has looked at what its engine fetches.
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / ADAPTERS_DIR / "someengine").mkdir(parents=True)
            (root / ADAPTERS_DIR / "someengine" / "__init__.py").write_text(
                "", encoding="utf-8"
            )
            violations = register_violations(root, {})
        self.assertEqual(len(violations), 1)
        self.assertIn("someengine", violations[0])

    def test_an_entry_naming_no_adapter_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            violations = register_violations(Path(name), {"gone": "fetched nothing"})
        self.assertEqual(len(violations), 1)
        self.assertIn("there is no adapter package there", violations[0])

    def test_an_adapter_with_an_entry_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / ADAPTERS_DIR / "someengine").mkdir(parents=True)
            (root / ADAPTERS_DIR / "someengine" / "__init__.py").write_text(
                "", encoding="utf-8"
            )
            violations = register_violations(
                root, {"someengine": "fetches a model file on import"}
            )
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
