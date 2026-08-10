"""Each of the five hygiene conditions, shown to bite.

Issue #93. Every test here is the clean change with one thing changed, so a
condition that had started refusing everything shows up as the clean case
failing rather than as a green. `clean()` is that clean change and is itself
asserted to pass all five.

What is deliberately not tested here is whether the conditions are the right
ones. That is the argument in the issue and in the module docstring, and no test
decides it.

    python -m unittest discover -s tests -k hygiene
"""

from __future__ import annotations

import io
import re
import unittest
from pathlib import Path

import hygiene

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "hygiene.yml"

# An issue body of the shape this tracker actually writes, so the scope reader
# is exercised against the real thing rather than against one line.
ISSUE_93_BODY = """Scope: .github/workflows/

The reference gate requires a hygiene check as a named gate.

### Done when

- The check runs on every change with a fixed name.
"""

MEANS_SENTENCE = (
    "The means is the standard library in the same Python this tree already "
    "carries, because it adds no runtime and no dependency."
)


def clean() -> hygiene.Change:
    """A change that passes all five conditions.

    One added file, inside the scope its issue declares, a body naming the
    means, no result record and no published artefact.
    """
    return hygiene.Change(
        paths=(hygiene.ChangedPath("A", ".github/workflows/hygiene.yml"),),
        messages=("Add the hygiene check, part of #93\n",),
        body=f"Closes #93.\n\n{MEANS_SENTENCE}\n",
        issue_bodies={93: ISSUE_93_BODY},
        known_suffixes=frozenset({".py", ".md", ".yml"}),
    )


def outcome(findings, condition: str) -> str:
    return next(f.outcome for f in findings if f.condition == condition)


def detail(findings, condition: str) -> str:
    return next(f.detail for f in findings if f.condition == condition)


class TheCleanChange(unittest.TestCase):
    """The fixture every other test departs from, asserted rather than assumed."""

    def test_every_condition_passes(self) -> None:
        findings = hygiene.decide(clean())
        self.assertEqual(
            [f.outcome for f in findings], [hygiene.PASSED] * 5, [f.detail for f in findings]
        )

    def test_the_clean_change_is_not_refused(self) -> None:
        self.assertFalse(hygiene.refused(hygiene.decide(clean())))

    def test_all_five_conditions_are_decided_in_a_fixed_order(self) -> None:
        self.assertEqual(
            [f.condition for f in hygiene.decide(clean())],
            [
                hygiene.NAMES_AN_ISSUE,
                hygiene.INSIDE_SCOPE,
                hygiene.MEANS_RECORDED,
                hygiene.RECORD_ADDED_NOT_MODIFIED,
                hygiene.NUMBER_CARRIES_ITS_RECORD,
            ],
        )


class TheChangeNamesAnIssue(unittest.TestCase):
    def test_a_change_naming_nothing_is_refused(self) -> None:
        change = hygiene.Change(
            paths=clean().paths,
            messages=("Add the hygiene check\n",),
            body=MEANS_SENTENCE,
            issue_bodies={},
            known_suffixes=clean().known_suffixes,
        )
        self.assertEqual(
            hygiene.names_an_issue(change).outcome, hygiene.REFUSED
        )

    def test_the_message_alone_is_enough(self) -> None:
        change = hygiene.Change(messages=("part of #93\n",))
        self.assertEqual(hygiene.names_an_issue(change).outcome, hygiene.PASSED)

    def test_the_body_alone_is_enough(self) -> None:
        change = hygiene.Change(body="Closes #93.")
        self.assertEqual(hygiene.names_an_issue(change).outcome, hygiene.PASSED)

    def test_a_bare_number_is_not_an_issue_reference(self) -> None:
        change = hygiene.Change(messages=("part of 93\n",), body="see 93")
        self.assertEqual(hygiene.names_an_issue(change).outcome, hygiene.REFUSED)

    def test_a_hash_with_no_digits_is_not_an_issue_reference(self) -> None:
        change = hygiene.Change(body="a heading marker # and a colour #ffffff")
        self.assertEqual(hygiene.names_an_issue(change).outcome, hygiene.REFUSED)

    def test_every_named_issue_is_reported_and_deduplicated(self) -> None:
        change = hygiene.Change(messages=("#93 and #27\n", "#93 again\n"))
        self.assertEqual(hygiene.referenced_issues(change), (27, 93))


