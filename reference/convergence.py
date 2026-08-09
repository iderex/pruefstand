"""The order this reference reaches, measured on this implementation.

Issue #46. `docs/decisions/reference-integration.md` fixes the class of method and
says the base update in that class is second order, then leaves the number this
implementation actually reaches to be measured here. Until it is measured, the
order is a property of the paper the method came from rather than of the code
every published number in this suite is compared against.

What a refinement study catches, and none of the three is visible at a single
step:

- An implementation a whole order lower than intended. One misplaced factor does
  that, and at one step the result is merely small rather than wrong.
- A term evaluated at the wrong point in the step, which costs exactly one order
  and nothing else.
- A rounding floor reached earlier than expected. That one is not a defect, and
  it is worth as much as the other two, because it says which steps this
  reference may be run at instead of leaving it to be discovered by a number that
  looked strange.

## The two ladders, and why there are two

`against_the_closed_form` refines the torque-free symmetric body against its
elementary solution. The answer is known, so the quantity on the ladder is the
error and the slope is the order with nothing standing in for it. The body has to
be symmetric for that to be true: the torque-free asymmetric top's solution is
elliptic and is #44's, and the heavy symmetric top's is elliptic too. So the
closed-form ladder reaches the free half of the update and no further.

`against_the_next_refinement` covers the rest by comparing each run against the
run at half its step. Where the method converges at order p, that difference falls
at order p as well, so the slope is the same number without a known answer behind
it. What it is not is a check against the truth: a method converging steadily to
the wrong answer has a clean slope here. It is used for the heavy top, where the
moment term enters, and the closed-form ladder is what says the arithmetic under
both of them lands on the right answer at all.

## What the slope is read from

The order between two rungs is the log of the ratio of their errors over the log
of the ratio of their steps, so a ladder whose steps do not halve reads correctly
and a ladder that does halve is not a special case of anything.

A single pair of rungs is not a measurement. `Ladder` refuses fewer than three,
because two rungs give one number and there is nothing for it to be consistent
with, and an order that holds over one interval and nowhere else is the shape a
coincidence takes.

## The means

Python and the standard library, in the numerical core, which is where nothing
imports an adapter or an engine. A study that pulled in an array library to hold
nine numbers would add a dependency to the part of the tree with the least reason
to carry one, and the runs it drives are in `reference/integrator.py`, which is
written the same way. The three rules survive it: every condition below is refused
by code rather than asserted in prose, each refusal is tripped by a fixture in
`tests/test_convergence.py`, and every number this module states is one it
computes.

    python -m reference.convergence
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from reference.integrator import (
    Body,
    Matrix,
    State,
    every_step,
    exponential,
    matmul,
    matvec,
    scale,
    spatial_momentum,
)


class StudyRefused(ValueError):
    """A ladder that cannot carry an order, refused at the point it is built."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(problems))


def _refuse(problems: list[str]) -> None:
    if problems:
        raise StudyRefused(sorted(set(problems)))


@dataclass(frozen=True)
class Rung:
    """One run of a refinement study: its step, and what the error was at it.

    `count` is carried beside `step` rather than derived from it because the two
    ends of the range this module reports are bounded by different quantities. The
    coarse end is a step the implicit solve stops contracting at, and the fine end
    is a count of steps the orientation's rounding accumulates over.
    """

    count: int
    step: float
    error: float

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not isinstance(self.count, int) or isinstance(self.count, bool):
            problems.append(f"a rung runs a whole number of steps and this is "
                            f"{self.count!r}")
        elif self.count < 1:
            problems.append(f"a rung runs at least one step and this is "
                            f"{self.count!r}")
        if not isinstance(self.step, float) or not math.isfinite(self.step):
            problems.append(f"a step is a finite float and this is {self.step!r}")
        elif self.step <= 0.0:
            problems.append(f"a step is positive and this is {self.step!r}")
        if not isinstance(self.error, float) or not math.isfinite(self.error):
            problems.append(f"an error is a finite float and this is "
                            f"{self.error!r}")
        elif self.error <= 0.0:
            # Zero is refused rather than admitted as the smallest error. An
            # order is read from a ratio, so a zero has no slope through it, and
            # a run that agreed with its oracle in every bit is the bottom of the
            # ladder rather than a rung on it. The ladder is built above it.
            problems.append(
                f"an error is positive, and this is {self.error!r}, which is the "
                f"bottom of the ladder rather than a rung on it"
            )
        _refuse(problems)


