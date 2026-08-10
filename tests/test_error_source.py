"""The conclusion drawn from a resolution ladder, against curves of each kind.

Issue #57. The estimator is fed error curves this file builds, so the answer is
known before it is asked for. Three kinds: one that falls at a stated order all
the way down, one that falls and then stops, and one whose slope sits between the
two bands where neither verdict is available.

The pair worth reading is the one that separates the finding from the study's own
limits. The same floored curve reaches two different verdicts depending only on
what the caller declares the study contributes: with the floor undeclared it is a
finding about the engine, and with the floor declared as the reference's bound it
is converging, because what stopped falling was never the engine's.

    python -m unittest discover -s tests -k error_source
"""

from __future__ import annotations

import unittest

from metrics.error_source import (
    CONVERGING,
    FLOORED,
    ORDER_A_FLOOR_HAS_FALLEN_BELOW,
    ORDER_CONVERGENCE_HOLDS,
    RUNGS_FLOOR,
    UNDECIDED,
    VERDICTS,
    Conclusion,
    Excluded,
    LadderRefused,
    Rung,
    conclude,
)

# The steps every ladder below is built on, coarsest first, each half the last.
STEPS = (0.1, 0.05, 0.025, 0.0125, 0.00625, 0.003125, 0.0015625, 0.00078125)

# The curve the converging ladder is built from: a second-order method with a
# scale of three, which is what the fit has to return.
SCALE = 3.0
ORDER = 2.0


def ladder(floor: float = 0.0, order: float = ORDER) -> tuple[Rung, ...]:
    """`SCALE * step ** order + floor`, at every step above."""
    return tuple(Rung(step, SCALE * step**order + floor) for step in STEPS)


# A second term that is negligible at the coarse end and dominant at the fine
# end, at an order between the two bands. It is what a curve looks like when it
# is flattening and has not flattened: not a floor, because it is still falling,
# and not convergence, because it has stopped falling at a useful rate.
SHALLOW_SCALE = 1e-3
SHALLOW_ORDER = 0.375


def flattening_ladder() -> tuple[Rung, ...]:
    return tuple(
        Rung(step, SCALE * step**ORDER + SHALLOW_SCALE * step**SHALLOW_ORDER)
        for step in STEPS
    )


class TheVerdictsAreThreeAndNoMore(unittest.TestCase):
    def test_there_are_exactly_three(self) -> None:
        # A fourth value is how a floor becomes a softer word for one, and it is
        # the thing this issue's third item is about.
        self.assertEqual(len(VERDICTS), 3)
        self.assertEqual(set(VERDICTS), {CONVERGING, FLOORED, UNDECIDED})

    def test_a_verdict_outside_the_three_is_refused(self) -> None:
        with self.assertRaises(LadderRefused) as refused:
            Conclusion(
                verdict="mostly converging",
                reason="a fourth word",
                fitted_over=(0.1, 0.01),
                rungs_used=4,
                order=2.0,
                scale=3.0,
            )
        self.assertIn("fourth word", str(refused.exception))

    def test_a_decided_conclusion_carries_the_range_it_was_fitted_over(self) -> None:
        for missing in ({"fitted_over": None}, {"rungs_used": 2}):
            with self.subTest(missing=missing):
                arguments = dict(
                    verdict=CONVERGING,
                    reason="fitted",
                    fitted_over=(0.1, 0.01),
                    rungs_used=4,
                    order=2.0,
                    scale=3.0,
                )
                arguments.update(missing)
                with self.assertRaises(LadderRefused):
                    Conclusion(**arguments)

    def test_a_decided_conclusion_carries_the_fitted_parameters(self) -> None:
        with self.assertRaises(LadderRefused):
            Conclusion(
                verdict=FLOORED,
                reason="fitted",
                fitted_over=(0.1, 0.01),
                rungs_used=4,
                order=None,
                scale=3.0,
            )

    def test_an_undecided_conclusion_needs_neither(self) -> None:
        # It is the state where there is nothing to carry, and requiring a fit
        # there would make undecided unreachable, which is the value this issue
        # says has to be produced rather than avoided.
        found = Conclusion(
            verdict=UNDECIDED,
            reason="two rungs clear of the exclusions",
            fitted_over=None,
            rungs_used=2,
        )
        self.assertEqual(found.verdict, UNDECIDED)

    def test_a_conclusion_with_no_reason_is_refused(self) -> None:
        with self.assertRaises(LadderRefused):
            Conclusion(
                verdict=UNDECIDED, reason="   ", fitted_over=None, rungs_used=0
            )


