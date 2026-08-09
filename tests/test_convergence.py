"""The reference's order, measured in the gate at a reduced sampling.

Issue #46. The long study is `python -m reference.convergence` and it is quoted in
`reference/order-of-convergence.md`. What runs here is the same two ladders over a
shorter horizon and fewer rungs, which is the fourth done-when item: a change that
costs the reference an order reds on the next run rather than being found later by
a number that looked odd.

Reduced in the horizon and the rung count, never in what is asserted. Every
interval of both ladders has to sit at order two, so a change costing one order
moves every interval to one and fails, and a change costing an order at only one
end of the range fails as well.

Two ladders because they reach different halves of the update. The closed-form
ladder turns a torque-free body, where the moment is zero and every term carrying
it is unreached. The self-convergence ladder turns a heavy top, where the moment
enters at both ends of the step, and it is the one that catches a term evaluated
at the wrong point in the step.

Neither ladder is allowed to pass on noise. A ratio of four between two rounding
errors is a coincidence, so each measurement asserts its finest rung is well above
the floor the long study measures.

    python -m unittest discover -s tests -k convergence
"""

from __future__ import annotations

import math
import unittest

from reference import convergence
from reference.convergence import (
    HEAVY,
    HEAVY_SPIN,
    HEAVY_TILT,
    Ladder,
    Rung,
    StudyRefused,
    against_the_closed_form,
    against_the_next_refinement,
    departure,
    exact_orientation,
    free_symmetric_top,
    report,
)
from reference.integrator import (
    IDENTITY,
    State,
    exponential,
    matvec,
    off_the_group,
)

# The reduced sampling. The horizons are short enough that the whole file runs in
# well under a second and long enough that the coarsest rung is out of the range
# where the leading term does not yet dominate.
CLOSED_FORM_HORIZON = 0.5
CLOSED_FORM_COUNTS = (16, 32, 64, 128, 256)
HEAVY_HORIZON = 0.5
HEAVY_COUNTS = (32, 64, 128, 256, 512, 1024)

# How far an interval may sit from two. The long study's worst departure is 0.001
# on the closed-form ladder and 0.016 on the heavy top's, and a change costing one
# order puts every interval a whole unit away, so this bound has room for the last
# bits to fall differently on another machine and no room for a lost order.
TOLERANCE = 0.1

_LADDERS: dict[str, Ladder] = {}


def closed_form_ladder() -> Ladder:
    if "closed" not in _LADDERS:
        _LADDERS["closed"] = against_the_closed_form(
            CLOSED_FORM_HORIZON, CLOSED_FORM_COUNTS
        )
    return _LADDERS["closed"]


def heavy_start() -> State:
    return State(
        exponential((HEAVY_TILT, 0.0, 0.0)),
        matvec(HEAVY.inertia, (0.0, 0.0, HEAVY_SPIN)),
    )


def heavy_ladder() -> Ladder:
    if "heavy" not in _LADDERS:
        _LADDERS["heavy"] = against_the_next_refinement(
            HEAVY, heavy_start(), HEAVY_HORIZON, HEAVY_COUNTS
        )
    return _LADDERS["heavy"]


class TheOracleIsWorthMeasuringAgainst(unittest.TestCase):
    """The closed form, before anything is measured against it.

    A study against an oracle that is wrong measures the oracle. These are the
    three things about it that can be checked without integrating anything.
    """

    def test_the_closed_form_starts_where_the_run_starts(self) -> None:
        _, start = free_symmetric_top()
        self.assertLess(departure(exact_orientation(start, 0.0), start.orientation), 1e-15)

    def test_the_closed_form_is_a_rotation_at_every_time(self) -> None:
        _, start = free_symmetric_top()
        for time in (0.05, 0.5, 2.0, 20.0):
            with self.subTest(time=time):
                self.assertLess(off_the_group(exact_orientation(start, time)), 1e-14)

    def test_the_closed_form_actually_moves(self) -> None:
        # Without this the ladder above could be measuring a run against a
        # constant, which converges at every order at once.
        _, start = free_symmetric_top()
        self.assertGreater(
            departure(exact_orientation(start, 0.5), start.orientation), 0.1
        )