@dataclass(frozen=True)
class Stretch:
    """The part of a ladder whose order is the one being looked for.

    Reported as the two steps that bound it rather than as indices, because the
    thing a reader of this study needs is the range of steps the reference may be
    run at, and an index into a ladder that was chosen here is not that.
    """

    coarsest: Rung
    finest: Rung
    orders: tuple[float, ...]

    @property
    def worst_departure(self) -> float:
        """How far the least convincing interval in the stretch sits from two."""
        return max(abs(order - 2.0) for order in self.orders)


@dataclass(frozen=True)
class Ladder:
    """A refinement study: what the error is of, and the rungs it was taken at.

    The rungs run from the coarsest step to the finest, which is the direction the
    study is read in, and a ladder given them in any other order is refused rather
    than sorted. A study whose rungs arrived out of order is a study whose runs
    were paired with the wrong steps, and sorting it would hide that.
    """

    what: str
    horizon: float
    rungs: tuple[Rung, ...]

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not isinstance(self.horizon, float) or not math.isfinite(self.horizon):
            problems.append(f"a horizon is a finite float and this is "
                            f"{self.horizon!r}")
        elif self.horizon <= 0.0:
            problems.append(f"a horizon is positive and this is "
                            f"{self.horizon!r}")
        if not isinstance(self.rungs, tuple) or not all(
            isinstance(rung, Rung) for rung in self.rungs
        ):
            problems.append(f"a ladder is built of rungs and this is "
                            f"{self.rungs!r}")
            _refuse(problems)
        if len(self.rungs) < 3:
            problems.append(
                f"an order measured over one interval is consistent with nothing, "
                f"so a ladder carries at least three rungs and this one carries "
                f"{len(self.rungs)}"
            )
        for earlier, later in zip(self.rungs, self.rungs[1:]):
            if later.step >= earlier.step:
                problems.append(
                    f"a ladder refines, so each step is smaller than the one "
                    f"before it, and {later.step!r} does not follow "
                    f"{earlier.step!r}"
                )
        _refuse(problems)

    @property
    def orders(self) -> tuple[float, ...]:
        """The observed order over each interval, coarse to fine."""
        return tuple(
            math.log(earlier.error / later.error)
            / math.log(earlier.step / later.step)
            for earlier, later in zip(self.rungs, self.rungs[1:])
        )

    def stretch_at(self, order: float, tolerance: float) -> Stretch | None:
        """The longest run of consecutive intervals that sit at `order`.

        Longest run rather than every interval that qualifies. A ladder leaves the
        asymptotic range at both ends, at the coarse end because the step is too
        large for the leading term to dominate and at the fine end because
        rounding does, and an interval out at one end that lands on the number by
        accident is not part of the range the reference may be run over.
        """
        observed = self.orders
        best_start, best_stop = 0, 0
        start = 0
        for index in range(len(observed) + 1):
            if index == len(observed) or abs(observed[index] - order) > tolerance:
                if index - start > best_stop - best_start:
                    best_start, best_stop = start, index
                start = index + 1
        if best_stop == best_start:
            return None
        return Stretch(
            coarsest=self.rungs[best_start],
            finest=self.rungs[best_stop],
            orders=observed[best_start:best_stop],
        )

    def rounding_floor(self) -> Rung | None:
        """The first rung refining onto did not buy, or None if there is none.

        This is where rounding takes over: below it the error stops falling and
        starts rising, because the accumulated rounding of more steps is larger
        than the truncation the smaller step removed. A ladder that never reaches
        it says so by returning nothing, which is a different statement from a
        floor at the last rung and must not be written as one.
        """
        for earlier, later in zip(self.rungs, self.rungs[1:]):
            if later.error >= earlier.error:
                return later
        return None