class TheScopeReader(unittest.TestCase):
    """The line every route here reads out of an issue body."""

    def test_a_scope_at_column_zero_is_read(self) -> None:
        self.assertEqual(scopes := hygiene.scopes_in(ISSUE_93_BODY), (".github/workflows/",))
        self.assertEqual(len(scopes), 1)

    def test_an_indented_scope_is_not_read(self) -> None:
        self.assertEqual(hygiene.scopes_in("    Scope: docs/\n"), ())

    def test_a_scope_inside_a_sentence_is_not_read(self) -> None:
        self.assertEqual(hygiene.scopes_in("the Scope: docs/ it declares\n"), ())

    def test_a_scope_value_with_a_space_is_one_scope_and_not_two(self) -> None:
        # The near-miss this refuses by name. Word-splitting the value turns a
        # directory whose name carries a space into two scopes, neither of which
        # matches anything, and the gate then refuses valid work.
        self.assertEqual(
            hygiene.scopes_in("Scope: docs/decision notes/\n"),
            ("docs/decision notes/",),
        )

    def test_a_comma_divides_two_scopes(self) -> None:
        self.assertEqual(
            hygiene.scopes_in("Scope: docs/, tests/\n"), ("docs/", "tests/")
        )

    def test_two_scope_lines_are_both_read(self) -> None:
        self.assertEqual(
            hygiene.scopes_in("Scope: docs/\n\nbody\n\nScope: tests/\n"),
            ("docs/", "tests/"),
        )

    def test_an_empty_scope_value_declares_nothing(self) -> None:
        self.assertEqual(hygiene.scopes_in("Scope:\n"), ())


