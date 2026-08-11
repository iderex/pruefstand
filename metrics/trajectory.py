"""Trajectory comparison, admitted only where it is a statement about an engine.

Issue #76. `docs/decisions/metric-per-class.md` refused trajectory comparison as
the default and named the route by which a case may ask for one anyway: a
`[measured.trajectory]` block carrying a horizon and a reason. This is where that
refusal stops being a document.

It needs a mechanism rather than discipline because trajectory comparison is the
easiest thing in this project to implement, produces a number for anything, and
looks like a measurement. Somebody adding a case in a year will reach for it, and
the number will be published beside the real ones with nothing on it saying it is
of a different kind.

## The two refusals

The first is by class and is not overridable. For a case whose class is
`chaotic` there is no horizon over which trajectory agreement says anything about
an engine: two trajectories from one initial condition separate exponentially
even when both integrators are excellent, so what comes out is a function of the
horizon and the exponent. A block there is refused however short its horizon,
and the message names what to use instead, because somebody hitting a refusal
with no alternative in it will find a way around it.

The second is by horizon and applies to every other class. It is derived rather
than fixed, and the derivation is the whole of it.

An engine and the reference start from one initial condition, so the separation
between them begins at the rounding of the state and not at zero. Under a
positive divergence rate that seed grows, and a comparison reports the engine's
error only while the engine's error is larger than what the seed has grown into.
Writing `eps` for the rounding, `tol` for the case's own tolerance and `tau` for
the divergence time, the unavoidable floor at time `T` is `eps * exp(T / tau)`,
and it reaches the tolerance at

    T = tau * log(tol / eps)

so `log(tol / eps)` is the ceiling in divergence times. It is a number the case
produces rather than one this file chooses: a case with a tighter tolerance is
asking a harder question and gets a shorter window for it. A fixed multiple
written here would be the same window for every tolerance, which is a constant
nobody could argue with because it came from nowhere.

## Which exponent the divergence time comes from

The upper end of the estimate at the caller's spread, `value + spread *
uncertainty`, and not the central value. An estimate consistent with a faster
divergence than it reports is an estimate that could be hiding a shorter window,
and the direction that fails closed is the one that shortens the window rather
than the one that lengthens it. Where that upper end is at or below zero the
estimate carries no positive divergence rate at all, no divergence time exists,
and the horizon ceiling does not bind. That is stated on the window rather than
left as an absent field, because a window nothing bounded and a window that
passed its bound are opposite statements.

`spread` is the caller's, never this file's, for the reason
`metrics.lyapunov.Estimate.agrees_with` gives: how many uncertainties count is a
statement about what is being claimed.

## What is not refused here

That the block's horizon is shorter than the case's own is refused by
`casefile.py`, where the block's shape is held, and it is not repeated here. Two
statements of one rule drift, and the one a reader trusts is whichever they
found first.

## The means

Python and the standard library, in the numerical core, where nothing imports an
adapter or an engine. What this module does is arithmetic over scalars and a
comparison of two sequences of states, so an array library would be a dependency
carried for one square root. It reads a case through `casefile.Case` rather than
through a table of its own, so a comparison cannot be judged from content that
never passed the schema. The three rules survive it: every condition below is
refused by code rather than asserted in prose, each refusal is tripped by a
fixture in `tests/test_trajectory.py` that is a working call with one thing
changed, and every number this module states is one it computes.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import casefile
from metrics.lyapunov import Estimate, State, separation

# The one class for which the block is refused however short its horizon.
# Spelled here as one value rather than as a copy of the vocabulary, which is
# `casefile.CLASSES` and is the schema's; `tests/test_trajectory.py` refuses a
# value that is not one of them, so this cannot drift into naming a class that
# does not exist.
REFUSED_CLASS = "chaotic"

# What a reader of the refusal is sent to instead. Named rather than left to be
# looked up, because a refusal with no alternative in it is a refusal somebody
# works around.
ALTERNATIVES = (
    "the largest Lyapunov exponent, estimated from the engine's own trajectory, "
    "in metrics/lyapunov.py, and the Poincare section beside it as a second and "
    "independent view"
)

# The fields of a case this module reads, named here rather than spelled at each
# point of use. `tests/test_greppable_invariants.py` refuses the second shape,
# for a reason that applies here rather than only in general: the schema is
# `casefile.py`'s and can move, and a name written at the point of use is one a
# reader goes on using after the field it names has gone. Held in one place, a
# schema that moved is a repair in this block, and
# `tests/test_trajectory.py` checks these against a case the schema accepted.
MEASURED = "measured"
TRAJECTORY = "trajectory"
TRAJECTORY_HORIZON = "horizon_seconds"
TOLERANCE = "tolerance"
TOLERANCE_VALUE = "value"

# The smallest separation two runs from one initial condition can be said to
# have: the relative rounding of a float. Read from the interpreter rather than
# written down, so it is right on an interpreter this was not measured on, and
# it is the same quantity `metrics.lyapunov.ROUNDING` reads for the same reason.
ROUNDING = sys.float_info.epsilon

# The fewest samples a comparison is computed over. One sample is a state and
# not a trajectory, and a separation at a single time carries no shape at all.
SAMPLES_FLOOR = 2


class ComparisonRefused(ValueError):
    """Raised instead of returning a comparison that would be quoted.

    It carries every problem found rather than the first, for the reason
    `casefile.CaseRefused` gives: a reader that stops at the first turns one
    review into several.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(self.problems))


