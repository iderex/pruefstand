"""The Lyapunov exponent estimator, against systems whose exponent is known.

Issue #75. Two kinds of test are here and they answer different questions.

The refusals are the ordinary kind: a working call with one thing changed, so
each one is tripped by the mistake it names rather than by a call that was broken
in several ways at once. Every refusal in `metrics/lyapunov.py` has one.

The calibrations are the reason this file exists. An estimator can refuse
everything it should refuse and still return a plausible wrong number, and the
only thing that catches that is a system whose exponent somebody else computed.
`metrics/known_exponents.py` carries three, and the spread each is compared
within is stated here rather than there, because how many uncertainties count as
agreement is a claim the comparison makes.

The long form of the same measurements, at horizons this file cannot afford, is
`python -m metrics.lyapunov`, and it is quoted in `metrics/lyapunov-exponent.md`.

    python -m unittest discover -s tests -k lyapunov
"""

from __future__ import annotations

import math
import statistics
import unittest

from metrics import known_exponents as known
from metrics.lyapunov import (
    BLOCKS,
    INTERVALS_PER_BLOCK_FLOOR,
    ROUNDING,
    Estimate,
    EstimateRefused,
    by_the_rule,
    choose_interval,
    choose_separation,
    excursion,
    from_samples,
    growth_samples,
    largest_exponent,
    reproducibility_floor,
    separation,
    snapped,
    unit_direction,
)

# How many uncertainties away from a published number still counts as agreement.
# Three, which is the ordinary reading of an uncertainty that is one standard
# error over the blocks, and it is stated here rather than in the estimator
# because it is a property of the claim being made and not of the arithmetic.
AGREEMENT = 3.0

# The clean estimate. Every refusal below is this with one field changed, so a
# refusal that fired for another reason would show up as this one failing.
CLEAN = dict(
    value=0.9,
    uncertainty=0.02,
    intervals=400,
    blocks=20,
    settled=40,
    interval=1.1,
    displacement=2.2e-7,
    horizon=440.0,
)


def hyperbolic(state: tuple[float, ...], duration: float) -> tuple[float, ...]:
    """One expanding direction and one contracting one, at a rate of exactly one.

    Started from `HYPERBOLIC_START`, which is on the contracting axis, the run
    itself stays bounded while any perturbation off that axis grows by exactly
    `exp(duration)`. So the largest exponent is one to the last bit, and this is
    the fixture that says the arithmetic is right before any physics is involved.

    A flow that only expanded would be simpler and would not work: its own state
    outgrows the perturbation, the two runs land on the same float, and what the
    estimator meets is a pair that met exactly rather than a growth rate. That is
    a real bound on the construction and it is why the separation has a floor.
    """
    x, y = state
    return (x * math.exp(duration), y * math.exp(-duration))


HYPERBOLIC_START = (0.0, 1.0)


def turning(state: tuple[float, ...], duration: float) -> tuple[float, ...]:
    """A rotation, which separates nothing. Its largest exponent is zero."""
    x, y = state
    return (
        x * math.cos(duration) - y * math.sin(duration),
        x * math.sin(duration) + y * math.cos(duration),
    )


