"""The suite every adapter passes, and the fixtures that make it reachable.

Issue #33. `interface.py` states the contract. This is the mechanism that refuses
a violation of it, because a contract nothing refuses is a description.

It is written as functions returning sentences a reader can act on rather than as
`unittest` cases, for one reason: the same operators have to run in two places.
`tests/test_conformance.py` runs them against deliberately wrong adapters written
in that file, on any machine and with no engine, which is what proves each
refusal bites. `harness/engine/test_conformance.py` runs them against every real
adapter package in the tree, which needs the engine installed and is therefore
the engine half of the gate. One implementation, two callers, and the empty list
is the only passing verdict in both.

## The two fixtures

`CONFORMANCE_CASE` is a valid case file whose numbers exist to make the boundary
conversion visible. Its orientation is a rotation about no coordinate axis and its
angular velocity lies along no principal direction of it, so the world-frame and
body-frame angular velocities differ in every component. An adapter that reports
the engine's own body-frame vector under the bare name is then wrong by a quantity
this file computes rather than assumes.

`PROBE_CASE` is that case with one constraint added, whose `kind` is
`inexpressible-probe`. No engine expresses it, because it is not physics: its
whole job is to make the refusal path reachable in every adapter. An adapter that
builds it has demonstrated that it does not read the constraint block, which is
the failure that would otherwise first appear as a plausible number for the
Chaplygin sleigh.

Both are fixtures and their vocabularies are fixture vocabularies. Neither is a
case of this suite, neither lives in `cases/`, and no metric is computed from
either. The cases of this suite are sourced rather than invented and belong to the
issues that write them.

## What this suite cannot check

An engine's version read from a literal in the adapter rather than from the
engine. A literal and a read are indistinguishable at every surface this project
has, so `Identification` states the requirement and nothing here enforces it.

Whether the physics is right. Every property below is about the boundary: the
conventions a state is returned in, the vocabulary a departure is written in, and
whether a refusal happens where one is owed. An adapter that converts correctly
and drives the engine into nonsense passes this suite, and the reference
comparison is what catches that.

What the engine did inside a step. Subdivided timesteps, solver iterations,
contact limits and non-finite events are #41's, and the `clamped` and
`not-read-back` kinds below are the shape it writes into rather than the asking.

Anything about an adapter that does not exist. THERE IS NO ADAPTER PACKAGE IN THIS
TREE, so the count of real adapters this suite has run against is zero:

    git ls-files 'adapters/*/__init__.py' | wc -l
    0

That is stated here rather than left to be inferred from a green.
`tests/test_conformance.py` reds the day the first one lands, which is what makes
the statement expire instead of persisting as a note nobody re-read.
"""

from __future__ import annotations

import math
from typing import Any, Callable

import casefile
from adapters import interface