@dataclass(frozen=True)
class Window:
    """An admitted trajectory-comparison window, and what admitted it.

    Every number the admission turned on is carried, so a reader of a result can
    see that the comparison was legitimate without re-deriving it. That is the
    point of the type: `compare` takes one of these and not a horizon, so there
    is no route to a comparison that skipped the judgement.
    """

    case_id: str
    case_class: str
    horizon: float
    tolerance: float
    rounding: float
    exponent: float
    uncertainty: float
    spread: float
    rate: float
    divergence_time: float | None
    ceiling: float | None

    @property
    def multiple(self) -> float:
        """The ceiling in divergence times, `log(tolerance / rounding)`."""
        return math.log(self.tolerance / self.rounding)

    def __str__(self) -> str:
        if self.divergence_time is None:
            return (
                f"{self.case_id}: {self.horizon:g} s, against no divergence "
                f"time, the exponent being {self.exponent:+.4g} +/- "
                f"{self.uncertainty:.4g} and its upper end at {self.spread:g} "
                f"uncertainties {self.rate:+.4g}, which is not positive"
            )
        return (
            f"{self.case_id}: {self.horizon:g} s, which is "
            f"{self.horizon / self.divergence_time:.3g} divergence time(s) of "
            f"{self.divergence_time:.4g} s, against a ceiling of "
            f"{self.multiple:.3g}"
        )


@dataclass(frozen=True)
class Comparison:
    """A separation between two runs, and the window that admitted it."""

    window: Window
    times: tuple[float, ...]
    separations: tuple[float, ...]

    @property
    def largest(self) -> float:
        return max(self.separations)

    @property
    def at(self) -> float:
        """The time the largest separation was reached."""
        return self.times[self.separations.index(self.largest)]

    @property
    def divergence_time(self) -> float | None:
        """Carried through from the window, so a result states what bounded it."""
        return self.window.divergence_time

    def __str__(self) -> str:
        return (
            f"{self.window.case_id}: largest separation {self.largest:.4g} at "
            f"{self.at:g} s, over {len(self.times)} sample(s) of {self.window}"
        )


def _is_finite_float(value: object) -> bool:
    return isinstance(value, float) and math.isfinite(value)


def _finite_state(state: object) -> bool:
    return (
        isinstance(state, tuple)
        and len(state) > 0
        and all(_is_finite_float(value) for value in state)
    )


