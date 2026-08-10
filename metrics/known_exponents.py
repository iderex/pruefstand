"""The systems whose largest exponent somebody else already published.

Issue #75. An estimator checked against itself proves it is consistent. What says
it returns the right number is a system where the right number was computed by
other people, by other methods, and written down before this repository existed.

Three systems, and each is here for a different reason.

`PENDULUM` is regular. It is a mechanical system of the kind this suite is about,
its motion is periodic, and its largest exponent is zero for the same reason every
integrable system's is: neighbouring orbits separate because their periods differ,
which is linear in time and not exponential. An estimator that reports a positive
exponent for it reports chaos in a system that has none, and that is the failure
that would matter most here, because the report card would be saying an engine
found chaos where the physics has none.

`LORENZ` is the standard chaotic flow and the one whose exponent is quoted most
often. It is a flow rather than a map, so it exercises the same shape as a rigid
body: a state advanced through continuous time by an integrator with a step.

`HENON` is a map, so its exponent is per iteration rather than per unit time, and
it is here because it is cheap and because it is a second independent number. Two
published values agreeing with this estimator is a much stronger statement than
one, and the two came from different authors and different methods.

None of these is a case in this suite. They are the estimator's own calibration,
they never enter a report card, and the numbers below are not tolerances: they are
what the literature says, and the spread each is compared within is stated by
whoever compares, in `tests/test_lyapunov.py`.

## The means

The two flows are advanced by classical fourth-order Runge-Kutta at a fixed step.
That is not the method this project's reference integration uses, and it is not
supposed to be: the systems here are not rigid bodies, they have no rotation group
to stay on, and what is asked of the integrator is only that it be accurate enough
that the exponent it produces is the system's rather than the integrator's. The
step is stated per system and the sensitivity of the exponent to it is in
`metrics/lyapunov-exponent.md`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from metrics.lyapunov import EstimateRefused, Flow, State

# The derivative of a state, in the same coordinates.
Derivative = Callable[[State], tuple[float, ...]]


def runge_kutta(derivative: Derivative, state: State, step: float) -> State:
    """One classical fourth-order Runge-Kutta step."""
    first = derivative(state)
    second = derivative(
        tuple(value + step * rate / 2.0 for value, rate in zip(state, first))
    )
    third = derivative(
        tuple(value + step * rate / 2.0 for value, rate in zip(state, second))
    )
    fourth = derivative(
        tuple(value + step * rate for value, rate in zip(state, third))
    )
    return tuple(
        value + step * (a + 2.0 * b + 2.0 * c + d) / 6.0
        for value, a, b, c, d in zip(state, first, second, third, fourth)
    )


def stepped_flow(derivative: Derivative, step: float) -> Flow:
    """A flow that advances by exactly the duration asked, at no more than `step`.

    The duration is cut into equal substeps, as few as reach `step` or finer. So
    the flow never advances by a different duration from the one it was asked
    for, whatever interval the rule picks, and the substep it actually takes is at
    most the one this system declares.

    A flow that rounded the duration to whole steps would be the shape `snapped`
    in `metrics/lyapunov.py` exists to stop: it advances by one duration and the
    exponent is divided by another, which is a wrong number that looks entirely
    ordinary.
    """

    def flow(state: State, duration: float) -> State:
        taken = max(1, math.ceil(duration / step))
        substep = duration / taken
        for _ in range(taken):
            state = runge_kutta(derivative, state, substep)
        return state

    return flow


@dataclass(frozen=True)
class KnownSystem:
    """A system, a state to start it from, and what its exponent is known to be."""

    name: str
    # Where the published number comes from, named so a reader can go and check
    # it rather than take this file's word for it.
    source: str
    published: float
    flow: Flow
    start: State
    # The smallest duration this flow advances by. A renormalisation interval is
    # snapped to a whole number of these before it is used, because a flow asked
    # for a duration between two of its own units either refuses or rounds, and
    # the rounding is the silent one.
    grain: float
    # The interval a pilot run uses before the rule has chosen one.
    pilot_interval: float
    # How much of the run is discarded while the perturbation turns into the
    # direction the system actually separates along.
    settling: float
    # The horizon the long study in `metrics/lyapunov.py` runs at, and the
    # shorter one the suite runs at.
    study_horizon: float
    suite_horizon: float


# Gravity over length, taken as one, so time is in units of the small-amplitude
# period over two pi. The amplitude is a radian, which is far enough from both
# the small-angle limit and the separatrix that the period depends on it and
# neighbouring orbits shear apart.
PENDULUM_START: State = (1.0, 0.0)
PENDULUM_STEP = 0.005


def _pendulum(state: State) -> tuple[float, ...]:
    from math import sin

    angle, rate = state
    return (rate, -sin(angle))


PENDULUM = KnownSystem(
    name="plane pendulum, amplitude one radian",
    source=(
        "integrable, so every Lyapunov exponent is zero. Not a measured number "
        "and not a number anybody published: it follows from the motion being "
        "periodic, and it is the one entry here whose value is known before any "
        "computation"
    ),
    published=0.0,
    flow=stepped_flow(_pendulum, PENDULUM_STEP),
    start=PENDULUM_START,
    grain=PENDULUM_STEP,
    pilot_interval=0.5,
    settling=20.0,
    study_horizon=6400.0,
    suite_horizon=400.0,
)


# The parameters Lorenz used and everybody since has quoted.
LORENZ_SIGMA = 10.0
LORENZ_RHO = 28.0
LORENZ_BETA = 8.0 / 3.0
LORENZ_START: State = (1.0, 1.0, 1.0)
LORENZ_STEP = 0.005


def _lorenz(state: State) -> tuple[float, ...]:
    x, y, z = state
    return (
        LORENZ_SIGMA * (y - x),
        x * (LORENZ_RHO - z) - y,
        x * y - LORENZ_BETA * z,
    )


LORENZ = KnownSystem(
    name="Lorenz, sigma 10, rho 28, beta 8/3",
    source=(
        "Wolf, Swift, Swinney and Vastano, Determining Lyapunov exponents from a "
        "time series, Physica D 16 (1985), which reports 0.9056 for this system "
        "at these parameters"
    ),
    published=0.9056,
    flow=stepped_flow(_lorenz, LORENZ_STEP),
    start=LORENZ_START,
    grain=LORENZ_STEP,
    pilot_interval=0.5,
    settling=20.0,
    study_horizon=1000.0,
    suite_horizon=400.0,
)


# The parameters Henon used, and the state below is inside the basin of the
# attractor rather than on the divergent side of it.
HENON_A = 1.4
HENON_B = 0.3
HENON_START: State = (0.1, 0.3)


def _henon_flow(state: State, duration: float) -> State:
    """The map, iterated. A duration here is a count of iterations.

    A duration that is not a whole number of iterations is refused rather than
    rounded. There is nothing between two iterations of a map, so rounding would
    advance by one duration and report growth per another, and the caller snaps
    the interval with `snapped` before it gets here.
    """
    taken = round(duration)
    if taken < 1 or float(taken) != duration:
        raise EstimateRefused(
            f"a map advances in whole iterations and was asked for {duration!r}"
        )
    x, y = state
    for _ in range(taken):
        x, y = 1.0 - HENON_A * x * x + y, HENON_B * x
    return (x, y)


HENON = KnownSystem(
    name="Henon map, a 1.4, b 0.3",
    source=(
        "the value quoted for the Henon attractor at these parameters is 0.41922 "
        "per iteration, and it is the number reached by the tangent-map "
        "construction this estimator deliberately does not use"
    ),
    published=0.41922,
    flow=_henon_flow,
    start=HENON_START,
    grain=1.0,
    pilot_interval=5.0,
    settling=200.0,
    study_horizon=40000.0,
    suite_horizon=40000.0,
)

SYSTEMS = (PENDULUM, LORENZ, HENON)