def departure(reached: Matrix, expected: Matrix) -> float:
    """How far two orientations are apart, as the worst of their nine entries.

    A max norm rather than a rotation angle. The entries are what the update
    computes and what rounding lands in, an angle would put a trigonometric
    function between the measurement and the thing measured, and at the bottom of
    the ladder that function's own rounding is the same size as the error.
    """
    return max(
        abs(reached[row][column] - expected[row][column])
        for row in range(3)
        for column in range(3)
    )


# The symmetric body the closed form is available for. Its numbers are here to
# exercise the reference and are not a case of this suite; the cases carry
# parameters that are sourced rather than invented and they are #52 to #54.
TRANSVERSE = 2.0
AXIAL = 3.0
SYMMETRIC: Matrix = (
    (TRANSVERSE, 0.0, 0.0),
    (0.0, TRANSVERSE, 0.0),
    (0.0, 0.0, AXIAL),
)
FREE_VELOCITY = (0.7, 0.0, 1.3)
FREE_TILT = (0.3, -0.2, 0.15)

# A heavy symmetric top about its pivot. The body is the one the integrator's own
# tests turn, and the initial condition is not: it is tilted far over and spun
# slowly, where that file spins it fast and tilts it a little.
#
# The reason is the near-miss this ladder exists to catch, which is the moment
# read at the wrong end of the step. That mistake costs one order, and whether a
# ladder sees it depends on how large the first-order term it introduces is beside
# the second-order term the method already has. A fast top's own second-order term
# is large, because the step has to resolve the spin, and it hides the mistake
# down to a step of about 1e-5, which is far below anything a study would run at.
# Slowing the spin and tilting the body over shrinks the second-order term and
# leaves the moment varying, and the mistake then shows at every rung. Measured
# both ways, in `tests/test_convergence.py`, and the numbers are in
# `reference/order-of-convergence.md`.
HEAVY = Body(
    inertia=((0.02, 0.0, 0.0), (0.0, 0.02, 0.0), (0.0, 0.0, 0.008)),
    mass=0.3,
    gravity=9.81,
    centre_of_mass=(0.0, 0.0, 0.05),
)
HEAVY_TILT = 1.2
HEAVY_SPIN = 8.0


def free_symmetric_top() -> tuple[Body, State]:
    """The torque-free symmetric body and the state it starts from."""
    return (
        Body(inertia=SYMMETRIC),
        State(exponential(FREE_TILT), matvec(SYMMETRIC, FREE_VELOCITY)),
    )


def exact_orientation(start: State, time: float) -> Matrix:
    """Where the free symmetric body is at `time`, from the elementary solution.

    A torque-free symmetric body turns about the fixed spatial angular momentum at
    a constant rate while turning about its own axis at a constant rate, so its
    orientation is a product of two exponentials with nothing to solve. Written
    out here rather than obtained by integrating something, which is the whole
    point of using this body: an oracle that shared the update's arithmetic would
    measure the order of nothing.
    """
    spatial = spatial_momentum(start)
    rate = (AXIAL - TRANSVERSE) * FREE_VELOCITY[2] / TRANSVERSE
    return matmul(
        matmul(exponential(scale(spatial, time / TRANSVERSE)), start.orientation),
        exponential((0.0, 0.0, -rate * time)),
    )


def against_the_closed_form(horizon: float, counts: tuple[int, ...]) -> Ladder:
    """The free symmetric body's error against its solution, at each step.

    Every rung is compared at `count * step` rather than at `horizon`. The two are
    the same number in exact arithmetic and are not always the same float, and
    comparing at a time the run did not reach would put a piece of the exact
    motion into the error and call it truncation.
    """
    body, start = free_symmetric_top()
    rungs: list[Rung] = []
    for count in _refined(horizon, counts):
        step = horizon / count
        reached = every_step(body, start, step, count)[-1]
        rungs.append(
            Rung(
                count=count,
                step=step,
                error=departure(
                    reached.orientation, exact_orientation(start, step * count)
                ),
            )
        )
    return Ladder(
        what="the orientation, against the free symmetric top's closed form",
        horizon=horizon,
        rungs=tuple(rungs),
    )