# The fixture case. Every number in it is chosen, which its own provenance says,
# and the choices are made to be awkward on purpose:
#
#   The orientation is a rotation of 0.9 radians about the axis (1, 2, 3)
#   normalised, so no row or column of the matrix is a coordinate axis and a
#   transposed matrix is a different matrix.
#
#   The angular velocity is (0.3, -1.1, 2.7) in the world frame, which is along
#   no eigenvector of that rotation, so the body-frame vector differs from it in
#   every component.
#
#   The inertia carries a non-zero xy, so an engine that will not take a
#   non-diagonal tensor meets that on the fixture rather than first on the
#   rattleback.
#
# The quaternion and the discrepancy the last two produce:
#
#     python -c "
#     import math
#     ax = (1.0, 2.0, 3.0); n = math.sqrt(sum(c * c for c in ax))
#     ax = tuple(c / n for c in ax); w = math.cos(0.45); s = math.sin(0.45)
#     print((w, ax[0] * s, ax[1] * s, ax[2] * s))
#     "
#     (0.9004471023526769, 0.11624942883566838, 0.23249885767133677, 0.3487482865070052)
CONFORMANCE_CASE = """\
format = 1
id = "adapter-conformance-fixture"
title = "The fixture every adapter is driven through, which is not a case of this suite"
class = "integrable"
convention = "pruefstand-units-frames-inertia-1"
summary = \"\"\"
A single body, no reference answer and no metric. It exists to be handed to an
adapter so that the conversion at the boundary can be held against numbers this
project already knows. Its orientation is about no coordinate axis and its
angular velocity along no eigenvector of that orientation, so an adapter
reporting a body-frame angular velocity under the world-frame name is wrong by a
quantity the conformance suite computes. Nothing here is physics anybody sourced
and no number from it is publishable.
\"\"\"

[horizon]
seconds = 1.0
why = "A round number. Nothing integrates this fixture."

[[body]]
id = "probe"
mass = 0.5
inertia = { xx = 0.002, yy = 0.003, zz = 0.004, xy = 0.0005, xz = 0.0, yz = 0.0 }
[[body.geometry]]
kind = "sphere"
dimensions = [0.05]
why = "The simplest shape every engine has, so a refusal is never geometry."

[initial.probe]
placement = [0.4, -0.2, 0.35]
orientation = { w = 0.9004471023526769, x = 0.11624942883566838, y = 0.23249885767133677, z = 0.3487482865070052 }
velocity = [0.0, 0.0, 0.0]
angular_velocity = [0.3, -1.1, 2.7]

[contact]
model = \"\"\"
None. This fixture touches nothing, so an adapter that refuses it has refused
something other than a contact model it could not express.
\"\"\"
dissipation = "None."

[measured]
quantity = "Nothing. No metric is computed from this fixture."
units = "dimensionless"
why = \"\"\"
The format requires the block. What is measured about an adapter is measured by
the conformance suite rather than by a metric over this case.
\"\"\"

[reference]
kind = "none"
statement = \"\"\"
There is no reference answer. This fixture is handed to an adapter and its
trajectory is compared against nothing.
\"\"\"
bound = \"\"\"
None, because there is no reference answer to bound. A metric asked for from
this fixture is refused for exactly that reason, which is #49.
\"\"\"

[tolerance]
value = 1.0
units = "dimensionless"
why = \"\"\"
The format requires a positive number and nothing reads this one, because no
metric is computed from this fixture. It is not a tolerance anybody derived.
\"\"\"

[[provenance]]
field = "horizon.seconds"
kind = "chosen"
why = "A round number for a fixture that nothing integrates."
[[provenance]]
field = "body.probe.mass"
kind = "chosen"
why = "A round number no engine will refuse."
[[provenance]]
field = "body.probe.inertia"
kind = "chosen"
why = \"\"\"
Positive diagonal with a small non-zero xy, so an engine that will not take a
non-diagonal tensor meets that here rather than first on the rattleback.
\"\"\"
[[provenance]]
field = "body.probe.geometry.0.dimensions"
kind = "chosen"
why = "Five centimetres, far from any engine's own scale limits."
[[provenance]]
field = "initial.probe.placement"
kind = "chosen"
why = \"\"\"
Away from the origin and off both axes, so a placement dropped or permuted by an
adapter is visible in every component.
\"\"\"
[[provenance]]
field = "initial.probe.orientation"
kind = "chosen"
why = \"\"\"
A rotation of 0.9 radians about (1, 2, 3) normalised, so no row of the matrix is
a coordinate axis and a transposed matrix is a different matrix.
\"\"\"
[[provenance]]
field = "initial.probe.velocity"
kind = "chosen"
why = \"\"\"
Zero, so the one moving quantity is the angular velocity and a failure here is
not two failures at once.
\"\"\"
[[provenance]]
field = "initial.probe.angular_velocity"
kind = "chosen"
why = \"\"\"
Along no eigenvector of this orientation, so the world-frame and body-frame
vectors differ in every component.
\"\"\"
[[provenance]]
field = "tolerance.value"
kind = "chosen"
why = "Unread, as the tolerance block above says."
"""

# The constraint kind that makes the refusal path reachable. It is not physics and
# no engine expresses it. An adapter that builds a case carrying it has told us
# that it does not read the constraint block, and the next case to carry a
# constraint it cannot express would be built too.
PROBE_CONSTRAINT_KIND = "inexpressible-probe"

PROBE_CASE = CONFORMANCE_CASE + f"""
[[constraint]]
kind = "{PROBE_CONSTRAINT_KIND}"
holds = \"\"\"
Nothing. This constraint is expressible by no engine because it states no
physics, and it is here so that every adapter's refusal path is reached by the
conformance suite rather than assumed to work. An adapter that builds this case
is refused.
\"\"\"
"""

