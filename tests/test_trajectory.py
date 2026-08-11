"""A chaotic case cannot ask for trajectory comparison, and a long one cannot either.

Issue #76. The fixture is a case rather than a table: the text below goes through
`casefile.loads`, so every refusal here fires on something the schema already
accepted, and a refusal that fired because the fixture was malformed shows up as
`test_the_fixture_is_a_case` failing rather than as a green.

The fixture is the double pendulum because that is the chaotic case in this
suite, and it is deliberately not the case file #74 owes: it lives here, nothing
walks it, and its parameters are chosen for a refusal rather than sourced for a
measurement.

Every fixture below is the clean case with one thing changed.

    python -m unittest discover -s tests -k trajectory
"""

from __future__ import annotations

import math
import unittest

import casefile
from metrics.lyapunov import Estimate
from metrics.trajectory import (
    ALTERNATIVES,
    MEASURED,
    REFUSED_CLASS,
    ROUNDING,
    SAMPLES_FLOOR,
    TOLERANCE,
    TOLERANCE_VALUE,
    TRAJECTORY,
    TRAJECTORY_HORIZON,
    Comparison,
    ComparisonRefused,
    Window,
    admit,
    compare,
)

# A thin cylinder of length 0.3 m and radius 0.005 m at 0.5 kg, about its centre
# of mass, with the long axis along the body's x. Computed rather than quoted:
#
#     python -c "m, L, r = 0.5, 0.3, 0.005; print(repr(m*r*r/2), repr(m*(3*r*r+L*L)/12))"
#     6.25e-06 0.003753125
AXIAL = 6.25e-06
TRANSVERSE = 0.003753125

CLEAN_CLASS = "integrable"
CLEAN_TOLERANCE = 1e-06
CLEAN_TRAJECTORY_HORIZON = 2.0
CASE_HORIZON = 100.0


