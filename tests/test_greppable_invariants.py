"""The rules that are a pattern over the source, and the ones that are not.

Part of #92. Some of this project's rules are a pattern over the tree, and where
that is true the rule belongs in a check rather than in a paragraph somebody
remembers. This file is where those live, and it is also where a rule that is
NOT expressible as a pattern is recorded as such, because the alternative to
recording it is approximating it with a pattern that mostly works.

The register below carries one entry per candidate rule, each with a status. A
test asserts the register's size, so a rule cannot be dropped by deleting its
entry, and every status carries a check of its own:

- A rule enforced here has an operator in this file and fixtures that trip it.
- A rule enforced elsewhere names the file that refuses it, and that file has to
  exist.
- A rule with no subject in the tree yet names the directories that would be its
  subject, and the suite REDS the day one of them holds Python. That is what
  stops this register from becoming a note that went stale: the trigger is
  derived from the tree rather than from anyone remembering to come back.
- A rule that is not expressible as a pattern carries the reason, and nothing
  fires for it. That state is terminal rather than a placeholder.

What this file cannot do, stated so a green is not read as more than it is. The
workflow reader is text-level: it finds `uses:` by pattern and does not parse
YAML, so a value built at run time out of an expression is invisible to it, and
so is anything a called action does once it is running. It judges the reference
a step names, never what that reference resolves to on the day it runs.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = ".github/workflows"

# `uses:` and its value, up to the first space or the comment that usually
# carries the human-readable version beside a hash.
USES_KEY = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<value>[^\s#]+)")

# A commit pin: something, an at sign, and forty lowercase hex digits. A tag, a
# branch and a shortened hash are all refused, and the shortened hash is the
# near-miss worth having, because it looks pinned and is not.
COMMIT_PIN = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")

# An action in this repository is referenced by path and has no ref to pin. It
# is inside the tree the check is protecting, so there is nothing to pin it to.
LOCAL_ACTION = re.compile(r"^\./")

# Floors, so a reader that found nothing cannot pass as a tree with nothing
# wrong. Measured at the commit these landed in:
#
#     git ls-files .github/workflows | wc -l
#     6
#     grep -hcE '^\s*(-\s+)?uses:' .github/workflows/*.yml | paste -sd+ | python -c "import sys; print(sum(int(n) for n in sys.stdin.read().split('+')))"
#     13
#
# The gap between each floor and its count is deliberate: a floor equal to the
# count reds on every deliberate removal, which trains a reader to lower it.
WORKFLOW_FLOOR = 5
ACTION_FLOOR = 10

ENFORCED_HERE = "enforced by an operator in this file"
ENFORCED_ELSEWHERE = "enforced by a check that already exists"
NO_SUBJECT_YET = "expressible, and nothing in the tree is its subject yet"
NOT_A_PATTERN = "not expressible as a pattern, recorded rather than approximated"


@dataclass(frozen=True)
class Rule:
    """One candidate invariant and what is true of it today."""

    rule: str
    status: str
    # For ENFORCED_ELSEWHERE: the file that refuses it, which must exist.
    refused_by: str | None = None
    # For NO_SUBJECT_YET: the directories whose first Python file makes the rule
    # live. The suite reds then, naming the rule.
    subject_dirs: tuple[str, ...] = ()
    # For NO_SUBJECT_YET and NOT_A_PATTERN: why, in a sentence a reader can act on.
    note: str = ""


# Seven of these are the candidates in #92's own body. The eighth is the rule
# `docs/decisions/reference-integration.md` states and hands to #92 by name, and
# it is here so that handing it over was not the last time anybody saw it.
REGISTER: tuple[Rule, ...] = (
    Rule(
        rule="every workflow action is pinned to a commit hash",
        status=ENFORCED_HERE,
    ),
    Rule(
        rule="no file outside an adapter imports an engine",
        status=ENFORCED_ELSEWHERE,
        refused_by="tests/test_package_boundaries.py",
        note=(
            "The boundary check reads the declared engine module of each adapter "
            "and refuses the import from anywhere else. Restating it here would "
            "be a second source of truth for one rule."
        ),
    ),
    Rule(
        rule="no tolerance appears as a literal in the metric code",
        status=NO_SUBJECT_YET,
        subject_dirs=("metrics",),
        note=(
            "Every tolerance belongs to a case file, which is where the "
            "derivation that justifies it lives. The estimators that would carry "
            "a literal instead start at #75."
        ),
    ),
    Rule(
        rule="no result field is read by a string literal outside the record reader",
        status=NO_SUBJECT_YET,
        subject_dirs=("runner", "report", "metrics"),
        note=(
            "A field name spelled out at the point of use is a field the record "
            "reader cannot rename or refuse. The record is #10 and #40, the "
            "reader lands with #79."
        ),
    ),
    Rule(
        rule="no aggregate is computed across classes",
        status=NO_SUBJECT_YET,
        subject_dirs=("report",),
        note=(
            "The refusal of a single score is a design constraint, #17, and the "
            "assembly that could violate it is #80."
        ),
    ),
    Rule(
        rule="every published number's rendering carries an uncertainty",
        status=NO_SUBJECT_YET,
        subject_dirs=("report",),
        note=(
            "A bare number is refused by #15's decision; the rendering that would "
            "produce one is #81."
        ),
    ),
    Rule(
        rule="no document enumerates the checks, the engines or the cases",
        status=NOT_A_PATTERN,
        note=(
            "The rule is about where a list came from rather than about the list. "
            "docs/reference-gate-parity.md is an enumeration of checks and is "
            "legitimate, because every list in it is command output with the "
            "command above it. A pattern reads the list and cannot read its "
            "provenance, so any pattern here refuses the honest document and the "
            "dishonest one identically. Recorded rather than approximated."
        ),
    ),
    Rule(
        rule="the word symplectic is not written about the non-Hamiltonian half",
        status=NOT_A_PATTERN,
        note=(
            "Asking for a symplectic method on a nonholonomic system is a "
            "category error, and the rule exists so the word does not travel "
            "there. What a pattern cannot decide is which half a sentence is "
            "about: docs/decisions/reference-integration.md uses the word "
            "correctly about one half and names the other in the same file, so a "
            "collocation rule would refuse the document that states the rule. A "
            "narrower and sound form becomes available when reference/ holds one "
            "module per case, and it belongs to #48."
        ),
    ),
)


def workflow_files(root: Path) -> list[Path]:
    directory = root / WORKFLOW_DIR
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.suffix in (".yml", ".yaml"))


def action_references(text: str) -> list[str]:
    """Every `uses:` value the text declares, in order. Comments are not steps."""
    values = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        found = USES_KEY.match(line)
        if found:
            values.append(found.group("value"))
    return values


def unpinned_actions(root: Path) -> list[str]:
    """Every action reference that is not a commit pin. Empty is the only pass.

    A local action is accepted: it is a path into this tree and there is no ref
    to pin. Everything else, including a Docker reference, is refused, so an
    unfamiliar shape reds rather than being waved through by a rule that was
    written without it in mind.
    """
    violations = []
    for path in workflow_files(root):
        name = path.relative_to(root).as_posix()
        for value in action_references(path.read_text(encoding="utf-8")):
            if LOCAL_ACTION.match(value) or COMMIT_PIN.match(value):
                continue
            violations.append(
                f"{name} uses {value}, which is not pinned to a commit hash, so "
                f"what runs is decided by whoever can move that reference"
            )
    return sorted(violations)


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


CLEAN_WORKFLOW = """\
name: example
jobs:
  example:
    steps:
      # uses: actions/checkout@v7 in a comment is not a step
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: A local action
        uses: ./.github/actions/something
      - name: Something else
        uses: ossf/scorecard-action@2d1146689b8cda280b9bc96326124645441f03bc # v2.4.4
