"""The largest Lyapunov exponent, estimated from runs rather than from equations.

Issue #75. The exponent is the metric for the chaotic class, so this is a piece of
numerical code that has to be right, and it is easy to write one that returns a
plausible number for anything. What makes it checkable is that two of the systems
below have an exponent somebody else published, so the estimator can be wrong in a
way this repository can see.

## What "from runs alone" means here

Two constructions estimate this quantity. One evolves a perturbation under the
linearised equations, which is cleaner and needs the equations. The other evolves a
second trajectory started from a nearby state and measures how the two separate,
which needs no linearisation at all.

Most of the engines in scope will not give a linearisation, so this implements the
second. It is stated precisely because "from trajectories alone" can be read two
ways and only one of them is achievable: this estimator needs no derivative, no
Jacobian and no knowledge of the equations, and it does need to start a run from a
state it chooses. That second thing is what renormalisation is. Two recorded
trajectories and nothing else cannot be renormalised, and without renormalisation
the accumulated growth telescopes to the ratio of the last separation to the first,
which saturates at the size of the attractor and reports a number that falls like
one over the horizon whatever the system does. So the input here is a `flow`: a
callable that advances a state by a duration. Every engine offers one and no
engine's linearisation does.

## The construction

    y is placed at distance d from x, in a direction
    each interval of length tau, both are advanced by the flow
    s is the separation reached
    log(s / d) is one interval's growth
    y is pulled back onto the line from x to y at distance d again

The exponent is the mean of `log(s / d) / tau` over the intervals that are kept.

Three things that construction gets right and a single long run does not. The
perturbation is held small, so what is measured is the separation rate of the
system rather than the diameter of its attractor. The direction of the
perturbation is not chosen: after a few intervals it lies along the most unstable
direction whatever it started as, which is why the settling window below is
discarded rather than averaged in. And every interval contributes one sample, so
the spread of those samples is a measurement rather than an assumption.

## The uncertainty, and why it is not the plain standard error

The per-interval exponents are correlated: an orbit passing through a strongly
separating region gives several large ones in a row. Dividing their standard
deviation by the square root of their count would therefore report an uncertainty
too small by whatever the correlation length is, which is the failure mode that
makes a benchmark number look decisive when it is not.

So the samples are cut into contiguous blocks, each block is averaged, and the
uncertainty is the standard error over the block means. A block long compared with
the correlation length makes the block means nearly independent, and the estimator
refuses a run that cannot give it blocks long enough to say that. `BLOCKS` and
`INTERVALS_PER_BLOCK_FLOOR` are the two numbers behind that, and both are printed
by every estimate rather than left in this file.

## Choosing the separation and the interval

`choose_separation` and `choose_interval` implement the rule. Neither is a default
somebody can drift; both are measured from the system being run and both are
recorded on the estimate they produced. The rule and what was measured under it are
in `metrics/lyapunov-exponent.md`, together with the sensitivity of the answer to
both.

## The means

Python and the standard library, in the numerical core, where nothing imports an
adapter or an engine. The state is a tuple of floats and the arithmetic is over
scalars, so an array library would hold three numbers at a time and add a
dependency to the part of the tree with the least reason to carry one. The three
rules survive it: every condition below is refused by code rather than asserted,
each refusal is tripped by a fixture in `tests/test_lyapunov.py` that is a working
call with one thing changed, and every number this module states is one it
computes.

    python -m metrics.lyapunov
"""

from __future__ import annotations

import math
import random
import statistics
import sys
from dataclasses import dataclass
from typing import Callable, Sequence

# A point in the system's phase space. A tuple rather than a class, because this
# estimator is not allowed to know what the coordinates mean: an estimator that
# could tell an orientation from an angular velocity is one that could weigh them
# differently for two engines.
State = tuple[float, ...]

# A callable that advances a state by a duration and returns the state reached.
# This is the whole of what the estimator asks of a system, and it is what an
# engine can be asked for.
Flow = Callable[[State, float], State]

