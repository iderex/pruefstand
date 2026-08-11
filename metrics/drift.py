"""The drift of a conserved quantity: its sign, its rate and its swing.

Issue #56. `metrics/drift-sign-and-shape.md` fixed what a conserved-quantity
metric reports and the conditions under which each part of it means anything.
This computes them, and it is the first thing in this tree that reads that
document rather than restating it.

The document's own argument is not repeated here. What is here is the part a
reader of the code needs and the two places where implementing it found the
document reading more than one way.

## What is computed

Write `I(t)` for the integral the case names and `g(t)` for its relative change,
`(I(t) - I(0)) / abs(I(0))`. The value is `g` at the end of the horizon, signed,
and it is the number the class already scores. Beside it:

- the secular rate, the signed slope of the least-squares straight line fitted
  to `g` over the whole horizon, in relative change per second;
- the oscillation amplitude, the largest absolute residual about that line;
- the oscillation growth, the amplitude over the second half divided by the
  amplitude over the first half.

A vector integral is done per component and never as a norm. `per_component`
exists for that and takes no shortcut through a magnitude, because a momentum
that walks along its own direction and one that walks across it are different
faults and a norm reports them identically.

## Where a component is withheld

The document names three conditions and says that where any of them fails "the
result says which one and the two components are absent rather than zero".

That sentence reads two ways, and this takes the narrower one: each condition
withholds what it actually invalidates, rather than every component whenever any
condition fails. The document's own third condition is what decides it, because
that condition treats the two separately in its own words, an amplitude below
the floor and a rate whose change over the horizon is below the same floor being
two sentences with two verdicts. Withholding both together would contradict the
condition it came from. The reading is stated here rather than left live, and
`Drift.withheld` names every condition that fired whether or not it was the one
that removed a given number.

So: a residual that does not change sign twice, and a run sampled too coarsely
for the period its own residual shows, each remove the amplitude and the growth
and leave the rate. The floor removes whichever of the two it reaches.

## The floor is the caller's

The third condition leans on the run-to-run term from
`docs/decisions/uncertainty-reporting.md`, which is a measured property of a set
of runs and not a number this file could invent. It is a required argument. A
default here would be a tolerance written into the metric code, which is the
shape `tests/test_greppable_invariants.py` refuses by name, and it would be the
same floor for every case.

## A straight line fitted to a pure swing has a slope, and it is not zero

Measured rather than assumed, and it is a property of the method the document
fixes rather than of this implementation. A sinusoid of amplitude `A` sampled
over `n` whole periods, with no walk in it at all, produces a least-squares
slope whose change over the horizon is about `1.9 * A / n`, and an amplitude
about `1 + 0.95 / n` times `A`:

    python -c "
    import math, sys; sys.path.insert(0, '.')
    from metrics.drift import drift
    def sinus(periods, per_period=32, A=1e-05):
        step = 1.0 / per_period
        return [(k * step, 4.0 * (1.0 + A * math.sin(2 * math.pi * k * step)))
                for k in range(periods * per_period)]
    for p in (5, 10, 25, 50, 100, 200):
        d = drift(sinus(p), floor=0.0)
        print(p, f'{d.rate * d.horizon / 1e-05:+.5f}', f'{d.amplitude / 1e-05:.5f}')
    "
    5 -0.37838 1.13446
    10 -0.18978 1.08121
    25 -0.07605 1.03584
    50 -0.03805 1.01848
    100 -0.01903 1.00472

So a run over five periods reports a secular change nearly two fifths of its own
swing when there is no secular change in it. The document's remedy is the one
already in it and it is the third condition: a rate whose change over the
horizon does not exceed the run-to-run floor is not reported. What this
measurement adds is that the floor is doing more work than the document says,
because it is also what keeps a short window from reporting its own swing as a
walk, and that a case whose horizon is a few periods of the motion has a
secular rate this method cannot separate from zero however clean the run was.
Neither is repaired here. Windowing or a longer horizon are both decisions
about a case rather than about an estimator, and discarding a partial period
would be discarding a transient, which the document refuses by name.

## What this cannot do

The resolution condition counts samples per period over the whole horizon, so it
assumes the run sampled at roughly one rate. A run whose interval varied by a
large factor can pass it while the swing was undersampled in one stretch, and
nothing here sees that. Uneven sampling is not refused, because a record that
sampled on the integrator's own steps is a legitimate record and refusing it
would be inventing a requirement the run record has not fixed; #10 is where the
interval is decided.

The straight-line model is the document's and its cost is the document's too: a
drift growing faster than linearly is not described by these numbers, and what
refuses to report them as if it were is the sign-change condition rather than
anything cleverer.

## The means

Python and the standard library, in the numerical core, where nothing imports an
adapter or an engine. Two least-squares fits over a list of pairs is a dozen
lines of scalar arithmetic and an array library would be a dependency taken for
a dot product, which is the same answer `metrics/error_source.py` reached for
the same shape of work. The three rules survive it: every condition below is
refused by code rather than asserted in prose, each refusal is tripped by a
fixture in `tests/test_drift.py` that is a working series with one thing
changed, and every number in this module's own docstrings is one its tests
compute.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# The names of the three conditions, as they appear on a withheld result and as
# a report card would render them. Strings rather than an enumeration, because
# what a cell says is the string, and a cell saying which condition failed is
# the document's requirement rather than a convenience.
NO_SWING = "the residual does not change sign twice, so there is no swing to size"
TOO_COARSE = "fewer than {found:.3g} samples per residual period, and the floor is {floor}"
BELOW_FLOOR = "the {part} does not exceed the run-to-run floor {floor!r}"
NO_FIRST_HALF = "the first half of the horizon has no swing to take a ratio against"

# Samples per residual period, below which the amplitude is an artefact of where
# the samples fell rather than the size of the swing. From
# `metrics/drift-sign-and-shape.md`: a sample can fall half an interval from the
# true extremum, so a sinusoid sampled n times per period has its peak
# underestimated by at most 1 - cos(pi/n), which is under two per cent at
# sixteen and 7.61 per cent at eight.
#
#     python -c "import math; [print(n, f'{100*(1-math.cos(math.pi/n)):.2f}') for n in (8, 16)]"
#     8 7.61
#     16 1.92
SAMPLES_PER_PERIOD_FLOOR = 16.0

# The fewest sign changes the residual may show for the largest absolute
# residual to be a swing rather than a systematic departure from the line.
SIGN_CHANGES_FLOOR = 2

# The fewest samples a fit is made from. Two determine a line exactly and leave
# no residual at all, so three is the first count at which the model can be
# wrong about anything.
SAMPLES_FLOOR = 3


class DriftRefused(ValueError):
    """Raised instead of returning a drift computed from something else.

    A refusal here is about the samples rather than about the drift. A run this
    cannot read is a different statement from a run whose swing could not be
    separated, and the second is a `Drift` carrying what was withheld.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(self.problems))