class TheLadderIsRefusedRatherThanRead(unittest.TestCase):
    def test_a_ladder_with_too_few_rungs_is_refused(self) -> None:
        with self.assertRaises(LadderRefused) as refused:
            conclude(ladder()[: RUNGS_FLOOR - 1])
        self.assertIn(str(RUNGS_FLOOR), str(refused.exception))

    def test_the_shortest_admissible_ladder_is_accepted(self) -> None:
        # The neighbour of the refusal above, so the refusal is at the floor
        # rather than somewhere near it.
        self.assertEqual(conclude(ladder()[:RUNGS_FLOOR]).verdict, CONVERGING)

    def test_two_rungs_at_one_step_are_refused(self) -> None:
        doubled = ladder()[:-1] + (Rung(STEPS[0], 1.0),)
        with self.assertRaises(LadderRefused) as refused:
            conclude(doubled)
        self.assertIn("same step", str(refused.exception))

    def test_a_step_of_zero_or_less_is_refused(self) -> None:
        for step in (0.0, -0.1, float("nan"), float("inf")):
            with self.subTest(step=step):
                with self.assertRaises(LadderRefused):
                    Rung(step, 1.0)

    def test_a_negative_error_is_refused(self) -> None:
        for error in (-1e-9, float("nan"), float("inf"), "1e-9"):
            with self.subTest(error=error):
                with self.assertRaises(LadderRefused):
                    Rung(0.1, error)

    def test_a_negative_excluded_contribution_is_refused(self) -> None:
        with self.assertRaises(LadderRefused):
            Excluded(rounding=-1e-12)
        with self.assertRaises(LadderRefused):
            Excluded(reference=float("nan"))

    def test_a_margin_of_one_or_less_is_refused(self) -> None:
        # A margin of one admits a rung level with the study's own contribution,
        # which carries no statement about the engine in either direction.
        with self.assertRaises(LadderRefused):
            conclude(ladder(), Excluded(reference=1e-9), margin=1.0)

    def test_the_rungs_may_arrive_in_any_order(self) -> None:
        # A study that wrote its rungs finest first is a study written the other
        # way round, not a different ladder.
        forwards = conclude(ladder())
        backwards = conclude(tuple(reversed(ladder())))
        self.assertEqual(forwards.verdict, backwards.verdict)
        self.assertAlmostEqual(forwards.order, backwards.order, places=12)
        self.assertEqual(forwards.fitted_over, backwards.fitted_over)


class TheConvergingCurveIsRecognised(unittest.TestCase):
    def setUp(self) -> None:
        self.found = conclude(ladder())

    def test_the_verdict_is_converging(self) -> None:
        self.assertEqual(self.found.verdict, CONVERGING)

    def test_the_fitted_order_is_the_one_the_curve_was_built_with(self) -> None:
        self.assertAlmostEqual(self.found.order, ORDER, places=9)

    def test_the_fitted_scale_is_the_one_the_curve_was_built_with(self) -> None:
        self.assertAlmostEqual(self.found.scale, SCALE, places=9)

    def test_the_range_is_the_whole_ladder(self) -> None:
        self.assertEqual(self.found.fitted_over, (STEPS[0], STEPS[-1]))
        self.assertEqual(self.found.rungs_used, len(STEPS))
        self.assertEqual(self.found.dropped, ())

    def test_every_local_order_is_carried(self) -> None:
        self.assertEqual(len(self.found.local_orders), len(STEPS) - 1)
        for order in self.found.local_orders:
            self.assertAlmostEqual(order, ORDER, places=9)

    def test_a_first_order_curve_is_converging_too(self) -> None:
        # The verdict is about whether the error falls, never about how fast, and
        # a check that only accepted second order would refuse half the engines
        # this suite exists to measure.
        self.assertEqual(conclude(ladder(order=1.0)).verdict, CONVERGING)