# The case field a refusal of the probe has to name. The constraint is the first
# and only entry of the block, so its path is fixed.
PROBE_FIELD = "constraint[0].kind"

# How far a state read back from an engine may sit from the case's own initial
# state before this suite says the conversion is wrong, expressed as the widest
# an adapter's own `STATE_TOLERANCE` may be. It is derived rather than chosen: it
# is the largest component difference between the fixture's world-frame angular
# velocity and its body-frame one, which is the error a frame confusion produces
# on this fixture, so a tolerance at or above it could not distinguish the
# mistake the read-back exists to catch.
#
#     python -c "
#     import adapters.conformance as c
#     print(c.tolerance_ceiling())
#     "
#     1.7673147085885486
#
# It is a ceiling and not a recommendation. What each adapter's tolerance should
# actually be is a property of the representation its engine stores state in, and
# `TOLERANCE_WHY` is where that reasoning goes.


def _case(text: str) -> casefile.Case:
    """The fixture as a validated case, refused loudly if it stops being one."""
    return casefile.loads(text)


def conformance_case() -> casefile.Case:
    return _case(CONFORMANCE_CASE)


def probe_case() -> casefile.Case:
    return _case(PROBE_CASE)


def _body(case: casefile.Case, body_id: str) -> dict[str, Any]:
    return case.content["initial"][body_id]


def expected_state(case: casefile.Case) -> dict[str, interface.BodyState]:
    """The case's own initial state, in the conventions a record carries.

    This is the whole of the read-back comparison and it is computed from the
    case rather than from anything an adapter said. The orientation becomes the
    body-to-world rotation matrix, the world-frame quantities stay as written, and
    the body-frame angular velocity is the world one taken back through that
    matrix.
    """
    expected: dict[str, interface.BodyState] = {}
    for body_id in case.body_ids:
        state = _body(case, body_id)
        orientation = state["orientation"]
        if orientation == casefile.IDENTITY:
            components = (1.0, 0.0, 0.0, 0.0)
        else:
            components = tuple(
                orientation[key] for key in casefile.QUATERNION_COMPONENTS
            )
        rotation = interface.rotation_from_quaternion(*components)
        angular = tuple(state["angular_velocity"])
        expected[body_id] = interface.BodyState(
            position=tuple(state["placement"]),
            rotation=rotation,
            velocity=tuple(state["velocity"]),
            angular_velocity=angular,
            angular_velocity_body=interface.apply_transpose(rotation, angular),
        )
    return expected


def tolerance_ceiling() -> float:
    """The widest a `STATE_TOLERANCE` may be, derived from the fixture itself.

    The largest component difference between the fixture's world-frame angular
    velocity and its body-frame one. A tolerance at or above this accepts an
    adapter that reported the body-frame vector under the world-frame name, which
    is the error the read-back is for.
    """
    widest = 0.0
    for expected in expected_state(conformance_case()).values():
        for world, body in zip(
            expected.angular_velocity, expected.angular_velocity_body
        ):
            widest = max(widest, abs(world - body))
    return widest


def _finite(value: Any) -> bool:
    return isinstance(value, float) and math.isfinite(value)


def _vector_problem(where: str, value: Any) -> str | None:
    if not isinstance(value, tuple) or len(value) != 3:
        return f"{where} is not three floats"
    if not all(_finite(component) for component in value):
        return f"{where} carries a value that is not a finite float"
    return None


def declaration_violations(name: str, package: Any) -> list[str]:
    """What an adapter package has to declare before it can be driven at all."""
    violations: list[str] = []
    engine = getattr(package, interface.ENGINE_DECLARATION, None)
    if not isinstance(engine, str) or not engine.strip():
        violations.append(
            f"{name} declares no {interface.ENGINE_DECLARATION}, so nothing "
            f"knows which engine it is for"
        )
    if not callable(getattr(package, interface.FACTORY, None)):
        violations.append(
            f"{name} has no {interface.FACTORY}(), so there is no way to obtain "
            f"an adapter from it"
        )

    why = getattr(package, interface.TOLERANCE_WHY_DECLARATION, None)
    if not isinstance(why, str) or not why.strip():
        violations.append(
            f"{name} declares no {interface.TOLERANCE_WHY_DECLARATION}, and a "
            f"tolerance nobody argued for is a number somebody widened"
        )

    tolerance = getattr(package, interface.TOLERANCE_DECLARATION, None)
    ceiling = tolerance_ceiling()
    if not isinstance(tolerance, float) or not math.isfinite(tolerance):
        violations.append(
            f"{name} declares no {interface.TOLERANCE_DECLARATION} as a finite "
            f"float"
        )
    elif tolerance <= 0.0:
        violations.append(
            f"{name} declares {interface.TOLERANCE_DECLARATION} as {tolerance!r}, "
            f"and a tolerance has to be greater than zero"
        )
    elif tolerance >= ceiling:
        violations.append(
            f"{name} declares {interface.TOLERANCE_DECLARATION} as {tolerance!r}, "
            f"which is at or above {ceiling!r}, the error a frame confusion "
            f"produces on this fixture, so the read-back could not distinguish it"
        )
    return sorted(violations)