class TheEstimateCarriesItsUncertainty(unittest.TestCase):
    def test_the_clean_estimate_is_accepted(self) -> None:
        # Without this every refusal below could be passing for another reason.
        self.assertEqual(Estimate(**CLEAN).value, CLEAN["value"])

    def test_an_estimate_cannot_be_built_without_an_uncertainty(self) -> None:
        # The interpreter refuses this before any validation in the module runs,
        # which is the whole point of the field being required and positional.
        missing = {k: v for k, v in CLEAN.items() if k != "uncertainty"}
        with self.assertRaises(TypeError):
            Estimate(**missing)  # type: ignore[arg-type]

    def test_an_uncertainty_of_zero_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused) as refused:
            Estimate(**{**CLEAN, "uncertainty": 0.0})
        self.assertIn("exact", str(refused.exception))

    def test_a_negative_uncertainty_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            Estimate(**{**CLEAN, "uncertainty": -0.02})

    def test_an_uncertainty_that_is_not_a_number_is_refused(self) -> None:
        for value in (float("nan"), float("inf"), "0.02", None):
            with self.subTest(value=value):
                with self.assertRaises(EstimateRefused):
                    Estimate(**{**CLEAN, "uncertainty": value})

    def test_a_value_that_is_not_a_number_is_refused(self) -> None:
        for value in (float("nan"), float("-inf"), "0.9"):
            with self.subTest(value=value):
                with self.assertRaises(EstimateRefused):
                    Estimate(**{**CLEAN, "value": value})

    def test_a_spread_over_one_block_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused) as refused:
            Estimate(**{**CLEAN, "blocks": 1})
        self.assertIn("not a measurement", str(refused.exception))

    def test_fewer_intervals_than_blocks_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            Estimate(**{**CLEAN, "intervals": 3})

    def test_a_horizon_or_interval_of_zero_is_refused(self) -> None:
        for field in ("interval", "displacement", "horizon"):
            with self.subTest(field=field):
                with self.assertRaises(EstimateRefused) as refused:
                    Estimate(**{**CLEAN, field: 0.0})
                self.assertIn(field, str(refused.exception))

    def test_a_relative_uncertainty_on_zero_is_refused(self) -> None:
        # The regular systems report zero, so this is reachable rather than
        # theoretical, and returning infinity there would be a number.
        with self.assertRaises(EstimateRefused):
            Estimate(**{**CLEAN, "value": 0.0}).relative_uncertainty

    def test_agreement_is_measured_in_uncertainties(self) -> None:
        found = Estimate(**CLEAN)
        self.assertTrue(found.agrees_with(0.94, 2.0))
        self.assertFalse(found.agrees_with(0.94, 1.0))

    def test_a_spread_of_zero_uncertainties_is_refused(self) -> None:
        # Agreement within zero uncertainties is exact equality dressed up as a
        # comparison, and it would make every claim about a published number
        # false whatever the estimate said.
        with self.assertRaises(EstimateRefused):
            Estimate(**CLEAN).agrees_with(0.9, 0.0)


class TheSamplesAreRefusedRatherThanRepaired(unittest.TestCase):
    def call(self, **changed: object) -> list[float]:
        arguments = dict(
            displacement=1e-6,
            interval=0.5,
            horizon=100.0,
            settling=10.0,
        )
        arguments.update(changed)
        flow = arguments.pop("flow", hyperbolic)
        start = arguments.pop("start", HYPERBOLIC_START)
        return growth_samples(flow, start, **arguments)  # type: ignore[arg-type]

    def test_the_clean_call_measures_the_exponent_it_was_built_with(self) -> None:
        samples = self.call()
        self.assertEqual(len(samples), int(90.0 / 0.5))
        for sample in samples:
            self.assertAlmostEqual(sample, 1.0, places=9)

    def test_a_start_that_is_not_finite_is_refused(self) -> None:
        for start in ((1.0, float("nan")), (1.0, 1), "xyz", ()):
            with self.subTest(start=start):
                with self.assertRaises(EstimateRefused):
                    self.call(start=start)

    def test_a_separation_of_zero_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            self.call(displacement=0.0)

    def test_an_interval_of_zero_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            self.call(interval=0.0)

    def test_a_negative_settling_window_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            self.call(settling=-1.0)

    def test_a_settling_window_longer_than_the_horizon_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused) as refused:
            self.call(settling=100.0)
        self.assertIn("every interval would be discarded", str(refused.exception))

    def test_a_perturbation_in_the_wrong_number_of_coordinates_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            self.call(direction=(1.0, 0.0, 0.0))

    def test_a_flow_that_leaves_the_phase_space_is_refused(self) -> None:
        # Not truncated to the intervals before it. An exponent fitted over the
        # part that ran is an exponent for a run that did not finish, and an
        # engine that recovers from a non-finite state is exactly what #41 is
        # about.
        def leaves(state: tuple[float, ...], duration: float) -> tuple[float, ...]:
            grown = hyperbolic(state, duration)
            return tuple(value * float("inf") for value in grown)

        with self.assertRaises(EstimateRefused) as refused:
            self.call(flow=leaves)
        self.assertIn("left the phase space", str(refused.exception))

    def test_a_flow_that_collapses_two_states_onto_one_is_refused(self) -> None:
        def collapses(state: tuple[float, ...], duration: float) -> tuple[float, ...]:
            return (0.0, 0.0)

        with self.assertRaises(EstimateRefused) as refused:
            self.call(flow=collapses)
        self.assertIn("met exactly", str(refused.exception))

    def test_two_states_in_different_phase_spaces_are_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            separation((1.0, 2.0), (1.0, 2.0, 3.0))

    def test_the_perturbation_direction_does_not_decide_the_answer(self) -> None:
        # The construction exists because the direction stops mattering. Two
        # deliberately different directions have to reach the same exponent, and
        # one of them is along a coordinate axis, which is the direction somebody
        # would pick by hand.
        first = self.call(direction=(1.0, 0.0))
        second = self.call(direction=unit_direction(2, seed=1))
        self.assertAlmostEqual(
            statistics.fmean(first), statistics.fmean(second), places=9
        )

    def test_the_drawn_direction_is_a_unit_vector_and_is_reproducible(self) -> None:
        drawn = unit_direction(3)
        self.assertAlmostEqual(math.sqrt(sum(v**2 for v in drawn)), 1.0, places=12)
        self.assertEqual(drawn, unit_direction(3))
        self.assertNotEqual(drawn, unit_direction(3, seed=2))

    def test_a_phase_space_with_no_coordinates_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            unit_direction(0)