def case_text(
    declared_class: str = CLEAN_CLASS,
    tolerance: float = CLEAN_TOLERANCE,
    trajectory_horizon: float | None = CLEAN_TRAJECTORY_HORIZON,
) -> str:
    """The fixture case, with the one thing each test changes."""
    block = ""
    trajectory_provenance = ""
    if trajectory_horizon is not None:
        block = f"""
[measured.trajectory]
horizon_seconds = {trajectory_horizon!r}
why = \"\"\"
Over the first seconds the two links have not yet separated, so agreement there
is a statement about the integrator rather than about the horizon. Whether that
window survives the divergence rate is decided by metrics/trajectory.py and not
by this field.
\"\"\"
"""
        trajectory_provenance = """
[[provenance]]
field = "measured.trajectory.horizon_seconds"
kind = "chosen"
why = "A short early window, held against the divergence rate rather than asserted."
"""
    return f"""
format = 1
id = "double-pendulum-fixture"
title = "Double pendulum, released horizontal, as a fixture"
class = "{declared_class}"
convention = "{casefile.CONVENTION}"
summary = \"\"\"
Two identical thin rods, the first pinned to the world and the second pinned to
the far end of the first, released from rest with both lying along the world x
axis. It exists to be refused: it is a fixture in tests/ and not a case file.
\"\"\"

[horizon]
seconds = {CASE_HORIZON!r}
why = \"\"\"
Long enough that the two links have separated many times over, which is what
makes the early-window question worth asking at all.
\"\"\"

[[body]]
id = "upper"
mass = 0.5
inertia = {{ xx = {AXIAL!r}, yy = {TRANSVERSE!r}, zz = {TRANSVERSE!r}, xy = 0.0, xz = 0.0, yz = 0.0 }}

[[body.geometry]]
kind = "none"
why = "Neither rod touches the world; both joints are constraints and not contacts."

[[body]]
id = "lower"
mass = 0.5
inertia = {{ xx = {AXIAL!r}, yy = {TRANSVERSE!r}, zz = {TRANSVERSE!r}, xy = 0.0, xz = 0.0, yz = 0.0 }}

[[body.geometry]]
kind = "none"
why = "Neither rod touches the world; both joints are constraints and not contacts."

[initial.upper]
placement = [0.15, 0.0, 0.0]
orientation = "identity"
velocity = [0.0, 0.0, 0.0]
angular_velocity = [0.0, 0.0, 0.0]

[initial.lower]
placement = [0.45, 0.0, 0.0]
orientation = "identity"
velocity = [0.0, 0.0, 0.0]
angular_velocity = [0.0, 0.0, 0.0]

[[constraint]]
kind = "A revolute joint between the world and the upper rod, at the world origin, about the world y axis."
holds = "For the whole horizon."

[[constraint]]
kind = "A revolute joint between the two rods, at the far end of the upper rod, about the world y axis."
holds = "For the whole horizon."

[contact]
model = "None. Neither body has geometry that touches anything."
dissipation = "none"

[measured]
quantity = "the largest Lyapunov exponent of the two-link motion"
units = "per second"
why = \"\"\"
The exponent is an invariant of the dynamics rather than a property of one
trajectory, so it survives the separation that makes a late trajectory
comparison meaningless here.
\"\"\"
{block}
[reference]
kind = "computed"
statement = "Computed by this project's own reference integration."
bound = "Computed with the run."

[tolerance]
value = {tolerance!r}
units = "dimensionless"
why = \"\"\"
Placeholder, because this is a fixture and not a case. It is the number the
horizon ceiling is derived from and it is here to be varied by a test.
\"\"\"

[[provenance]]
field = "horizon.seconds"
kind = "chosen"
why = "Long against the divergence rate, for the reason in the horizon's own field."

[[provenance]]
field = "body.upper.mass"
kind = "chosen"
why = "A round mass. Nothing in this fixture depends on its value."

[[provenance]]
field = "body.upper.inertia"
kind = "chosen"
why = "A thin cylinder about its centre of mass, from the standard expressions."

[[provenance]]
field = "body.lower.mass"
kind = "chosen"
why = "The same rod again, so the two links are identical."

[[provenance]]
field = "body.lower.inertia"
kind = "chosen"
why = "The same rod again, so the two links are identical."

[[provenance]]
field = "initial.upper.placement"
kind = "chosen"
why = "The centre of a rod pinned at the origin and lying along the world x axis."

[[provenance]]
field = "initial.upper.velocity"
kind = "chosen"
why = "Released from rest."

[[provenance]]
field = "initial.upper.angular_velocity"
kind = "chosen"
why = "Released from rest."

[[provenance]]
field = "initial.lower.placement"
kind = "chosen"
why = "The centre of the second rod, pinned to the far end of the first."

[[provenance]]
field = "initial.lower.velocity"
kind = "chosen"
why = "Released from rest."

[[provenance]]
field = "initial.lower.angular_velocity"
kind = "chosen"
why = "Released from rest."

[[provenance]]
field = "tolerance.value"
kind = "chosen"
why = "A placeholder, for the reason in the tolerance's own field."
{trajectory_provenance}"""


def case(declared_class: str = CLEAN_CLASS, **changed: object) -> casefile.Case:
    return casefile.loads(case_text(declared_class, **changed))  # type: ignore[arg-type]


def estimate(value: float, uncertainty: float) -> Estimate:
    """An estimate whose exponent and uncertainty are the test's own.

    Every other field is a working value, so a test that changed one of them
    would be testing `Estimate` rather than this module.
    """
    return Estimate(value, uncertainty, 200, 20, 40, 0.5, 1.0e-06, CASE_HORIZON)


def ceiling(rate: float, tolerance: float = CLEAN_TOLERANCE) -> float:
    """The ceiling in seconds, from the same two numbers `admit` uses."""
    return math.log(tolerance / ROUNDING) / rate


def run(times: tuple[float, ...], offset: float = 0.0) -> list[tuple[float, tuple[float, ...]]]:
    return [(at, (at, offset, 0.0)) for at in times]


TIMES = (0.0, 0.5, 1.0, 1.5, 2.0)


class TheFixtureIsACase(unittest.TestCase):
    """Everything below rests on the fixture passing the schema."""

    def test_the_fixture_is_a_case(self) -> None:
        self.assertEqual([], casefile.problems_of(case_text()))

    def test_the_chaotic_fixture_is_a_case(self) -> None:
        # The refused combination is refused by this module and not by the
        # schema, which is what makes the refusal below worth having.
        self.assertEqual([], casefile.problems_of(case_text(REFUSED_CLASS)))

    def test_the_fixture_without_a_block_is_a_case(self) -> None:
        self.assertEqual([], casefile.problems_of(case_text(trajectory_horizon=None)))

    def test_the_fields_this_module_reads_are_fields_of_a_case(self) -> None:
        # The names are held in one block rather than written at each point of
        # use, and this is what binds that block to the schema that decides
        # them: a field renamed in `casefile.py` reds here rather than showing
        # up as a comparison that quietly stopped being made.
        content = case().content
        self.assertIn(MEASURED, content)
        self.assertIn(TRAJECTORY, content[MEASURED])
        self.assertIn(TRAJECTORY_HORIZON, content[MEASURED][TRAJECTORY])
        self.assertIn(TOLERANCE, content)
        self.assertIn(TOLERANCE_VALUE, content[TOLERANCE])

    def test_the_refused_class_is_one_the_schema_knows(self) -> None:
        # So this module cannot drift into refusing a class that does not exist,
        # which would be a refusal nothing could ever trip.
        self.assertIn(REFUSED_CLASS, casefile.CLASSES)


