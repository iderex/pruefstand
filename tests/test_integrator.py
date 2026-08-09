"""What the reference integrator keeps, measured rather than argued.

Issue #43. These are the tests that matter most in this repository, because
everything downstream is compared against this output and a bug here would read as
a finding about an engine.

Four measurements answer the issue's four done-when items, and each is a number
this file computes rather than a number written into it:

- The orientation stays on the rotation group over a long horizon, and the residual
  grows like the square root of the step count rather than like the step count,
  which is the trigger `docs/decisions/reference-integration.md` writes for
  reconsidering the whole configuration choice.
- The free rotation of a symmetric body is reproduced against its elementary
  closed form. Elementary is the point: the asymmetric top's closed form is
  elliptic and is #44's, and using it here would test this integrator against
  another piece of unwritten code.
- Energy and angular momentum behave as the method class predicts rather than
  merely being small. For a free body this method conserves energy to rounding, so
  the band and its scaling are measured on the heavy top, where energy is not
  conserved exactly and the prediction has content: a band that does not walk and
  that shrinks with the square of the step.
- The step is fixed, and the places a variable step could enter are refused.

Every refusal below is tripped by a fixture that is a valid object with one thing
changed, so what a test proves is that thing and not the rest of the shape.

    python -m unittest discover -s tests -k integrator
"""

from __future__ import annotations

import math
import unittest

from reference import integrator
from reference.integrator import (
    Body,
    IntegrationRefused,
    State,
    advance,
    angular_velocity_body,
    cross,
    dot,
    energy,
    every_step,
    exponential,
    hat,
    matmul,
    matvec,
    norm,
    off_the_group,
    scale,
    shifted_to_the_pivot,
    spatial_momentum,
    trajectory,
    transpose,
)

# A body whose principal axes are skewed relative to its geometry, which is the
# shape the rattleback needs and the one a diagonal tensor would silently replace.
SKEWED = (
    (2.0, 0.3, -0.7),
    (0.3, 3.5, 0.11),
    (-0.7, 0.11, 4.25),
)

# A symmetric body, for the case whose motion is elementary.
TRANSVERSE = 2.0
AXIAL = 3.0
SYMMETRIC = (
    (TRANSVERSE, 0.0, 0.0),
    (0.0, TRANSVERSE, 0.0),
    (0.0, 0.0, AXIAL),
)

# A heavy symmetric top about its pivot: a small fast top of the kind a lecture
# demonstration uses, whose numbers are here to exercise the integrator and are
# not a case of this suite. The cases carry parameters that are sourced rather
# than invented, and they are #52 to #54 and #68.
TOP = Body(
    inertia=((0.02, 0.0, 0.0), (0.0, 0.02, 0.0), (0.0, 0.0, 0.008)),
    mass=0.3,
    gravity=9.81,
    centre_of_mass=(0.0, 0.0, 0.05),
)
TOP_TILT = 0.4
TOP_SPIN = 120.0

# The horizons the long measurements run over, kept where a reader can see all of
# them at once. They are a compromise between a horizon long enough for a walk to
# show and a suite that stays quick enough to be run on every change.
LONG_STEP = 2e-3
LONG_STEPS = 16000
SHORT_STEPS = 1000

_RUNS: dict[tuple[str, float, int], tuple[State, ...]] = {}


def free_run(step: float, count: int) -> tuple[State, ...]:
    """The free skewed body, run once per horizon and remembered."""
    key = ("free", step, count)
    if key not in _RUNS:
        start = State(integrator.IDENTITY, matvec(SKEWED, (1.1, -0.4, 0.9)))
        _RUNS[key] = every_step(Body(inertia=SKEWED), start, step, count)
    return _RUNS[key]


def top_run(step: float, count: int) -> tuple[State, ...]:
    """The heavy symmetric top, tilted and spinning, run once per horizon."""
    key = ("top", step, count)
    if key not in _RUNS:
        start = State(
            exponential((TOP_TILT, 0.0, 0.0)),
            matvec(TOP.inertia, (0.0, 0.0, TOP_SPIN)),
        )
        _RUNS[key] = every_step(TOP, start, step, count)
    return _RUNS[key]


def band(body: Body, states: tuple[State, ...]) -> float:
    """The widest the energy departs from its initial value along a run."""
    start = energy(body, states[0])
    return max(abs(energy(body, state) - start) for state in states)


