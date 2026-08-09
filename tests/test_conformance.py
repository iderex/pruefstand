"""The conformance suite, shown to bite, on a machine with no engine.

Issue #33. `adapters/conformance.py` refuses an adapter that breaks the contract
in `adapters/interface.py`. This file is the proof that each of those refusals
happens, and it is the reason the contract is a mechanism rather than a
description.

Every adapter below is a stand-in for an engine and none of them is one. The
clean one stores the case's state the way an engine plausibly would, which is a
scalar-last quaternion and an angular velocity in the body frame, and converts on
the way out. So the round trip the suite checks is a real conversion here and not
an identity: the state comes back through a representation this project does not
use, which is exactly the surface a real adapter has.

Each wrong adapter below is the clean one with ONE thing changed, so what a
refusal proves is that thing and not the rest of the shape. The one-character
mistakes are the ones worth having, and three of them are in here: a quaternion
read scalar-last, a rotation matrix transposed, and a body-frame angular velocity
returned under the world-frame name. Each of those produces a plausible
trajectory, none of them raises anything, and every one is a wrong number for
every case that engine ever runs.

    python -m unittest discover -s tests -k conformance

## What a green here does not cover

No engine. The clean adapter passes because it converts correctly between two
conventions this file wrote down, which proves the suite accepts a correct adapter
and says nothing about whether any engine can be driven this way. That is what
`harness/engine/test_conformance.py` is for, and it has run against nothing:

    git ls-files 'adapters/*/__init__.py' | wc -l
    0

The last test in this file reds the day that count moves, so the sentence above
expires rather than being read later as a covered case.
"""

from __future__ import annotations

import math
import unittest
from pathlib import Path
from typing import Any

import casefile
from adapters import conformance, interface

REPO_ROOT = Path(__file__).resolve().parent.parent

# What the fixture's frame discrepancy is, and therefore the ceiling on any
# adapter's declared tolerance. It is quoted in `adapters/conformance.py` and is
# asserted here, so the number in that docstring cannot drift away from the number
# the code computes.
CEILING = 1.7673147085885486

# A tolerance a careful adapter could declare. Far below the ceiling and far above
# what a double-precision round trip through a quaternion costs.
TOLERANCE = 1e-9


class Engine:
    """The state a plausible engine holds, in the engine's own conventions.

    Scalar-last quaternion, because several of these engines store one, and the
    angular velocity in the body frame, because several report only that. Neither
    is what this project's record carries, which is the point of it.
    """

    def __init__(self, case: casefile.Case) -> None:
        state = case.content["initial"]["probe"]
        components = tuple(
            state["orientation"][key] for key in casefile.QUATERNION_COMPONENTS
        )
        rotation = interface.rotation_from_quaternion(*components)
        w, x, y, z = components
        self.quaternion_scalar_last = (x, y, z, w)
        self.position = tuple(state["placement"])
        self.velocity = tuple(state["velocity"])
        self.angular_velocity_body = interface.apply_transpose(
            rotation, tuple(state["angular_velocity"])
        )
        self.time = 0.0