class TheChaoticClassIsRefused(unittest.TestCase):
    """Not overridable, however short the horizon."""

    def test_a_chaotic_case_is_refused(self) -> None:
        with self.assertRaises(ComparisonRefused) as refusal:
            admit(case(REFUSED_CLASS), estimate(1.0, 0.05), spread=1.0)
        self.assertIn(REFUSED_CLASS, str(refusal.exception))

    def test_the_refusal_names_the_alternative_metrics(self) -> None:
        with self.assertRaises(ComparisonRefused) as refusal:
            admit(case(REFUSED_CLASS), estimate(1.0, 0.05), spread=1.0)
        self.assertIn(ALTERNATIVES, str(refusal.exception))

    def test_a_shorter_horizon_does_not_buy_it(self) -> None:
        # The whole of the class refusal: a horizon far inside the ceiling still
        # does not make trajectory agreement a statement about the engine here.
        inside = ceiling(1.05) / 100.0
        self.assertLess(inside, ceiling(1.05))
        with self.assertRaises(ComparisonRefused):
            admit(
                case(REFUSED_CLASS, trajectory_horizon=inside),
                estimate(1.0, 0.05),
                spread=1.0,
            )

    def test_the_same_case_in_another_class_is_admitted(self) -> None:
        # So the refusal above fired for the class and not for the horizon.
        window = admit(case(), estimate(1.0, 0.05), spread=1.0)
        self.assertEqual(CLEAN_CLASS, window.case_class)


class ALongHorizonIsRefused(unittest.TestCase):
    """The second refusal, derived from the tolerance and the divergence rate."""

    def test_a_horizon_past_the_ceiling_is_refused(self) -> None:
        # rate = 12.0 + 0.5 = 12.5, so the ceiling is 1.778 s and the case asks
        # for 2.0 s.
        self.assertLess(ceiling(12.5), CLEAN_TRAJECTORY_HORIZON)
        with self.assertRaises(ComparisonRefused) as refusal:
            admit(case(), estimate(12.0, 0.5), spread=1.0)
        self.assertIn(repr(ceiling(12.5)), str(refusal.exception))

    def test_the_refusal_shows_the_computation(self) -> None:
        with self.assertRaises(ComparisonRefused) as refusal:
            admit(case(), estimate(12.0, 0.5), spread=1.0)
        message = str(refusal.exception)
        for number in (
            repr(CLEAN_TRAJECTORY_HORIZON),
            repr(ROUNDING),
            repr(CLEAN_TOLERANCE),
            repr(1.0 / 12.5),
            repr(math.log(CLEAN_TOLERANCE / ROUNDING)),
        ):
            self.assertIn(number, message)

    def test_the_refusal_names_the_alternative_metrics(self) -> None:
        with self.assertRaises(ComparisonRefused) as refusal:
            admit(case(), estimate(12.0, 0.5), spread=1.0)
        self.assertIn(ALTERNATIVES, str(refusal.exception))

    def test_a_horizon_inside_the_ceiling_is_admitted(self) -> None:
        window = admit(case(), estimate(1.0, 0.05), spread=1.0)
        self.assertEqual(1.0 / 1.05, window.divergence_time)
        self.assertEqual(ceiling(1.05), window.ceiling)

    def test_a_horizon_exactly_at_the_ceiling_is_admitted(self) -> None:
        # The boundary, in the direction that a strict comparison decides.
        exact = ceiling(12.5)
        window = admit(
            case(trajectory_horizon=exact), estimate(12.0, 0.5), spread=1.0
        )
        self.assertEqual(exact, window.horizon)

    def test_a_tighter_tolerance_shortens_the_window(self) -> None:
        # The ceiling is the case's, not this module's: the same divergence rate
        # buys a shorter window for a case asking a harder question.
        loose = admit(case(tolerance=1e-06), estimate(1.0, 0.05), spread=1.0)
        tight = admit(case(tolerance=1e-12), estimate(1.0, 0.05), spread=1.0)
        assert loose.ceiling is not None and tight.ceiling is not None
        self.assertLess(tight.ceiling, loose.ceiling)

    def test_a_tolerance_at_the_rounding_admits_no_window(self) -> None:
        # Against an estimate carrying no positive rate, so nothing amplifies
        # and the ceiling is not what refuses this. It is the refusal the
        # ceiling cannot make: the two runs start at the whole tolerance.
        with self.assertRaises(ComparisonRefused) as refusal:
            admit(case(tolerance=ROUNDING), estimate(-0.2, 0.05), spread=1.0)
        self.assertIn(repr(ROUNDING), str(refusal.exception))

    def test_a_tolerance_below_the_rounding_admits_no_window(self) -> None:
        with self.assertRaises(ComparisonRefused):
            admit(case(tolerance=1e-17), estimate(-0.2, 0.05), spread=1.0)

    def test_the_same_case_with_a_workable_tolerance_is_admitted(self) -> None:
        # So the two above fired for the tolerance and not for the estimate.
        window = admit(case(), estimate(-0.2, 0.05), spread=1.0)
        self.assertEqual(CLEAN_TOLERANCE, window.tolerance)