class TheIdentityTheSolveRestsOn(unittest.TestCase):
    """The three scalar equations one step solves are nine, written smaller.

    The module replaces `F Jd - Jd F^T` with a vector expression in `f`. Every
    number this project publishes goes through that replacement, and an algebraic
    slip in it would produce a plausible trajectory rather than an error, so the
    two sides are compared directly here.
    """

    def test_the_closed_form_matches_the_matrix_expression(self) -> None:
        for inertia in (SYMMETRIC, SKEWED):
            body = Body(inertia=inertia)
            dual = body._dual_inertia
            for rotation_vector in (
                (0.1, 0.0, 0.0),
                (0.3, -0.2, 0.5),
                (1.0, 1.0, 0.0),
                (2.5, -1.25, 0.75),
                (1e-9, 2e-9, -3e-9),
            ):
                with self.subTest(inertia=inertia[0][0], f=rotation_vector):
                    turn = exponential(rotation_vector)
                    left = matmul(turn, dual)
                    right = matmul(dual, transpose(turn))
                    first, second = integrator._coefficients(norm(rotation_vector))
                    closed = hat(
                        integrator.subtract(
                            scale(matvec(inertia, rotation_vector), first),
                            scale(
                                cross(
                                    rotation_vector, matvec(dual, rotation_vector)
                                ),
                                second,
                            ),
                        )
                    )
                    worst = max(
                        abs(left[row][column] - right[row][column]
                            - closed[row][column])
                        for row in range(3)
                        for column in range(3)
                    )
                    self.assertLess(worst, 1e-14)

    def test_the_exponential_is_a_rotation_at_every_size(self) -> None:
        for rotation_vector in (
            (0.0, 0.0, 0.0),
            (1e-14, 0.0, 0.0),
            (0.5, -0.25, 0.125),
            (math.pi, 0.0, 0.0),
            (0.0, 0.0, 40.0),
        ):
            with self.subTest(f=rotation_vector):
                self.assertLess(off_the_group(exponential(rotation_vector)), 1e-15)

    def test_the_exponential_of_nothing_is_the_identity(self) -> None:
        self.assertEqual(exponential((0.0, 0.0, 0.0)), integrator.IDENTITY)

    def test_the_second_coefficient_survives_a_small_angle(self) -> None:
        # The one-character mistake this guards. Written as `(1 - cos(phi)) / phi**2`
        # the coefficient subtracts two nearly equal numbers, and at the step sizes
        # this reference runs at that is where its digits go. The comparison is
        # against the series, which converges to well past binary64 at this angle.
        angle = 1e-3
        squared = angle * angle
        series = (
            0.5
            - squared / 24.0
            + squared * squared / 720.0
            - squared**3 / 40320.0
        )
        _, second = integrator._coefficients(angle)
        direct = (1.0 - math.cos(angle)) / squared
        # One ulp of a number near a half is 1.1e-16, so the bound below is two
        # of them. The direct form is four orders of magnitude worse than that,
        # and the gap between the two bounds is the whole content of this test.
        self.assertLess(abs(second - series), 2.3e-16 * series)
        self.assertGreater(abs(direct - series), 1e-11 * series)