class Conforming:
    """An adapter that meets every property in the contract.

    The near-miss this whole file rests on. If it were refused, every test below
    would pass for the wrong reason, so it is asserted first and on its own.
    """

    ENGINE_MODULE = "engine_of_no_consequence"

    def __init__(self) -> None:
        self.engine: Engine | None = None
        self.closed = False

    # The interface, in the order a run uses it.

    def identify(self) -> interface.Identification:
        return interface.Identification(
            engine_module=self.ENGINE_MODULE,
            version="0.0.0",
            build="a fixture, not a build of anything",
        )

    def build(self, case: Any) -> None:
        for index, constraint in enumerate(case.content.get("constraint", []) or []):
            raise interface.CannotExpress(
                interface.CANNOT_EXPRESS,
                f"constraint[{index}].kind",
                f"this engine has no equivalent of {constraint['kind']!r} and the "
                f"case admits no substitution for it",
            )
        self.engine = Engine(case)

    def configuration(self) -> interface.Configuration:
        effective = {
            "solver": "the accurate one",
            "iterations": "40",
            "timestep": "0.001",
        }
        return interface.Configuration(
            effective=effective,
            source={
                "solver": "step 2",
                "iterations": "step 3",
                "timestep": "step 5",
            },
            absent=(
                interface.AbsentSetting(
                    step=4,
                    setting="solver tolerance",
                    related=None,
                ),
            ),
            deviation=(),
        )

    def departures(self) -> tuple[interface.Departure, ...]:
        return ()

    def rotation(self) -> tuple[float, ...]:
        x, y, z, w = self.engine.quaternion_scalar_last
        return interface.rotation_from_quaternion(w, x, y, z)

    def body_state(self) -> interface.BodyState:
        rotation = self.rotation()
        body = self.engine.angular_velocity_body
        return interface.BodyState(
            position=self.engine.position,
            rotation=rotation,
            velocity=self.engine.velocity,
            angular_velocity=interface.apply(rotation, body),
            angular_velocity_body=body,
        )

    def state(self) -> interface.State:
        return interface.State(
            time=self.engine.time, bodies={"probe": self.body_state()}
        )

    def step(self, seconds: float) -> interface.State:
        self.engine.time += seconds
        return self.state()

    def diagnostics(self) -> interface.Diagnostics:
        return interface.Diagnostics(
            contact_normal=None,
            slip=None,
            contact_force=None,
            not_reported=("contact_normal", "slip", "contact_force"),
        )

    def close(self) -> None:
        self.closed = True
        self.engine = None


# Each class below is the clean adapter with one method changed.


class BodyFrameUnderTheWorldName(Conforming):
    """The engine's own angular velocity returned under the bare name.

    The mistake this project is most likely to make and the one that cannot be
    seen in a trajectory. The convention states that the bare name is the world
    frame and the body one carries `_body`, so this adapter has returned the right
    numbers under the wrong names and every metric over rotation is wrong.
    """

    def body_state(self) -> interface.BodyState:
        clean = super().body_state()
        body = clean.angular_velocity_body
        return interface.BodyState(
            position=clean.position,
            rotation=clean.rotation,
            velocity=clean.velocity,
            angular_velocity=body,
            angular_velocity_body=body,
        )


class ScalarLastQuaternion(Conforming):
    """The engine's quaternion handed to the conversion without being reordered."""

    def rotation(self) -> tuple[float, ...]:
        return interface.rotation_from_quaternion(*self.engine.quaternion_scalar_last)


