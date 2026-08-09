"""The interface every engine adapter implements.

Issue #33. What an adapter owes was decided first, in
`docs/decisions/one-description-per-engine.md` for the four edges where a case
and an engine do not fit, in `docs/decisions/configuration-procedure.md` for what
a record carries about the settings a run was made under, and in
`docs/decisions/units-frames-and-inertia.md` for what every number means. This is
the contract those three documents say they are owed, and from here the names
below are the authority for what an adapter is asked while the documents keep the
reasons.

Everything above this layer works in cases, states and metrics. An adapter is the
only place in this project that knows an engine exists, and this module is the
only place that decides what such a place is asked.

## What the contract turns on

An adapter never papers over a difference. Substituting a value the engine can
take, and returning as though the engine had been given what the case asked for,
produces a wrong number with a clean provenance, and it is wrong in the direction
that flatters the engine, because a value an engine will accept is usually a value
inside the range it is stable in. So every departure from what the case said is
returned as a departure, and a quantity that was not read back is returned as not
read back rather than as agreed.

The state conversion is the other half. A case file states an orientation as a
unit quaternion and every vector quantity in the world frame; a record carries the
rotation matrix and, where a quantity exists in both frames, the bare name is the
world one. An engine has its own ordering, its own frame for angular velocity and
sometimes only the body-frame one, so the conversion happens here, once per
engine, at the boundary. A mistake in it is a mistake in every number from that
engine and it looks like a physics result.

That is why `BodyState` carries the angular velocity in both frames rather than
one. An adapter reporting only the world-frame vector would be asking to be
believed about a conversion nobody can see, and requiring both makes the
conversion a pair of numbers that `conformance.py` can hold against the case.

## What an adapter declares

Four module-level names in its `__init__.py`, read by the conformance suite and
by the boundary check rather than by a person:

    ENGINE_MODULE     the one engine this package imports, a plain string
    STATE_TOLERANCE   how far a read-back state may sit from the case's own
    TOLERANCE_WHY     why that number and not a looser one
    open_adapter()    returns something implementing `Adapter`

`STATE_TOLERANCE` is per engine because the representation an engine stores state
in is the engine's, and a number this project fixed for all of them would be
either too loose for the careful ones or a refusal of the others. It is bounded
from above rather than left open: `conformance.py` refuses a tolerance wide enough
to hide the frame error the read-back exists to catch.

## What this module does not decide

The result record's field list and what refuses a record missing one: #10 and
#40. Asking the engine what it actually did, which is the read-back of solver
iterations, contact limits, subdivided steps and non-finite events: #41, and the
`clamped` and `not-read-back` departure kinds below are the shape it writes into.
The runner that derives a configuration rather than accepting one: #39. Which
engines exist: #16, which waits on entry 3 of #1. How ideal rolling is asked of an
engine that has only friction: #12.

## The means

Python and the standard library, in the language the rest of this tree is
written in, and no dependency added to a tree that carries none. `typing.Protocol`
states the contract structurally, so an adapter is judged by what it does rather
than by what it inherits, and nothing here can be satisfied by importing a base
class. The rotation conversion is nine multiplications and needs no array
library. The three rules survive it: every property this module states is refused
by an operator in `conformance.py` rather than asserted here, each of those
refusals is tripped by a deliberately wrong adapter in `tests/test_conformance.py`,
and the numbers in the docstrings below are the ones those tests compute.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

# The four situations `docs/decisions/one-description-per-engine.md` names, in
# its own order, by the response each one gets. A record's `refusal.situation`
# and a departure's `kind` both come out of this vocabulary rather than out of a
# sentence somebody wrote at the time.
CANNOT_EXPRESS = "cannot-express"
UNMATCHED_PARAMETER = "unmatched-parameter"
UNSET_QUANTITY = "unset-quantity"
CLAMPED = "clamped"

SITUATIONS = (CANNOT_EXPRESS, UNMATCHED_PARAMETER, UNSET_QUANTITY, CLAMPED)

# The two situations that refuse rather than record. The other two produce a run
# that happened and a departure beside its number.
REFUSING_SITUATIONS = (CANNOT_EXPRESS, UNSET_QUANTITY)

# The departure kinds a record carries. `substitution` and `unmatched-parameter`
# are the second situation, `clamped` and `not-read-back` are the fourth.
SUBSTITUTION = "substitution"
NOT_READ_BACK = "not-read-back"

DEPARTURE_KINDS = (SUBSTITUTION, UNMATCHED_PARAMETER, CLAMPED, NOT_READ_BACK)

# The one kind whose `given` is absent. An engine that offers no read-back for a
# quantity leaves nothing to compare, and `given` equal to `asked` there would
# turn a negative disclosure into a positive one.
KIND_WITHOUT_GIVEN = NOT_READ_BACK

# The one kind that names what admitted it. A substitution is legal only where the
# case admitted it in advance, so an entry with nothing in this field is a
# substitution the adapter decided on its own, which is the thing the whole
# vocabulary exists to make visible.
KIND_WITH_ADMISSION = SUBSTITUTION

# What a departure says about the number the run produced. Issue #37: an entry
# naming the property and the substitution and saying nothing about the
# measurement is a complete-looking list in which nothing says whether the number
# moved, and the report card then shows a departure beside a number with no way to
# tell whether the two are related.
#
# The third value is why this is a vocabulary of three rather than a boolean. An
# adapter author who does not know is the case a boolean cannot carry, and forcing
# a guess into one of the other two would publish a judgement nobody made. It is
# the same shape `reference.answer.Unbounded` takes for a bound that could not be
# produced, for the same reason: an honest absence beats a field filled to look
# complete.
MOVES_THE_MEASUREMENT = "moves-the-measurement"
LEAVES_THE_MEASUREMENT = "leaves-the-measurement"
EFFECT_NOT_KNOWN = "not-known"

EXPECTED_EFFECTS = (
    MOVES_THE_MEASUREMENT,
    LEAVES_THE_MEASUREMENT,
    EFFECT_NOT_KNOWN,
)

# The one kind whose expected effect is absent rather than unknown. A quantity the
# engine never read back is a quantity nothing was substituted for, so there is no
# effect on the measurement to state and `not-known` there would report an open
# question where there is none.
KIND_WITHOUT_EXPECTED_EFFECT = NOT_READ_BACK

# What may admit a configuration deviation, from the configuration procedure,
# which gives this field no free-text option: the case declared the deviation, or
# the engine refused the procedure's value and reported what it took instead.
ADMITTED_BY_CASE = "case"
ADMITTED_BY_ENGINE_REFUSAL = "engine-refusal"
DEVIATION_ADMITTED_BY = (ADMITTED_BY_CASE, ADMITTED_BY_ENGINE_REFUSAL)

# The numbered steps of the configuration procedure. An absent setting names the
# step it was absent from, so an absence is placed in the procedure rather than
# left as a name a reader has to look up.
PROCEDURE_STEPS = 7

# The names an adapter package declares at module level. Read by the conformance
# suite out of the imported package, by these spellings and no others.
ENGINE_DECLARATION = "ENGINE_MODULE"
TOLERANCE_DECLARATION = "STATE_TOLERANCE"
TOLERANCE_WHY_DECLARATION = "TOLERANCE_WHY"
FACTORY = "open_adapter"

# A rotation matrix is nine floats, row-major.
ROTATION_COMPONENTS = 9


class CannotExpress(Exception):
    """Raised by `build` instead of constructing a scene that is not the case.

    It carries which of the four situations it was, the case field that could not
    be carried, and a sentence naming what the engine could not express or which
    quantity the case left unset. Those three become `refusal.situation`,
    `refusal.field` and `refusal.why` on a record whose outcome is
    `refused-at-compilation`.

    Only the two situations in `REFUSING_SITUATIONS` may appear here. The other
    two describe a run that happened and are carried as a `Departure` beside its
    number, so raising them would report a completed run as a refusal.
    """

    def __init__(self, situation: str, field: str, why: str) -> None:
        self.situation = situation
        self.field = field
        self.why = why
        super().__init__(f"{situation}: {field}: {why}")


@dataclass(frozen=True)
class Identification:
    """What the engine says it is, asked of the engine rather than written down.

    `engine_module` is the module the adapter imported, which the conformance
    suite holds against the package's own `ENGINE_MODULE` declaration. `version`
    and `build` are whatever the engine reports about itself.

    Nothing can check that these were read from the engine rather than typed into
    the adapter. A literal is indistinguishable from a read at every surface this
    project has, so the requirement is a contract here and `conformance.py`
    records that it cannot enforce it.
    """

    engine_module: str
    version: str
    build: str


@dataclass(frozen=True)
class BodyState:
    """One body's state, in this project's conventions rather than the engine's.

    `position` is the centre of mass in the world frame, metres. `rotation` is the
    body-to-world rotation matrix, row-major, nine floats, which is what a record
    carries instead of a quaternion. `velocity` is the centre of mass velocity in
    the world frame. `angular_velocity` is the world-frame angular velocity and
    `angular_velocity_body` is the same quantity in the body frame, both in
    radians per second, and the bare name is the world one because that is the
    naming rule the convention states.

    Both angular velocities are required. `angular_velocity` equals `rotation`
    applied to `angular_velocity_body`, and that identity is what makes the
    conversion checkable instead of trusted.
    """

    position: tuple[float, float, float]
    rotation: tuple[float, ...]
    velocity: tuple[float, float, float]
    angular_velocity: tuple[float, float, float]
    angular_velocity_body: tuple[float, float, float]


@dataclass(frozen=True)
class State:
    """The whole state at one time, keyed by the case's own body ids.

    Keyed by id rather than ordered, so a body that the engine happened to build
    second cannot be read as the case's second body.
    """

    time: float
    bodies: Mapping[str, BodyState]


@dataclass(frozen=True)
class Diagnostics:
    """What the metrics need beyond the body state, and what was not reported.

    The rolling cases are judged on the slip at the contact point and on the
    contact force, so an adapter that reports only the body state cannot carry
    them, and a metric computed without them would be computed over an assumption.

    `contact_normal` is the outward unit normal of the supporting surface at the
    contact point, which for a horizontal plane is the world z direction. A slip
    is a world-frame vector whose component along that normal is zero by
    construction, so a slip with a normal component is a diagnostic about the
    engine and is carried rather than corrected.

    `not_reported` names every field this engine does not expose. A field that is
    `None` and unnamed there is refused, and a name there whose field carries a
    value is refused too, because "not reported" and "reported as nothing" are
    different statements and only one of them is a disclosure.
    """

    contact_normal: tuple[float, float, float] | None
    slip: tuple[float, float, float] | None
    contact_force: tuple[float, float, float] | None
    not_reported: tuple[str, ...]


@dataclass(frozen=True)
class Departure:
    """One place the run was not the run the case describes.

    `kind` is from `DEPARTURE_KINDS`. `field` is the case field or setting it is
    about. `asked` is what the case stated and `given` is what the engine holds,
    both as the strings a record carries, and `given` is absent exactly for
    `not-read-back`. `admitted_by` names the case's own admission and is present
    exactly for `substitution`.

    `why` is why the departure was made. `expected_effect` is a different
    statement and issue #37 is where it comes from: whether the measured quantity
    is expected to move because of it, from `EXPECTED_EFFECTS`, absent exactly for
    `not-read-back`. It is a judgement, and it belongs to whoever wrote the
    adapter rather than to whoever reads the report card afterwards, because by
    then the engine's own behaviour is no longer in front of anybody.

    A record whose departure list is empty asserts that the engine holds exactly
    what the case said on every quantity the case set. That is a strong claim and
    it is the one this project wants to be able to make, which is why an empty
    list has to be earned rather than defaulted to.
    """

    kind: str
    field: str
    asked: str
    given: str | None
    why: str
    admitted_by: str | None
    expected_effect: str | None


@dataclass(frozen=True)
class AbsentSetting:
    """A procedure step this engine had no setting for.

    `related` names the engine's own nearest setting where one exists and was
    deliberately not used, and is absent where there is none. Naming it is not
    permission to use it: a nearest thing chosen per engine is a judgement by
    whoever wrote that adapter, and the differences between engines would then
    include the differences between those judgements.
    """

    step: int
    setting: str
    related: str | None


@dataclass(frozen=True)
class Deviation:
    """A setting the procedure would have produced and the run did not use.

    `admitted_by` is one of `DEVIATION_ADMITTED_BY`. A deviation admitted by
    nothing is not a deviation, it is a hand-tuned run, which is what the
    configuration procedure exists to refuse.
    """

    setting: str
    procedure_value: str
    used_value: str
    why: str
    admitted_by: str


@dataclass(frozen=True)
class Configuration:
    """Every setting the engine holds after construction, as the engine reports it.

    `effective` is the whole set by the engine's own setting names, including the
    settings the case never mentions and the settings nobody changed. Including
    the untouched ones is the point: a hand-set value shows up only as a value the
    procedure would not have produced, and that comparison is impossible against a
    set carrying only what somebody chose to write down.

    `source` says, per setting, which numbered step of the procedure produced it or
    that it is the engine's default. Its keys are exactly the keys of `effective`,
    in both directions, so a setting with no stated source and a source naming no
    setting are each refused.
    """

    effective: Mapping[str, str]
    source: Mapping[str, str]
    absent: tuple[AbsentSetting, ...]
    deviation: tuple[Deviation, ...]


@runtime_checkable
class Adapter(Protocol):
    """What every engine adapter implements.

    Structural rather than inherited, so an adapter cannot acquire conformance by
    subclassing something. The order below is the order a run uses: identify,
    build, read the configuration back, read the state at time zero, step, read
    the diagnostics, close.
    """

    def identify(self) -> Identification:
        """What the engine says it is. Never a literal in the adapter."""

    def build(self, case: object) -> None:
        """Build the scene from a validated case, or raise `CannotExpress`.

        The case is what `casefile.read` returned. Building is by the engine's own
        construction calls in this process, never by writing a scene file the
        engine reads back, because a text format is a second artefact that can go
        stale against the case and a parser this project does not own between the
        two.

        What it may not do: approximate a constraint the case did not admit,
        build a case that leaves unset a quantity this engine has a default for,
        or narrow a value into the engine's own range and return as though the
        case's value had been taken. The first two raise. The third is a
        `clamped` departure found by reading the value back, because nothing at
        construction time can know it happened.
        """

    def configuration(self) -> Configuration:
        """The full effective configuration, after construction and before the run.

        Read from the engine, not from the adapter's own record of what it set,
        which is the thing being checked, and not from the engine's documentation,
        which is a statement about a version that may not be the installed one.

        An engine that cannot be asked what it holds cannot be configured by a
        procedure that reads back. That case raises rather than returning a
        configuration the adapter believes.
        """

    def departures(self) -> tuple[Departure, ...]:
        """Every place the run is not the case as written, possibly empty."""

    def state(self) -> State:
        """The state now, in this project's conventions.

        Called before any step, it is the read-back of the case's own initial
        state and is the one place an adapter's conversion can be held against a
        number this project already knows.
        """

    def step(self, seconds: float) -> State:
        """Advance by exactly `seconds` and return the state.

        What the engine did inside the step is #41's to ask about. What this
        method owes is that the time it returns advanced by the amount it was
        given, or that a `clamped` departure on the timestep says it did not.
        """

    def diagnostics(self) -> Diagnostics:
        """The contact quantities the metrics need, and what is not reported."""

    def close(self) -> None:
        """Release whatever the engine holds.

        Several of these engines keep global state, so a run that does not clean
        up is a run that can change the next one. Isolation between runs is the
        runner's, #39, and this is the half of it the engine side owes.
        """


def rotation_from_quaternion(
    w: float, x: float, y: float, z: float
) -> tuple[float, ...]:
    """The body-to-world rotation matrix of a unit quaternion, row-major.

    Hamilton, so `ij = k`, and the rotation that maps body-frame components to
    world-frame ones, meaning `v_world = R v_body`. That is the convention the
    case file states and the matrix a record carries, and this is the one
    implementation of it, so an adapter converts by calling rather than by
    writing the nine expressions again with a sign moved.

    It assumes a unit quaternion and normalises nothing. A case file's
    orientation is refused rather than normalised if its norm is further than
    `1e-12` from one, so by the time a quaternion reaches here it has been
    refused or it is a unit one.
    """
    return (
        1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - w * z), 2.0 * (x * z + w * y),
        2.0 * (x * y + w * z), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - w * x),
        2.0 * (x * z - w * y), 2.0 * (y * z + w * x), 1.0 - 2.0 * (x * x + y * y),
    )


def apply(
    rotation: tuple[float, ...], vector: tuple[float, float, float]
) -> tuple[float, float, float]:
    """`R v`, which takes a body-frame vector to the world frame."""
    return tuple(
        sum(rotation[3 * row + column] * vector[column] for column in range(3))
        for row in range(3)
    )


def apply_transpose(
    rotation: tuple[float, ...], vector: tuple[float, float, float]
) -> tuple[float, float, float]:
    """`R^T v`, which takes a world-frame vector to the body frame.

    A rotation's transpose is its inverse, so this is the conversion an adapter
    performs to report the body-frame angular velocity beside the world-frame one.
    """
    return tuple(
        sum(rotation[3 * column + row] * vector[column] for column in range(3))
        for row in range(3)
    )