# The blocks the samples are cut into for the uncertainty, and the fewest
# intervals a block may hold. Two blocks give a standard error over two numbers,
# which is a number and is not a measurement, so the floor is higher than the
# arithmetic needs.
BLOCKS = 20
INTERVALS_PER_BLOCK_FLOOR = 8

# The rounding scale of a float, used as the smallest separation that is a
# separation rather than the difference between two roundings. Read from the
# interpreter rather than written down, so it is right on an interpreter this
# was not measured on.
ROUNDING = sys.float_info.epsilon

# The perturbation direction is drawn from this seed and no other. A direction
# somebody picks by hand is a direction that can be special: along the flow it
# measures nothing for several intervals, and in a symmetry plane of the system it
# can stay there. Drawing it fixes the arbitrariness in one place and keeps the
# whole estimate reproducible, which is what the determinism promise asks for.
DIRECTION_SEED = 75

# What `choose_separation` puts between the noise floor and the ceiling, as the
# exponent of the geometric mean. A half is the mean itself.
SEPARATION_PLACEMENT = 0.5

# `choose_interval` asks for about this much growth per interval, in factors of e.
# One is the scale on which the separation stops being small compared with the
# attractor and starts being bent by it.
GROWTH_PER_INTERVAL = 1.0


class EstimateRefused(ValueError):
    """A run that cannot produce an exponent this project would publish."""


def _is_finite_float(value: object) -> bool:
    return isinstance(value, float) and math.isfinite(value)


def _finite_state(state: object) -> bool:
    return (
        isinstance(state, tuple)
        and len(state) > 0
        and all(_is_finite_float(value) for value in state)
    )


def separation(first: State, second: State) -> float:
    """The distance between two states.

    Euclidean over the coordinates as given. The estimator has no way to know
    that one coordinate is an angle and another a rate, so the caller states the
    phase space it wants measured by choosing what a state holds. That is a bound
    on this file rather than a property of it, and it is why the systems in
    `known_exponents.py` carry their state in the coordinates their published
    exponent was computed in.
    """
    if len(first) != len(second):
        raise EstimateRefused(
            f"the two runs are in different phase spaces, of {len(first)} and "
            f"{len(second)} coordinates, so nothing measures between them"
        )
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def snapped(interval: float, grain: float) -> float:
    """`interval`, moved to the nearest whole number of `grain`, never below one.

    A flow that advances in whole units of something cannot be asked for a
    duration between two of them, and the wrong repair is for the flow to round
    the request silently. That rounding is invisible and it scales the answer:
    the growth measured is the growth over the duration taken, and it is divided
    by the duration asked for. A map asked for 2.386 iterations and taking 2
    reports an exponent 2 over 2.386 of the true one, which is a plausible number
    that is wrong by sixteen per cent. Measured, in
    `metrics/lyapunov-exponent.md`.

    So the snapping happens here, where the caller can see it and record which
    interval was used, and the flow refuses anything it cannot advance by exactly.
    """
    if not _is_finite_float(grain) or grain <= 0.0:
        raise EstimateRefused(f"a grain is a positive finite float and is {grain!r}")
    if not _is_finite_float(interval) or interval <= 0.0:
        raise EstimateRefused(
            f"an interval is a positive finite float and is {interval!r}"
        )
    return grain * max(1, round(interval / grain))


def _displaced(base: State, direction: Sequence[float], distance: float) -> State:
    return tuple(value + distance * step for value, step in zip(base, direction))


def _pulled_back(base: State, far: State, reached: float, distance: float) -> State:
    """`far`, moved back along the line to `base` until it is `distance` away."""
    scale = distance / reached
    return tuple(a + (b - a) * scale for a, b in zip(base, far))


def unit_direction(dimension: int, seed: int = DIRECTION_SEED) -> tuple[float, ...]:
    """A unit vector in `dimension` coordinates, drawn from a stated seed."""
    if dimension < 1:
        raise EstimateRefused("a phase space has at least one coordinate")
    draw = random.Random(seed)
    while True:
        raw = tuple(draw.gauss(0.0, 1.0) for _ in range(dimension))
        length = math.sqrt(sum(value**2 for value in raw))
        if length > 0.0:
            return tuple(value / length for value in raw)