def admit(case: casefile.Case, estimate: Estimate, *, spread: float) -> Window:
    """The window this case's trajectory block asks for, or a refusal.

    `case` has passed the schema, so the block's shape and the rule that its
    horizon is shorter than the case's own are already held. What is decided
    here is whether the class admits a comparison at all and whether the horizon
    survives the divergence rate.
    """
    problems: list[str] = []

    if not isinstance(estimate, Estimate):
        raise ComparisonRefused(
            [
                f"the divergence rate is {type(estimate).__name__} and has to be "
                f"a metrics.lyapunov.Estimate, which is an exponent and an "
                f"uncertainty together"
            ]
        )
    if not _is_finite_float(spread) or spread <= 0.0:
        problems.append(
            f"the spread is {spread!r} and has to be a positive finite float, "
            f"being how many uncertainties the caller counts as supported"
        )

    measured = case.content[MEASURED]
    block = measured.get(TRAJECTORY)
    if block is None:
        problems.append(
            f"case {case.id!r} declares no [measured.trajectory] block, so it "
            f"asked for no trajectory comparison and one is not made for it"
        )

    if case.case_class == REFUSED_CLASS:
        problems.append(
            f"case {case.id!r} is in the {REFUSED_CLASS!r} class, where two "
            f"trajectories from one initial condition separate exponentially "
            f"whatever the engine does, so there is no horizon over which their "
            f"agreement is a statement about the engine. This refusal is not "
            f"overridable by a shorter horizon. Use {ALTERNATIVES}."
        )

    if problems:
        raise ComparisonRefused(sorted(set(problems)))

    horizon = float(block[TRAJECTORY_HORIZON])
    tolerance = float(case.content[TOLERANCE][TOLERANCE_VALUE])
    rate = estimate.value + spread * estimate.uncertainty

    if tolerance <= ROUNDING:
        raise ComparisonRefused(
            [
                f"case {case.id!r} has a tolerance of {tolerance!r}, which is at "
                f"or below the rounding of a float, {ROUNDING!r}, so the "
                f"separation two runs start with is already the whole tolerance "
                f"and no window measures the engine"
            ]
        )

    if rate <= 0.0:
        return Window(
            case_id=case.id,
            case_class=case.case_class,
            horizon=horizon,
            tolerance=tolerance,
            rounding=ROUNDING,
            exponent=estimate.value,
            uncertainty=estimate.uncertainty,
            spread=spread,
            rate=rate,
            divergence_time=None,
            ceiling=None,
        )

    divergence_time = 1.0 / rate
    multiple = math.log(tolerance / ROUNDING)
    ceiling = divergence_time * multiple

    if horizon > ceiling:
        raise ComparisonRefused(
            [
                f"case {case.id!r} asks for trajectory agreement over "
                f"{horizon!r} s, and the ceiling is {ceiling!r} s. The exponent "
                f"is {estimate.value!r} +/- {estimate.uncertainty!r} per unit "
                f"time, whose upper end at {spread!r} uncertainties is "
                f"{rate!r}, so the divergence time is 1 / {rate!r} = "
                f"{divergence_time!r} s. The separation two runs start with is "
                f"the rounding {ROUNDING!r} and it reaches the case's tolerance "
                f"{tolerance!r} after log({tolerance!r} / {ROUNDING!r}) = "
                f"{multiple!r} divergence times, which is "
                f"{divergence_time!r} * {multiple!r} = {ceiling!r} s. Past that "
                f"the separation reported is the amplified rounding rather than "
                f"the engine. Shorten the horizon, or use {ALTERNATIVES}."
            ]
        )

    return Window(
        case_id=case.id,
        case_class=case.case_class,
        horizon=horizon,
        tolerance=tolerance,
        rounding=ROUNDING,
        exponent=estimate.value,
        uncertainty=estimate.uncertainty,
        spread=spread,
        rate=rate,
        divergence_time=divergence_time,
        ceiling=ceiling,
    )


def compare(
    window: Window,
    reference: list[tuple[float, State]],
    engine: list[tuple[float, State]],
) -> Comparison:
    """The separation between two runs over an admitted window.

    Both sequences are `(time, state)` pairs at the same times, in the same
    coordinates. Resampling one onto the other is deliberately not done here: an
    interpolation between two states of a rigid body is a decision about the
    representation, it would be made silently, and the separation it produced
    would carry the interpolation's error as though it were the engine's.
    """
    problems: list[str] = []

    if len(reference) != len(engine):
        problems.append(
            f"the reference has {len(reference)} sample(s) and the engine has "
            f"{len(engine)}, and a separation is between two states at one time"
        )
    if len(reference) < SAMPLES_FLOOR or len(engine) < SAMPLES_FLOOR:
        problems.append(
            f"the runs carry {len(reference)} and {len(engine)} sample(s), and "
            f"the floor is {SAMPLES_FLOOR}, below which there is no trajectory "
            f"to compare"
        )
    if problems:
        raise ComparisonRefused(sorted(set(problems)))

    times: list[float] = []
    separations: list[float] = []
    previous: float | None = None
    for index, ((at, first), (also, second)) in enumerate(zip(reference, engine)):
        where = f"sample {index}"
        if not _is_finite_float(at) or not _is_finite_float(also):
            problems.append(f"{where} is at {at!r} and {also!r}, and a time is a "
                            f"finite float")
            continue
        if at != also:
            problems.append(
                f"{where} is at {at!r} in the reference and {also!r} in the "
                f"engine, and a separation between two different times is not a "
                f"separation"
            )
            continue
        if at < 0.0:
            problems.append(f"{where} is at {at!r}, and a window starts at zero")
            continue
        if previous is not None and at <= previous:
            problems.append(
                f"{where} is at {at!r} and the one before it at {previous!r}, "
                f"and samples are in increasing time"
            )
            continue
        previous = at
        if at > window.horizon:
            problems.append(
                f"{where} is at {at!r} s and the admitted window ends at "
                f"{window.horizon!r} s, so this run reaches past what was judged"
            )
            continue
        if not _finite_state(first) or not _finite_state(second):
            problems.append(
                f"{where} carries {first!r} and {second!r}, and a state is a "
                f"non-empty tuple of finite floats"
            )
            continue
        if len(first) != len(second):
            problems.append(
                f"{where} is in phase spaces of {len(first)} and {len(second)} "
                f"coordinates, so nothing measures between them"
            )
            continue
        times.append(at)
        separations.append(separation(first, second))

    if problems:
        raise ComparisonRefused(sorted(set(problems)))

    return Comparison(
        window=window, times=tuple(times), separations=tuple(separations)
    )
