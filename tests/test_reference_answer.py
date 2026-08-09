"""A reference value cannot be constructed without its bound, shown here.

Issue #49. `reference/answer.py` carries the value and the trust statement as one
thing. This file is where each refusal is tripped, and every fixture below is a
valid reference answer with ONE thing changed, so what a test proves is that thing
and not the rest of the shape.

Two refusals are worth reading before the rest, because they are the ones the issue
is actually about.

Omitting the trust statement is a `TypeError` from the interpreter, before any code
in that module runs. That is the structural half: there is no constructor that
takes a value without a bound, so the comparison code cannot be written without
one.

A bound equal to the case's tolerance produces the `bounded` cell state and not
`measured`. That is the one-character version of this whole issue: at equality the
reference's own error is the size of the tolerance, so what is known is an interval,
and a `>` where a `>=` belongs publishes it as a value.

    python -m unittest discover -s tests -k reference_answer
"""

from __future__ import annotations

import unittest
from pathlib import Path

import casefile
from reference import answer as reference_answer
from reference.answer import (
    Bound,
    Comparison,
    ReferenceAnswer,
    ReferenceRefused,
    Stability,
    Unbounded,
    compare,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = "cases"

# How each case in `cases/` obtains its reference answer, one entry per case file,
# keyed by the case's own id.
#
# An entry names where the answer comes from, so a case whose reference is
# unbounded is a case somebody wrote that down for. #49's third done-when is that
# no case in this repository uses an unbounded reference without a note saying
# why, and the note has two halves: `Unbounded` cannot be constructed without a
# reason, which is refused in `reference/answer.py`, and the case has to be
# accounted for at all, which is this register.
#
# EMPTY IS NOT A FINDING TODAY. There is no case file in this tree:
#
#     git ls-files 'cases/*.toml' | wc -l
#     0
#
# so no case uses a reference of any kind and none could. The check below is what
# makes that state expire rather than persist as an unread note: it fails closed in
# both directions, so the day a case lands without an entry the suite reds, and an
# entry naming no case reds too.
REFERENCE_ANSWERS: dict[str, str] = {}


def case_ids(root: Path) -> list[str]:
    """The id of every case file in the tree, read through the case reader."""
    found = []
    for path in sorted((root / CASES_DIR).rglob("*.toml")):
        found.append(casefile.read(path).id)
    return sorted(found)


def register_violations(ids: list[str], register: dict[str, str]) -> list[str]:
    """Every way the register and a list of case ids disagree.

    Empty is the only passing verdict, and it fails closed in both directions: a
    case with no entry is a reference nobody accounted for, and an entry naming no
    case is a note about something that is no longer here, which is the state a
    register rots into.

    It takes the ids rather than reading them, because the tree it will read has no
    cases in it and an operator that cannot be driven is an operator nobody proved.
    `tree_violations` is the reading.
    """
    violations: list[str] = []
    for identifier in sorted(ids):
        if identifier not in register:
            violations.append(
                f"the case {identifier!r} exists and the register says nothing "
                f"about where its reference answer comes from"
            )
        elif not register[identifier].strip():
            violations.append(
                f"the register carries an empty entry for the case {identifier!r}"
            )
    for identifier in sorted(register):
        if identifier not in ids:
            violations.append(
                f"the register carries an entry for the case {identifier!r}, and "
                f"there is no such case in {CASES_DIR}/"
            )
    return sorted(violations)


def tree_violations(root: Path, register: dict[str, str]) -> list[str]:
    """`register_violations` against the cases this tree actually holds."""
    return register_violations(case_ids(root), register)


def a_bound(**changed: object) -> Bound:
    """A bound nothing here refuses, with the changes a test asks for applied."""
    fields: dict[str, object] = {
        "value": 1e-9,
        "units": "radians",
        "routes": ("the closed form", "the same method at higher precision"),
    }
    fields.update(changed)
    return Bound(**fields)  # type: ignore[arg-type]


def a_stability(**changed: object) -> Stability:
    fields: dict[str, object] = {
        "outcome": "the body reversed twice, both times towards the same sense",
        "ladder": (1e-4, 5e-5, 2.5e-5),
        "perturbations": 8,
    }
    fields.update(changed)
    return Stability(**fields)  # type: ignore[arg-type]


def an_answer(**changed: object) -> ReferenceAnswer:
    fields: dict[str, object] = {
        "case_id": "a-case",
        "case_class": "integrable",
        "value": 0.25,
        "trust": a_bound(),
    }
    fields.update(changed)
    return ReferenceAnswer(**fields)  # type: ignore[arg-type]


def a_qualitative_answer(**changed: object) -> ReferenceAnswer:
    fields: dict[str, object] = {
        "case_id": "the-rattleback",
        "case_class": "qualitative",
        "value": "the body reversed twice",
        "trust": a_stability(),
    }
    fields.update(changed)
    return ReferenceAnswer(**fields)  # type: ignore[arg-type]


class TheValidAnswersAreAccepted(unittest.TestCase):
    """The near-misses. If any of these were refused every test below would pass
    for the wrong reason."""

    def test_a_bounded_numeric_answer_is_accepted(self) -> None:
        self.assertTrue(an_answer().is_bounded)

    def test_a_qualitative_answer_with_a_stability_statement_is_accepted(self) -> None:
        self.assertTrue(a_qualitative_answer().is_bounded)

    def test_an_unbounded_answer_with_a_reason_is_accepted(self) -> None:
        # A legitimate state rather than a failure. What it costs is the mark on
        # every comparison against it, which is the point of admitting it.
        found = an_answer(trust=Unbounded(why="no second route exists for this case"))
        self.assertFalse(found.is_bounded)

    def test_every_class_in_the_vocabulary_can_carry_an_answer(self) -> None:
        # Without this, a rule written for one class could refuse another and the
        # refusal would look like a property of the reference rather than a defect.
        for name in casefile.CLASSES:
            with self.subTest(case_class=name):
                if name == reference_answer.QUALITATIVE:
                    self.assertTrue(a_qualitative_answer(case_class=name).is_bounded)
                else:
                    self.assertTrue(an_answer(case_class=name).is_bounded)


class TheTrustStatementCannotBeOmitted(unittest.TestCase):
    def test_a_value_with_no_trust_statement_cannot_be_constructed(self) -> None:
        # The structural half of this issue. The interpreter refuses it before any
        # validation runs, so there is no code path that produces a reference value
        # with nothing said about it.
        with self.assertRaises(TypeError):
            ReferenceAnswer(  # type: ignore[call-arg]
                case_id="a-case", case_class="integrable", value=0.25
            )

    def test_a_trust_statement_of_none_is_refused(self) -> None:
        # The other spelling of the same mistake: the argument supplied and filled
        # with nothing, which the interpreter accepts and this refuses.
        with self.assertRaises(ReferenceRefused) as refusal:
            an_answer(trust=None)
        self.assertIn("NoneType", str(refusal.exception))

    def test_a_bare_number_as_a_trust_statement_is_refused(self) -> None:
        # A bound with no units and no route, which is the shape somebody reaches
        # for when the field is in the way.
        with self.assertRaises(ReferenceRefused):
            an_answer(trust=1e-9)


class TheBoundIsRefusedWhenItSaysNothing(unittest.TestCase):
    def assertRefused(self, fragment: str, **changed: object) -> None:
        with self.assertRaises(ReferenceRefused) as refusal:
            a_bound(**changed)
        self.assertIn(fragment, str(refusal.exception))

    def test_a_bound_of_zero_is_refused(self) -> None:
        self.assertRefused("claims the reference is exact", value=0.0)

    def test_a_negative_bound_is_refused(self) -> None:
        self.assertRefused("claims the reference is exact", value=-1e-9)

    def test_an_infinite_bound_is_refused(self) -> None:
        # An infinite bound is true of every reference and says nothing. The state
        # for a reference nobody could bound is `Unbounded`, which carries a reason.
        self.assertRefused("finite float", value=float("inf"))

    def test_a_bound_that_is_not_a_number_is_refused(self) -> None:
        self.assertRefused("finite float", value=float("nan"))

    def test_an_integer_bound_is_refused(self) -> None:
        # Refused rather than widened, which is the rule the case reader applies to
        # every number it reads, for the same reason.
        self.assertRefused("finite float", value=1)

    def test_a_bound_with_no_units_is_refused(self) -> None:
        self.assertRefused("no units", units="   ")

    def test_a_bound_naming_no_route_is_refused(self) -> None:
        self.assertRefused("at least one route", routes=())

    def test_a_bound_whose_routes_are_not_a_tuple_is_refused(self) -> None:
        # A string is iterable, so a single route written without its comma would
        # otherwise be read as a route per character.
        self.assertRefused("at least one route", routes="the closed form")

    def test_a_bound_with_an_empty_route_is_refused(self) -> None:
        self.assertRefused("non-empty statement", routes=("the closed form", " "))


class TheStabilityStatementIsRefusedWhenItSaysNothing(unittest.TestCase):
    def assertRefused(self, fragment: str, **changed: object) -> None:
        with self.assertRaises(ReferenceRefused) as refusal:
            a_stability(**changed)
        self.assertIn(fragment, str(refusal.exception))

    def test_a_ladder_of_one_rung_is_refused(self) -> None:
        self.assertRefused("moved across nothing", ladder=(1e-4,))

    def test_a_ladder_whose_rungs_are_all_the_same_is_refused(self) -> None:
        # The one-character version: a ladder written with the same step three
        # times looks like three rungs and is one run repeated.
        self.assertRefused("moved across nothing", ladder=(1e-4, 1e-4, 1e-4))

    def test_a_ladder_with_a_non_positive_rung_is_refused(self) -> None:
        self.assertRefused("finite positive floats", ladder=(1e-4, 0.0))

    def test_no_perturbation_is_refused(self) -> None:
        self.assertRefused("stability under a perturbation", perturbations=0)

    def test_a_perturbation_count_that_is_a_boolean_is_refused(self) -> None:
        self.assertRefused("whole number", perturbations=True)

    def test_a_stability_statement_with_no_outcome_is_refused(self) -> None:
        self.assertRefused("names the outcome", outcome="")


class TheUnboundedStateCarriesItsReason(unittest.TestCase):
    def test_an_unbounded_reference_with_no_reason_is_refused(self) -> None:
        # Without this the unbounded state is a way to opt out of the whole issue
        # by writing one word, and an unbounded reference with no reason is
        # indistinguishable from a bound somebody forgot.
        with self.assertRaises(ReferenceRefused) as refusal:
            Unbounded(why="  ")
        self.assertIn("no bound could be produced", str(refusal.exception))


class TheTrustStatementBelongsToTheClass(unittest.TestCase):
    def test_a_qualitative_answer_may_not_carry_a_numeric_bound(self) -> None:
        # The clause the decision adds to this issue by name: a case with no
        # continuous error must not pass by having nothing to bound, and the way it
        # would is by being handed a number about something else.
        with self.assertRaises(ReferenceRefused) as refusal:
            a_qualitative_answer(trust=a_bound())
        self.assertIn("no continuous error", str(refusal.exception))

    def test_a_numeric_answer_may_not_carry_a_stability_statement(self) -> None:
        with self.assertRaises(ReferenceRefused) as refusal:
            an_answer(trust=a_stability())
        self.assertIn("not a bound on a", str(refusal.exception))

    def test_a_qualitative_value_that_is_a_number_is_refused(self) -> None:
        with self.assertRaises(ReferenceRefused) as refusal:
            a_qualitative_answer(value=1.0)
        self.assertIn("is an outcome", str(refusal.exception))

    def test_a_numeric_value_that_is_an_outcome_is_refused(self) -> None:
        with self.assertRaises(ReferenceRefused) as refusal:
            an_answer(value="the body reversed")
        self.assertIn("finite float", str(refusal.exception))

    def test_a_class_outside_the_vocabulary_is_refused(self) -> None:
        with self.assertRaises(ReferenceRefused) as refusal:
            an_answer(case_class="approximately-integrable")
        self.assertIn("the vocabulary is", str(refusal.exception))

    def test_an_answer_naming_no_case_is_refused(self) -> None:
        with self.assertRaises(ReferenceRefused):
            an_answer(case_id=" ")


class TheComparisonCarriesTheBound(unittest.TestCase):
    def test_a_bound_below_the_tolerance_is_measured(self) -> None:
        found = compare(an_answer(), tolerance=1e-6)
        self.assertIsInstance(found, Comparison)
        self.assertEqual(found.state, reference_answer.MEASURED)
        self.assertFalse(found.reference_unbounded)

    def test_a_bound_equal_to_the_tolerance_is_bounded(self) -> None:
        # The one-character mistake. At equality the reference's own error is the
        # size of the tolerance, so nothing about the engine has been measured, and
        # a `>` here would publish an interval as a value.
        found = compare(an_answer(), tolerance=1e-9)
        self.assertEqual(found.state, reference_answer.BOUNDED)
        self.assertFalse(found.reference_unbounded)
        self.assertIn("an interval rather than a value", found.why)

    def test_a_bound_above_the_tolerance_is_bounded(self) -> None:
        found = compare(an_answer(), tolerance=1e-12)
        self.assertEqual(found.state, reference_answer.BOUNDED)

    def test_an_unbounded_reference_marks_the_comparison(self) -> None:
        # The mark #49 asks to survive. It is a field of its own rather than
        # something read off the state, because a bounded cell from a bound that
        # was too large and one from a reference nobody could bound are different
        # statements.
        found = compare(
            an_answer(trust=Unbounded(why="no independent route exists here")),
            tolerance=1e-6,
        )
        self.assertEqual(found.state, reference_answer.BOUNDED)
        self.assertTrue(found.reference_unbounded)
        self.assertIn("no independent route exists here", found.why)

    def test_a_stable_qualitative_answer_is_measured(self) -> None:
        found = compare(a_qualitative_answer(), tolerance=None)
        self.assertEqual(found.state, reference_answer.MEASURED)
        self.assertFalse(found.reference_unbounded)

    def test_an_unbounded_qualitative_answer_marks_the_comparison(self) -> None:
        found = compare(
            a_qualitative_answer(
                trust=Unbounded(why="the outcome moved on the ladder")
            ),
            tolerance=None,
        )
        self.assertEqual(found.state, reference_answer.BOUNDED)
        self.assertTrue(found.reference_unbounded)

    def test_a_numeric_comparison_with_no_tolerance_is_refused(self) -> None:
        # Fails closed. Without this a caller with no tolerance to hand gets a
        # comparison that read no tolerance at all.
        with self.assertRaises(ReferenceRefused) as refusal:
            compare(an_answer(), tolerance=None)
        self.assertIn("a comparison nobody made", str(refusal.exception))

    def test_a_qualitative_comparison_with_a_tolerance_is_refused(self) -> None:
        with self.assertRaises(ReferenceRefused) as refusal:
            compare(a_qualitative_answer(), tolerance=1e-6)
        self.assertIn("a number about something else", str(refusal.exception))

    def test_a_tolerance_of_zero_is_refused(self) -> None:
        with self.assertRaises(ReferenceRefused):
            compare(an_answer(), tolerance=0.0)

    def test_a_comparison_against_something_else_is_refused(self) -> None:
        with self.assertRaises(ReferenceRefused) as refusal:
            compare(a_bound(), tolerance=1e-6)  # type: ignore[arg-type]
        self.assertIn("against a ReferenceAnswer", str(refusal.exception))


class TheRegisterAndTheCasesAgree(unittest.TestCase):
    def test_this_repository_has_no_register_violations(self) -> None:
        self.assertEqual(tree_violations(REPO_ROOT, REFERENCE_ANSWERS), [])

    def test_there_is_still_no_case_using_a_reference(self) -> None:
        # The trigger. Every green above is over reference answers written in this
        # file, and no case in this repository uses a reference of any kind because
        # there is no case. The day the first one lands, either its reference is
        # accounted for in the register above or the suite reds naming it.
        self.assertEqual(case_ids(REPO_ROOT), [])
        self.assertEqual(REFERENCE_ANSWERS, {})

    def test_a_case_with_no_entry_is_refused(self) -> None:
        # Driven with the reading supplied, because the tree it will read holds no
        # cases. What these four prove is the operator; that the tree is empty is
        # the test above.
        self.assertEqual(
            register_violations(["a-case"], {}),
            [
                "the case 'a-case' exists and the register says nothing about "
                "where its reference answer comes from"
            ],
        )

    def test_an_entry_naming_no_case_is_refused(self) -> None:
        self.assertEqual(
            register_violations([], {"a-case": "the closed form"}),
            [
                "the register carries an entry for the case 'a-case', and there "
                "is no such case in cases/"
            ],
        )

    def test_an_empty_entry_is_refused(self) -> None:
        self.assertEqual(
            register_violations(["a-case"], {"a-case": "  "}),
            ["the register carries an empty entry for the case 'a-case'"],
        )

    def test_a_case_with_an_entry_is_accepted(self) -> None:
        self.assertEqual(
            register_violations(["a-case"], {"a-case": "the closed form of #44"}),
            [],
        )


if __name__ == "__main__":
    unittest.main()