@dataclass(frozen=True)
class Estimate:
    """An exponent and how far it is known, which are one thing.

    There is no constructor that produces a value without an uncertainty. The
    field is required and positional, so omitting it is a `TypeError` from the
    interpreter before any of this runs, and a value that is not a positive
    finite float is refused here. A bare exponent invites a comparison between two
    engines that the data does not support, and it is the single most likely way
    this project publishes a wrong conclusion from a right number.
    """

    value: float
    uncertainty: float
    intervals: int
    blocks: int
    settled: int
    interval: float
    displacement: float
    horizon: float

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not _is_finite_float(self.value):
            problems.append(f"an exponent is a finite float and this is {self.value!r}")
        if not _is_finite_float(self.uncertainty):
            problems.append(
                f"an uncertainty is a finite float and this is {self.uncertainty!r}"
            )
        elif self.uncertainty <= 0.0:
            problems.append(
                f"the uncertainty is {self.uncertainty!r}, and an uncertainty of "
                f"zero or less claims the exponent is exact, which no estimate "
                f"from a finite run is"
            )
        if self.blocks < 2:
            problems.append(
                f"the uncertainty is a spread over {self.blocks} block(s), and a "
                f"spread over fewer than two is not a measurement"
            )
        if self.intervals < self.blocks:
            problems.append(
                f"{self.intervals} interval(s) cannot fill {self.blocks} block(s)"
            )
        if self.settled < 0:
            problems.append("the settling window is a count of intervals discarded")
        for name, found in (
            ("interval", self.interval),
            ("displacement", self.displacement),
            ("horizon", self.horizon),
        ):
            if not _is_finite_float(found) or found <= 0.0:
                problems.append(f"{name} is a positive finite float and is {found!r}")
        if problems:
            raise EstimateRefused("; ".join(problems))

    @property
    def relative_uncertainty(self) -> float:
        """The uncertainty as a fraction of the value, for a non-zero value."""
        if self.value == 0.0:
            raise EstimateRefused(
                "a relative uncertainty on an exponent of zero is a division by "
                "zero, and an exponent of zero is exactly the answer the regular "
                "systems are here to produce"
            )
        return abs(self.uncertainty / self.value)

    def agrees_with(self, published: float, spread: float) -> bool:
        """Whether `published` lies within `spread` uncertainties of this value.

        `spread` is the caller's, never this file's. How many uncertainties count
        as agreement is a statement about what is being claimed, and a number
        here would be one this module made on every caller's behalf.
        """
        if not _is_finite_float(published):
            raise EstimateRefused(f"a published exponent is a float, not {published!r}")
        if not _is_finite_float(spread) or spread <= 0.0:
            raise EstimateRefused(
                f"a spread is a positive finite float, not {spread!r}"
            )
        return abs(self.value - published) <= spread * self.uncertainty

    def __str__(self) -> str:
        return (
            f"{self.value:+.4f} +/- {self.uncertainty:.4f} per unit time, over "
            f"{self.intervals} interval(s) of {self.interval:g} at a separation "
            f"of {self.displacement:.3e}, in {self.blocks} block(s), after "
            f"{self.settled} discarded"
        )