class TheFlooredCurveIsRecognised(unittest.TestCase):
    FLOOR = 1e-4

    def setUp(self) -> None:
        self.found = conclude(ladder(floor=self.FLOOR))

    def test_the_verdict_is_floored(self) -> None:
        self.assertEqual(self.found.verdict, FLOORED)

    def test_the_floor_it_settled_at_is_recorded(self) -> None:
        self.assertAlmostEqual(
            self.found.attributed_floor / self.FLOOR, 1.0, delta=0.05
        )

    def test_the_coarse_end_still_converges_and_the_fine_end_does_not(self) -> None:
        self.assertGreaterEqual(self.found.local_orders[0], ORDER_CONVERGENCE_HOLDS)
        self.assertLess(self.found.local_orders[-1], ORDER_A_FLOOR_HAS_FALLEN_BELOW)

    def test_the_single_fitted_slope_would_have_said_neither(self) -> None:
        # Why the verdict is read from the local orders rather than from the fit.
        # One slope over a curve that is second order at one end and flat at the
        # other lands between the bands and says nothing.
        self.assertLess(self.found.order, ORDER)
        self.assertGreater(self.found.order, ORDER_A_FLOOR_HAS_FALLEN_BELOW)


class TheStudysOwnErrorIsTakenOutFirst(unittest.TestCase):
    """The same floored curve, read against three different declarations.

    This is the second done-when item, and it is the one that decides whether a
    finding is about an engine or about this project. Nothing changes in the
    ladder between these three: only what the caller states the study itself
    contributes.
    """

    FLOOR = 1e-4

    def test_with_nothing_declared_the_floor_is_the_engines(self) -> None:
        found = conclude(ladder(floor=self.FLOOR))
        self.assertEqual(found.verdict, FLOORED)

    def test_a_floor_that_is_the_reference_bound_is_not_a_finding(self) -> None:
        found = conclude(
            ladder(floor=self.FLOOR), Excluded(reference=self.FLOOR)
        )
        self.assertEqual(found.verdict, CONVERGING)
        self.assertAlmostEqual(found.order, ORDER, places=6)

    def test_a_floor_that_is_the_rounding_of_the_run_is_not_a_finding(self) -> None:
        found = conclude(ladder(floor=self.FLOOR), Excluded(rounding=self.FLOOR))
        self.assertEqual(found.verdict, CONVERGING)

    def test_the_two_contributions_add(self) -> None:
        # Split across both fields rather than carried in one, which is how a
        # real study states them, and the verdict is the same because the sum is.
        found = conclude(
            ladder(floor=self.FLOOR),
            Excluded(rounding=self.FLOOR / 2.0, reference=self.FLOOR / 2.0),
        )
        self.assertEqual(found.verdict, CONVERGING)

    def test_a_rung_inside_the_exclusions_is_dropped_with_its_reason(self) -> None:
        found = conclude(ladder(floor=self.FLOOR), Excluded(reference=self.FLOOR))
        self.assertTrue(found.dropped)
        self.assertIn("says nothing about the engine", found.dropped[0])
        self.assertEqual(found.rungs_used + len(found.dropped), len(STEPS))

    def test_the_declaration_is_carried_on_the_conclusion(self) -> None:
        # A verdict that excluded something without saying what cannot be argued
        # with, and the reference bound is a number that moves when #47 lands.
        found = conclude(ladder(floor=self.FLOOR), Excluded(reference=self.FLOOR))
        self.assertEqual(found.excluded.reference, self.FLOOR)
        self.assertEqual(found.excluded.total, self.FLOOR)

    def test_an_exclusion_larger_than_the_floor_does_not_invent_convergence(
        self,
    ) -> None:
        # The other direction. Over-declaring drops rungs rather than flattening
        # them, so what is left is a shorter ladder and eventually undecided,
        # never a converging verdict manufactured out of a subtraction.
        found = conclude(ladder(floor=self.FLOOR), Excluded(reference=1e-2))
        self.assertEqual(found.verdict, UNDECIDED)
        self.assertIn("too narrow to decide", found.reason)