class TheOrderAgainstTheClosedForm(unittest.TestCase):
    """The first and second done-when items, on the half with a known answer."""

    def test_every_interval_sits_at_order_two(self) -> None:
        ladder = closed_form_ladder()
        stretch = ladder.stretch_at(2.0, TOLERANCE)
        self.assertIsNotNone(stretch)
        assert stretch is not None
        # Every interval, not merely the longest stretch of them. A change that
        # costs an order at one end of the range leaves a stretch behind it and
        # would pass a test that only asked for one.
        self.assertEqual(len(stretch.orders), len(ladder.orders))
        self.assertLess(stretch.worst_departure, TOLERANCE)

    def test_the_measurement_is_not_made_of_rounding(self) -> None:
        ladder = closed_form_ladder()
        self.assertGreater(ladder.rungs[-1].error, 1e-9)

    def test_the_ladder_does_not_reach_the_rounding_floor(self) -> None:
        # Stated as a property rather than left implied. The floor for this body
        # is measured by the long study, and a reduced sampling that fell into it
        # would report an order made of noise.
        self.assertIsNone(closed_form_ladder().rounding_floor())


class TheOrderWhereTheMomentEnters(unittest.TestCase):
    """The same measurement on the heavy top, where the closed form is #45's.

    Self-convergence, so what this proves is the rate at which refinements agree
    with each other. It is not a check against the truth and is not written as
    one: a method converging steadily onto the wrong answer has a clean slope
    here, and what says this update lands on the right answer at all is the
    closed-form ladder above.
    """

    def test_every_interval_sits_at_order_two(self) -> None:
        ladder = heavy_ladder()
        stretch = ladder.stretch_at(2.0, TOLERANCE)
        self.assertIsNotNone(stretch)
        assert stretch is not None
        self.assertEqual(len(stretch.orders), len(ladder.orders))
        self.assertLess(stretch.worst_departure, TOLERANCE)

    def test_the_measurement_is_not_made_of_rounding(self) -> None:
        self.assertGreater(heavy_ladder().rungs[-1].error, 1e-9)

    def test_the_top_actually_moved_over_the_horizon(self) -> None:
        # The difference between two refinements is small when both are accurate
        # and also when neither went anywhere, and only one of those is a
        # measurement of an order.
        from reference.integrator import every_step

        reached = every_step(HEAVY, heavy_start(), HEAVY_HORIZON / 1024, 1024)[-1]
        self.assertGreater(departure(reached.orientation, heavy_start().orientation), 0.1)


class ALadderThatCannotCarryAnOrder(unittest.TestCase):
    """Each refusal, tripped by a valid ladder with one thing changed."""

    def rungs(self) -> tuple[Rung, ...]:
        return (
            Rung(count=10, step=0.1, error=1e-2),
            Rung(count=20, step=0.05, error=2.5e-3),
            Rung(count=40, step=0.025, error=6.25e-4),
        )

    def test_the_valid_ladder_is_accepted(self) -> None:
        ladder = Ladder(what="a fixture", horizon=1.0, rungs=self.rungs())
        for order in ladder.orders:
            self.assertAlmostEqual(order, 2.0, places=9)

    def test_two_rungs_are_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Ladder(what="a fixture", horizon=1.0, rungs=self.rungs()[:2])
        self.assertIn("at least three rungs", str(refused.exception))

    def test_rungs_that_do_not_refine_are_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Ladder(what="a fixture", horizon=1.0, rungs=tuple(reversed(self.rungs())))
        self.assertIn("a ladder refines", str(refused.exception))

    def test_two_rungs_at_one_step_are_refused(self) -> None:
        repeated = self.rungs()[:2] + (self.rungs()[1],)
        with self.assertRaises(StudyRefused) as refused:
            Ladder(what="a fixture", horizon=1.0, rungs=repeated)
        self.assertIn("a ladder refines", str(refused.exception))

    def test_a_horizon_of_zero_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Ladder(what="a fixture", horizon=0.0, rungs=self.rungs())
        self.assertIn("a horizon is positive", str(refused.exception))

    def test_something_that_is_not_a_rung_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Ladder(what="a fixture", horizon=1.0, rungs=(0.1, 0.05, 0.025))  # type: ignore[arg-type]
        self.assertIn("a ladder is built of rungs", str(refused.exception))