def growth_samples(
    flow: Flow,
    start: State,
    *,
    displacement: float,
    interval: float,
    horizon: float,
    settling: float,
    direction: Sequence[float] | None = None,
) -> list[float]:
    """One finite-time exponent per renormalisation interval, settling discarded.

    Every refusal here is a run that cannot carry an exponent, and each is refused
    rather than repaired, because every repair available invents something. A flow
    that returned a non-finite state has left the phase space, and an exponent
    fitted over the intervals before it would be an exponent for a run that did
    not finish.
    """
    if not _finite_state(start):
        raise EstimateRefused(f"the starting state is not finite: {start!r}")
    for name, found in (
        ("the separation", displacement),
        ("the interval", interval),
        ("the horizon", horizon),
    ):
        if not _is_finite_float(found) or found <= 0.0:
            raise EstimateRefused(f"{name} is a positive finite float and is {found!r}")
    if not _is_finite_float(settling) or settling < 0.0:
        raise EstimateRefused(
            f"the settling window is a finite duration of zero or more and is "
            f"{settling!r}"
        )
    if settling >= horizon:
        raise EstimateRefused(
            f"the settling window is {settling} of a horizon of {horizon}, so "
            f"every interval would be discarded and nothing would be measured"
        )

    if direction is None:
        direction = unit_direction(len(start))
    elif len(direction) != len(start):
        raise EstimateRefused(
            f"the perturbation is in {len(direction)} coordinates and the state "
            f"is in {len(start)}"
        )

    here = start
    there = _displaced(start, direction, displacement)
    taken = int(horizon / interval)
    discarded = int(settling / interval)
    samples: list[float] = []
    for step in range(taken):
        here = flow(here, interval)
        there = flow(there, interval)
        if not _finite_state(here) or not _finite_state(there):
            raise EstimateRefused(
                f"the flow left the phase space at interval {step + 1} of {taken}, "
                f"so there is no exponent for this run rather than a shorter one"
            )
        reached = separation(here, there)
        if reached <= 0.0:
            raise EstimateRefused(
                f"the two runs met exactly at interval {step + 1}, so the growth "
                f"over that interval has no logarithm. A flow that collapses two "
                f"distinct states onto one is not one this estimator can read"
            )
        if step >= discarded:
            samples.append(math.log(reached / displacement) / interval)
        there = _pulled_back(here, there, reached, displacement)
    return samples


def from_samples(
    samples: Sequence[float],
    *,
    interval: float,
    displacement: float,
    horizon: float,
    settled: int,
    blocks: int = BLOCKS,
) -> Estimate:
    """The exponent and its uncertainty, by block means over the samples."""
    if blocks < 2:
        raise EstimateRefused(
            f"the uncertainty is a spread over {blocks} block(s), and a spread "
            f"over fewer than two is not a measurement"
        )
    per_block = len(samples) // blocks
    if per_block < INTERVALS_PER_BLOCK_FLOOR:
        raise EstimateRefused(
            f"{len(samples)} interval(s) over {blocks} block(s) is {per_block} "
            f"each, and the floor is {INTERVALS_PER_BLOCK_FLOOR}. A block shorter "
            f"than the correlation between neighbouring intervals reports an "
            f"uncertainty smaller than the spread it is measuring. Lengthen the "
            f"horizon rather than lowering the floor"
        )
    used = per_block * blocks
    means = [
        statistics.fmean(samples[index * per_block : (index + 1) * per_block])
        for index in range(blocks)
    ]
    spread = statistics.stdev(means)
    if spread <= 0.0:
        raise EstimateRefused(
            "every block mean is identical, so the spread is zero and the "
            "estimate would claim to be exact. That is a run whose samples do "
            "not vary rather than a run measured very well"
        )
    return Estimate(
        value=statistics.fmean(means),
        uncertainty=spread / math.sqrt(blocks),
        intervals=used,
        blocks=blocks,
        settled=settled,
        interval=interval,
        displacement=displacement,
        horizon=horizon,
    )


def largest_exponent(
    flow: Flow,
    start: State,
    *,
    displacement: float,
    interval: float,
    horizon: float,
    settling: float,
    blocks: int = BLOCKS,
    direction: Sequence[float] | None = None,
) -> Estimate:
    """The largest Lyapunov exponent of `flow` at `start`, with its uncertainty."""
    samples = growth_samples(
        flow,
        start,
        displacement=displacement,
        interval=interval,
        horizon=horizon,
        settling=settling,
        direction=direction,
    )
    return from_samples(
        samples,
        interval=interval,
        displacement=displacement,
        horizon=horizon,
        settled=int(settling / interval),
        blocks=blocks,
    )