class TheStepIsFixed(unittest.TestCase):
    """One step per run, and no route to a second one."""

    def setUp(self) -> None:
        self.body = Body(inertia=SKEWED)
        self.start = State(integrator.IDENTITY, (0.5, -0.2, 0.3))

    def test_a_run_at_a_step_of_zero_is_refused(self) -> None:
        with self.assertRaises(IntegrationRefused) as refused:
            advance(self.body, self.start, 0.0)
        self.assertIn("a run has one step", str(refused.exception))

    def test_a_run_at_a_negative_step_is_refused(self) -> None:
        with self.assertRaises(IntegrationRefused):
            advance(self.body, self.start, -1e-3)

    def test_a_step_that_is_an_integer_is_refused(self) -> None:
        # An integer where a float belongs is refused rather than widened, which
        # is the rule casefile applies to every number in a case file.
        with self.assertRaises(IntegrationRefused):
            advance(self.body, self.start, 1)

    def test_a_sequence_of_steps_is_refused(self) -> None:
        # The shape a variable step would arrive in. It is refused at the same
        # place a bad scalar is, so there is one door and it is shut.
        with self.assertRaises(IntegrationRefused) as refused:
            trajectory(self.body, self.start, (1e-3, 2e-3), (1e-3,))  # type: ignore[arg-type]
        self.assertIn("a run has one step", str(refused.exception))

    def test_a_requested_time_off_the_grid_is_refused(self) -> None:
        with self.assertRaises(IntegrationRefused) as refused:
            trajectory(self.body, self.start, 1e-3, (0.0015,))
        message = str(refused.exception)
        self.assertIn("is not on the grid of the step", message)
        self.assertIn("neither interpolates", message)

    def test_a_requested_time_on_the_grid_is_reached_by_stepping(self) -> None:
        samples = trajectory(self.body, self.start, 1e-3, (0.002, 0.005))
        stepped = every_step(self.body, self.start, 1e-3, 5)
        self.assertEqual([sample.time for sample in samples], [0.002, 0.005])
        self.assertEqual(samples[0].state, stepped[2])
        self.assertEqual(samples[1].state, stepped[5])

    def test_requested_times_that_do_not_increase_are_refused(self) -> None:
        with self.assertRaises(IntegrationRefused) as refused:
            trajectory(self.body, self.start, 1e-3, (0.003, 0.002))
        self.assertIn("strictly increasing", str(refused.exception))

    def test_a_negative_requested_time_is_refused(self) -> None:
        with self.assertRaises(IntegrationRefused):
            trajectory(self.body, self.start, 1e-3, (-0.001,))

    def test_a_run_reporting_at_no_time_at_all_is_refused(self) -> None:
        with self.assertRaises(IntegrationRefused):
            trajectory(self.body, self.start, 1e-3, ())

    def test_a_step_too_large_for_the_method_is_refused(self) -> None:
        # Not truncated at the last iterate. A step that breaks the contraction
        # would otherwise produce a trajectory with an unrecorded error in it.
        with self.assertRaises(IntegrationRefused) as refused:
            advance(self.body, State(integrator.IDENTITY, (400.0, 0.0, 0.0)), 5.0)
        self.assertIn("did not converge", str(refused.exception))

    def test_the_solve_is_as_accurate_at_a_small_step_as_at_a_large_one(self) -> None:
        # The one property of the solve that a trajectory measurement would hide.
        # Its tolerance is relative to the right-hand side, which scales with the
        # step, so an absolute floor under that tolerance loosens the solve as the
        # step shrinks: at the bottom of this ladder a floor at the module's own
        # constant returns the first guess untouched. The error would then enter a
        # convergence study as the method's, which is the study the whole choice
        # of method rests on.
        for step in (1e-2, 1e-4, 1e-6, 1e-8):
            with self.subTest(step=step):
                target = scale(self.start.momentum, step)
                rotation_vector = integrator._solve(self.body, target)
                first, second = integrator._coefficients(norm(rotation_vector))
                residual = integrator.subtract(
                    integrator.subtract(
                        scale(matvec(SKEWED, rotation_vector), first),
                        scale(
                            cross(
                                rotation_vector,
                                matvec(self.body._dual_inertia, rotation_vector),
                            ),
                            second,
                        ),
                    ),
                    target,
                )
                self.assertLess(
                    norm(residual) / norm(target), integrator.SOLVE_TOLERANCE
                )

    def test_a_whole_number_of_steps_is_required(self) -> None:
        for count in (0, -1, 2.0, True):
            with self.subTest(count=count):
                with self.assertRaises(IntegrationRefused):
                    every_step(self.body, self.start, 1e-3, count)  # type: ignore[arg-type]