class TheScopeComparison(unittest.TestCase):
    def test_the_whole_tree_admits_anything(self) -> None:
        self.assertTrue(hygiene.inside("reference/answer.py", "."))

    def test_a_prefix_matches_at_a_separator(self) -> None:
        self.assertTrue(hygiene.inside("docs/decisions/run-record.md", "docs/"))
        self.assertTrue(hygiene.inside("docs/decisions/run-record.md", "docs"))

    def test_a_prefix_does_not_swallow_a_longer_sibling(self) -> None:
        self.assertFalse(hygiene.inside("reporting/page.md", "report"))
        self.assertFalse(hygiene.inside("reporting/page.md", "report/"))

    def test_the_directory_itself_is_inside_its_own_scope(self) -> None:
        self.assertTrue(hygiene.inside("cases", "cases/"))

    def test_a_path_outside_every_scope_is_refused(self) -> None:
        change = hygiene.Change(
            paths=(
                hygiene.ChangedPath("A", ".github/workflows/hygiene.yml"),
                hygiene.ChangedPath("M", "gate.py"),
            ),
            messages=("part of #93\n",),
            issue_bodies={93: ISSUE_93_BODY},
        )
        finding = hygiene.changed_paths_inside_scope(change)
        self.assertEqual(finding.outcome, hygiene.REFUSED)
        self.assertIn("gate.py", finding.detail)

    def test_two_issues_contribute_their_scopes_together(self) -> None:
        change = hygiene.Change(
            paths=(
                hygiene.ChangedPath("A", ".github/workflows/hygiene.yml"),
                hygiene.ChangedPath("M", "docs/requested-gate-checks.md"),
            ),
            messages=("part of #93 and #27\n",),
            issue_bodies={93: ISSUE_93_BODY, 27: "Scope: docs/\n"},
        )
        self.assertEqual(
            hygiene.changed_paths_inside_scope(change).outcome, hygiene.PASSED
        )

    def test_a_departure_the_body_names_is_admitted(self) -> None:
        change = hygiene.Change(
            paths=(
                hygiene.ChangedPath("A", ".github/workflows/hygiene.yml"),
                hygiene.ChangedPath("A", "hygiene.py"),
            ),
            messages=("part of #93\n",),
            body="Closes #93. It also writes hygiene.py at the repository root, "
            "because the declared scope cannot hold a check written in Python.",
            issue_bodies={93: ISSUE_93_BODY},
        )
        finding = hygiene.changed_paths_inside_scope(change)
        self.assertEqual(finding.outcome, hygiene.PASSED)
        # A pass may never read as a change that stayed inside its scope.
        self.assertIn("OUTSIDE IT", finding.detail)
        self.assertIn("hygiene.py", finding.detail)

    def test_a_departure_the_body_does_not_name_is_refused(self) -> None:
        # The same change with the sentence removed. That one difference is the
        # whole of what this condition decides.
        change = hygiene.Change(
            paths=(
                hygiene.ChangedPath("A", ".github/workflows/hygiene.yml"),
                hygiene.ChangedPath("A", "hygiene.py"),
            ),
            messages=("part of #93\n",),
            body="Closes #93.",
            issue_bodies={93: ISSUE_93_BODY},
        )
        finding = hygiene.changed_paths_inside_scope(change)
        self.assertEqual(finding.outcome, hygiene.REFUSED)
        self.assertIn("named nowhere in the body", finding.detail)

    def test_one_named_departure_does_not_admit_the_others(self) -> None:
        change = hygiene.Change(
            paths=(
                hygiene.ChangedPath("A", "hygiene.py"),
                hygiene.ChangedPath("M", "gate.py"),
            ),
            messages=("part of #93\n",),
            body="Closes #93. It writes hygiene.py at the repository root.",
            issue_bodies={93: ISSUE_93_BODY},
        )
        finding = hygiene.changed_paths_inside_scope(change)
        self.assertEqual(finding.outcome, hygiene.REFUSED)
        self.assertIn("gate.py", finding.detail)
        self.assertNotIn("hygiene.py", finding.detail.split(":")[-1])

    def test_a_whole_tree_scope_decides_nothing_and_says_so(self) -> None:
        # Found by running this check on its own pull request. The body quoted
        # the gate's output, which names #19 and #24, both of which declare the
        # whole tree, and the comparison passed having admitted every path for a
        # reason that had nothing to do with the change.
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "gate.py"),),
            messages=("part of #93\n",),
            body="Closes #93. The formatter part is #19's.",
            issue_bodies={93: ISSUE_93_BODY, 19: "Scope: .\n"},
        )
        finding = hygiene.changed_paths_inside_scope(change)
        self.assertEqual(finding.outcome, hygiene.NOT_DECIDED)
        self.assertIn("DISTINGUISHES NOTHING", finding.detail)
        self.assertIn("#19", finding.detail)

    def test_the_same_change_without_the_whole_tree_scope_is_decided(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "gate.py"),),
            messages=("part of #93\n",),
            body="Closes #93. The formatter part is #19's.",
            issue_bodies={93: ISSUE_93_BODY, 19: "Scope: docs/\n"},
        )
        self.assertEqual(
            hygiene.changed_paths_inside_scope(change).outcome, hygiene.REFUSED
        )

    def test_a_change_naming_no_issue_leaves_the_comparison_undecided(self) -> None:
        change = hygiene.Change(paths=clean().paths)
        self.assertEqual(
            hygiene.changed_paths_inside_scope(change).outcome, hygiene.NOT_DECIDED
        )

    def test_an_issue_declaring_no_scope_leaves_the_comparison_undecided(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "gate.py"),),
            messages=("part of #93\n",),
            issue_bodies={93: "No scope line anywhere in this body.\n"},
        )
        finding = hygiene.changed_paths_inside_scope(change)
        self.assertEqual(finding.outcome, hygiene.NOT_DECIDED)
        # The requirement is that it says so rather than passing quietly.
        self.assertIn("NOT MADE", finding.detail)

    def test_an_unreadable_issue_is_absent_rather_than_scopeless(self) -> None:
        # The body could not be read, so nothing is known about its scope. The
        # run says the comparison was not made instead of passing on a scope it
        # never saw.
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "gate.py"),),
            messages=("part of #93\n",),
            issue_bodies={},
        )
        finding = hygiene.changed_paths_inside_scope(change)
        self.assertEqual(finding.outcome, hygiene.NOT_DECIDED)
        self.assertIn("could not be read", finding.detail)

    def test_a_partially_read_set_says_how_many_were_missed(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("A", ".github/workflows/hygiene.yml"),),
            messages=("part of #93 and #27\n",),
            issue_bodies={93: ISSUE_93_BODY},
        )
        finding = hygiene.changed_paths_inside_scope(change)
        self.assertEqual(finding.outcome, hygiene.PASSED)
        self.assertIn("could not be read", finding.detail)


