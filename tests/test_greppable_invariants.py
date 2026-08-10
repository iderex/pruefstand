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

import ast
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
# The names a tolerance is written under in this tree. A tolerance is the number
# that decides whether a case passed, it belongs to the case file where the
# derivation that justifies it lives, and an estimator carrying its own is an
# estimator that judges a case the case did not ask to be judged by.
TOLERANCE_NAMES = frozenset(
    {"tolerance", "tolerances", "tol", "atol", "rtol", "eps", "epsilon", "threshold"}
)

# Where the metric code is. Derived from the tree in the same breath as the rule
# that reads it, so the check starts running the day the directory holds Python.
METRIC_DIRS = ("metrics",)

# Where a result field could be read by a name spelled out at the point of use.
# The record reader, once it exists, is the one place that may, and it does not
# exist yet, so nothing here is exempt today.
RECORD_READER_DIRS = ("runner", "report", "metrics")

# Floors under the two operators below, so a reader that found no file cannot
# pass as a tree with nothing wrong. Measured at the commit these landed in:
#
#     git ls-files 'metrics/*.py' | wc -l
#     3
#     git ls-files 'runner/*.py' 'report/*.py' | wc -l
#     0
METRIC_FILE_FLOOR = 3
RECORD_READER_FILE_FLOOR = 3

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
        status=ENFORCED_HERE,
        subject_dirs=METRIC_DIRS,
        note=(
            "Every tolerance belongs to a case file, which is where the "
            "derivation that justifies it lives. This rule had no subject until "
            "#75 put the first estimator under metrics/, which is the day this "
            "register said it would become live."
        ),
    ),
    Rule(
        rule="no result field is read by a string literal outside the record reader",
        status=ENFORCED_HERE,
        subject_dirs=RECORD_READER_DIRS,
        note=(
            "A field name spelled out at the point of use is a field the record "
            "reader cannot rename or refuse. The record is #10 and #40 and the "
            "reader lands with #79, so nothing is exempt yet and the exemption "
            "is written by whoever writes the reader."
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


def _numeric_literal(node: ast.expr) -> bool:
    """Whether an expression is a number written out where it stands.

    A negative literal is a unary minus over one, which is the spelling somebody
    reaches for and which a check reading only constants walks straight past.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _numeric_literal(node.operand)
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float))


def _is_tolerance(name: str) -> bool:
    return name.strip("_").lower() in TOLERANCE_NAMES


def _python_files(root: Path, directories: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for name in directories:
        directory = root / name
        if directory.is_dir():
            found.extend(sorted(p for p in directory.rglob("*.py") if p.is_file()))
    return found


def _defaults(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, ast.expr]]:
    """Each parameter of a function that has a default, with that default."""
    arguments = node.args
    positional = arguments.posonlyargs + arguments.args
    pairs: list[tuple[str, ast.expr]] = []
    for argument, default in zip(
        positional[len(positional) - len(arguments.defaults) :], arguments.defaults
    ):
        pairs.append((argument.arg, default))
    for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults):
        if default is not None:
            pairs.append((argument.arg, default))
    return pairs


def literal_tolerances(
    root: Path, directories: tuple[str, ...] = METRIC_DIRS
) -> list[str]:
    """Every place the metric code writes a tolerance out as a number.

    Three shapes, because those are the three ways a number arrives under one of
    these names: an assignment, a parameter default, and a keyword at a call.

    What this cannot do, so a green is not read as more than it is. It reads
    NAMES. A tolerance carried under a name outside the vocabulary is invisible
    to it, and so is one built out of two literals rather than written as one.
    The vocabulary is a floor rather than a guarantee, and it is the shape this
    rule can take at all: a check that tried to decide from the value whether a
    number is a tolerance would refuse every constant in the file.
    """
    violations: list[str] = []
    for path in _python_files(root, directories):
        where = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                named = [
                    target.id
                    for target in node.targets
                    if isinstance(target, ast.Name) and _is_tolerance(target.id)
                ]
                if named and _numeric_literal(node.value):
                    violations.append(
                        f"{where}:{node.lineno} assigns {named[0]} a number "
                        f"written here, and a tolerance belongs to the case file "
                        f"whose result it decides"
                    )
            elif isinstance(node, ast.AnnAssign):
                target = node.target
                if (
                    isinstance(target, ast.Name)
                    and _is_tolerance(target.id)
                    and node.value is not None
                    and _numeric_literal(node.value)
                ):
                    violations.append(
                        f"{where}:{node.lineno} assigns {target.id} a number "
                        f"written here, and a tolerance belongs to the case file "
                        f"whose result it decides"
                    )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for name, default in _defaults(node):
                    if _is_tolerance(name) and _numeric_literal(default):
                        violations.append(
                            f"{where}:{node.lineno} defaults {name} to a number "
                            f"written here, which is a tolerance no caller stated"
                        )
            elif isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if (
                        keyword.arg is not None
                        and _is_tolerance(keyword.arg)
                        and _numeric_literal(keyword.value)
                    ):
                        violations.append(
                            f"{where}:{node.lineno} passes {keyword.arg} as a "
                            f"number written here"
                        )
    return sorted(violations)


def literal_field_reads(
    root: Path, directories: tuple[str, ...] = RECORD_READER_DIRS
) -> list[str]:
    """Every place a field is reached by a name spelled out where it is used.

    Two shapes: a subscript carrying a string, and `getattr` or `setattr`
    carrying one. Both are a field name the record reader cannot rename and
    cannot refuse, and both survive a schema that moved under them, which is the
    failure this rule is about: a report that goes on rendering a field the
    record stopped carrying.

    What this cannot do. A name held in a variable is invisible to it. That is
    the honest cost of reading source rather than running it, and it is also the
    shape a reader written against the schema legitimately takes, which is why
    the exemption this rule names is for a file rather than for a spelling. That
    file does not exist yet, so nothing is exempt today: #79.
    """
    violations: list[str] = []
    for path in _python_files(root, directories):
        where = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                index = node.slice
                if isinstance(index, ast.Constant) and isinstance(index.value, str):
                    violations.append(
                        f"{where}:{node.lineno} reads the field {index.value!r} "
                        f"by a name written here"
                    )
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in ("getattr", "setattr")
                and len(node.args) >= 2
            ):
                named = node.args[1]
                if isinstance(named, ast.Constant) and isinstance(named.value, str):
                    violations.append(
                        f"{where}:{node.lineno} reads the field {named.value!r} "
                        f"by a name written here"
                    )
    return sorted(violations)


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


# A metric module that breaks neither rule, so every refusal below is this with
# one thing changed and a refusal firing for another reason shows up as this
# fixture failing.
CLEAN_METRIC = """\
BLOCKS = 20
SETTLING_FRACTION = 0.05


def compare(measured, case, field):
    tolerance = case.tolerance
    reading = getattr(case, field)
    return abs(measured - reading) <= tolerance
"""


class TheToleranceCheckBites(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        _write(self.root, "metrics/estimator.py", CLEAN_METRIC)

    def refused(self, source: str) -> list[str]:
        _write(self.root, "metrics/estimator.py", source)
        return literal_tolerances(self.root)

    def test_the_clean_metric_is_accepted(self) -> None:
        # Two constants that are not tolerances, and a tolerance read from the
        # case rather than written here. Without this the refusals below could
        # all be passing because the check refuses everything.
        self.assertEqual(literal_tolerances(self.root), [])

    def test_a_tolerance_assigned_a_number_is_refused(self) -> None:
        found = self.refused(CLEAN_METRIC + "\nTOLERANCE = 1e-9\n")
        self.assertEqual(len(found), 1)
        self.assertIn("TOLERANCE", found[0])

    def test_a_negative_literal_is_refused(self) -> None:
        # The one-character mistake: a minus sign in front turns the constant
        # into a unary operation, and a check reading only constants walks past.
        self.assertEqual(len(self.refused(CLEAN_METRIC + "\nrtol = -1e-9\n")), 1)

    def test_an_annotated_assignment_is_refused(self) -> None:
        self.assertEqual(
            len(self.refused(CLEAN_METRIC + "\nepsilon: float = 1e-12\n")), 1
        )

    def test_a_parameter_default_is_refused(self) -> None:
        source = CLEAN_METRIC + "\n\ndef close(a, b, atol=1e-8):\n    return a - b\n"
        found = self.refused(source)
        self.assertEqual(len(found), 1)
        self.assertIn("atol", found[0])

    def test_a_keyword_only_default_is_refused(self) -> None:
        source = CLEAN_METRIC + "\n\ndef close(a, *, tol=1e-8):\n    return a\n"
        self.assertEqual(len(self.refused(source)), 1)

    def test_a_keyword_at_a_call_is_refused(self) -> None:
        source = CLEAN_METRIC + "\n\nchecked = compare(1.0, 2.0, threshold=1e-6)\n"
        self.assertEqual(len(self.refused(source)), 1)

    def test_a_private_spelling_is_refused(self) -> None:
        # Leading underscores are how a constant is hidden, and hiding it does
        # not make it belong here.
        self.assertEqual(len(self.refused(CLEAN_METRIC + "\n_TOL_ = 1e-9\n")), 1)

    def test_a_tolerance_that_is_not_a_number_is_accepted(self) -> None:
        # The near-miss on the other side. A tolerance taken from the case is
        # exactly what this rule asks for, and a check that refused the name
        # rather than the literal would refuse it.
        source = CLEAN_METRIC + "\ntolerance = case.tolerance * 2.0\n"
        self.assertEqual(self.refused(source), [])

    def test_a_second_file_is_read_too(self) -> None:
        _write(self.root, "metrics/second.py", "TOLERANCE = 1e-9\n")
        found = literal_tolerances(self.root)
        self.assertEqual(len(found), 1)
        self.assertIn("second.py", found[0])


class TheFieldReadCheckBites(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        _write(self.root, "metrics/estimator.py", CLEAN_METRIC)

    def refused(self, source: str) -> list[str]:
        _write(self.root, "metrics/estimator.py", source)
        return literal_field_reads(self.root)

    def test_the_clean_metric_is_accepted(self) -> None:
        # It calls getattr, and the name it reads is a parameter rather than a
        # string written at the point of use, which is the legal shape.
        self.assertEqual(literal_field_reads(self.root), [])

    def test_a_string_subscript_is_refused(self) -> None:
        found = self.refused(CLEAN_METRIC + '\nvalue = record["exponent"]\n')
        self.assertEqual(len(found), 1)
        self.assertIn("exponent", found[0])

    def test_a_getattr_with_a_name_written_here_is_refused(self) -> None:
        self.assertEqual(
            len(self.refused(CLEAN_METRIC + '\nvalue = getattr(record, "exponent")\n')),
            1,
        )

    def test_a_setattr_with_a_name_written_here_is_refused(self) -> None:
        self.assertEqual(
            len(self.refused(CLEAN_METRIC + '\nsetattr(record, "exponent", 1.0)\n')), 1
        )

    def test_an_index_that_is_not_a_field_name_is_accepted(self) -> None:
        # Two near-misses that a check reading subscripts loosely would refuse: a
        # position in a sequence, and a field named by a variable.
        source = CLEAN_METRIC + "\nfirst = trajectory[0]\nvalue = record[field]\n"
        self.assertEqual(self.refused(source), [])

    def test_a_slice_is_accepted(self) -> None:
        self.assertEqual(self.refused(CLEAN_METRIC + "\nhead = samples[0:10]\n"), [])


class TheMetricCodeInThisTree(unittest.TestCase):
    def test_no_tolerance_is_written_out_as_a_number(self) -> None:
        self.assertEqual(literal_tolerances(REPO_ROOT), [])

    def test_no_field_is_read_by_a_name_written_at_the_point_of_use(self) -> None:
        self.assertEqual(literal_field_reads(REPO_ROOT), [])

    def test_the_reader_found_the_metric_files(self) -> None:
        # A green over an empty file list is the shape #30 is about, and both of
        # these rules spent a while with nothing to read.
        found = len(_python_files(REPO_ROOT, METRIC_DIRS))
        self.assertGreaterEqual(
            found,
            METRIC_FILE_FLOOR,
            f"found {found} metric files, floor {METRIC_FILE_FLOOR}",
        )

    def test_the_reader_found_the_files_a_record_could_be_read_in(self) -> None:
        found = len(_python_files(REPO_ROOT, RECORD_READER_DIRS))
        self.assertGreaterEqual(
            found,
            RECORD_READER_FILE_FLOOR,
            f"found {found} files, floor {RECORD_READER_FILE_FLOOR}",
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