class ARungThatCannotCarryAnError(unittest.TestCase):
    def test_the_valid_rung_is_accepted(self) -> None:
        self.assertEqual(Rung(count=10, step=0.1, error=1e-3).count, 10)

    def test_an_error_of_zero_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Rung(count=10, step=0.1, error=0.0)
        self.assertIn("bottom of the ladder", str(refused.exception))

    def test_a_negative_error_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Rung(count=10, step=0.1, error=-1e-3)
        self.assertIn("an error is positive", str(refused.exception))

    def test_an_error_that_is_not_a_number_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Rung(count=10, step=0.1, error=math.nan)
        self.assertIn("an error is a finite float", str(refused.exception))

    def test_a_step_of_zero_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Rung(count=10, step=0.0, error=1e-3)
        self.assertIn("a step is positive", str(refused.exception))

    def test_a_count_of_zero_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Rung(count=0, step=0.1, error=1e-3)
        self.assertIn("at least one step", str(refused.exception))

    def test_a_count_that_is_not_a_whole_number_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            Rung(count=10.0, step=0.1, error=1e-3)  # type: ignore[arg-type]
        self.assertIn("a whole number of steps", str(refused.exception))


class AStudyThatDoesNotRefine(unittest.TestCase):
    """The counts are refused before the runs are spent on them."""

    def test_counts_that_do_not_increase_are_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            against_the_closed_form(0.5, (64, 32, 16))
        self.assertIn("a study refines", str(refused.exception))

    def test_one_count_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            against_the_closed_form(0.5, (64,))
        self.assertIn("at least two step counts", str(refused.exception))

    def test_a_negative_horizon_is_refused(self) -> None:
        with self.assertRaises(StudyRefused) as refused:
            against_the_next_refinement(HEAVY, heavy_start(), -1.0, (16, 32, 64, 128))
        self.assertIn("a horizon is a positive finite float", str(refused.exception))