class TheMeansIsRecorded(unittest.TestCase):
    def test_a_change_choosing_no_means_needs_no_sentence(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "reference/answer.py"),),
            messages=("part of #47\n",),
            body="Closes #47.",
            known_suffixes=frozenset({".py"}),
        )
        self.assertEqual(hygiene.means_recorded(change).outcome, hygiene.PASSED)

    def test_an_added_dependency_manifest_needs_one(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("A", "pyproject.toml"),),
            body="Closes #19.",
            known_suffixes=frozenset({".py", ".md", ".yml", ".toml"}),
        )
        self.assertEqual(hygiene.means_recorded(change).outcome, hygiene.REFUSED)

    def test_the_same_manifest_with_the_sentence_passes(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("A", "pyproject.toml"),),
            body=f"Closes #19.\n\n{MEANS_SENTENCE}\n",
            known_suffixes=frozenset({".py", ".md", ".yml", ".toml"}),
        )
        self.assertEqual(hygiene.means_recorded(change).outcome, hygiene.PASSED)

    def test_an_edited_manifest_is_a_version_and_not_a_means(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "pyproject.toml"),),
            body="Closes #19.",
            known_suffixes=frozenset({".py", ".md", ".yml", ".toml"}),
        )
        self.assertEqual(hygiene.means_recorded(change).outcome, hygiene.PASSED)

    def test_a_suffix_the_tree_did_not_carry_needs_one(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("A", "reference/kovalevskaya.rs"),),
            body="Closes #45.",
            known_suffixes=frozenset({".py", ".md", ".yml"}),
        )
        finding = hygiene.means_recorded(change)
        self.assertEqual(finding.outcome, hygiene.REFUSED)
        self.assertIn(".rs", finding.detail)

    def test_a_suffix_the_tree_already_carries_does_not(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("A", "reference/kovalevskaya.py"),),
            body="Closes #45.",
            known_suffixes=frozenset({".py", ".md", ".yml"}),
        )
        self.assertEqual(hygiene.means_recorded(change).outcome, hygiene.PASSED)

    def test_an_added_workflow_needs_one(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("A", ".github/workflows/codeql.yml"),),
            body="Closes #87.",
            known_suffixes=frozenset({".py", ".md", ".yml"}),
        )
        self.assertEqual(hygiene.means_recorded(change).outcome, hygiene.REFUSED)

    def test_a_short_line_carrying_the_word_is_not_a_sentence(self) -> None:
        # The near-miss. A body that happens to contain the word `means` says
        # nothing about which means was chosen, and the floor is what separates
        # the two without asking anybody to judge the sentence.
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("A", "pyproject.toml"),),
            body="Closes #19.\n\nby any means.\n",
            known_suffixes=frozenset({".toml"}),
        )
        self.assertEqual(hygiene.means_recorded(change).outcome, hygiene.REFUSED)

    def test_the_floor_is_the_only_thing_length_decides(self) -> None:
        self.assertEqual(len("by any means.") < hygiene.MEANS_SENTENCE_FLOOR, True)
        self.assertEqual(len(MEANS_SENTENCE) >= hygiene.MEANS_SENTENCE_FLOOR, True)


class ARecordIsAddedAndNeverModified(unittest.TestCase):
    def test_a_change_with_no_record_passes(self) -> None:
        self.assertEqual(
            hygiene.record_added_not_modified(clean()).outcome, hygiene.PASSED
        )

    def test_an_added_record_passes(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("A", "results/mujoco-rattleback-01.toml"),)
        )
        self.assertEqual(
            hygiene.record_added_not_modified(change).outcome, hygiene.PASSED
        )

    def test_a_modified_record_is_refused(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "results/mujoco-rattleback-01.toml"),)
        )
        finding = hygiene.record_added_not_modified(change)
        self.assertEqual(finding.outcome, hygiene.REFUSED)
        self.assertIn("mujoco-rattleback-01.toml", finding.detail)

    def test_a_deleted_record_is_refused(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("D", "results/mujoco-rattleback-01.toml"),)
        )
        self.assertEqual(
            hygiene.record_added_not_modified(change).outcome, hygiene.REFUSED
        )

    def test_a_renamed_record_is_refused(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("R", "results/renamed.toml"),)
        )
        self.assertEqual(
            hygiene.record_added_not_modified(change).outcome, hygiene.REFUSED
        )

    def test_the_directory_note_is_not_a_record(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "results/README.md"),)
        )
        self.assertEqual(
            hygiene.record_added_not_modified(change).outcome, hygiene.PASSED
        )


class APublishedNumberCarriesItsRecord(unittest.TestCase):
    def test_a_change_touching_no_artefact_passes(self) -> None:
        self.assertEqual(
            hygiene.published_number_carries_its_record(clean()).outcome,
            hygiene.PASSED,
        )

    def test_an_artefact_moving_alone_is_refused(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "report/report-card.md"),)
        )
        finding = hygiene.published_number_carries_its_record(change)
        self.assertEqual(finding.outcome, hygiene.REFUSED)
        self.assertIn("report-card.md", finding.detail)

    def test_an_artefact_moving_with_a_new_record_passes(self) -> None:
        change = hygiene.Change(
            paths=(
                hygiene.ChangedPath("M", "report/report-card.md"),
                hygiene.ChangedPath("A", "results/mujoco-rattleback-02.toml"),
            )
        )
        self.assertEqual(
            hygiene.published_number_carries_its_record(change).outcome,
            hygiene.PASSED,
        )

    def test_a_modified_record_does_not_stand_in_for_a_new_one(self) -> None:
        change = hygiene.Change(
            paths=(
                hygiene.ChangedPath("M", "report/report-card.md"),
                hygiene.ChangedPath("M", "results/mujoco-rattleback-01.toml"),
            )
        )
        self.assertEqual(
            hygiene.published_number_carries_its_record(change).outcome,
            hygiene.REFUSED,
        )

    def test_the_assembly_is_code_and_not_a_number(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "report/assemble.py"),)
        )
        self.assertEqual(
            hygiene.published_number_carries_its_record(change).outcome,
            hygiene.PASSED,
        )

    def test_the_directory_note_is_not_a_number(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "report/README.md"),)
        )
        self.assertEqual(
            hygiene.published_number_carries_its_record(change).outcome,
            hygiene.PASSED,
        )