@dataclass(frozen=True)
class Drift:
    """The signed value of a conserved-quantity metric, and its two components.

    `rate`, `amplitude` and `growth` are `None` where the conditions did not
    support them, and never zero. A zero is a measurement and an absence is not,
    and the whole of this issue is that the two must not look alike.
    """

    value: float
    rate: float | None
    amplitude: float | None
    growth: float | None
    withheld: tuple[str, ...]
    samples: int
    horizon: float
    floor: float
    sign_changes: int
    samples_per_period: float | None

    @property
    def separated(self) -> bool:
        """Whether every component was measured."""
        return not self.withheld

    def __str__(self) -> str:
        def show(name: str, found: float | None) -> str:
            return f"{name} {found:+.4g}" if found is not None else f"{name} withheld"

        head = (
            f"{self.value:+.4g} over {self.horizon:g} s, "
            f"{show('rate', self.rate)}, "
            f"{show('amplitude', self.amplitude)}, "
            f"{show('growth', self.growth)}"
        )
        if not self.withheld:
            return head
        return head + "; " + "; ".join(self.withheld)


def _is_finite_float(value: object) -> bool:
    return isinstance(value, float) and math.isfinite(value)


def _line(points: list[tuple[float, float]]) -> tuple[float, float]:
    """The least-squares straight line through `points`, as slope and intercept.

    Written out rather than taken from `statistics.linear_regression`, which
    raises where the times do not vary; the caller has already refused that
    case, and this keeps the two least-squares fits in this file identical.
    """
    count = len(points)
    mean_at = sum(at for at, _ in points) / count
    mean_of = sum(of for _, of in points) / count
    across = sum((at - mean_at) * (of - mean_of) for at, of in points)
    along = sum((at - mean_at) ** 2 for at, _ in points)
    slope = across / along
    return slope, mean_of - slope * mean_at


def _sign_changes(residuals: list[float]) -> int:
    """How often the residual crosses the line, counting a zero as no crossing.

    A residual of exactly zero is a sample sitting on the line, which is neither
    side of it. Treating it as a crossing would let a flat series that touches
    the line report a swing.
    """
    changes = 0
    last = 0.0
    for residual in residuals:
        if residual == 0.0:
            continue
        if last != 0.0 and (residual > 0.0) != (last > 0.0):
            changes += 1
        last = residual
    return changes


def _amplitude(residuals: list[float]) -> float:
    return max(abs(residual) for residual in residuals)