class ABodyIsRefused(unittest.TestCase):
    """Each fixture is the skewed body with one thing changed."""

    def test_the_skewed_body_is_accepted(self) -> None:
        # The near-miss. If this were refused every test below would pass for the
        # wrong reason, and a skewed tensor is the shape the deciding case needs.
        self.assertEqual(Body(inertia=SKEWED).inertia, SKEWED)

    def test_an_inertia_that_is_not_symmetric_is_refused(self) -> None:
        wrong = ((2.0, 0.3, -0.7), (0.31, 3.5, 0.11), (-0.7, 0.11, 4.25))
        with self.assertRaises(IntegrationRefused) as refused:
            Body(inertia=wrong)
        self.assertIn("symmetric", str(refused.exception))

    def test_an_inertia_that_is_not_positive_definite_is_refused(self) -> None:
        wrong = ((2.0, 0.3, -0.7), (0.3, 3.5, 0.11), (-0.7, 0.11, -4.25))
        with self.assertRaises(IntegrationRefused) as refused:
            Body(inertia=wrong)
        self.assertIn("positive definite", str(refused.exception))

    def test_an_inertia_of_three_components_is_refused(self) -> None:
        # Refused rather than read as a diagonal tensor, which is the refusal
        # docs/decisions/units-frames-and-inertia.md asks for by name.
        with self.assertRaises(IntegrationRefused):
            Body(inertia=(2.0, 3.5, 4.25))  # type: ignore[arg-type]

    def test_an_inertia_carrying_an_integer_is_refused(self) -> None:
        wrong = ((2, 0.3, -0.7), (0.3, 3.5, 0.11), (-0.7, 0.11, 4.25))
        with self.assertRaises(IntegrationRefused):
            Body(inertia=wrong)  # type: ignore[arg-type]

    def test_a_negative_mass_is_refused(self) -> None:
        with self.assertRaises(IntegrationRefused):
            Body(inertia=SKEWED, mass=-1.0, gravity=9.81)

    def test_a_negative_gravity_is_refused(self) -> None:
        # The direction of the vertical is the world frame's, not this number's,
        # so a negative here is somebody encoding the direction twice.
        with self.assertRaises(IntegrationRefused) as refused:
            Body(inertia=SKEWED, mass=1.0, gravity=-9.81)
        self.assertIn("fixed by the world frame", str(refused.exception))

    def test_the_parallel_axis_shift_is_the_theorem(self) -> None:
        offset = (0.0, 0.0, 0.05)
        shifted = shifted_to_the_pivot(SYMMETRIC, 0.3, offset)
        added = 0.3 * dot(offset, offset)
        self.assertAlmostEqual(shifted[0][0], TRANSVERSE + added)
        self.assertAlmostEqual(shifted[1][1], TRANSVERSE + added)
        self.assertAlmostEqual(shifted[2][2], AXIAL)


class AStateIsRefused(unittest.TestCase):
    def test_a_rotation_is_accepted(self) -> None:
        turn = exponential((0.3, -0.2, 0.15))
        self.assertEqual(State(turn, (1.0, 0.0, 0.0)).orientation, turn)

    def test_an_orientation_slightly_off_the_group_is_refused(self) -> None:
        stretched = tuple(
            tuple(entry * (1.0 + 1e-9) for entry in row) for row in exponential(
                (0.3, -0.2, 0.15)
            )
        )
        with self.assertRaises(IntegrationRefused) as refused:
            State(stretched, (1.0, 0.0, 0.0))  # type: ignore[arg-type]
        self.assertIn("off the group", str(refused.exception))

    def test_a_reflection_is_refused(self) -> None:
        # The near-miss worth having. A reflection satisfies `R^T R = I` exactly,
        # so a residual that read orthogonality alone would accept it, and a
        # reflected rattleback is the mirror body rather than the same one.
        reflection = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))
        with self.assertRaises(IntegrationRefused):
            State(reflection, (1.0, 0.0, 0.0))

    def test_a_momentum_that_is_not_three_floats_is_refused(self) -> None:
        with self.assertRaises(IntegrationRefused):
            State(integrator.IDENTITY, (1.0, 0.0))  # type: ignore[arg-type]

    def test_a_momentum_carrying_an_infinity_is_refused(self) -> None:
        with self.assertRaises(IntegrationRefused):
            State(integrator.IDENTITY, (1.0, 0.0, math.inf))