def identification_violations(name: str, adapter: Any, package: Any) -> list[str]:
    violations: list[str] = []
    found = adapter.identify()
    if not isinstance(found, interface.Identification):
        return [f"{name} identify() did not return an Identification"]
    declared = getattr(package, interface.ENGINE_DECLARATION, None)
    if found.engine_module != declared:
        violations.append(
            f"{name} identify() reports the engine module {found.engine_module!r} "
            f"and the package declares {declared!r}"
        )
    for field in ("version", "build"):
        value = getattr(found, field)
        if not isinstance(value, str) or not value.strip():
            violations.append(
                f"{name} identify() reports no {field}, and a result record names "
                f"the exact engine a number came from"
            )
    return sorted(violations)


def refusal_violations(name: str, adapter: Any) -> list[str]:
    """The probe case is refused, with a situation and a field from the vocabulary."""
    try:
        adapter.build(probe_case())
    except interface.CannotExpress as refusal:
        violations: list[str] = []
        if refusal.situation not in interface.REFUSING_SITUATIONS:
            violations.append(
                f"{name} refused the probe case with the situation "
                f"{refusal.situation!r}, and a refusal carries one of "
                f"{', '.join(interface.REFUSING_SITUATIONS)}"
            )
        if refusal.field != PROBE_FIELD:
            violations.append(
                f"{name} refused the probe case naming the field "
                f"{refusal.field!r}, and the constraint it could not express is "
                f"at {PROBE_FIELD}"
            )
        if not refusal.why.strip():
            violations.append(
                f"{name} refused the probe case with no reason, and a refused "
                f"cell renders the reason rather than a blank"
            )
        return sorted(violations)
    except Exception as error:
        # Deliberately wide. Anything other than CannotExpress means the refusal
        # did not arrive in the shape a record can carry, and which exception it
        # was is a detail beside that.
        return [
            f"{name} raised {type(error).__name__} on the probe case rather than "
            f"CannotExpress, so a refusal this project can record became a crash"
        ]
    return [
        f"{name} built the probe case instead of refusing it, so it does not read "
        f"the constraint block and would build a constraint it cannot express"
    ]