def drift(samples: list[tuple[float, float]], *, floor: float) -> Drift:
    """The drift of one scalar integral over a run, with its two components.

    `samples` is `(time, integral)` in increasing time, over the whole horizon
    the case declares. `floor` is the run-to-run term the third condition leans
    on, and it is the caller's.
    """
    problems: list[str] = []

    if not _is_finite_float(floor) or floor < 0.0:
        problems.append(
            f"the run-to-run floor is {floor!r} and has to be a finite float that "
            f"is not negative, being a spread over repeats"
        )
    if len(samples) < SAMPLES_FLOOR:
        problems.append(
            f"the run carries {len(samples)} sample(s) and the floor is "
            f"{SAMPLES_FLOOR}, below which a straight line has no residual and "
            f"nothing here is a measurement"
        )
    if problems:
        raise DriftRefused(sorted(set(problems)))

    previous: float | None = None
    for index, pair in enumerate(samples):
        if not isinstance(pair, tuple) or len(pair) != 2:
            problems.append(f"sample {index} is not a (time, integral) pair")
            continue
        at, of = pair
        if not _is_finite_float(at) or not _is_finite_float(of):
            problems.append(
                f"sample {index} is {at!r} and {of!r}, and both are finite floats"
            )
            continue
        if previous is not None and at <= previous:
            problems.append(
                f"sample {index} is at {at!r} and the one before it at "
                f"{previous!r}, and samples are in increasing time"
            )
        previous = at
    if problems:
        raise DriftRefused(sorted(set(problems)))

    start = samples[0][1]
    if start == 0.0:
        raise DriftRefused(
            [
                "the integral is zero at the initial condition, so a relative "
                "change in it is a division by zero. A case whose integral "
                "starts at zero is scored on an absolute change, and which one "
                "it is is the case's to name"
            ]
        )

    relative = [(at, (of - start) / abs(start)) for at, of in samples]
    horizon = relative[-1][0] - relative[0][0]
    value = relative[-1][1]

    slope, intercept = _line(relative)
    residuals = [of - (slope * at + intercept) for at, of in relative]
    changes = _sign_changes(residuals)

    withheld: list[str] = []

    # The rate, and the only condition that reaches it: a walk whose whole
    # change over the horizon is inside the run-to-run spread is a walk this
    # study cannot distinguish from repeating the run.
    rate: float | None = slope
    if abs(slope * horizon) <= floor:
        rate = None
        withheld.append(BELOW_FLOOR.format(part="rate over the horizon", floor=floor))

    # The amplitude and the growth, and the three conditions that reach them.
    amplitude: float | None = _amplitude(residuals)
    per_period: float | None = None
    if changes < SIGN_CHANGES_FLOOR:
        amplitude = None
        withheld.append(NO_SWING)
    else:
        # The period is read from the residual's own sign changes: two changes
        # to a period, so the samples per period follow from the count alone and
        # nothing has to be declared in the case file.
        per_period = 2.0 * len(relative) / changes
        if per_period < SAMPLES_PER_PERIOD_FLOOR:
            amplitude = None
            withheld.append(
                TOO_COARSE.format(found=per_period, floor=SAMPLES_PER_PERIOD_FLOOR)
            )
    if amplitude is not None and amplitude <= floor:
        amplitude = None
        withheld.append(BELOW_FLOOR.format(part="amplitude", floor=floor))

    growth: float | None = None
    if amplitude is not None:
        half = len(residuals) // 2
        first = _amplitude(residuals[:half])
        second = _amplitude(residuals[half:])
        if first == 0.0:
            withheld.append(NO_FIRST_HALF)
        else:
            growth = second / first

    return Drift(
        value=value,
        rate=rate,
        amplitude=amplitude,
        growth=growth,
        withheld=tuple(withheld),
        samples=len(relative),
        horizon=horizon,
        floor=floor,
        sign_changes=changes,
        samples_per_period=per_period,
    )


def per_component(
    samples: list[tuple[float, tuple[float, ...]]], *, floor: float
) -> tuple[Drift, ...]:
    """One `Drift` per component of a vector integral, in the order given.

    Never a norm, and there is no route here that produces one. A vector
    integral is reported as a vector of the same shape, which is fixed in
    `docs/decisions/metric-per-class.md`, and the reason is that a quantity
    walking along its own direction and one walking across it are different
    faults that a magnitude reports identically.
    """
    if not samples:
        raise DriftRefused(["the run carries no samples"])

    widths = {len(of) for _, of in samples if isinstance(of, tuple)}
    if len(widths) != 1 or not isinstance(samples[0][1], tuple):
        raise DriftRefused(
            [
                f"the integral is a vector of one shape over the run, and this "
                f"carries {sorted(widths)} component(s)"
            ]
        )

    width = widths.pop()
    if width == 0:
        raise DriftRefused(["the integral has no components"])

    return tuple(
        drift([(at, of[index]) for at, of in samples], floor=floor)
        for index in range(width)
    )