"""


class ThePinCheckBites(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        _write(self.root, f"{WORKFLOW_DIR}/example.yml", CLEAN_WORKFLOW)

    def test_the_clean_workflow_is_accepted(self) -> None:
        # The near-miss. A hash pin with a version comment beside it, a local
        # action with no ref, and a commented-out tag are all legal. Without
        # this every refusal below could be passing for the wrong reason.
        self.assertEqual(unpinned_actions(self.root), [])

    def test_a_tag_pin_is_refused(self) -> None:
        _write(
            self.root,
            f"{WORKFLOW_DIR}/example.yml",
            CLEAN_WORKFLOW.replace(
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", "actions/checkout@v7"
            ),
        )
        violations = unpinned_actions(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("actions/checkout@v7", violations[0])

    def test_a_branch_pin_is_refused(self) -> None:
        _write(
            self.root,
            f"{WORKFLOW_DIR}/example.yml",
            CLEAN_WORKFLOW.replace(
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", "actions/checkout@main"
            ),
        )
        self.assertEqual(len(unpinned_actions(self.root)), 1)

    def test_a_shortened_hash_is_refused(self) -> None:
        # The one-character mistake somebody will actually make: a hash that
        # looks pinned, is a prefix, and can be made to resolve elsewhere.
        _write(
            self.root,
            f"{WORKFLOW_DIR}/example.yml",
            CLEAN_WORKFLOW.replace(
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b",
            ),
        )
        self.assertEqual(len(unpinned_actions(self.root)), 1)

    def test_an_uppercase_hash_is_refused(self) -> None:
        # Git prints lowercase, so an uppercase forty is a hash somebody typed
        # rather than copied, and accepting it would widen the pattern for no
        # gain.
        _write(
            self.root,
            f"{WORKFLOW_DIR}/example.yml",
            CLEAN_WORKFLOW.replace(
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                "actions/checkout@3D3C42E5AAC5BA805825DA76410C181273BA90B1",
            ),
        )
        self.assertEqual(len(unpinned_actions(self.root)), 1)

    def test_a_docker_reference_is_refused(self) -> None:
        _write(
            self.root,
            f"{WORKFLOW_DIR}/example.yml",
            CLEAN_WORKFLOW.replace(
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                "docker://alpine:3.20",
            ),
        )
        self.assertEqual(len(unpinned_actions(self.root)), 1)

    def test_a_second_workflow_is_read_too(self) -> None:
        # Without this, a reader that stopped after the first file would pass a
        # tree whose second workflow is unpinned.
        _write(
            self.root,
            f"{WORKFLOW_DIR}/second.yml",
            "jobs:\n  x:\n    steps:\n      - uses: actions/checkout@v7\n",
        )
        violations = unpinned_actions(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("second.yml", violations[0])


class TheWorkflowsInThisTree(unittest.TestCase):
    def test_every_action_is_pinned_to_a_commit(self) -> None:
        self.assertEqual(unpinned_actions(REPO_ROOT), [])

    def test_the_reader_found_the_workflows(self) -> None:
        # A green over an empty file list is the shape #30 is about.
        found = len(workflow_files(REPO_ROOT))
        self.assertGreaterEqual(
            found, WORKFLOW_FLOOR, f"found {found} workflow files, floor {WORKFLOW_FLOOR}"
        )

    def test_the_reader_found_the_action_references(self) -> None:
        found = sum(
            len(action_references(path.read_text(encoding="utf-8")))
            for path in workflow_files(REPO_ROOT)
        )
        self.assertGreaterEqual(
            found, ACTION_FLOOR, f"found {found} action references, floor {ACTION_FLOOR}"
        )


class TheRegisterIsHonest(unittest.TestCase):
    def test_no_rule_is_dropped_by_deleting_its_entry(self) -> None:
        # Seven from #92's body, one handed over by the reference note. A
        # register that shrinks is a rule that stopped being tracked, and
        # nothing else in the tree would notice.
        self.assertEqual(len(REGISTER), 8)

    def test_every_rule_has_a_known_status(self) -> None:
        known = {ENFORCED_HERE, ENFORCED_ELSEWHERE, NO_SUBJECT_YET, NOT_A_PATTERN}
        for entry in REGISTER:
            self.assertIn(entry.status, known, entry.rule)

    def test_a_rule_enforced_elsewhere_names_a_file_that_exists(self) -> None:
        named = [e for e in REGISTER if e.status == ENFORCED_ELSEWHERE]
        self.assertTrue(named)
        for entry in named:
            self.assertIsNotNone(entry.refused_by, entry.rule)
            self.assertTrue(
                (REPO_ROOT / entry.refused_by).is_file(),
                f"{entry.rule}: {entry.refused_by} does not exist, so the rule is "
                f"recorded as enforced by nothing",
            )

    def test_a_rule_that_is_not_a_pattern_says_why(self) -> None:
        for entry in REGISTER:
            if entry.status == NOT_A_PATTERN:
                self.assertTrue(entry.note.strip(), entry.rule)

    def test_a_rule_with_no_subject_yet_still_has_no_subject(self) -> None:
        # The trigger. Each of these rules is expressible and has nothing in the
        # tree to run against, so it is recorded rather than written. The day one
        # of the named directories holds Python, this reds and says which rule
        # became live. Repairing it is writing that rule's operator here, or
        # moving the entry to whichever check took it.
        for entry in REGISTER:
            if entry.status != NO_SUBJECT_YET:
                continue
            self.assertTrue(entry.subject_dirs, entry.rule)
            for directory in entry.subject_dirs:
                found = sorted(
                    path.relative_to(REPO_ROOT).as_posix()
                    for path in (REPO_ROOT / directory).rglob("*.py")
                )
                self.assertEqual(
                    found,
                    [],
                    f"the rule '{entry.rule}' now has a subject in {directory}/ "
                    f"({', '.join(found)}), so it is no longer a rule with "
                    f"nothing to check. Write its operator in this file, or move "
                    f"its entry to the check that took it. #92.",
                )


if __name__ == "__main__":
    unittest.main()