def against_the_next_refinement(
    body: Body, start: State, horizon: float, counts: tuple[int, ...]
) -> Ladder:
    """Each run against the run at the next step down, for a case with no oracle.

    The rung's step is the coarser of the two the difference is taken between, so
    the slope is read against the step whose truncation dominates the difference.
    Attributing the difference to the finer step would report the same slope
    shifted by one rung and would make the reported range of steps wrong at both
    ends.
    """
    ordered = _refined(horizon, counts)
    reached = []
    for count in ordered:
        reached.append(every_step(body, start, horizon / count, count)[-1])
    rungs = [
        Rung(
            count=count,
            step=horizon / count,
            error=departure(coarse.orientation, fine.orientation),
        )
        for count, coarse, fine in zip(ordered, reached, reached[1:])
    ]
    return Ladder(
        what="the orientation, against the run at the next step down",
        horizon=horizon,
        rungs=tuple(rungs),
    )


def _refined(horizon: float, counts: tuple[int, ...]) -> tuple[int, ...]:
    """The step counts of a study, refused unless they are a refinement.

    Counts rather than steps are what a caller writes, because a run takes a whole
    number of steps and a step written as a decimal is a request to land on a grid
    the run may not have. Refusing here rather than in `Ladder` means a study that
    was going to be unreadable does not cost the runs first.
    """
    problems: list[str] = []
    if not isinstance(horizon, float) or not math.isfinite(horizon) or horizon <= 0:
        problems.append(f"a horizon is a positive finite float and this is "
                        f"{horizon!r}")
    if not isinstance(counts, tuple) or len(counts) < 2:
        problems.append(
            f"a study runs at least two step counts and this is {counts!r}"
        )
        _refuse(problems)
    for earlier, later in zip(counts, counts[1:]):
        if later <= earlier:
            problems.append(
                f"a study refines, so each count is larger than the one before "
                f"it, and {later!r} does not follow {earlier!r}"
            )
    _refuse(problems)
    return counts


def report(ladder: Ladder) -> str:
    """The ladder as the lines this module prints, and as a document quotes them."""
    lines = [f"{ladder.what}, horizon {ladder.horizon}"]
    observed = ladder.orders
    for index, rung in enumerate(ladder.rungs):
        order = "" if index == 0 else f"{observed[index - 1]:.3f}"
        lines.append(
            f"  N={rung.count:<9d} h={rung.step:.4e}  error={rung.error:.6e}  "
            f"order={order:>6}"
        )
    stretch = ladder.stretch_at(2.0, 0.1)
    if stretch is None:
        lines.append("  no stretch of this ladder sits at order two")
    else:
        lines.append(
            f"  order two from h={stretch.coarsest.step:.4e} to "
            f"h={stretch.finest.step:.4e}, over "
            f"{len(stretch.orders)} interval(s), worst departure "
            f"{stretch.worst_departure:.3f}"
        )
    floor = ladder.rounding_floor()
    if floor is None:
        lines.append(
            "  rounding does not take over anywhere on this ladder, so the "
            "floor is below its finest step and is not measured here"
        )
    else:
        lines.append(
            f"  rounding takes over at h={floor.step:.4e}, where the error is "
            f"{floor.error:.6e} after {floor.count} steps"
        )
    return "\n".join(lines)


def main() -> None:
    """The study at the sampling the record quotes, which the gate does not run.

    The gate runs the same ladders at fewer rungs over a shorter horizon, in
    `tests/test_convergence.py`. What is here is the long form: it reaches the
    rounding floor, which the reduced sampling deliberately does not, because a
    ladder that runs down to the floor costs more time than a gate should spend on
    one property.
    """
    print(report(against_the_closed_form(2.0, (4, 8, 16, 32, 64, 128, 256, 512))))
    print()
    print(
        report(
            against_the_closed_form(
                0.005, (16, 32, 64, 128, 256, 512, 1024, 2048, 4096)
            )
        )
    )
    print()
    start = State(
        exponential((HEAVY_TILT, 0.0, 0.0)),
        matvec(HEAVY.inertia, (0.0, 0.0, HEAVY_SPIN)),
    )
    print(
        report(
            against_the_next_refinement(
                HEAVY, start, 0.5, (32, 64, 128, 256, 512, 1024, 2048, 4096)
            )
        )
    )


if __name__ == "__main__":
    main()