class UndecidedIsProducedRatherThanAvoided(unittest.TestCase):
    def test_a_slope_between_the_two_bands_is_undecided(self) -> None:
        # Order 0.35 sits above the band a floor has fallen below and beneath the
        # one convergence holds at, which is exactly the evidence that points
        # neither way.
        between = (ORDER_CONVERGENCE_HOLDS + ORDER_A_FLOOR_HAS_FALLEN_BELOW) / 2.0
        found = conclude(ladder(order=between))
        self.assertEqual(found.verdict, UNDECIDED)
        self.assertIn("thin", found.reason)

    def test_it_still_carries_the_fit_it_could_make(self) -> None:
        between = (ORDER_CONVERGENCE_HOLDS + ORDER_A_FLOOR_HAS_FALLEN_BELOW) / 2.0
        found = conclude(ladder(order=between))
        self.assertAlmostEqual(found.order, between, places=9)
        self.assertEqual(found.fitted_over, (STEPS[0], STEPS[-1]))

    def test_a_ladder_entirely_inside_the_exclusions_is_undecided(self) -> None:
        found = conclude(ladder(), Excluded(rounding=1.0))
        self.assertEqual(found.verdict, UNDECIDED)
        self.assertEqual(found.rungs_used, 0)
        self.assertEqual(len(found.dropped), len(STEPS))

    def test_a_range_one_rung_too_narrow_is_undecided_rather_than_decided(
        self,
    ) -> None:
        # The near-miss on the range. Two rungs survive the exclusions, the two
        # of them fall at order two, and a module willing to conclude from two
        # would report converging on the strength of one interval.
        rungs = ladder()
        excluded = Excluded(reference=rungs[2].error / 2.0)
        found = conclude(rungs, excluded)
        self.assertEqual(found.rungs_used, RUNGS_FLOOR - 1)
        self.assertEqual(found.verdict, UNDECIDED)
        self.assertIn("too narrow to decide", found.reason)

    def test_a_ladder_that_flattens_without_reaching_a_floor_is_undecided(
        self,
    ) -> None:
        # The case the gap between the two bands exists for, and the one a
        # two-valued conclusion gets wrong in the direction that matters. The
        # coarse end still falls at order two and the fine end has slowed to a
        # third of an order, which is neither convergence nor a floor. A module
        # that called anything below the convergence band a floor would publish
        # this as a modelling error in somebody else's software.
        found = conclude(flattening_ladder())
        self.assertEqual(found.verdict, UNDECIDED)
        self.assertGreaterEqual(found.local_orders[0], ORDER_CONVERGENCE_HOLDS)
        self.assertLess(found.local_orders[-1], ORDER_CONVERGENCE_HOLDS)
        self.assertGreaterEqual(
            found.local_orders[-1], ORDER_A_FLOOR_HAS_FALLEN_BELOW
        )

    def test_the_verdict_says_which_route_produced_it(self) -> None:
        # Three undecided conclusions from three different routes, and no two of
        # them say the same thing. An undecided that did not say why is the shape
        # a reader takes as an opinion.
        reasons = {
            conclude(ladder(), Excluded(rounding=1.0)).reason,
            conclude(ladder(order=0.375)).reason,
            conclude(
                ladder(), Excluded(reference=ladder()[2].error / 2.0)
            ).reason,
        }
        self.assertEqual(len(reasons), 3)


class TheConclusionReadsAsASentence(unittest.TestCase):
    def test_a_decided_conclusion_prints_its_order_and_its_range(self) -> None:
        printed = str(conclude(ladder()))
        self.assertIn(CONVERGING, printed)
        self.assertIn("order 2.00", printed)
        self.assertIn("0.1", printed)

    def test_an_undecided_conclusion_prints_its_reason(self) -> None:
        printed = str(conclude(ladder(), Excluded(rounding=1.0)))
        self.assertTrue(printed.startswith(UNDECIDED))

    def test_the_scale_and_the_order_reproduce_the_curve(self) -> None:
        # The fitted parameters are a curve a reader can redraw, which is what
        # the fourth done-when item is for.
        found = conclude(ladder())
        for step in STEPS:
            with self.subTest(step=step):
                self.assertAlmostEqual(
                    found.scale * step**found.order / (SCALE * step**ORDER),
                    1.0,
                    places=9,
                )


if __name__ == "__main__":
    unittest.main()
