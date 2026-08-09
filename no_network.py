"""Outbound network refused inside the process that runs the suite.

Issue #23. A unit test that reaches the network is slow, flaky and a supply
chain surface nobody looks at, and in this project it is also a leak: the suite
handles case files and result records, and a test that uploads one somewhere is
the exact failure the legal position of this project forbids.

The engines make it more likely rather than less. Several of them fetch assets,
check for updates or resolve model files on first use, inside a call that looks
local, so the refusal has to be a property of the running process rather than a
sentence a contributor is asked to remember.

What is refused, and where the refusal is placed:

- Every outbound call on an internet socket, at ``socket.socket`` itself, so
  everything layered above it reaches the same refusal. ``urllib``,
  ``http.client`` and an engine's own client all go through it.
- Name resolution, separately from connection. A test that only resolves is
  still a test that talks to somewhere, and it is the half that leaks a
  hostname without ever opening a connection.

What is deliberately not refused. A socket on a family that is not
``AF_INET`` or ``AF_INET6`` is local by construction and is passed through, as
is creating an internet socket without using it, binding one, and
``socket.gethostname``. Refusing those would make the guard a thing that breaks
unrelated code, which is how a guard gets switched off.

Two bounds, so a green here is not read as more than it is.

The refusal lives in this process and not in the kernel. A test that shells out
to a child process is refusing nothing in that child, because the child imports
none of this. What closes that gap is a sandbox around the whole run rather
than a patch inside it, and this module cannot be it.

The refusal covers what goes through ``socket``. A call reaching the network by
another route, an extension module opening its own descriptor among them, is
invisible here. That route is what the engines are most likely to take, which is
why the register of what an engine fetches on first use is a separate obligation
in ``tests/test_no_network.py`` rather than something this module could observe.

Installed by importing ``tests/test_no_network.py``, which discovery imports
before it runs any test, so every test in a discovered run has it in force
whether the run was started by the gate or by ``unittest`` directly. Running a
single test module by name is the one route that does not carry it.
"""

from __future__ import annotations

import socket
from typing import Any, Callable

# The families that reach somewhere else. Everything outside this set is local
# by construction and is passed through untouched.
REFUSED_FAMILIES = frozenset({socket.AF_INET, socket.AF_INET6})

# Module-level calls that turn a name into an address, or an address back into a
# name. Refused whole: there is no such call in this suite that is not a call to
# somewhere.
RESOLVERS = (
    "getaddrinfo",
    "gethostbyname",
    "gethostbyname_ex",
    "gethostbyaddr",
    "getnameinfo",
)

# Methods on a socket that send something outward. `sendmsg` is absent on some
# platforms, and a method that does not exist is not a route, so the list of
# what was actually replaced is reported by `refused_calls` rather than assumed
# from this one.
OUTBOUND_METHODS = ("connect", "connect_ex", "sendto", "sendmsg")

# What was replaced, name to the original, so `in_force` is derived from the
# state of the socket module rather than from a flag somebody set.
_REPLACED: dict[str, Any] = {}


class NetworkRefused(RuntimeError):
    """What an outbound call raises instead of reaching somewhere.

    It is an error and not a skip. A test that trips this has found a route out
    of the machine, and a run that quietly stepped over it would be a green
    covering the thing the refusal exists for.
    """


def _resolver_refusal(name: str) -> Callable[..., Any]:
    def refuse(*_args: Any, **_kwargs: Any) -> Any:
        raise NetworkRefused(
            f"socket.{name} was called. Name resolution is refused in the suite "
            f"that runs anywhere, because a test that resolves a name has "
            f"already talked to somewhere. A test that needs the network "
            f"belongs in a harness whose name says so."
        )

    return refuse


def _method_refusal(name: str, original: Callable[..., Any]) -> Callable[..., Any]:
    def refuse(self: socket.socket, *args: Any, **kwargs: Any) -> Any:
        if self.family not in REFUSED_FAMILIES:
            return original(self, *args, **kwargs)
        raise NetworkRefused(
            f"socket.socket.{name} was called on an {self.family!r} socket. "
            f"Outbound network is refused in the suite that runs anywhere. A "
            f"test that needs the network belongs in a harness whose name says "
            f"so."
        )

    return refuse


def refuse_outbound() -> bool:
    """Refuse outbound network in this process. True if this call did it.

    Idempotent, and it keeps no second copy of the originals: a second call
    finds the refusals already in place and changes nothing, so importing this
    from two places cannot end with a refusal wrapping a refusal.
    """
    if _REPLACED:
        return False

    for name in RESOLVERS:
        _REPLACED[f"socket.{name}"] = getattr(socket, name)
        setattr(socket, name, _resolver_refusal(name))

    for name in OUTBOUND_METHODS:
        original = getattr(socket.socket, name, None)
        if original is None:
            continue
        _REPLACED[f"socket.socket.{name}"] = original
        setattr(socket.socket, name, _method_refusal(name, original))

    return True


def in_force() -> bool:
    """Whether the refusal is installed in this process."""
    return bool(_REPLACED)


def refused_calls() -> tuple[str, ...]:
    """Every call that was replaced, so a reader sees the reach and not a claim."""
    return tuple(sorted(_REPLACED))