class TransposedRotation(Conforming):
    """The world-to-body matrix returned where the body-to-world one belongs.

    Still orthogonal, still with determinant one, so nothing about the shape of
    the matrix gives it away. Only the comparison against the case does.
    """

    def rotation(self) -> tuple[float, ...]:
        clean = super().rotation()
        return tuple(clean[3 * (index % 3) + index // 3] for index in range(9))


class DegreesPerSecond(Conforming):
    """An angular velocity in the engine's units rather than in the convention's."""

    def body_state(self) -> interface.BodyState:
        clean = super().body_state()
        return interface.BodyState(
            position=clean.position,
            rotation=clean.rotation,
            velocity=clean.velocity,
            angular_velocity=tuple(math.degrees(c) for c in clean.angular_velocity),
            angular_velocity_body=tuple(
                math.degrees(c) for c in clean.angular_velocity_body
            ),
        )


class TimeThatDoesNotMove(Conforming):
    """A step that does not advance the clock and does not say so."""

    def step(self, seconds: float) -> interface.State:
        return self.state()


class ClampedStepDeclared(TimeThatDoesNotMove):
    """The same engine, disclosing the clamp. This one has to pass.

    A step the engine did not take is not a defect the suite refuses. Reporting it
    as taken is, and the difference between the two is this one departure entry.
    """

    def departures(self) -> tuple[interface.Departure, ...]:
        return (
            interface.Departure(
                kind=interface.CLAMPED,
                field="timestep",
                asked="0.001",
                given="0.0",
                why="this fixture engine advances nothing",
                admitted_by=None,
                expected_effect=interface.MOVES_THE_MEASUREMENT,
            ),
        )


class BuildsTheProbe(Conforming):
    """An adapter that does not read the constraint block at all."""

    def build(self, case: Any) -> None:
        self.engine = Engine(case)


class RefusesWithTheWrongSituation(Conforming):
    def build(self, case: Any) -> None:
        if case.content.get("constraint"):
            raise interface.CannotExpress(
                interface.CLAMPED, conformance.PROBE_FIELD, "the wrong situation"
            )
        self.engine = Engine(case)


class RefusesNamingTheWrongField(Conforming):
    def build(self, case: Any) -> None:
        if case.content.get("constraint"):
            raise interface.CannotExpress(
                interface.CANNOT_EXPRESS, "contact.model", "the wrong field"
            )
        self.engine = Engine(case)


class CrashesOnTheProbe(Conforming):
    """A refusal that arrives as a crash, which a record cannot carry."""

    def build(self, case: Any) -> None:
        if case.content.get("constraint"):
            raise ValueError("a constraint I did not expect")
        self.engine = Engine(case)


class UnadmittedSubstitution(Conforming):
    def departures(self) -> tuple[interface.Departure, ...]:
        return (
            interface.Departure(
                kind=interface.SUBSTITUTION,
                field="contact.model",
                asked="none",
                given="a friction cone",
                why="the engine has no frictionless option",
                admitted_by=None,
                expected_effect=interface.MOVES_THE_MEASUREMENT,
            ),
        )


class ReadBackClaimedForSomethingUnread(Conforming):
    def departures(self) -> tuple[interface.Departure, ...]:
        return (
            interface.Departure(
                kind=interface.NOT_READ_BACK,
                field="body.probe.inertia",
                asked="the case's tensor",
                given="the case's tensor",
                why="the engine exposes no read-back",
                admitted_by=None,
                expected_effect=None,
            ),
        )


class DepartureSayingNothingAboutTheMeasurement(Conforming):
    """A departure list that looks complete and answers #37's question with nothing.

    Every other field is filled in and correct. What is missing is the one field
    that says whether the number the run produced is expected to have moved, which
    is what makes a departure something a reader can act on rather than a note.
    """

    def departures(self) -> tuple[interface.Departure, ...]:
        return (
            interface.Departure(
                kind=interface.CLAMPED,
                field="timestep",
                asked="0.001",
                given="0.0",
                why="this fixture engine advances nothing",
                admitted_by=None,
                expected_effect=None,
            ),
        )


class DepartureWithAnEffectOutsideTheVocabulary(Conforming):
    def departures(self) -> tuple[interface.Departure, ...]:
        return (
            interface.Departure(
                kind=interface.CLAMPED,
                field="timestep",
                asked="0.001",
                given="0.0",
                why="this fixture engine advances nothing",
                admitted_by=None,
                expected_effect="probably fine",
            ),
        )


class UnreadQuantityWithAnEffectStated(Conforming):
    """The other direction: a judgement about a value the engine never reported."""

    def departures(self) -> tuple[interface.Departure, ...]:
        return (
            interface.Departure(
                kind=interface.NOT_READ_BACK,
                field="body.probe.inertia",
                asked="the case's tensor",
                given=None,
                why="the engine exposes no read-back",
                admitted_by=None,
                expected_effect=interface.LEAVES_THE_MEASUREMENT,
            ),
        )


class EffectNotKnownDeclared(TimeThatDoesNotMove):
    """An adapter author who cannot judge the effect and says so. This has to pass.

    The near-miss for the whole field. If the vocabulary refused this, an author
    who does not know would have to choose one of the other two, and the record
    would then carry a judgement nobody made rather than an open question.
    """

    def departures(self) -> tuple[interface.Departure, ...]:
        return (
            interface.Departure(
                kind=interface.CLAMPED,
                field="timestep",
                asked="0.001",
                given="0.0",
                why="this fixture engine advances nothing",
                admitted_by=None,
                expected_effect=interface.EFFECT_NOT_KNOWN,
            ),
        )


class SettingWithNoSource(Conforming):
    def configuration(self) -> interface.Configuration:
        clean = super().configuration()
        return interface.Configuration(
            effective=dict(clean.effective) | {"restitution": "0.0"},
            source=clean.source,
            absent=clean.absent,
            deviation=clean.deviation,
        )


class DeviationAdmittedByNobody(Conforming):
    def configuration(self) -> interface.Configuration:
        clean = super().configuration()
        return interface.Configuration(
            effective=clean.effective,
            source=clean.source,
            absent=clean.absent,
            deviation=(
                interface.Deviation(
                    setting="iterations",
                    procedure_value="40",
                    used_value="8",
                    why="the run was slow",
                    admitted_by="whoever was watching",
                ),
            ),
        )


class UndisclosedMissingSlip(Conforming):
    def diagnostics(self) -> interface.Diagnostics:
        return interface.Diagnostics(
            contact_normal=None,
            slip=None,
            contact_force=None,
            not_reported=("contact_normal", "contact_force"),
        )


class SlipBothReportedAndNot(Conforming):
    def diagnostics(self) -> interface.Diagnostics:
        return interface.Diagnostics(
            contact_normal=(0.0, 0.0, 1.0),
            slip=(0.1, 0.0, 0.0),
            contact_force=None,
            not_reported=("slip", "contact_force"),
        )


class ReportsAnEngineItDoesNotDeclare(Conforming):
    def identify(self) -> interface.Identification:
        return interface.Identification(
            engine_module="engine_something_else",
            version="0.0.0",
            build="a fixture",
        )


class ReportsNoVersion(Conforming):
    def identify(self) -> interface.Identification:
        return interface.Identification(
            engine_module=self.ENGINE_MODULE, version="  ", build="a fixture"
        )


class Package:
    """What an adapter package looks like to the conformance suite.

    The suite reads four module-level names out of a package. This carries the
    same four, so a fixture is a package as far as the suite is concerned and the
    declaration checks are driven by the same code that will read a real one.
    """

    def __init__(
        self, adapter: type[Conforming] | None = None, **overrides: Any
    ) -> None:
        self.ENGINE_MODULE = Conforming.ENGINE_MODULE
        self.STATE_TOLERANCE = TOLERANCE
        self.TOLERANCE_WHY = (
            "the fixture engine stores what it was given, so the only error is the "
            "conversion, which costs a few units in the last place"
        )
        self._adapter = adapter or Conforming
        for name, value in overrides.items():
            setattr(self, name, value)

    def open_adapter(self) -> Conforming:
        return self._adapter()


def violations(adapter: type[Conforming] | None = None, **overrides: Any) -> list[str]:
    return conformance.conformance_violations(
        "the fixture adapter", Package(adapter, **overrides)
    )


class TheFixturesAreCases(unittest.TestCase):
    def test_the_conformance_case_is_a_valid_case(self) -> None:
        # Every refusal below is driven through this case, so a fixture that had
        # stopped being a case would turn the whole file into a green over
        # nothing.
        self.assertEqual(casefile.problems_of(conformance.CONFORMANCE_CASE), [])

    def test_the_probe_case_is_a_valid_case(self) -> None:
        # A probe that no longer parses would be refused by the reader rather
        # than by the adapter, and the refusal path would stop being reached.
        self.assertEqual(casefile.problems_of(conformance.PROBE_CASE), [])

    def test_the_probe_differs_only_by_its_constraint(self) -> None:
        clean = conformance.conformance_case().content
        probe = conformance.probe_case().content
        self.assertNotIn("constraint", clean)
        self.assertEqual(len(probe["constraint"]), 1)
        self.assertEqual(
            probe["constraint"][0]["kind"], conformance.PROBE_CONSTRAINT_KIND
        )
        self.assertEqual(
            {key: value for key, value in probe.items() if key != "constraint"}, clean
        )

    def test_no_case_file_carries_the_probe_constraint(self) -> None:
        # The probe is not physics. A case in `cases/` that acquired it would be
        # a case every adapter is required to refuse.
        for path in sorted((REPO_ROOT / "cases").rglob("*.toml")):
            with self.subTest(case=path.name):
                self.assertNotIn(
                    conformance.PROBE_CONSTRAINT_KIND,
                    path.read_text(encoding="utf-8"),
                )


class TheRotationConversion(unittest.TestCase):
    """The nine expressions nothing else in this tree would catch a sign in."""

    QUATERNION = (
        0.9004471023526769,
        0.11624942883566838,
        0.23249885767133677,
        0.3487482865070052,
    )

    def test_the_identity_quaternion_gives_the_identity_matrix(self) -> None:
        self.assertEqual(
            interface.rotation_from_quaternion(1.0, 0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
        )

    def test_the_matrix_is_orthogonal_with_determinant_one(self) -> None:
        r = interface.rotation_from_quaternion(*self.QUATERNION)
        for row in range(3):
            for column in range(3):
                product = sum(r[3 * row + k] * r[3 * column + k] for k in range(3))
                want = 1.0 if row == column else 0.0
                self.assertAlmostEqual(product, want, places=15)
        determinant = (
            r[0] * (r[4] * r[8] - r[5] * r[7])
            - r[1] * (r[3] * r[8] - r[5] * r[6])
            + r[2] * (r[3] * r[7] - r[4] * r[6])
        )
        self.assertAlmostEqual(determinant, 1.0, places=15)

    def test_a_rotation_about_z_turns_x_towards_y(self) -> None:
        # A sign convention has to be pinned by a case somebody can check by
        # hand. A quarter turn about z takes the body x axis to world y.
        half = math.sqrt(0.5)
        r = interface.rotation_from_quaternion(half, 0.0, 0.0, half)
        turned = interface.apply(r, (1.0, 0.0, 0.0))
        for found, want in zip(turned, (0.0, 1.0, 0.0)):
            self.assertAlmostEqual(found, want, places=15)

    def test_the_transpose_undoes_the_rotation(self) -> None:
        r = interface.rotation_from_quaternion(*self.QUATERNION)
        world = (0.3, -1.1, 2.7)
        again = interface.apply(r, interface.apply_transpose(r, world))
        for found, want in zip(again, world):
            self.assertAlmostEqual(found, want, places=14)


class TheCeilingIsDerived(unittest.TestCase):
    def test_the_ceiling_is_the_frame_error_on_the_fixture(self) -> None:
        self.assertEqual(conformance.tolerance_ceiling(), CEILING)

    def test_the_ceiling_is_the_number_the_module_quotes(self) -> None:
        # A number written beside the command that produced it is still a number
        # that drifts, unless something reads both. This reads the source rather
        # than the docstring, because that is where the command and its output
        # are.
        source = (REPO_ROOT / "adapters" / "conformance.py").read_text(encoding="utf-8")
        self.assertIn(repr(CEILING), source)


class TheSuiteAcceptsAConformingAdapter(unittest.TestCase):
    def test_the_clean_adapter_passes(self) -> None:
        self.assertEqual(violations(), [])

    def test_a_step_the_engine_did_not_take_passes_when_it_is_declared(self) -> None:
        # The other near-miss. The suite refuses an undisclosed clamp and accepts
        # a disclosed one, and if it accepted both the departure vocabulary would
        # be decoration.
        self.assertEqual(violations(ClampedStepDeclared), [])

    def test_the_clean_adapter_satisfies_the_protocol(self) -> None:
        # Structural, so this checks the method names exist and nothing about
        # what they return. What they return is every other test in this file.
        self.assertIsInstance(Conforming(), interface.Adapter)

    def test_every_adapter_is_closed_after_a_run(self) -> None:
        opened: list[Conforming] = []

        class Recording(Package):
            def open_adapter(self) -> Conforming:
                adapter = Conforming()
                opened.append(adapter)
                return adapter

        self.assertEqual(
            conformance.conformance_violations("recording", Recording()), []
        )
        self.assertTrue(opened)
        self.assertTrue(all(adapter.closed for adapter in opened))


class TheStateCheckBites(unittest.TestCase):
    def assertRefused(self, found: list[str], fragment: str) -> None:
        self.assertTrue(found, "the suite accepted this adapter")
        self.assertTrue(
            any(fragment in sentence for sentence in found),
            f"no refusal mentioned {fragment!r}: {found}",
        )

    def test_a_body_frame_angular_velocity_under_the_world_name_is_refused(
        self,
    ) -> None:
        # The deliberately wrong implementation #33's last done-when asks for.
        self.assertRefused(
            violations(BodyFrameUnderTheWorldName), "angular_velocity[0]"
        )

    def test_a_scalar_last_quaternion_is_refused(self) -> None:
        self.assertRefused(violations(ScalarLastQuaternion), "rotation[0]")

    def test_a_transposed_rotation_is_refused(self) -> None:
        self.assertRefused(violations(TransposedRotation), "rotation[1]")

    def test_an_angular_velocity_in_degrees_is_refused(self) -> None:
        self.assertRefused(violations(DegreesPerSecond), "angular_velocity[0]")

    def test_a_step_that_does_not_advance_the_clock_is_refused(self) -> None:
        self.assertRefused(violations(TimeThatDoesNotMove), "departure saying")


class TheRefusalCheckBites(unittest.TestCase):
    def test_an_adapter_that_builds_the_probe_is_refused(self) -> None:
        found = violations(BuildsTheProbe)
        self.assertTrue(any("built the probe case" in s for s in found), found)

    def test_a_refusal_outside_the_vocabulary_is_refused(self) -> None:
        found = violations(RefusesWithTheWrongSituation)
        self.assertTrue(any("with the situation" in s for s in found), found)

    def test_a_refusal_naming_the_wrong_field_is_refused(self) -> None:
        found = violations(RefusesNamingTheWrongField)
        self.assertTrue(any("naming the field" in s for s in found), found)

    def test_a_crash_where_a_refusal_belongs_is_refused(self) -> None:
        found = violations(CrashesOnTheProbe)
        self.assertTrue(any("became a crash" in s for s in found), found)


class TheDepartureCheckBites(unittest.TestCase):
    def test_a_substitution_nobody_admitted_is_refused(self) -> None:
        found = violations(UnadmittedSubstitution)
        self.assertTrue(any("names nothing as admitting it" in s for s in found), found)

    def test_a_not_read_back_entry_carrying_a_value_is_refused(self) -> None:
        # The negative disclosure turning into a positive one, in one field.
        found = violations(ReadBackClaimedForSomethingUnread)
        self.assertTrue(any("read back and agreed" in s for s in found), found)

    def test_a_departure_saying_nothing_about_the_measurement_is_refused(
        self,
    ) -> None:
        # #37's second done-when. Without this the list can be complete in every
        # field a reader checks and still leave the one question the report card
        # needs answered.
        found = violations(DepartureSayingNothingAboutTheMeasurement)
        self.assertTrue(
            any("expected effect None on the measurement" in s for s in found), found
        )

    def test_an_effect_outside_the_vocabulary_is_refused(self) -> None:
        found = violations(DepartureWithAnEffectOutsideTheVocabulary)
        self.assertTrue(
            any("'probably fine'" in s for s in found), found
        )

    def test_an_effect_stated_for_a_quantity_nobody_read_is_refused(self) -> None:
        # The other direction, and the one that would read as knowledge. Nothing
        # was substituted for a quantity the engine never reported, so there is
        # no effect on the measurement to state.
        found = violations(UnreadQuantityWithAnEffectStated)
        self.assertTrue(
            any("never reported" in s for s in found), found
        )

    def test_an_author_who_cannot_judge_the_effect_and_says_so_passes(self) -> None:
        # The near-miss. A vocabulary refusing this would turn an author who does
        # not know into an author who has to pick, and the record would then carry
        # a judgement nobody made.
        self.assertEqual(violations(EffectNotKnownDeclared), [])


class TheConfigurationCheckBites(unittest.TestCase):
    def test_a_setting_with_no_stated_source_is_refused(self) -> None:
        found = violations(SettingWithNoSource)
        self.assertTrue(any("restitution" in s for s in found), found)

    def test_a_deviation_admitted_by_nobody_is_refused(self) -> None:
        found = violations(DeviationAdmittedByNobody)
        self.assertTrue(any("hand-tuned run" in s for s in found), found)


class TheDiagnosticsCheckBites(unittest.TestCase):
    def test_an_absent_diagnostic_that_is_not_disclosed_is_refused(self) -> None:
        found = violations(UndisclosedMissingSlip)
        self.assertTrue(any("read an absence as a" in s for s in found), found)

    def test_a_diagnostic_both_reported_and_named_unreported_is_refused(self) -> None:
        found = violations(SlipBothReportedAndNot)
        self.assertTrue(any("names slip as unreported" in s for s in found), found)


class TheDeclarationCheckBites(unittest.TestCase):
    def test_a_package_declaring_no_engine_is_refused(self) -> None:
        found = violations(ENGINE_MODULE=None)
        self.assertTrue(any("declares no ENGINE_MODULE" in s for s in found), found)

    def test_a_package_with_no_factory_is_refused(self) -> None:
        # An instance attribute shadows the method, which is how a package that
        # declares the name and does not supply a callable is reached.
        found = violations(open_adapter=None)
        self.assertTrue(any("no open_adapter()" in s for s in found), found)

    def test_a_tolerance_at_the_ceiling_is_refused(self) -> None:
        # At the ceiling rather than above it. A tolerance equal to the error it
        # has to distinguish distinguishes nothing, and this is the one-character
        # version of widening it until the suite goes quiet.
        found = violations(STATE_TOLERANCE=CEILING)
        self.assertTrue(any("could not distinguish" in s for s in found), found)

    def test_a_tolerance_that_is_not_positive_is_refused(self) -> None:
        found = violations(STATE_TOLERANCE=0.0)
        self.assertTrue(any("greater than zero" in s for s in found), found)

    def test_a_tolerance_that_is_not_a_float_is_refused(self) -> None:
        found = violations(STATE_TOLERANCE=1)
        self.assertTrue(any("as a finite float" in s for s in found), found)

    def test_a_tolerance_with_no_reason_is_refused(self) -> None:
        found = violations(TOLERANCE_WHY="   ")
        self.assertTrue(any("somebody widened" in s for s in found), found)

    def test_a_declaration_defect_stops_the_run(self) -> None:
        # An adapter that cannot be opened produces one finding rather than a
        # list of consequences of the same defect.
        self.assertEqual(len(violations(ENGINE_MODULE=None, TOLERANCE_WHY="")), 2)


class TheIdentificationCheckBites(unittest.TestCase):
    def test_an_engine_other_than_the_declared_one_is_refused(self) -> None:
        found = violations(ReportsAnEngineItDoesNotDeclare)
        self.assertTrue(any("and the package declares" in s for s in found), found)

    def test_an_empty_version_is_refused(self) -> None:
        found = violations(ReportsNoVersion)
        self.assertTrue(any("reports no version" in s for s in found), found)


class TheAdaptersInThisTree(unittest.TestCase):
    def test_there_is_still_no_adapter_package(self) -> None:
        # The trigger. Every green in this file is over adapters written in this
        # file, and the number of real adapters the conformance suite has ever
        # run against is zero. The day the first one lands this reds, and whoever
        # lands it is the person who reads that.
        #
        # Repairing it is deleting this test, once
        # `harness/engine/test_conformance.py` has been run on a machine with the
        # engine installed and the run is recorded on the adapter's own issue.
        # The first adapter is #34 and the second is #35.
        packages = sorted(
            path.parent.name
            for path in (REPO_ROOT / "adapters").glob("*/__init__.py")
        )
        self.assertEqual(
            packages,
            [],
            f"adapters/{', adapters/'.join(packages)} now exists, so the "
            f"conformance suite has a real subject. Run it through "
            f"harness/engine/test_conformance.py with the engine installed, "
            f"record the run on that adapter's issue, and delete this test. #33.",
        )


if __name__ == "__main__":
    unittest.main()