def state_violations(name: str, adapter: Any, tolerance: float) -> list[str]:
    """The state at time zero is the case's own initial state, in these conventions.

    This is the round trip: the case's numbers go into the engine through the
    adapter and come back through it, and what they are held against is the case
    rather than anything the adapter said about itself.
    """
    case = conformance_case()
    adapter.build(case)
    found = adapter.state()
    if not isinstance(found, interface.State):
        return [f"{name} state() did not return a State"]

    violations: list[str] = []
    if not _finite(found.time) or found.time != 0.0:
        violations.append(
            f"{name} state() before any step reports the time {found.time!r} "
            f"rather than zero"
        )

    expected = expected_state(case)
    missing = sorted(set(expected) - set(found.bodies))
    extra = sorted(set(found.bodies) - set(expected))
    for body_id in missing:
        violations.append(f"{name} state() carries no body {body_id!r} from the case")
    for body_id in extra:
        violations.append(
            f"{name} state() carries a body {body_id!r} that the case does not"
        )

    for body_id in sorted(set(expected) & set(found.bodies)):
        want = expected[body_id]
        got = found.bodies[body_id]
        if not isinstance(got, interface.BodyState):
            violations.append(f"{name} state() body {body_id!r} is not a BodyState")
            continue

        components = interface.ROTATION_COMPONENTS
        if not isinstance(got.rotation, tuple) or len(got.rotation) != components:
            violations.append(
                f"{name} state() body {body_id!r} rotation is not "
                f"{components} floats, and a record carries "
                f"the matrix rather than the quaternion"
            )
        elif not all(_finite(component) for component in got.rotation):
            violations.append(
                f"{name} state() body {body_id!r} rotation carries a value that "
                f"is not a finite float"
            )
        else:
            for index, (a, b) in enumerate(zip(want.rotation, got.rotation)):
                if abs(a - b) > tolerance:
                    violations.append(
                        f"{name} state() body {body_id!r} rotation[{index}] is "
                        f"{b!r} and the case's own orientation gives {a!r}, a "
                        f"difference of {abs(a - b)!r} against a tolerance of "
                        f"{tolerance!r}"
                    )

        vectors = ("position", "velocity", "angular_velocity",
                   "angular_velocity_body")
        for field in vectors:
            mine = getattr(got, field)
            problem = _vector_problem(f"{name} state() body {body_id!r} {field}", mine)
            if problem is not None:
                violations.append(problem)
                continue
            theirs = getattr(want, field)
            for index, (a, b) in enumerate(zip(theirs, mine)):
                if abs(a - b) > tolerance:
                    violations.append(
                        f"{name} state() body {body_id!r} {field}[{index}] is "
                        f"{b!r} and the case says {a!r}, a difference of "
                        f"{abs(a - b)!r} against a tolerance of {tolerance!r}"
                    )
    return sorted(violations)


def step_violations(name: str, adapter: Any, tolerance: float) -> list[str]:
    """A step advances the time by the amount it was given, or says it did not."""
    case = conformance_case()
    adapter.build(case)
    seconds = 0.001
    found = adapter.step(seconds)
    if not isinstance(found, interface.State):
        return [f"{name} step() did not return a State"]

    violations: list[str] = []
    if not _finite(found.time):
        violations.append(f"{name} step() reports the time {found.time!r}")
    elif abs(found.time - seconds) > tolerance:
        clamped = [
            entry
            for entry in adapter.departures()
            if entry.kind == interface.CLAMPED
        ]
        if not clamped:
            violations.append(
                f"{name} step({seconds!r}) reports the time {found.time!r} and "
                f"carries no {interface.CLAMPED} departure saying the engine did "
                f"not take the step it was given"
            )
    if set(found.bodies) != set(expected_state(case)):
        violations.append(
            f"{name} step() returns a different set of bodies from the case"
        )
    return sorted(violations)


def configuration_violations(name: str, adapter: Any) -> list[str]:
    adapter.build(conformance_case())
    found = adapter.configuration()
    if not isinstance(found, interface.Configuration):
        return [f"{name} configuration() did not return a Configuration"]

    violations: list[str] = []
    if not found.effective:
        violations.append(
            f"{name} configuration() reports no effective setting at all, and "
            f"every record carries every setting the engine holds"
        )
    unsourced = sorted(set(found.effective) - set(found.source))
    unsettled = sorted(set(found.source) - set(found.effective))
    for setting in unsourced:
        violations.append(
            f"{name} configuration() reports the setting {setting!r} and does not "
            f"say which step of the procedure produced it"
        )
    for setting in unsettled:
        violations.append(
            f"{name} configuration() names a source for {setting!r}, which is not "
            f"a setting the engine reports"
        )

    for entry in found.absent:
        if not 1 <= entry.step <= interface.PROCEDURE_STEPS:
            violations.append(
                f"{name} configuration() reports an absent setting at step "
                f"{entry.step!r}, and the procedure has "
                f"{interface.PROCEDURE_STEPS} steps"
            )
        if not entry.setting.strip():
            violations.append(
                f"{name} configuration() reports an absent setting with no name"
            )

    for entry in found.deviation:
        if entry.admitted_by not in interface.DEVIATION_ADMITTED_BY:
            violations.append(
                f"{name} configuration() reports a deviation on {entry.setting!r} "
                f"admitted by {entry.admitted_by!r}, and a deviation admitted by "
                f"nothing is a hand-tuned run"
            )
        if not entry.why.strip():
            violations.append(
                f"{name} configuration() reports a deviation on {entry.setting!r} "
                f"with no reason"
            )
    return sorted(violations)