class TheUncertaintyIsASpreadOverBlocks(unittest.TestCase):
    def samples(self, count: int) -> list[float]:
        # Deterministic and not constant, so the block means differ for a reason
        # a reader can check by hand rather than by chance.
        return [1.0 + math.sin(index) for index in range(count)]

    def clean(self, **changed: object) -> Estimate:
        arguments = dict(
            interval=0.5,
            displacement=1e-6,
            horizon=100.0,
            settled=20,
        )
        arguments.update(changed)
        samples = arguments.pop("samples", self.samples(400))
        return from_samples(samples, **arguments)  # type: ignore[arg-type]

    def test_the_value_and_the_uncertainty_are_the_block_means(self) -> None:
        samples = self.samples(400)
        found = self.clean()
        per_block = len(samples) // BLOCKS
        means = [
            statistics.fmean(samples[i * per_block : (i + 1) * per_block])
            for i in range(BLOCKS)
        ]
        self.assertAlmostEqual(found.value, statistics.fmean(means), places=12)
        self.assertAlmostEqual(
            found.uncertainty, statistics.stdev(means) / math.sqrt(BLOCKS), places=12
        )

    def test_fewer_than_two_blocks_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            self.clean(blocks=1)

    def test_a_block_shorter_than_the_floor_is_refused(self) -> None:
        shortest = BLOCKS * INTERVALS_PER_BLOCK_FLOOR
        with self.assertRaises(EstimateRefused) as refused:
            self.clean(samples=self.samples(shortest - 1))
        self.assertIn(str(INTERVALS_PER_BLOCK_FLOOR), str(refused.exception))
        # The one-interval-longer neighbour passes, so the refusal is at the
        # floor rather than somewhere near it.
        self.assertGreater(self.clean(samples=self.samples(shortest)).uncertainty, 0.0)

    def test_identical_blocks_are_refused_rather_than_called_exact(self) -> None:
        with self.assertRaises(EstimateRefused) as refused:
            self.clean(samples=[1.0] * 400)
        self.assertIn("claim to be exact", str(refused.exception))

    def test_the_intervals_past_the_last_whole_block_are_not_counted(self) -> None:
        # A block structure that swallowed the remainder would report a count the
        # blocks were not computed from.
        found = self.clean(samples=self.samples(409))
        self.assertEqual(found.intervals, (409 // BLOCKS) * BLOCKS)


class TheIntervalIsSnappedToWhatTheFlowCanAdvanceBy(unittest.TestCase):
    def test_it_moves_to_the_nearest_whole_grain(self) -> None:
        self.assertAlmostEqual(snapped(2.386, 1.0), 2.0, places=12)
        self.assertAlmostEqual(snapped(2.6, 1.0), 3.0, places=12)
        self.assertAlmostEqual(snapped(1.1105, 0.005), 1.11, places=12)

    def test_it_never_returns_less_than_one_grain(self) -> None:
        # Rounding to zero would ask the flow to advance by nothing and the
        # growth over it would have no logarithm.
        self.assertAlmostEqual(snapped(0.1, 1.0), 1.0, places=12)

    def test_a_grain_or_interval_of_zero_is_refused(self) -> None:
        with self.assertRaises(EstimateRefused):
            snapped(1.0, 0.0)
        with self.assertRaises(EstimateRefused):
            snapped(0.0, 1.0)

    def test_a_map_refuses_a_duration_between_two_iterations(self) -> None:
        with self.assertRaises(EstimateRefused) as refused:
            known.HENON.flow(known.HENON.start, 2.386)
        self.assertIn("whole iterations", str(refused.exception))

    def test_a_stepped_flow_advances_by_exactly_the_duration_asked(self) -> None:
        # A constant derivative is integrated exactly by this method, so the
        # answer is known and any duration the flow silently changed shows up as
        # the wrong answer rather than as a small error.
        flow = known.stepped_flow(lambda state: (2.0,), 0.005)
        for duration in (0.001, 0.005, 0.0123, 1.0, 2.386):
            with self.subTest(duration=duration):
                self.assertAlmostEqual(
                    flow((0.0,), duration)[0], 2.0 * duration, places=12
                )


class TheRuleChoosesTheSeparationAndTheInterval(unittest.TestCase):
    def test_the_separation_is_the_geometric_mean_of_floor_and_ceiling(self) -> None:
        system = known.LORENZ
        horizon = 40.0
        chosen = choose_separation(
            system.flow, system.start, interval=system.pilot_interval, horizon=horizon
        )
        wander = excursion(
            system.flow, system.start, interval=system.pilot_interval, horizon=horizon
        )
        noise = reproducibility_floor(
            system.flow, system.start, interval=system.pilot_interval
        )
        # This flow is deterministic, so its own noise is nothing and the floor
        # is the rounding of the excursion. An engine reached through a runner is
        # not obliged to be, which is why the floor is measured at all.
        self.assertEqual(noise, 0.0)
        self.assertAlmostEqual(
            chosen / math.sqrt(wander * wander * ROUNDING), 1.0, places=9
        )
        self.assertLess(chosen, wander)

    def test_a_placement_outside_the_two_bounds_is_refused(self) -> None:
        system = known.LORENZ
        for placement in (0.0, 1.0, -0.5, 2.0):
            with self.subTest(placement=placement):
                with self.assertRaises(EstimateRefused):
                    choose_separation(
                        system.flow,
                        system.start,
                        interval=system.pilot_interval,
                        horizon=40.0,
                        placement=placement,
                    )

    def test_a_run_that_does_not_move_has_no_separation_to_choose(self) -> None:
        with self.assertRaises(EstimateRefused) as refused:
            choose_separation(
                lambda state, duration: state,
                (1.0, 1.0),
                interval=0.5,
                horizon=40.0,
            )
        self.assertIn("does not move", str(refused.exception))

    def test_the_interval_is_one_e_fold_where_the_horizon_allows_it(self) -> None:
        system = known.LORENZ
        horizon = 400.0
        displacement = choose_separation(
            system.flow, system.start, interval=system.pilot_interval, horizon=horizon
        )
        chosen = choose_interval(
            system.flow,
            system.start,
            pilot=system.pilot_interval,
            horizon=horizon,
            settling=system.settling,
            displacement=displacement,
        )
        # One over the exponent, which for this system is a shade over one.
        self.assertAlmostEqual(chosen, 1.0 / system.published, delta=0.1)

    def test_a_regular_system_is_bounded_by_the_horizon_and_not_by_a_growth_rate(
        self,
    ) -> None:
        # A pilot exponent that is small and positive asks for an interval longer
        # than any horizon. What comes back is the longest the block structure
        # carries, which is the bound this test exists to hold.
        system = known.PENDULUM
        horizon = 200.0
        displacement = choose_separation(
            system.flow, system.start, interval=system.pilot_interval, horizon=horizon
        )
        chosen = choose_interval(
            system.flow,
            system.start,
            pilot=system.pilot_interval,
            horizon=horizon,
            settling=system.settling,
            displacement=displacement,
        )
        longest = (horizon - system.settling) / (BLOCKS * INTERVALS_PER_BLOCK_FLOOR)
        self.assertAlmostEqual(chosen, longest, places=12)

    def test_a_horizon_that_cannot_fill_the_blocks_is_refused(self) -> None:
        system = known.PENDULUM
        with self.assertRaises(EstimateRefused):
            choose_interval(
                system.flow,
                system.start,
                pilot=system.pilot_interval,
                horizon=10.0,
                settling=20.0,
                displacement=1e-8,
            )


class TheArithmeticIsRightBeforeAnyPhysics(unittest.TestCase):
    def test_a_run_with_no_spread_cannot_produce_an_estimate(self) -> None:
        # The hyperbolic fixture separates by exactly the same factor every
        # interval, so every block mean is the same number and there is nothing
        # to take a spread over. That is refused rather than reported with an
        # uncertainty of zero, which is the same rule as the one on the type: no
        # number leaves this module claiming to be exact. A real run never
        # reaches this, and a fixture is how the refusal is reached at all.
        with self.assertRaises(EstimateRefused) as refused:
            largest_exponent(
                hyperbolic,
                HYPERBOLIC_START,
                displacement=1e-6,
                interval=0.5,
                horizon=200.0,
                settling=10.0,
            )
        self.assertIn("claim to be exact", str(refused.exception))

    def test_the_growth_over_a_known_factor_is_that_factor(self) -> None:
        # The same fixture read one level down, where the exactness is the point.
        # Every sample is the rate the flow was built with, to the last place a
        # float carries, so an arithmetic slip anywhere between the perturbation
        # and the logarithm shows up here rather than as a slightly odd exponent
        # on a physical system.
        samples = growth_samples(
            hyperbolic,
            HYPERBOLIC_START,
            displacement=1e-6,
            interval=0.5,
            horizon=200.0,
            settling=10.0,
        )
        self.assertEqual(len(samples), int(190.0 / 0.5))
        for sample in samples:
            self.assertAlmostEqual(sample, 1.0, places=12)

    def test_a_flow_that_separates_nothing_reports_nothing(self) -> None:
        # A rotation holds every separation, so the exponent is zero and what is
        # left is the rounding of the rotation itself. This is the one place a
        # zero can be asserted directly: there is no shear here and no finite
        # horizon effect, so anything above the rounding would be the estimator
        # inventing a growth rate.
        found = largest_exponent(
            turning,
            (1.0, 0.0),
            displacement=1e-6,
            interval=0.5,
            horizon=200.0,
            settling=10.0,
        )
        # Measured at +2.74e-12 per unit time on the interpreter this landed on.
        # The residual is the rounding of the renormalisation rather than a
        # growth rate: it is eleven orders below the Lorenz exponent this same
        # estimator reports, and the bound below is two orders above what was
        # measured so that an interpreter rounding differently does not red it.
        self.assertLess(abs(found.value), 1e-10)
        self.assertLess(found.uncertainty, 1e-10)

    def test_the_same_call_twice_gives_the_same_estimate(self) -> None:
        # The determinism promise reaches this estimator through the drawn
        # direction, which is the only thing here that could have been random.
        arguments = dict(
            displacement=1e-6, interval=0.5, horizon=200.0, settling=10.0
        )
        first = largest_exponent(turning, (1.0, 0.0), **arguments)
        second = largest_exponent(turning, (1.0, 0.0), **arguments)
        self.assertEqual(first, second)


class TheKnownExponentsAreReproduced(unittest.TestCase):
    """Every estimate here is produced once and read by several tests.

    Computed in `setUpClass` rather than per test, because each of these is a
    run of a few hundred thousand steps and the same run answers more than one
    question. What is shared is the measurement, never the assertion.
    """

    PENDULUM_HORIZONS = (200.0, 800.0)

    @classmethod
    def by_the_rule(cls, system: known.KnownSystem, horizon: float) -> Estimate:
        chosen = by_the_rule(
            system.flow,
            system.start,
            grain=system.grain,
            pilot=system.pilot_interval,
            horizon=horizon,
            settling=system.settling,
        )
        return largest_exponent(
            system.flow,
            system.start,
            displacement=chosen.displacement,
            interval=chosen.interval,
            horizon=horizon,
            settling=system.settling,
        )

    @classmethod
    def setUpClass(cls) -> None:
        cls.lorenz = cls.by_the_rule(known.LORENZ, known.LORENZ.suite_horizon)
        cls.henon = cls.by_the_rule(known.HENON, known.HENON.suite_horizon)
        cls.pendulum = {
            horizon: cls.by_the_rule(known.PENDULUM, horizon)
            for horizon in cls.PENDULUM_HORIZONS
        }

    def test_the_lorenz_exponent_is_reproduced(self) -> None:
        published = known.LORENZ.published
        self.assertTrue(
            self.lorenz.agrees_with(published, AGREEMENT),
            f"{self.lorenz} against a published {published}",
        )

    def test_the_henon_exponent_is_reproduced(self) -> None:
        published = known.HENON.published
        self.assertTrue(
            self.henon.agrees_with(published, AGREEMENT),
            f"{self.henon} against a published {published}",
        )

    def test_the_two_published_numbers_are_not_reproduced_by_one_arrangement(
        self,
    ) -> None:
        # Two systems agreeing is only worth more than one if the estimator had
        # to do something different for each. It did: the map's interval is
        # snapped to a whole iteration and the flow's is not, and the two
        # exponents differ by more than a factor of two.
        self.assertNotAlmostEqual(self.lorenz.value, self.henon.value, places=1)

    def test_the_regular_system_reports_the_shear_and_not_an_exponent(self) -> None:
        # A regular system's answer is zero and a finite horizon cannot print
        # zero. What it prints is the separation that is linear in time, read as
        # a rate: the logarithm of the horizon over the horizon. So the claim
        # this file makes about the pendulum is that its number IS that shape,
        # which is a much stronger statement than a small number would be.
        settling = known.PENDULUM.settling
        for horizon, found in self.pendulum.items():
            with self.subTest(horizon=horizon):
                shear = math.log(horizon / settling) / (horizon - settling)
                self.assertAlmostEqual(found.value / shear, 1.0, delta=0.25)

    def test_the_regular_system_falls_as_the_horizon_is_extended(self) -> None:
        # The other half of the same claim. A constant exponent would survive a
        # longer horizon and this one has to shrink, which is what separates a
        # system with no chaos from one with a small amount of it.
        short, long = (self.pendulum[h] for h in self.PENDULUM_HORIZONS)
        self.assertLess(long.value, short.value / 2.0)

    def test_the_regular_system_is_far_below_the_chaotic_one(self) -> None:
        found = self.pendulum[self.PENDULUM_HORIZONS[0]]
        self.assertLess(found.value, self.lorenz.value / 10.0)

    def test_every_estimate_carries_what_it_was_measured_with(self) -> None:
        # A number without the separation and the interval behind it cannot be
        # rerun by anybody, which is the whole of what #82 asks of a published
        # number and is cheaper to build in here than to add later.
        for found in (self.lorenz, self.henon, *self.pendulum.values()):
            with self.subTest(found=str(found)):
                self.assertGreater(found.displacement, 0.0)
                self.assertGreater(found.interval, 0.0)
                self.assertGreater(found.intervals, 0)
                self.assertGreater(found.uncertainty, 0.0)

    def test_every_known_system_states_where_its_number_came_from(self) -> None:
        self.assertTrue(known.SYSTEMS)
        for system in known.SYSTEMS:
            with self.subTest(system=system.name):
                self.assertTrue(system.source.strip())
                self.assertTrue(math.isfinite(system.published))
                self.assertGreater(system.grain, 0.0)


class TheSnappingBites(unittest.TestCase):
    """The near-miss: an interval the flow cannot advance by, rounded silently.

    This is the one-character mistake somebody will actually make. The rule asks
    for 2.3864 iterations, a map rounds it to 2, and the growth over 2 iterations
    is divided by 2.3864. Nothing about the answer looks wrong: it is positive, it
    is stable, and it agrees with itself on every rerun.
    """

    def rounding_flow(
        self, state: tuple[float, ...], duration: float
    ) -> tuple[float, ...]:
        return known.HENON.flow(state, float(round(duration)))

    def test_a_rounded_interval_reports_the_wrong_exponent(self) -> None:
        system = known.HENON
        chosen = by_the_rule(
            system.flow,
            system.start,
            grain=system.grain,
            pilot=system.pilot_interval,
            horizon=system.suite_horizon,
            settling=system.settling,
        )
        self.assertNotAlmostEqual(chosen.asked, chosen.interval, places=3)
        careless = largest_exponent(
            self.rounding_flow,
            system.start,
            displacement=chosen.displacement,
            interval=chosen.asked,
            horizon=system.suite_horizon,
            settling=system.settling,
        )
        self.assertFalse(
            careless.agrees_with(system.published, AGREEMENT),
            f"a rounded interval reported {careless}, which agrees with the "
            f"published exponent, so this near-miss no longer bites",
        )
        # And it is wrong by exactly the ratio of the two durations, which is
        # what says the cause is the rounding rather than anything else.
        honest = largest_exponent(
            system.flow,
            system.start,
            displacement=chosen.displacement,
            interval=chosen.interval,
            horizon=system.suite_horizon,
            settling=system.settling,
        )
        self.assertAlmostEqual(
            honest.value / careless.value, chosen.asked / chosen.interval, delta=0.02
        )


if __name__ == "__main__":
    unittest.main()