def excursion(flow: Flow, start: State, *, interval: float, horizon: float) -> float:
    """How far the run wanders, as the root mean square about its own mean.

    This is the scale the perturbation has to stay well below. Measured from the
    run rather than declared, because the number is a property of the system and
    the initial state together, and a declared one would be right for the system
    it was measured on and wrong for the next.
    """
    here = start
    visited = [here]
    for _ in range(int(horizon / interval)):
        here = flow(here, interval)
        if not _finite_state(here):
            raise EstimateRefused(
                "the flow left the phase space while its excursion was measured"
            )
        visited.append(here)
    middle = tuple(
        statistics.fmean([point[axis] for point in visited])
        for axis in range(len(start))
    )
    return math.sqrt(
        statistics.fmean([separation(point, middle) ** 2 for point in visited])
    )


def reproducibility_floor(flow: Flow, start: State, *, interval: float) -> float:
    """The separation two runs of one state reach, which is not a separation.

    A deterministic flow returns zero here and a run that carries any
    irreproducibility returns what it carries. It is the floor below which a
    perturbation is indistinguishable from the run's own noise, and it is
    measured on the flow in hand rather than assumed to be rounding, because an
    engine reached through a runner is not obliged to be deterministic.
    """
    first = flow(start, interval)
    second = flow(start, interval)
    return separation(first, second)


def choose_separation(
    flow: Flow,
    start: State,
    *,
    interval: float,
    horizon: float,
    placement: float = SEPARATION_PLACEMENT,
) -> float:
    """The rule for the separation, applied to this flow and this state.

    The separation has a floor and a ceiling and neither is a preference. Below
    the floor the two runs differ by their own noise and the estimate measures
    that noise. Above the ceiling the perturbation is no longer small compared
    with the excursion of the run, the separation is bent by the shape of the
    attractor rather than by its instability, and the growth per interval
    saturates.

    The rule is the geometric mean of the two, which is the point that is as many
    decades above the floor as it is below the ceiling. `placement` moves it and
    is recorded when it is moved; the sensitivity of the answer to that choice is
    in `metrics/lyapunov-exponent.md` and is the reason the rule is stated rather
    than the number.
    """
    if not 0.0 < placement < 1.0:
        raise EstimateRefused(
            f"the placement is a fraction of the way from the floor to the "
            f"ceiling, strictly inside both, and is {placement!r}"
        )
    ceiling = excursion(flow, start, interval=interval, horizon=horizon)
    if not _is_finite_float(ceiling) or ceiling <= 0.0:
        raise EstimateRefused(
            "the run does not move, so there is no scale to place a perturbation "
            "against and no exponent to measure"
        )
    noise = reproducibility_floor(flow, start, interval=interval)
    floor = max(noise, ceiling * ROUNDING)
    if floor >= ceiling:
        raise EstimateRefused(
            f"the run's own noise is {noise:.3e} against an excursion of "
            f"{ceiling:.3e}, so there is no separation that is both above the "
            f"noise and below the attractor. This run cannot carry an exponent"
        )
    return math.exp(
        math.log(floor) * (1.0 - placement) + math.log(ceiling) * placement
    )


def choose_interval(
    flow: Flow,
    start: State,
    *,
    pilot: float,
    horizon: float,
    settling: float,
    displacement: float,
    blocks: int = BLOCKS,
    growth: float = GROWTH_PER_INTERVAL,
) -> float:
    """The rule for the renormalisation interval, applied to this flow.

    The interval wants the separation to grow by about one factor of e before it
    is pulled back. Much shorter and every sample is dominated by the rounding of
    a growth that barely happened; much longer and the perturbation leaves the
    linear regime inside the interval, which is the same saturation the ceiling
    on the separation exists to avoid.

    One factor of e per interval is one over the exponent, and the exponent is
    what is being measured, so the rule is a bootstrap: run a pilot at the
    caller's interval, take the exponent it reports, and set the interval from it.

    Two things bound the answer, and both of them are the horizon rather than the
    system. A pilot reporting an exponent of zero or less has no growth rate to
    invert, which is what a regular system reports, and the rule keeps the pilot
    interval there rather than dividing by a number that is not there. And an
    interval long enough to leave fewer intervals than the blocks can be cut from
    would buy a well-placed interval at the cost of the uncertainty, so it is cut
    back to the longest the horizon carries. A regular system reaches the second
    bound rather than the first: its pilot exponent is small and positive, being
    the shear that has not finished decaying, and one over it is longer than any
    horizon.
    """
    if not _is_finite_float(growth) or growth <= 0.0:
        raise EstimateRefused(f"the growth per interval is positive and is {growth!r}")
    if not _is_finite_float(horizon) or not _is_finite_float(settling):
        raise EstimateRefused("the horizon and the settling window are finite floats")
    if blocks < 2:
        raise EstimateRefused(f"the blocks are two or more and are {blocks!r}")
    longest = (horizon - settling) / (blocks * INTERVALS_PER_BLOCK_FLOOR)
    if longest <= 0.0:
        raise EstimateRefused(
            f"a horizon of {horizon} with {settling} settling cannot fill "
            f"{blocks} block(s) of {INTERVALS_PER_BLOCK_FLOOR} interval(s) at any "
            f"interval length"
        )
    first = largest_exponent(
        flow,
        start,
        displacement=displacement,
        interval=pilot,
        horizon=horizon,
        settling=settling,
        blocks=blocks,
    )
    asked = pilot if first.value <= 0.0 else growth / first.value
    return min(asked, longest)