class WhatTheSlopeReaderDoesWithALadder(unittest.TestCase):
    """The operator that reads a range out of a ladder, on fixtures.

    Every fixture here is a ladder written by hand rather than run, because what
    is being tested is the reading and not the integration. A first-order ladder
    is the one that matters: it is what a change costing an order produces, and a
    reader that returned a stretch for it would pass the studies above on a
    reference that had lost an order.
    """

    def ladder_at(self, order: float) -> Ladder:
        return Ladder(
            what="a fixture",
            horizon=1.0,
            rungs=tuple(
                Rung(count=10 * 2 ** k, step=0.1 / 2 ** k, error=1e-2 / 2 ** (k * order))
                for k in range(5)
            ),
        )

    def test_a_first_order_ladder_has_no_stretch_at_two(self) -> None:
        self.assertIsNone(self.ladder_at(1.0).stretch_at(2.0, TOLERANCE))

    def test_a_second_order_ladder_is_read_end_to_end(self) -> None:
        ladder = self.ladder_at(2.0)
        stretch = ladder.stretch_at(2.0, TOLERANCE)
        self.assertIsNotNone(stretch)
        assert stretch is not None
        self.assertEqual(len(stretch.orders), 4)
        self.assertEqual(stretch.coarsest, ladder.rungs[0])
        self.assertEqual(stretch.finest, ladder.rungs[-1])

    def test_the_longest_stretch_is_taken_and_not_the_first(self) -> None:
        # Two intervals at order two, then one that is not, then three that are.
        # A reader returning the first run would report a range three times too
        # narrow and would put the fine end of it in the wrong place.
        errors = (1e-2, 2.5e-3, 6.25e-4, 4.0e-4, 1.0e-4, 2.5e-5, 6.25e-6)
        ladder = Ladder(
            what="a fixture",
            horizon=1.0,
            rungs=tuple(
                Rung(count=10 * 2 ** k, step=0.1 / 2 ** k, error=error)
                for k, error in enumerate(errors)
            ),
        )
        stretch = ladder.stretch_at(2.0, TOLERANCE)
        self.assertIsNotNone(stretch)
        assert stretch is not None
        self.assertEqual(len(stretch.orders), 3)
        self.assertEqual(stretch.coarsest, ladder.rungs[3])
        self.assertEqual(stretch.finest, ladder.rungs[-1])

    def test_a_ladder_that_stops_falling_names_the_rung_it_stopped_at(self) -> None:
        errors = (1e-6, 2.5e-7, 6.25e-8, 7.0e-8, 9.0e-8)
        ladder = Ladder(
            what="a fixture",
            horizon=1.0,
            rungs=tuple(
                Rung(count=10 * 2 ** k, step=0.1 / 2 ** k, error=error)
                for k, error in enumerate(errors)
            ),
        )
        floor = ladder.rounding_floor()
        self.assertIsNotNone(floor)
        assert floor is not None
        self.assertEqual(floor, ladder.rungs[3])

    def test_a_ladder_that_keeps_falling_has_no_floor(self) -> None:
        self.assertIsNone(self.ladder_at(2.0).rounding_floor())

    def test_the_order_is_read_from_the_step_ratio_and_not_from_halving(self) -> None:
        # A ladder refined by three rather than by two. An operator that assumed
        # halving would read this as log base two of nine, which is 3.17.
        ladder = Ladder(
            what="a fixture",
            horizon=1.0,
            rungs=(
                Rung(count=10, step=0.09, error=8.1e-3),
                Rung(count=30, step=0.03, error=9.0e-4),
                Rung(count=90, step=0.01, error=1.0e-4),
            ),
        )
        for order in ladder.orders:
            self.assertAlmostEqual(order, 2.0, places=9)


class WhatTheReportSays(unittest.TestCase):
    """The printed form, since it is what the record quotes."""

    def test_a_ladder_with_no_floor_says_so_and_does_not_name_one(self) -> None:
        printed = report(closed_form_ladder())
        self.assertIn("rounding does not take over anywhere on this ladder", printed)
        self.assertNotIn("rounding takes over at", printed)

    def test_the_report_carries_every_rung_and_its_count(self) -> None:
        ladder = closed_form_ladder()
        printed = report(ladder)
        for rung in ladder.rungs:
            self.assertIn(f"N={rung.count}", printed)

    def test_a_ladder_with_no_stretch_at_two_says_that_rather_than_nothing(self) -> None:
        ladder = Ladder(
            what="a fixture",
            horizon=1.0,
            rungs=tuple(
                Rung(count=10 * 2 ** k, step=0.1 / 2 ** k, error=1e-2 / 2 ** k)
                for k in range(4)
            ),
        )
        self.assertIn("no stretch of this ladder sits at order two", report(ladder))


class TheDepartureBetweenTwoOrientations(unittest.TestCase):
    def test_it_is_the_worst_entry_and_not_the_first(self) -> None:
        moved = tuple(
            tuple(IDENTITY[row][column] + (0.25 if (row, column) == (2, 1) else 0.0)
                  for column in range(3))
            for row in range(3)
        )
        self.assertAlmostEqual(departure(moved, IDENTITY), 0.25)

    def test_a_matrix_against_itself_is_zero(self) -> None:
        self.assertEqual(departure(IDENTITY, IDENTITY), 0.0)


class TheModuleRunsAsACommand(unittest.TestCase):
    def test_main_is_the_entry_point_the_docstring_names(self) -> None:
        # The record quotes `python -m reference.convergence`, so the callable
        # behind it exists and is not a name that drifted out of the docstring.
        self.assertTrue(callable(convergence.main))


if __name__ == "__main__":
    unittest.main()