class TheRunReportsRatherThanStopping(unittest.TestCase):
    def test_two_refusals_are_both_reported(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "results/one.toml"),),
            messages=("no issue here\n",),
        )
        findings = hygiene.decide(change)
        self.assertEqual(outcome(findings, hygiene.NAMES_AN_ISSUE), hygiene.REFUSED)
        self.assertEqual(
            outcome(findings, hygiene.RECORD_ADDED_NOT_MODIFIED), hygiene.REFUSED
        )

    def test_a_refusal_fails_the_run(self) -> None:
        change = hygiene.Change(messages=("no issue here\n",))
        self.assertTrue(hygiene.refused(hygiene.decide(change)))

    def test_an_undecided_condition_does_not_fail_the_run(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "gate.py"),),
            messages=("part of #93\n",),
            issue_bodies={93: "no scope line here\n"},
        )
        findings = hygiene.decide(change)
        self.assertEqual(outcome(findings, hygiene.INSIDE_SCOPE), hygiene.NOT_DECIDED)
        self.assertFalse(hygiene.refused(findings))


class TheOutput(unittest.TestCase):
    """A comparison that could not be made says so, in the output itself."""

    def rendered(self, change: hygiene.Change) -> str:
        out = io.StringIO()
        hygiene.report(hygiene.decide(change), out)
        return out.getvalue()

    def test_every_condition_appears_with_its_outcome(self) -> None:
        text = self.rendered(clean())
        for condition in (
            hygiene.NAMES_AN_ISSUE,
            hygiene.INSIDE_SCOPE,
            hygiene.MEANS_RECORDED,
            hygiene.RECORD_ADDED_NOT_MODIFIED,
            hygiene.NUMBER_CARRIES_ITS_RECORD,
        ):
            self.assertIn(condition, text)

    def test_an_undecided_condition_is_counted_in_the_summary(self) -> None:
        change = hygiene.Change(
            paths=(hygiene.ChangedPath("M", "gate.py"),),
            messages=("part of #93\n",),
            issue_bodies={93: "no scope line here\n"},
        )
        text = self.rendered(change)
        self.assertIn(hygiene.NOT_DECIDED, text)
        self.assertIn("1 not decided", text)

    def test_the_bound_is_printed_on_every_run(self) -> None:
        self.assertIn(
            "merely touches the same paths", self.rendered(clean())
        )


class TheWorkflowThatRunsIt(unittest.TestCase):
    """The workflow is a wrapper and carries no logic of its own.

    The same rule `tests/test_gate_workflow.py` holds over the gate workflow,
    for the same reason: two procedures meant to be one procedure drift, and the
    drift is found by a merge that was green on a laptop and reds on the server.
    """

    def source(self) -> str:
        return WORKFLOW.read_text(encoding="utf-8")

    def test_the_workflow_exists(self) -> None:
        self.assertTrue(WORKFLOW.is_file(), f"{WORKFLOW} is not in this tree")

    def test_the_check_run_name_is_the_one_the_gate_list_asks_for(self) -> None:
        # A ruleset matches a required check by its literal name, so this string
        # is the thing being required and a rename removes the check from the
        # gate. docs/requested-gate-checks.md carries the same name.
        self.assertIn("name: Deterministic PR-hygiene checks", self.source())

    def test_it_runs_the_module_and_nothing_else(self) -> None:
        commands = [
            line.split("run:", 1)[1].strip()
            for line in self.source().splitlines()
            if re.match(r"^\s*run:", line)
        ]
        self.assertEqual(commands, ["python -m hygiene"])

    def test_it_asks_for_no_write_permission(self) -> None:
        self.assertNotIn("write", self.source())

    def test_the_requested_gate_list_carries_the_name(self) -> None:
        document = (REPO_ROOT / "docs" / "requested-gate-checks.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Deterministic PR-hygiene checks", document)


if __name__ == "__main__":
    unittest.main()