@dataclass(frozen=True)
class Chosen:
    """What the rule picked for one system, and what it picked it from."""

    displacement: float
    interval: float
    # The interval the growth rule asked for, before the horizon's bound and the
    # snapping to the flow's grain. Kept so a reader can see which of the two
    # decided the number rather than being told the answer.
    asked: float
    grain: float


def by_the_rule(
    flow: Flow,
    start: State,
    *,
    grain: float,
    pilot: float,
    horizon: float,
    settling: float,
    blocks: int = BLOCKS,
) -> Chosen:
    """Both rules, applied in the order they depend on each other.

    The separation is chosen first, from the excursion of the run and its own
    reproducibility, neither of which needs an exponent. The interval is chosen
    second, because it needs a pilot exponent and the pilot needs a separation.
    Then the interval is snapped to the grain of the flow, because a flow asked
    for a duration it cannot advance by either refuses or rounds.
    """
    displacement = choose_separation(
        flow, start, interval=pilot, horizon=horizon
    )
    asked = choose_interval(
        flow,
        start,
        pilot=pilot,
        horizon=horizon,
        settling=settling,
        displacement=displacement,
        blocks=blocks,
    )
    return Chosen(
        displacement=displacement,
        interval=snapped(asked, grain),
        asked=asked,
        grain=grain,
    )


# The sensitivity study. Not run by the suite: it is the long form of what
# `tests/test_lyapunov.py` runs at a reduced sampling, and what it printed is
# quoted in `metrics/lyapunov-exponent.md`.


def _line(label: str, found: "Estimate", published: float) -> str:
    away = abs(found.value - published) / found.uncertainty
    return (
        f"{label:<12} {found.value:+.4f}  +/- {found.uncertainty:.4f}   "
        f"published {published:+.5f}   {away:5.2f} uncertainties away"
    )


def _each_system() -> None:
    from metrics import known_exponents as known

    print("## The rule, and what it produced")
    print("")
    for system in known.SYSTEMS:
        chosen = by_the_rule(
            system.flow,
            system.start,
            grain=system.grain,
            pilot=system.pilot_interval,
            horizon=system.study_horizon,
            settling=system.settling,
        )
        found = largest_exponent(
            system.flow,
            system.start,
            displacement=chosen.displacement,
            interval=chosen.interval,
            horizon=system.study_horizon,
            settling=system.settling,
        )
        print(system.name)
        print(
            f"    horizon {system.study_horizon:g}, separation "
            f"{chosen.displacement:.4e}, interval {chosen.interval:g} "
            f"(the growth rule asked for {chosen.asked:.4f})"
        )
        print("    " + _line("", found, system.published))
        print("")