def departure_violations(name: str, adapter: Any) -> list[str]:
    adapter.build(conformance_case())
    found = adapter.departures()
    if not isinstance(found, tuple):
        return [f"{name} departures() did not return a tuple"]

    violations: list[str] = []
    for index, entry in enumerate(found):
        where = f"{name} departures()[{index}]"
        if not isinstance(entry, interface.Departure):
            violations.append(f"{where} is not a Departure")
            continue
        if entry.kind not in interface.DEPARTURE_KINDS:
            violations.append(
                f"{where} has the kind {entry.kind!r}, and the vocabulary is "
                f"{', '.join(interface.DEPARTURE_KINDS)}"
            )
        for field in ("field", "asked", "why"):
            value = getattr(entry, field)
            if not isinstance(value, str) or not value.strip():
                violations.append(f"{where} has no {field}")

        if entry.kind == interface.KIND_WITHOUT_GIVEN:
            if entry.given is not None:
                violations.append(
                    f"{where} is {interface.KIND_WITHOUT_GIVEN} and carries the "
                    f"given value {entry.given!r}, which would read as a value "
                    f"that was read back and agreed"
                )
        elif entry.given is None:
            violations.append(
                f"{where} is {entry.kind!r} and carries no given value, so what "
                f"the engine holds is not recorded"
            )

        if entry.kind == interface.KIND_WITH_ADMISSION:
            if not isinstance(entry.admitted_by, str) or not entry.admitted_by.strip():
                violations.append(
                    f"{where} is a {interface.KIND_WITH_ADMISSION} that names "
                    f"nothing as admitting it, and the admission is in the case "
                    f"rather than in the adapter"
                )
        elif entry.admitted_by is not None:
            violations.append(
                f"{where} is {entry.kind!r} and names an admission, which only a "
                f"{interface.KIND_WITH_ADMISSION} carries"
            )
    return sorted(violations)


def diagnostics_violations(name: str, adapter: Any) -> list[str]:
    """Every unreported quantity is named as unreported, in both directions."""
    adapter.build(conformance_case())
    found = adapter.diagnostics()
    if not isinstance(found, interface.Diagnostics):
        return [f"{name} diagnostics() did not return a Diagnostics"]

    violations: list[str] = []
    fields = ("contact_normal", "slip", "contact_force")
    named = set(found.not_reported)
    for field in fields:
        value = getattr(found, field)
        if value is None:
            if field not in named:
                violations.append(
                    f"{name} diagnostics() reports no {field} and does not name "
                    f"it as unreported, so a metric would read an absence as a "
                    f"zero"
                )
            continue
        if field in named:
            violations.append(
                f"{name} diagnostics() names {field} as unreported and carries a "
                f"value for it"
            )
        problem = _vector_problem(f"{name} diagnostics() {field}", value)
        if problem is not None:
            violations.append(problem)
    for field in sorted(named - set(fields)):
        violations.append(
            f"{name} diagnostics() names {field!r} as unreported, and there is no "
            f"such diagnostic"
        )
    return sorted(violations)


def conformance_violations(name: str, package: Any) -> list[str]:
    """Every way one adapter package fails the contract. Empty is the only pass.

    Each group of properties is driven on a fresh adapter, because a build that
    happened in an earlier group is state the next group would inherit, and an
    adapter that leaks state between runs is the thing the runner's isolation
    requirement exists against.
    """
    violations = declaration_violations(name, package)
    if violations:
        # Without the four declarations there is nothing to open and no tolerance
        # to compare against, so going further would report consequences of the
        # same defect as separate findings.
        return violations

    factory: Callable[[], Any] = getattr(package, interface.FACTORY)
    tolerance: float = getattr(package, interface.TOLERANCE_DECLARATION)

    groups = (
        lambda adapter: identification_violations(name, adapter, package),
        lambda adapter: refusal_violations(name, adapter),
        lambda adapter: state_violations(name, adapter, tolerance),
        lambda adapter: step_violations(name, adapter, tolerance),
        lambda adapter: configuration_violations(name, adapter),
        lambda adapter: departure_violations(name, adapter),
        lambda adapter: diagnostics_violations(name, adapter),
    )
    for group in groups:
        adapter = factory()
        try:
            violations.extend(group(adapter))
        finally:
            adapter.close()
    return sorted(set(violations))