class TheOrientationStaysOnTheGroup(unittest.TestCase):
    """The first done-when item, measured over a long horizon."""

    def test_the_residual_stays_near_the_working_precision(self) -> None:
        states = free_run(LONG_STEP, LONG_STEPS)
        worst = max(off_the_group(state.orientation) for state in states)
        self.assertLess(worst, 1e-13)

    def test_the_body_actually_turned(self) -> None:
        # Without this the measurement above passes on a run that did nothing,
        # which is the same green as a run that kept the group.
        states = free_run(LONG_STEP, LONG_STEPS)
        turned = math.acos(
            max(-1.0, min(1.0, (
                states[0].orientation[2][2] * states[-1].orientation[2][2]
                + states[0].orientation[2][1] * states[-1].orientation[2][1]
                + states[0].orientation[2][0] * states[-1].orientation[2][0]
            )))
        )
        self.assertGreater(turned, 0.5)
        self.assertGreater(norm(states[-1].momentum), 1.0)

    def test_the_residual_grows_like_the_square_root_of_the_step_count(self) -> None:
        # The trigger docs/decisions/reference-integration.md writes for
        # reconsidering the configuration variable: growth like the step count
        # would mean the update is not doing what that note says it does. Sixteen
        # times the steps is four times the residual under a square root and
        # sixteen under a linear law, and the bound below refuses the second.
        short = max(
            off_the_group(state.orientation)
            for state in free_run(LONG_STEP, SHORT_STEPS)
        )
        long = max(
            off_the_group(state.orientation)
            for state in free_run(LONG_STEP, SHORT_STEPS * 16)
        )
        self.assertGreater(short, 0.0)
        self.assertLess(long / short, 10.0)


class TheFreeSymmetricTop(unittest.TestCase):
    """The second done-when item, against a solution that needs no code.

    A torque-free symmetric body precesses at a constant rate about the fixed
    spatial angular momentum while turning about its own axis at a constant rate,
    so its orientation is a product of two exponentials and its body angular
    velocity is a circle. Both are written out here rather than imported, because
    an oracle that shares this module's arithmetic tests nothing.
    """

    STEP = 1e-3
    STEPS = 4000
    # The tolerance. The error is second order in the step, so at this step and
    # this horizon it measures near 2e-6; the bound sits about five times above
    # that, which is room for the last bits to fall differently on another machine
    # and is far below an error one order larger.
    TOLERANCE = 1e-5

    def setUp(self) -> None:
        self.body = Body(inertia=SYMMETRIC)
        self.velocity = (0.7, 0.0, 1.3)
        self.start = State(
            exponential((0.3, -0.2, 0.15)), matvec(SYMMETRIC, self.velocity)
        )
        self.spatial = spatial_momentum(self.start)
        self.rate = (AXIAL - TRANSVERSE) * self.velocity[2] / TRANSVERSE
        self.horizon = self.STEP * self.STEPS

    def exact_orientation(self, time: float) -> tuple[tuple[float, ...], ...]:
        return matmul(
            matmul(
                exponential(scale(self.spatial, time / TRANSVERSE)),
                self.start.orientation,
            ),
            exponential((0.0, 0.0, -self.rate * time)),
        )

    def test_the_orientation_matches_the_closed_form(self) -> None:
        reached = every_step(self.body, self.start, self.STEP, self.STEPS)[-1]
        expected = self.exact_orientation(self.horizon)
        worst = max(
            abs(reached.orientation[row][column] - expected[row][column])
            for row in range(3)
            for column in range(3)
        )
        self.assertLess(worst, self.TOLERANCE)

    def test_the_body_angular_velocity_matches_the_closed_form(self) -> None:
        reached = every_step(self.body, self.start, self.STEP, self.STEPS)[-1]
        radius = math.hypot(self.velocity[0], self.velocity[1])
        phase = math.atan2(self.velocity[1], self.velocity[0])
        angle = self.rate * self.horizon + phase
        expected = (
            radius * math.cos(angle),
            radius * math.sin(angle),
            self.velocity[2],
        )
        reached_velocity = angular_velocity_body(self.body, reached)
        for axis in range(3):
            with self.subTest(axis=axis):
                self.assertLess(
                    abs(reached_velocity[axis] - expected[axis]), self.TOLERANCE
                )

    def test_a_body_spinning_about_a_principal_axis_stays_on_it(self) -> None:
        start = State(integrator.IDENTITY, (0.0, 0.0, AXIAL * 5.0))
        reached = every_step(self.body, start, 1e-3, 500)[-1]
        self.assertLess(abs(reached.momentum[0]), 1e-14)
        self.assertLess(abs(reached.momentum[1]), 1e-14)
        self.assertLess(abs(reached.orientation[2][2] - 1.0), 1e-14)


