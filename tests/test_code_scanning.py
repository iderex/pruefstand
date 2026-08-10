"""A suppression is an argument, so it has to carry one.

Issue #87. The code scanning analysis is in `.github/workflows/codeql.yml` and
its baseline is zero findings. A baseline at zero survives exactly as long as
nobody suppresses a finding without saying why, and a suppression comment is the
cheapest thing in this tree to write and the hardest to notice afterwards: it is
one line, it sits beside the code it silences, and the analysis then reports
green over the thing that was found.

So a suppression names the rule it suppresses and gives the reason, and this
file refuses one that does neither. What it cannot do is judge whether the
reason is a good one, which is what the review is for.

The other half here is the check-run name. A ruleset matches a required check by
its literal name, so renaming the job removes the check from the gate while the
workflow goes on passing. `CodeQL` is held against the workflow that produces it
and against the document that requests it, which is the shape
`docs/requested-gate-checks.md` says is owed for the rest of the list.

    python -m unittest discover -s tests -k code_scanning
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "codeql.yml"
GATE_LIST = REPO_ROOT / "docs" / "requested-gate-checks.md"

CHECK_RUN_NAME = "CodeQL"

# The two spellings a code scanning suppression takes in Python source. Both are
# read, because a tree that refused one and not the other refuses nothing: the
# other spelling is one word away.
SUPPRESSION = re.compile(r"#\s*(?P<tool>lgtm|codeql)\b(?P<rest>.*)", re.IGNORECASE)

# What follows the tool name in a suppression that carries its argument: the
# rule id in brackets, then the reason.
RULE_AND_REASON = re.compile(r"\s*\[(?P<rule>[^\]]+)\](?P<reason>.*)")

# The shortest a reason may be. A suppression whose reason is `ok` or `fine` is
# a suppression with no argument behind it, and this is the cheapest thing that
# separates the two without asking anybody to judge the sentence. It is a floor
# rather than a judgement.
REASON_FLOOR = 20

# Directories that are not this repository's source.
SKIPPED = {".git", ".github", "__pycache__"}

# A floor under the walk, so a reader that found no Python cannot pass as a tree
# with nothing wrong. Measured at the commit this landed in:
#
#     git ls-files '*.py' | wc -l
#     35
PYTHON_FILE_FLOOR = 30


def python_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if not SKIPPED.intersection(path.relative_to(root).parts)
    )


def bad_suppressions(source: str) -> list[str]:
    """The suppression lines in one file that name no rule or give no reason.

    A line that carries no suppression at all is not one of these, and neither
    is a suppression that carries both. Everything else is returned with the
    line as it was written, because the repair is made by reading it.
    """
    offending: list[str] = []
    for line in source.splitlines():
        found = SUPPRESSION.search(line)
        if found is None:
            continue
        parts = RULE_AND_REASON.match(found.group("rest"))
        if parts is None:
            offending.append(line.strip())
            continue
        if not parts.group("rule").strip():
            offending.append(line.strip())
            continue
        if len(parts.group("reason").strip()) < REASON_FLOOR:
            offending.append(line.strip())
    return offending


def fixture(tool: str, tail: str) -> str:
    """One line of source carrying a suppression, assembled rather than written.

    The literal never appears in this file. A test file that wrote its own
    fixtures out in full would be refused by the operator it is testing, and the
    repair for that is either an exemption for this path or an elision here. The
    elision is the cheaper of the two: an exemption is a rule with a hole in it
    that somebody has to remember, and this is a string concatenation.
    """
    return f"value = read(path)  # {tool}{tail}\n"


class ASuppressionCarriesItsRuleAndItsReason(unittest.TestCase):
    def refused(self, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "module.py"
            path.write_text(source, encoding="utf-8")
            return bad_suppressions(path.read_text(encoding="utf-8"))

    def test_a_suppression_with_a_rule_and_a_reason_is_accepted(self) -> None:
        self.assertEqual(
            self.refused(
                fixture(
                    "codeql",
                    "[py/path-injection] the path comes from the case id, which "
                    "the schema refuses unless it matches the identifier pattern",
                )
            ),
            [],
        )

    def test_a_suppression_with_no_reason_is_refused(self) -> None:
        self.assertEqual(
            len(self.refused(fixture("codeql", "[py/path-injection]"))), 1
        )

    def test_a_reason_too_short_to_be_one_is_refused(self) -> None:
        self.assertEqual(
            len(self.refused(fixture("codeql", "[py/path-injection] ok"))), 1
        )

    def test_a_suppression_naming_no_rule_is_refused(self) -> None:
        # The blanket suppression. It silences everything at that line, which is
        # the one shape a reader is least able to check.
        self.assertEqual(len(self.refused(fixture("lgtm", ""))), 1)

    def test_a_rule_that_is_only_whitespace_is_refused_even_with_a_reason(self) -> None:
        # The reason is long enough to pass the floor on its own, so the blank
        # rule is the only thing left that can refuse this line. A shorter
        # reason would have this test passing for the other condition's sake
        # and this branch would never be reached, which is how it was measured:
        # the first spelling of this fixture wrote `[]`, which the rule pattern
        # cannot match at all, so it was refused one branch earlier and the
        # branch this test names went on being dead.
        self.assertEqual(
            len(
                self.refused(
                    fixture(
                        "lgtm",
                        "[ ] the schema refuses this path unless it matches the "
                        "identifier pattern",
                    )
                )
            ),
            1,
        )

    def test_the_other_spelling_is_read_too(self) -> None:
        # A tree that refused one spelling and not the other refuses nothing.
        self.assertEqual(len(self.refused(fixture("LGTM", ""))), 1)

    def test_an_ordinary_comment_is_not_a_suppression(self) -> None:
        self.assertEqual(
            self.refused("value = read(path)  # the path is the case id\n"), []
        )

    def test_a_file_with_no_comment_at_all_is_not_a_suppression(self) -> None:
        self.assertEqual(self.refused("value = read(path)\n"), [])


class TheTreeCarriesNoBareSuppression(unittest.TestCase):
    def test_every_python_file_is_read(self) -> None:
        # The floor. A walk that found nothing would otherwise pass as a tree
        # with nothing wrong in it.
        self.assertGreaterEqual(len(python_files(REPO_ROOT)), PYTHON_FILE_FLOOR)

    def test_no_suppression_in_this_tree_lacks_a_rule_or_a_reason(self) -> None:
        offending: dict[str, list[str]] = {}
        for path in python_files(REPO_ROOT):
            found = bad_suppressions(path.read_text(encoding="utf-8"))
            if found:
                offending[str(path.relative_to(REPO_ROOT))] = found
        self.assertEqual(offending, {})


class TheWorkflowThatRunsIt(unittest.TestCase):
    def source(self) -> str:
        return WORKFLOW.read_text(encoding="utf-8")

    def test_the_workflow_exists(self) -> None:
        self.assertTrue(WORKFLOW.is_file(), f"{WORKFLOW} is not in this tree")

    def test_the_check_run_name_is_fixed_by_the_job(self) -> None:
        self.assertIn(f"name: {CHECK_RUN_NAME}", self.source())

    def test_it_runs_on_every_change_and_on_a_schedule(self) -> None:
        source = self.source()
        self.assertIn("pull_request:", source)
        self.assertIn("schedule:", source)
        self.assertIn("cron:", source)

    def test_the_requested_gate_list_carries_the_name(self) -> None:
        self.assertIn(
            f"`{CHECK_RUN_NAME}`", GATE_LIST.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