class TheRateIsTheUpperEndOfTheEstimate(unittest.TestCase):
    """The direction that fails closed, and the case where it decides."""

    def test_the_spread_can_turn_an_admission_into_a_refusal(self) -> None:
        # One estimate, two spreads. At one uncertainty the upper end is 2.8 and
        # the ceiling is 7.9 s; at five it is 14.8 and the ceiling is 1.5 s.
        admitted = admit(case(), estimate(-0.2, 3.0), spread=1.0)
        self.assertEqual(ceiling(2.8), admitted.ceiling)
        with self.assertRaises(ComparisonRefused):
            admit(case(), estimate(-0.2, 3.0), spread=5.0)

    def test_an_upper_end_at_or_below_zero_bounds_nothing(self) -> None:
        window = admit(case(), estimate(-0.2, 0.05), spread=1.0)
        self.assertIsNone(window.divergence_time)
        self.assertIsNone(window.ceiling)
        self.assertIn("not positive", str(window))

    def test_an_upper_end_above_zero_from_a_negative_value_still_bounds(self) -> None:
        window = admit(case(), estimate(-0.2, 0.05), spread=5.0)
        self.assertEqual(1.0 / (-0.2 + 5.0 * 0.05), window.divergence_time)

    def test_a_spread_that_is_not_positive_is_refused(self) -> None:
        with self.assertRaises(ComparisonRefused):
            admit(case(), estimate(1.0, 0.05), spread=0.0)

    def test_a_spread_that_is_not_a_float_is_refused(self) -> None:
        with self.assertRaises(ComparisonRefused):
            admit(case(), estimate(1.0, 0.05), spread=1)  # type: ignore[arg-type]

    def test_a_rate_that_is_not_an_estimate_is_refused(self) -> None:
        # A bare exponent invites exactly the comparison the uncertainty exists
        # to hold back, so it is refused at the boundary.
        with self.assertRaises(ComparisonRefused):
            admit(case(), 1.0, spread=1.0)  # type: ignore[arg-type]


class ACaseThatAskedForNothingGetsNothing(unittest.TestCase):
    def test_a_case_with_no_block_is_refused(self) -> None:
        with self.assertRaises(ComparisonRefused) as refusal:
            admit(case(trajectory_horizon=None), estimate(1.0, 0.05), spread=1.0)
        self.assertIn("declares no [measured.trajectory] block",
                      str(refusal.exception))