class WhatTheMethodConserves(unittest.TestCase):
    """The third done-when item: behaviour that matches the prediction.

    Small is not the claim being tested anywhere below. Each quantity is checked
    against what the class of method says about it, and the two statements differ
    where it matters: an energy error that is small on the first step and walks is
    what a general-purpose explicit method gives, and it is the outcome the design
    note refuses the class for.
    """

    def test_the_free_body_keeps_its_spatial_angular_momentum(self) -> None:
        # Exact for this update, not merely small: the momentum is multiplied by
        # the transpose of the rotation the orientation is multiplied by.
        states = free_run(LONG_STEP, LONG_STEPS)
        start = spatial_momentum(states[0])
        worst = max(
            max(abs(component - start[axis])
                for axis, component in enumerate(spatial_momentum(state)))
            for state in states
        )
        self.assertLess(worst, 1e-13 * norm(start))

    def test_the_free_body_keeps_the_size_of_its_body_momentum(self) -> None:
        states = free_run(LONG_STEP, LONG_STEPS)
        start = norm(states[0].momentum)
        worst = max(abs(norm(state.momentum) - start) for state in states)
        self.assertLess(worst, 1e-13 * start)

    def test_the_free_body_keeps_its_energy_to_rounding(self) -> None:
        # This method is exactly energy conserving on a free body, which is why
        # the energy band below is measured on the heavy top instead. Recorded
        # here so a reader does not take the heavy top's band for the method's
        # behaviour everywhere.
        body = Body(inertia=SKEWED)
        states = free_run(LONG_STEP, LONG_STEPS)
        self.assertLess(band(body, states), 1e-12 * abs(energy(body, states[0])))

    def test_the_heavy_top_keeps_the_vertical_spatial_momentum(self) -> None:
        # Gravity breaks the rotational symmetry down to rotations about the
        # vertical, and the vertical component of the spatial angular momentum is
        # the momentum map that survives. Exact for this update, because the
        # moment is perpendicular to the vertical at both ends of every step.
        states = top_run(4e-4, 5000)
        start = dot(integrator.VERTICAL, spatial_momentum(states[0]))
        worst = max(
            abs(dot(integrator.VERTICAL, spatial_momentum(state)) - start)
            for state in states
        )
        self.assertLess(worst, 1e-12 * abs(start))

    def test_the_heavy_top_keeps_the_momentum_about_its_own_axis(self) -> None:
        # The second momentum map, and it is conserved for the separate reason
        # that a symmetric top's own axis is a symmetry of its inertia tensor.
        states = top_run(4e-4, 5000)
        start = states[0].momentum[2]
        worst = max(abs(state.momentum[2] - start) for state in states)
        self.assertLess(worst, 1e-12 * abs(start))

    def test_the_heavy_top_energy_band_does_not_walk(self) -> None:
        states = top_run(4e-4, 5000)
        start = energy(TOP, states[0])
        errors = [energy(TOP, state) - start for state in states]
        tenth = len(errors) // 10
        first = max(abs(error) for error in errors[:tenth])
        last = max(abs(error) for error in errors[-tenth:])
        # A walk shows as the band at the end of the run being wider than the
        # band at the start. Oscillation within a band shows as these two being
        # the same number, which is what the class predicts and what is measured.
        self.assertLess(abs(last - first), 0.01 * first)

    def test_the_heavy_top_energy_band_is_second_order_in_the_step(self) -> None:
        coarse = band(TOP, top_run(8e-4, 2500))
        fine = band(TOP, top_run(4e-4, 5000))
        # Same horizon, half the step. A second-order band quarters; a band that
        # halved would say the method is first order and a band that did not move
        # would say it is the solve rather than the method being measured.
        self.assertGreater(coarse / fine, 3.6)
        self.assertLess(coarse / fine, 4.4)

    def test_the_heavy_top_energy_band_is_not_at_rounding(self) -> None:
        # Without this the two tests above would pass on a band made of noise,
        # and a ratio of four between two rounding errors is a coincidence rather
        # than a measurement of the method.
        states = top_run(4e-4, 5000)
        self.assertGreater(band(TOP, states), 1e-10 * abs(energy(TOP, states[0])))


if __name__ == "__main__":
    unittest.main()
