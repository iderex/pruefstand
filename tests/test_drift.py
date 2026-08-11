"""The drift estimator, against series whose behaviour was built into them.

Issue #56. Every series below is constructed so its answer is known before it is
asked for: a walk with no swing, a swing with no walk, both together, a swing
that opens, one sampled too coarsely to size, and one whose swing is inside the
run-to-run floor. Each fixture is the clean series with one thing changed.

The pair worth reading is the two walks. A metric that returned a magnitude
would pass every test about size and fail only these two, which is the whole of
what this issue is about.

    python -m unittest discover -s tests -k drift
"""

from __future__ import annotations

import math
import unittest

from metrics.drift import (
    BELOW_FLOOR,
    NO_SWING,
    SAMPLES_FLOOR,
    SAMPLES_PER_PERIOD_FLOOR,
    SIGN_CHANGES_FLOOR,
    Drift,
    DriftRefused,
    drift,
    per_component,
)

# The horizon every series below runs over, the period of the swing in it, and
# how often it is sampled. Thirty-two samples per period is twice the floor, so
# the resolution condition is comfortably met except where a test lowers it.
HORIZON = 100.0
PERIOD = 2.0
PER_PERIOD = 32

# The value of the integral at the initial condition. Not one, so a test that
# confused the relative change with the absolute one fails rather than agreeing
# by accident.
START = 4.0

# A floor of zero for the series where the third condition is not the subject. A
# floor is required rather than defaulted, so every call states one.
NO_FLOOR = 0.0

# A floor above the spurious rate a straight line picks up from a pure swing,
# which is about 1.9 * amplitude / periods and is 3.8e-07 for the series below.
# Measured in `metrics/drift.py`, and it is why these fixtures do not use a
# floor of 1e-09: at that floor the swing's own tilt is reported as a walk.
SWING_FLOOR = 1e-06


def exact_line() -> list[tuple[float, float]]:
    """A series whose residual about the fitted line is exactly zero.

    The first condition is otherwise unreachable, and that is a fact about
    least squares rather than about this estimator: a residual is orthogonal to
    the times and sums to zero, so a non-zero one cannot be monotone and always
    crosses the line at least twice. Only an exact line has none, and the
    arithmetic here is exact because every value is a small multiple of a
    quarter.
    """
    return [(float(k), START + float(k)) for k in range(9)]


def times(per_period: int = PER_PERIOD) -> list[float]:
    """Whole periods, and the sample at the horizon itself is not repeated.

    A series covering fifty periods plus one extra sample at the phase it
    started in is a series whose least-squares line is tilted by that one
    sample, which showed up as a rate of 4e-09 on a swing with no walk in it.
    That is a property of the fixture and not of the estimator, so the fixture
    is what changed.
    """
    step = PERIOD / per_period
    return [index * step for index in range(int(HORIZON / step))]