class TheComparisonCarriesWhatAdmittedIt(unittest.TestCase):
    """Done-when three: the divergence time travels with the result."""

    def window(self) -> Window:
        return admit(case(), estimate(1.0, 0.05), spread=1.0)

    def test_the_result_carries_the_divergence_time(self) -> None:
        found = compare(self.window(), run(TIMES), run(TIMES, offset=0.25))
        self.assertEqual(1.0 / 1.05, found.divergence_time)

    def test_the_result_carries_the_horizon(self) -> None:
        found = compare(self.window(), run(TIMES), run(TIMES, offset=0.25))
        self.assertEqual(CLEAN_TRAJECTORY_HORIZON, found.window.horizon)

    def test_the_result_carries_the_divergence_time_when_there_was_none(self) -> None:
        window = admit(case(), estimate(-0.2, 0.05), spread=1.0)
        found = compare(window, run(TIMES), run(TIMES, offset=0.25))
        self.assertIsNone(found.divergence_time)

    def test_the_separations_are_the_distances(self) -> None:
        found = compare(self.window(), run(TIMES), run(TIMES, offset=0.25))
        self.assertEqual(tuple(0.25 for _ in TIMES), found.separations)
        self.assertEqual(0.25, found.largest)

    def test_the_largest_carries_the_time_it_was_reached(self) -> None:
        engine = [(at, (at, 0.1 * index, 0.0)) for index, at in enumerate(TIMES)]
        found = compare(self.window(), run(TIMES), engine)
        self.assertEqual(TIMES[-1], found.at)

    def test_a_comparison_prints_its_window(self) -> None:
        found = compare(self.window(), run(TIMES), run(TIMES, offset=0.25))
        self.assertIsInstance(found, Comparison)
        self.assertIn("divergence time(s)", str(found))


class TheComparisonRefusesRunsItCannotMeasure(unittest.TestCase):
    """Each fixture is the working call with one thing changed."""

    def setUp(self) -> None:
        self.admitted = admit(case(), estimate(1.0, 0.05), spread=1.0)

    def test_the_working_call_is_not_refused(self) -> None:
        compare(self.admitted, run(TIMES), run(TIMES, offset=0.25))

    def test_runs_of_different_lengths_are_refused(self) -> None:
        with self.assertRaises(ComparisonRefused):
            compare(self.admitted, run(TIMES), run(TIMES[:-1], offset=0.25))

    def test_runs_at_different_times_are_refused(self) -> None:
        shifted = [(at + 0.01, state) for at, state in run(TIMES, offset=0.25)]
        with self.assertRaises(ComparisonRefused) as refusal:
            compare(self.admitted, run(TIMES), shifted)
        self.assertIn("not a", str(refusal.exception))

    def test_a_sample_past_the_admitted_window_is_refused(self) -> None:
        past = TIMES + (CLEAN_TRAJECTORY_HORIZON + 0.5,)
        with self.assertRaises(ComparisonRefused) as refusal:
            compare(self.admitted, run(past), run(past, offset=0.25))
        self.assertIn("reaches past what was judged", str(refusal.exception))

    def test_fewer_samples_than_the_floor_are_refused(self) -> None:
        one = TIMES[:1]
        self.assertLess(len(one), SAMPLES_FLOOR)
        with self.assertRaises(ComparisonRefused):
            compare(self.admitted, run(one), run(one, offset=0.25))

    def test_times_that_do_not_increase_are_refused(self) -> None:
        repeated = (0.0, 0.5, 0.5, 1.0)
        with self.assertRaises(ComparisonRefused):
            compare(self.admitted, run(repeated), run(repeated, offset=0.25))

    def test_a_time_before_zero_is_refused(self) -> None:
        early = (-0.5, 0.0, 0.5)
        with self.assertRaises(ComparisonRefused):
            compare(self.admitted, run(early), run(early, offset=0.25))

    def test_a_state_that_is_not_finite_is_refused(self) -> None:
        engine = run(TIMES, offset=0.25)
        engine[2] = (engine[2][0], (float("nan"), 0.0, 0.0))
        with self.assertRaises(ComparisonRefused):
            compare(self.admitted, run(TIMES), engine)

    def test_states_in_different_phase_spaces_are_refused(self) -> None:
        engine = run(TIMES, offset=0.25)
        engine[2] = (engine[2][0], (0.0, 0.0))
        with self.assertRaises(ComparisonRefused):
            compare(self.admitted, run(TIMES), engine)

    def test_every_problem_is_reported_rather_than_the_first(self) -> None:
        engine = run(TIMES, offset=0.25)
        engine[1] = (engine[1][0], (float("inf"), 0.0, 0.0))
        engine[3] = (engine[3][0], (0.0, 0.0))
        with self.assertRaises(ComparisonRefused) as refusal:
            compare(self.admitted, run(TIMES), engine)
        self.assertEqual(2, len(refusal.exception.problems))


if __name__ == "__main__":
    unittest.main()