def _sensitivity() -> None:
    from metrics import known_exponents as known

    system = known.LORENZ
    chosen = by_the_rule(
        system.flow,
        system.start,
        grain=system.grain,
        pilot=system.pilot_interval,
        horizon=system.study_horizon,
        settling=system.settling,
    )
    wander = excursion(
        system.flow,
        system.start,
        interval=system.pilot_interval,
        horizon=system.study_horizon,
    )
    noise = reproducibility_floor(
        system.flow, system.start, interval=system.pilot_interval
    )
    print("## The sensitivity, on " + system.name)
    print(f"   horizon {system.study_horizon:g}, published {system.published:+.5f}")
    print(f"   the excursion is {wander:.4f} and the run's own noise is {noise:.1e}")
    print(f"   so the rule's separation is {chosen.displacement:.4e}")
    print("")
    print("separation    exponent   uncertainty")
    for power in range(-14, 2):
        size = 10.0**power
        try:
            found = largest_exponent(
                system.flow,
                system.start,
                displacement=size,
                interval=chosen.interval,
                horizon=system.study_horizon,
                settling=system.settling,
            )
        except EstimateRefused as refused:
            print(f"{size:.1e}       refused: {str(refused)[:48]}")
            continue
        print(f"{size:.1e}       {found.value:+.4f}    {found.uncertainty:.4f}")
    print("")
    print("interval      exponent   uncertainty")
    for asked in (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0):
        size = snapped(asked, system.grain)
        try:
            found = largest_exponent(
                system.flow,
                system.start,
                displacement=chosen.displacement,
                interval=size,
                horizon=system.study_horizon,
                settling=system.settling,
            )
        except EstimateRefused as refused:
            print(f"{size:<13g} refused: {str(refused)[:48]}")
            continue
        print(f"{size:<13g} {found.value:+.4f}    {found.uncertainty:.4f}")
    print("")


def _the_regular_system_falls() -> None:
    from metrics import known_exponents as known

    system = known.PENDULUM
    print("## The regular system, as the horizon is extended")
    print("")
    print("horizon       exponent   uncertainty   log(T/settling)/(T-settling)")
    horizon = 400.0
    while horizon <= system.study_horizon:
        chosen = by_the_rule(
            system.flow,
            system.start,
            grain=system.grain,
            pilot=system.pilot_interval,
            horizon=horizon,
            settling=system.settling,
        )
        found = largest_exponent(
            system.flow,
            system.start,
            displacement=chosen.displacement,
            interval=chosen.interval,
            horizon=horizon,
            settling=system.settling,
        )
        shear = math.log(horizon / system.settling) / (horizon - system.settling)
        print(
            f"{horizon:<13g} {found.value:+.5f}   {found.uncertainty:.5f}"
            f"       {shear:.5f}"
        )
        horizon *= 4.0
    print("")


def _what_rounding_the_interval_costs() -> None:
    from metrics import known_exponents as known

    system = known.HENON
    chosen = by_the_rule(
        system.flow,
        system.start,
        grain=system.grain,
        pilot=system.pilot_interval,
        horizon=system.study_horizon,
        settling=system.settling,
    )

    def rounding(state: State, duration: float) -> State:
        """The flow a caller writes when it does not think about the grain."""
        return system.flow(state, float(round(duration)))

    print("## What a rounded interval costs, on " + system.name)
    print("")
    honest = largest_exponent(
        system.flow,
        system.start,
        displacement=chosen.displacement,
        interval=chosen.interval,
        horizon=system.study_horizon,
        settling=system.settling,
    )
    print(_line(f"snapped {chosen.interval:g}", honest, system.published))
    careless = largest_exponent(
        rounding,
        system.start,
        displacement=chosen.displacement,
        interval=chosen.asked,
        horizon=system.study_horizon,
        settling=system.settling,
    )
    print(_line(f"asked {chosen.asked:.4f}", careless, system.published))
    print(
        f"    the ratio of the two intervals is "
        f"{chosen.asked / chosen.interval:.4f} and the ratio of the two exponents "
        f"is {honest.value / careless.value:.4f}"
    )
    print("")


def _study() -> None:
    _each_system()
    _sensitivity()
    _the_regular_system_falls()
    _what_rounding_the_interval_costs()


if __name__ == "__main__":
    _study()