def at_a_zero(built: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """`built`, cut at the last whole period, where the swing is at zero."""
    return built[: PER_PERIOD * int(HORIZON / PERIOD - 1) + 1]


def series(
    walk: float = 0.0,
    swing: float = 0.0,
    opening: float = 0.0,
    per_period: int = PER_PERIOD,
) -> list[tuple[float, float]]:
    """`(time, integral)` for a relative change of `walk * t` plus a swing.

    `swing` is the amplitude of the oscillation at time zero and `opening` is
    how much of itself it gains over the horizon, so `opening` of one doubles it
    by the end.
    """
    built = []
    for at in times(per_period):
        amplitude = swing * (1.0 + opening * at / HORIZON)
        relative = walk * at + amplitude * math.sin(2.0 * math.pi * at / PERIOD)
        built.append((at, START * (1.0 + relative)))
    return built


class TheSignSurvives(unittest.TestCase):
    """The two fixtures a magnitude would pass and this issue exists for."""

    def test_an_integral_that_grows_reports_a_positive_rate(self) -> None:
        found = drift(series(walk=1e-06), floor=NO_FLOOR)
        assert found.rate is not None
        self.assertGreater(found.rate, 0.0)
        self.assertGreater(found.value, 0.0)

    def test_an_integral_that_shrinks_reports_a_negative_rate(self) -> None:
        found = drift(series(walk=-1e-06), floor=NO_FLOOR)
        assert found.rate is not None
        self.assertLess(found.rate, 0.0)
        self.assertLess(found.value, 0.0)

    def test_the_two_differ_only_in_sign(self) -> None:
        up = drift(series(walk=1e-06), floor=NO_FLOOR)
        down = drift(series(walk=-1e-06), floor=NO_FLOOR)
        assert up.rate is not None and down.rate is not None
        self.assertAlmostEqual(up.rate, -down.rate, places=15)
        self.assertAlmostEqual(up.value, -down.value, places=15)

    def test_the_value_is_the_relative_change_at_the_end(self) -> None:
        # Against START, so a reading that forgot to divide by the initial value
        # is off by a factor of four rather than agreeing.
        built = series(walk=1e-06)
        found = drift(built, floor=NO_FLOOR)
        self.assertAlmostEqual(1e-06 * built[-1][0], found.value, places=15)

    def test_an_amplitude_is_never_negative(self) -> None:
        found = drift(series(walk=-1e-06, swing=1e-05), floor=NO_FLOOR)
        assert found.amplitude is not None
        self.assertGreater(found.amplitude, 0.0)


class TheWalkAndTheSwingAreSeparated(unittest.TestCase):
    """The whole point: neither number is recoverable from the other."""

    def test_a_walk_with_no_swing_reports_the_rate_and_withholds_the_amplitude(
        self,
    ) -> None:
        # The amplitude goes to the resolution condition rather than to the
        # first one, and that is the composition the document predicts: the
        # residual of a clean walk is rounding noise, which changes sign at
        # nearly every sample and is therefore not sampled sixteen times per
        # period of anything.
        found = drift(series(walk=1e-06), floor=NO_FLOOR)
        self.assertAlmostEqual(1e-06, found.rate or 0.0, places=15)
        self.assertIsNone(found.amplitude)
        self.assertIn("samples per residual period", " ".join(found.withheld))

    def test_an_exact_line_withholds_the_amplitude_and_keeps_the_rate(self) -> None:
        found = drift(exact_line(), floor=NO_FLOOR)
        self.assertEqual(0, found.sign_changes)
        self.assertIn(NO_SWING, found.withheld)
        self.assertIsNone(found.amplitude)
        self.assertEqual(0.25, found.rate)

    def test_a_swing_with_no_walk_reports_the_amplitude(self) -> None:
        found = drift(series(swing=1e-05), floor=NO_FLOOR)
        assert found.amplitude is not None
        self.assertAlmostEqual(1e-05, found.amplitude, delta=2.5e-07)

    def test_a_swing_with_no_walk_has_a_rate_near_zero(self) -> None:
        found = drift(series(swing=1e-05), floor=NO_FLOOR)
        assert found.rate is not None
        self.assertLess(abs(found.rate * HORIZON), 1e-05)

    def test_both_together_are_recovered_independently(self) -> None:
        found = drift(series(walk=1e-06, swing=1e-05), floor=NO_FLOOR)
        assert found.rate is not None and found.amplitude is not None
        self.assertAlmostEqual(1e-06, found.rate, delta=1e-08)
        self.assertAlmostEqual(1e-05, found.amplitude, delta=2.5e-07)

    def test_the_endpoint_alone_would_not_have_told_them_apart(self) -> None:
        # Two runs with the same endpoint, one of which swung ten times as far.
        # This is the sentence in the document made into a fixture. Both are cut
        # at a sample where the swing is passing through zero, so the endpoints
        # are the walk alone and the difference between the runs is entirely in
        # what the endpoint throws away.
        quiet = drift(at_a_zero(series(walk=1e-06, swing=1e-06)), floor=NO_FLOOR)
        loud = drift(at_a_zero(series(walk=1e-06, swing=1e-05)), floor=NO_FLOOR)
        self.assertEqual(quiet.value, loud.value)
        assert quiet.amplitude is not None and loud.amplitude is not None
        self.assertAlmostEqual(10.0, loud.amplitude / quiet.amplitude, delta=1e-06)


class TheSwingThatOpens(unittest.TestCase):
    def test_a_bounded_swing_gives_a_growth_near_one(self) -> None:
        found = drift(series(swing=1e-05), floor=NO_FLOOR)
        assert found.growth is not None
        self.assertAlmostEqual(1.0, found.growth, delta=0.01)

    def test_a_swing_that_doubles_gives_a_growth_above_one(self) -> None:
        found = drift(series(swing=1e-05, opening=1.0), floor=NO_FLOOR)
        assert found.growth is not None
        self.assertGreater(found.growth, 1.25)
        self.assertLess(found.growth, 1.45)

    def test_a_swing_that_closes_gives_a_growth_below_one(self) -> None:
        found = drift(series(swing=1e-05, opening=-0.5), floor=NO_FLOOR)
        assert found.growth is not None
        self.assertLess(found.growth, 1.0)

    def test_the_growth_is_absent_where_the_amplitude_is(self) -> None:
        found = drift(series(walk=1e-06), floor=NO_FLOOR)
        self.assertIsNone(found.growth)


class TheConditionsWithholdRatherThanReportZero(unittest.TestCase):
    """An absence and a measured zero are opposite statements."""

    def test_a_run_sampled_too_coarsely_withholds_the_amplitude(self) -> None:
        # Eight samples per period, half the floor, which the document costs at
        # 7.61 per cent of the peak.
        found = drift(series(swing=1e-05, per_period=8), floor=NO_FLOOR)
        self.assertIsNone(found.amplitude)
        assert found.samples_per_period is not None
        self.assertLess(found.samples_per_period, SAMPLES_PER_PERIOD_FLOOR)
        self.assertIn("samples per residual period", " ".join(found.withheld))

    def test_a_run_at_the_resolution_floor_keeps_the_amplitude(self) -> None:
        # The other side of the same boundary, so the condition is shown to
        # separate rather than only to refuse.
        found = drift(series(swing=1e-05, per_period=16), floor=NO_FLOOR)
        self.assertIsNotNone(found.amplitude)

    def test_a_swing_inside_the_floor_is_withheld(self) -> None:
        found = drift(series(swing=1e-12), floor=1e-09)
        self.assertIsNone(found.amplitude)
        self.assertIn(
            BELOW_FLOOR.format(part="amplitude", floor=1e-09), found.withheld
        )

    def test_a_walk_inside_the_floor_is_withheld(self) -> None:
        # A walk of 1e-12 per second is a change of 1e-10 over the horizon, and
        # what the fit actually returns is dominated by the swing's own tilt at
        # 3.8e-07. Both are inside this floor, so neither is distinguished from
        # repeating the run and the rate is not reported.
        found = drift(series(walk=1e-12, swing=1e-05), floor=SWING_FLOOR)
        self.assertIsNone(found.rate)
        self.assertIn(
            BELOW_FLOOR.format(part="rate over the horizon", floor=SWING_FLOOR),
            found.withheld,
        )

    def test_a_walk_outside_the_floor_is_reported(self) -> None:
        found = drift(series(walk=1e-06, swing=1e-05), floor=SWING_FLOOR)
        self.assertIsNotNone(found.rate)

    def test_the_floor_reaches_one_component_and_not_the_other(self) -> None:
        # The narrower reading this module takes, made into a fixture: the rate
        # is inside the floor and the swing is far outside it, and a reading
        # that withheld both would fail here.
        found = drift(series(walk=1e-12, swing=1e-05), floor=SWING_FLOOR)
        self.assertIsNone(found.rate)
        self.assertIsNotNone(found.amplitude)

    def test_a_separated_result_says_so(self) -> None:
        self.assertTrue(drift(series(walk=1e-06, swing=1e-05), floor=NO_FLOOR).separated)

    def test_a_withheld_result_says_which_condition(self) -> None:
        found = drift(exact_line(), floor=NO_FLOOR)
        self.assertFalse(found.separated)
        self.assertIn(NO_SWING, str(found))
        self.assertIn("withheld", str(found))

    def test_nothing_withheld_is_reported_as_zero(self) -> None:
        found = drift(exact_line(), floor=NO_FLOOR)
        self.assertIsNot(found.amplitude, 0.0)
        self.assertIsNone(found.amplitude)


class AVectorIntegralIsNeverANorm(unittest.TestCase):
    """Per component, in the order given, and no route produces a magnitude."""

    def vector(self) -> list[tuple[float, tuple[float, ...]]]:
        walking = series(walk=1e-06)
        swinging = series(swing=1e-05)
        steady = series()
        return [
            (at, (walking[index][1], swinging[index][1], steady[index][1]))
            for index, (at, _) in enumerate(walking)
        ]

    def test_one_result_per_component(self) -> None:
        self.assertEqual(3, len(per_component(self.vector(), floor=NO_FLOOR)))

    def test_a_component_that_walks_and_one_that_swings_are_told_apart(self) -> None:
        walks, swings, _ = per_component(self.vector(), floor=NO_FLOOR)
        self.assertIsNone(walks.amplitude)
        self.assertIsNotNone(walks.rate)
        self.assertIsNotNone(swings.amplitude)

    def test_a_component_that_does_nothing_reports_nothing_rather_than_zero(
        self,
    ) -> None:
        _, _, steady = per_component(self.vector(), floor=1e-15)
        self.assertIsNone(steady.rate)
        self.assertIsNone(steady.amplitude)

    def test_the_sign_of_each_component_is_its_own(self) -> None:
        # A norm would have made both of these positive, which is the failure
        # this whole function exists against.
        up = series(walk=1e-06)
        down = series(walk=-1e-06)
        pairs = [(at, (up[i][1], down[i][1])) for i, (at, _) in enumerate(up)]
        grew, shrank = per_component(pairs, floor=NO_FLOOR)
        assert grew.rate is not None and shrank.rate is not None
        self.assertGreater(grew.rate, 0.0)
        self.assertLess(shrank.rate, 0.0)

    def test_components_of_different_widths_are_refused(self) -> None:
        pairs = [(0.0, (1.0, 2.0)), (1.0, (1.0,)), (2.0, (1.0, 2.0))]
        with self.assertRaises(DriftRefused):
            per_component(pairs, floor=NO_FLOOR)

    def test_a_scalar_where_a_vector_belongs_is_refused(self) -> None:
        with self.assertRaises(DriftRefused):
            per_component([(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)], floor=NO_FLOOR)  # type: ignore[list-item]

    def test_no_components_at_all_is_refused(self) -> None:
        with self.assertRaises(DriftRefused):
            per_component([(0.0, ()), (1.0, ()), (2.0, ())], floor=NO_FLOOR)

    def test_an_empty_run_is_refused(self) -> None:
        with self.assertRaises(DriftRefused):
            per_component([], floor=NO_FLOOR)


class TheEstimatorRefusesWhatItCannotRead(unittest.TestCase):
    """Each fixture is the working call with one thing changed."""

    def test_the_working_call_is_not_refused(self) -> None:
        self.assertIsInstance(drift(series(walk=1e-06), floor=NO_FLOOR), Drift)

    def test_fewer_samples_than_the_floor_are_refused(self) -> None:
        short = series(walk=1e-06)[: SAMPLES_FLOOR - 1]
        with self.assertRaises(DriftRefused):
            drift(short, floor=NO_FLOOR)

    def test_the_floor_count_itself_is_not_refused(self) -> None:
        drift(series(walk=1e-06)[:SAMPLES_FLOOR], floor=NO_FLOOR)

    def test_times_that_do_not_increase_are_refused(self) -> None:
        built = series(walk=1e-06)
        built[2] = (built[1][0], built[2][1])
        with self.assertRaises(DriftRefused):
            drift(built, floor=NO_FLOOR)

    def test_a_value_that_is_not_finite_is_refused(self) -> None:
        built = series(walk=1e-06)
        built[3] = (built[3][0], float("nan"))
        with self.assertRaises(DriftRefused):
            drift(built, floor=NO_FLOOR)

    def test_an_integral_that_starts_at_zero_is_refused(self) -> None:
        built = [(at, of - START) for at, of in series()]
        with self.assertRaises(DriftRefused) as refusal:
            drift(built, floor=NO_FLOOR)
        self.assertIn("division by zero", str(refusal.exception))

    def test_a_negative_floor_is_refused(self) -> None:
        with self.assertRaises(DriftRefused):
            drift(series(walk=1e-06), floor=-1e-09)

    def test_a_floor_that_is_not_a_float_is_refused(self) -> None:
        with self.assertRaises(DriftRefused):
            drift(series(walk=1e-06), floor=0)  # type: ignore[arg-type]

    def test_every_problem_is_reported_rather_than_the_first(self) -> None:
        built = series(walk=1e-06)
        built[3] = (built[3][0], float("inf"))
        built[5] = (float("nan"), built[5][1])
        with self.assertRaises(DriftRefused) as refusal:
            drift(built, floor=NO_FLOOR)
        self.assertEqual(2, len(refusal.exception.problems))


class TheConstantsAreTheDocumentsNumbers(unittest.TestCase):
    def test_the_resolution_floor_costs_under_two_per_cent_at_the_peak(self) -> None:
        # The derivation the document gives for sixteen, recomputed rather than
        # trusted: a peak sampled n times per period is underestimated by at
        # most 1 - cos(pi/n).
        cost = 1.0 - math.cos(math.pi / SAMPLES_PER_PERIOD_FLOOR)
        self.assertLess(cost, 0.02)

    def test_half_the_resolution_floor_does_not(self) -> None:
        self.assertGreater(1.0 - math.cos(math.pi / (SAMPLES_PER_PERIOD_FLOOR / 2)), 0.02)

    def test_a_swing_needs_two_sign_changes(self) -> None:
        self.assertEqual(2, SIGN_CHANGES_FLOOR)
        found = drift(series(swing=1e-05), floor=NO_FLOOR)
        self.assertGreaterEqual(found.sign_changes, SIGN_CHANGES_FLOOR)


if __name__ == "__main__":
    unittest.main()
