"""Whether an engine's error is discretisation or modelling, decided from a ladder.

Issue #57. An engine whose error falls as the step is refined is integrating the
right equations imprecisely, and the fix is computer time. An engine whose error
stops falling is integrating something other than the right equations, and no
step size will fix it. Those are entirely different statements about a piece of
software, and the report card may never blur them.

The distinction is decidable from a resolution study, and this module is where it
is decided. What it takes is the rungs of that study, what the study's own error
sources contribute, and nothing else.

## Why a floor is not enough on its own

An error curve that stops falling has a floor, and three things can put one there:

- The engine is integrating the wrong equations. That is the finding.
- The arithmetic ran out of significant digits. That is the rounding floor, and
  it is a property of the run rather than of the engine.
- The reference the error was measured against is itself only known to a bound.
  Below that bound the error being measured is the reference's.

So a floor is attributed to the engine only after the other two are taken out,
and both are taken out explicitly rather than assumed small. `Excluded` carries
them, every rung is reduced by their sum, and a rung not clear of that sum is
dropped from the fit with the reason recorded rather than silently included.

## The three conclusions

`CONVERGING`, `FLOORED` and `UNDECIDED`, and there is no fourth. The third is what
keeps this honest: for some engines the usable step range will be too narrow to
decide, and reporting undecided is correct. A conclusion with two values forces a
verdict where the data does not support one, and the verdict it forces is the
interesting one, because a narrow range and a floor look identical.

Undecided is produced rather than avoided. A ladder with too few rungs left after
the exclusions, a ladder whose local orders neither hold up nor collapse, and a
ladder entirely inside the excluded contributions all reach it, and each says
which of those it was.

## What is fitted, and over what

The observed error of a discretisation of order p behaves like `C h^p` while the
discretisation dominates. The fit is ordinary least squares of the logarithm of
the attributed error against the logarithm of the step, over the rungs that
survived the exclusions, so the fitted order is a slope in a log-log plane and
the fitted scale is its intercept.

The verdict is not read from that slope. It is read from the LOCAL orders, one
per neighbouring pair, because a single slope over a curve that is second order
at the coarse end and flat at the fine end is a number near one and says nothing.
A ladder is floored when its coarse end still converges and its fine end has gone
flat, which is a statement about the two ends and not about their average. The
fitted slope is carried on the conclusion because it is the number a reader
compares against what an engine documents, never because it decided anything.

## The means

Python and the standard library, in the numerical core, where nothing imports an
adapter or an engine. The arithmetic is a two-parameter least squares over a
handful of points, which is a dozen lines of scalar code; an array library here
would be a dependency carried for one dot product. The three rules survive it:
every condition is refused by code rather than asserted, each refusal is tripped
by a fixture in `tests/test_error_source.py` that is a working ladder with one
thing changed, and every number in the tests is one this module computes.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field

CONVERGING = "converging"
FLOORED = "floored"
UNDECIDED = "undecided"

# The three and no fourth. A verdict outside this is refused at construction, so
# a caller cannot invent a softer word for a floor.
VERDICTS = (CONVERGING, FLOORED, UNDECIDED)

# How far above the excluded contributions a rung has to sit before its error is
# read as the engine's. A factor rather than a difference, because both excluded
# contributions are themselves estimates and a rung level with them carries no
# information about the engine either way.
MARGIN_ABOVE_EXCLUDED = 2.0

# The fewest rungs a conclusion may be drawn from. Two give one local order and
# there is nothing for it to be consistent with, which is the same argument
# `reference/convergence.py` makes about a ladder.
RUNGS_FLOOR = 3

# The local order a converging ladder holds at every step, and the one a floored
# ladder has fallen below at its fine end. The gap between them is deliberate:
# between the two the ladder is neither, and that is what undecided is for.
ORDER_CONVERGENCE_HOLDS = 0.5
ORDER_A_FLOOR_HAS_FALLEN_BELOW = 0.25


class LadderRefused(ValueError):
    """A resolution ladder this module will not draw a conclusion from."""


def _is_finite_float(value: object) -> bool:
    return isinstance(value, float) and math.isfinite(value)


@dataclass(frozen=True)
class Rung:
    """One run of the study: the step it was run at and the error it reached."""

    step: float
    error: float

    def __post_init__(self) -> None:
        if not _is_finite_float(self.step) or self.step <= 0.0:
            raise LadderRefused(f"a step is a positive finite float and is {self.step!r}")
        if not _is_finite_float(self.error) or self.error < 0.0:
            raise LadderRefused(
                f"an error is a finite float of zero or more and is {self.error!r}"
            )


@dataclass(frozen=True)
class Excluded:
    """What of an observed error is not the engine's, stated rather than assumed.

    `rounding` is the floor the arithmetic of the run puts under any error, and it
    is estimable: the study's finest rungs reach it and it scales with the
    magnitudes being differenced. `reference` is the bound the reference answer
    carries, which is known rather than estimated, because `reference/answer.py`
    refuses a reference value that does not carry one.

    Both default to nothing, and that default is the honest one rather than a
    convenience: a caller who states neither gets a conclusion that attributes
    every floor to the engine, which is what the conclusion says it did.
    """

    rounding: float = 0.0
    reference: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (("rounding", self.rounding), ("reference", self.reference)):
            if not _is_finite_float(value) or value < 0.0:
                raise LadderRefused(
                    f"the {name} contribution is a finite float of zero or more "
                    f"and is {value!r}"
                )

    @property
    def total(self) -> float:
        """Both together. They add: each is a contribution to the same error."""
        return self.rounding + self.reference


@dataclass(frozen=True)
class Conclusion:
    """One verdict, with everything it was drawn from.

    A verdict on its own is an opinion. What makes it something a reader can
    argue with is the range it was fitted over, the rungs that reached the fit,
    the ones that did not and why, and the order and scale the fit produced.
    """

    verdict: str
    reason: str
    # The coarsest and finest step the fit used, or None where nothing was fitted.
    fitted_over: tuple[float, float] | None
    rungs_used: int
    order: float | None = None
    scale: float | None = None
    # The local order between each neighbouring pair, coarse end first.
    local_orders: tuple[float, ...] = ()
    # What the engine's error settled at, where the verdict is that it settled.
    attributed_floor: float | None = None
    # One sentence per rung the exclusions removed.
    dropped: tuple[str, ...] = ()
    excluded: Excluded = field(default_factory=Excluded)

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise LadderRefused(
                f"a conclusion is one of {VERDICTS} and is {self.verdict!r}. A "
                f"fourth word is a verdict this project did not define"
            )
        if not self.reason.strip():
            raise LadderRefused("a conclusion says which of its routes produced it")
        if self.verdict == UNDECIDED:
            return
        if self.fitted_over is None or self.rungs_used < RUNGS_FLOOR:
            raise LadderRefused(
                f"a verdict of {self.verdict} is drawn from {self.rungs_used} "
                f"rung(s) over {self.fitted_over!r}, and a decided conclusion "
                f"carries the range it was fitted over"
            )
        if self.order is None or self.scale is None:
            raise LadderRefused(
                f"a verdict of {self.verdict} carries the fitted order and scale"
            )

    def __str__(self) -> str:
        if self.fitted_over is None:
            return f"{self.verdict}: {self.reason}"
        coarse, fine = self.fitted_over
        return (
            f"{self.verdict}: order {self.order:.2f} over {self.rungs_used} rung(s) "
            f"from a step of {coarse:g} to {fine:g}. {self.reason}"
        )


def _ordered(rungs: tuple[Rung, ...]) -> tuple[Rung, ...]:
    """The rungs, coarsest step first, refusing a ladder that is not one."""
    if len(rungs) < RUNGS_FLOOR:
        raise LadderRefused(
            f"a conclusion is drawn from at least {RUNGS_FLOOR} rungs and this "
            f"ladder has {len(rungs)}"
        )
    steps = [rung.step for rung in rungs]
    if len(set(steps)) != len(steps):
        raise LadderRefused(
            "two rungs of this ladder ran at the same step, so one of them is a "
            "rerun and which of the two errors is the ladder's is not this "
            "module's to choose"
        )
    return tuple(sorted(rungs, key=lambda rung: -rung.step))


def _local_order(coarse: Rung, fine: Rung, attributed: dict[float, float]) -> float:
    """The order between two neighbouring rungs, from their attributed errors."""
    return math.log(attributed[coarse.step] / attributed[fine.step]) / math.log(
        coarse.step / fine.step
    )


def _least_squares(points: list[tuple[float, float]]) -> tuple[float, float]:
    """The slope and intercept of a straight line through points, in that order."""
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(ys)
    spread = sum((x - mean_x) ** 2 for x in xs)
    if spread <= 0.0:
        raise LadderRefused("every rung of this ladder ran at the same step")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / spread
    return slope, mean_y - slope * mean_x


def conclude(
    rungs: tuple[Rung, ...],
    excluded: Excluded | None = None,
    *,
    margin: float = MARGIN_ABOVE_EXCLUDED,
) -> Conclusion:
    """Whether this ladder converges, is floored, or does not say.

    The exclusions come off first, because a rung whose error is the reference's
    bound carries no statement about the engine and including it would let the
    reference's own limits decide a finding about somebody else's software.
    """
    excluded = excluded or Excluded()
    if not _is_finite_float(margin) or margin <= 1.0:
        raise LadderRefused(
            f"the margin above the excluded contributions is a factor greater "
            f"than one and is {margin!r}"
        )
    ladder = _ordered(rungs)

    attributed: dict[float, float] = {}
    kept: list[Rung] = []
    dropped: list[str] = []
    for rung in ladder:
        if rung.error <= excluded.total * margin:
            dropped.append(
                f"the rung at a step of {rung.step:g} reached {rung.error:.3e}, "
                f"which is not {margin:g} times the {excluded.total:.3e} this "
                f"study contributes itself, so it says nothing about the engine"
            )
            continue
        left = rung.error - excluded.total
        attributed[rung.step] = left
        kept.append(rung)

    if len(kept) < RUNGS_FLOOR:
        return Conclusion(
            verdict=UNDECIDED,
            reason=(
                f"{len(kept)} rung(s) of {len(ladder)} sit clear of the "
                f"{excluded.total:.3e} this study contributes itself, and a "
                f"conclusion needs {RUNGS_FLOOR}. The usable step range is too "
                f"narrow to decide rather than the engine being either thing"
            ),
            fitted_over=None,
            rungs_used=len(kept),
            dropped=tuple(dropped),
            excluded=excluded,
        )

    orders = tuple(
        _local_order(coarse, fine, attributed)
        for coarse, fine in zip(kept, kept[1:])
    )
    slope, intercept = _least_squares(
        [(math.log(rung.step), math.log(attributed[rung.step])) for rung in kept]
    )
    shared = dict(
        fitted_over=(kept[0].step, kept[-1].step),
        rungs_used=len(kept),
        order=slope,
        scale=math.exp(intercept),
        local_orders=orders,
        dropped=tuple(dropped),
        excluded=excluded,
    )

    if all(order >= ORDER_CONVERGENCE_HOLDS for order in orders):
        return Conclusion(
            verdict=CONVERGING,
            reason=(
                f"every one of the {len(orders)} interval(s) falls at order "
                f"{ORDER_CONVERGENCE_HOLDS:g} or better, the shallowest at "
                f"{min(orders):.2f}, so what is left after the exclusions is a "
                f"discretisation error and a finer step buys accuracy"
            ),
            **shared,
        )

    if (
        orders[0] >= ORDER_CONVERGENCE_HOLDS
        and orders[-1] < ORDER_A_FLOOR_HAS_FALLEN_BELOW
    ):
        return Conclusion(
            verdict=FLOORED,
            reason=(
                f"the coarse end falls at order {orders[0]:.2f} and the fine end "
                f"at {orders[-1]:.2f}, so the error stops falling while the step "
                f"is still being refined. What is left at the finest rung is not "
                f"rounding and is not the reference, both of which were taken "
                f"out, so a finer step buys nothing"
            ),
            attributed_floor=attributed[kept[-1].step],
            **shared,
        )

    return Conclusion(
        verdict=UNDECIDED,
        reason=(
            f"the local orders run from {min(orders):.2f} to {max(orders):.2f} "
            f"and neither hold at {ORDER_CONVERGENCE_HOLDS:g} throughout nor "
            f"collapse below {ORDER_A_FLOOR_HAS_FALLEN_BELOW:g} at the fine end. "
            f"The evidence is thin rather than pointing either way"
        ),
        **shared,
    )
