"""The reference integration, advanced on the rotation group rather than onto it.

Issue #43. This is the code every engine in this suite is measured against, so it
is written to be slow and obviously correct. A bug here is a bug in every
published number and it would read as a finding about an engine.

The design it implements is `docs/decisions/reference-integration.md`, which fixes
the configuration variable and the class of method before any of this existed. Two
of its sentences are the whole shape of this module:

    The orientation is carried as a rotation matrix constrained to the rotation
    group, and it is advanced by a group operation rather than by adding a
    derivative to it. It is never renormalised, because there is nothing to
    renormalise.

    The state is the pair of the orientation and the body angular momentum, on the
    cotangent bundle of the rotation group, rather than the orientation and the
    angular velocity.

## The update

The state at step `k` is the orientation `R` and the body angular momentum `Pi`.
One step solves

    a(phi) J f  -  b(phi) (f x Jd f)  =  h Pi + (h^2 / 2) M

for the rotation vector `f`, where `phi` is its length, `J` is the inertia tensor
about the point the body turns about, `Jd` is `(trace(J) / 2) I - J`, `M` is the
moment in the body frame, `h` is the step, and

    a(phi) = sin(phi) / phi        b(phi) = (1 - cos(phi)) / phi^2

Then

    R_next  = R exp(hat(f))
    Pi_next = exp(hat(f))^T (Pi + (h / 2) M) + (h / 2) M_next

The left-hand side of the solve is `F Jd - Jd F^T` written as a vector, for
`F = exp(hat(f))`. That identity is what makes the implicit equation three scalar
equations instead of nine, and it is not taken on trust: the two sides are
compared directly in `tests/test_integrator.py`, over bodies whose axes are skewed
relative to their geometry, because the identity is the one place where an
algebraic slip would be invisible in every downstream number.

`exp(hat(f))` is Rodrigues' formula, and it is orthogonal with determinant one for
every finite `f`. That is the sense in which this update lands on the group by
construction: `R_next` is a product of two rotations and nothing projects it back.
What is left is rounding, which is measured rather than assumed, by
`off_the_group` below and by the long-horizon test.

## What it conserves, and what it does not

The spatial angular momentum `R Pi` is exact for a free body, because the update
multiplies `Pi` by `F^T` and `R` by `F`. Under gravity it is not, and the
component along the vertical still is, because the moment is perpendicular to the
vertical in the body frame at both ends of the step. Both are measured in the
tests rather than argued here.

Energy is not conserved and is not meant to be. The method is in the class the
design note chose for exactly this reason: its energy error oscillates in a band
and does not walk, and the suite's own metric on the integrable cases is energy
drift, so a reference whose energy walked would be reporting itself. The band and
its absence of a trend are measured, and so is how the band shrinks with the step.

## Fixed step, and no adaptivity

There is one step per run and no route to a second one. A requested output time
that is not on that step's grid is refused rather than reached by shortening a
step or by interpolating between two, because both would produce a trajectory
whose accuracy varies along it and a metric computed over it would not be what it
appears to be.

## The precision

Binary64 throughout, which is what `float` is on every platform this runs on. The
design note anticipates the same algorithm run at a higher precision for the
error bound in #47, and that is not built here: the standard library's
arbitrary-precision type carries no trigonometric functions, so a second precision
costs either a series for them or a dependency, and the note leaves that cost to
#47 to weigh. This module therefore carries one precision and says so rather than
carrying an abstraction over a second precision that nothing exercises.

## The means

Python and the standard library, in the numerical core, where nothing imports an
adapter or an engine. The arithmetic is nine floats and a matrix exponential in a
closed form, which needs no array library, and taking one here would put the first
third-party dependency in this tree under an issue that is not about dependencies.
Frozen dataclasses with validation in `__post_init__`, so a body or a state that is
wrong is refused at construction and there is no window in which a half-built one
exists to be integrated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Vector = tuple[float, float, float]
Matrix = tuple[Vector, Vector, Vector]

# The world frame's z axis points opposite to gravity, from
# `docs/decisions/units-frames-and-inertia.md`. Every use of the vertical in this
# module is this vector, so the sign is fixed in one place.
VERTICAL: Vector = (0.0, 0.0, 1.0)

IDENTITY: Matrix = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)

# How far a matrix may sit off the rotation group before it is refused as a state.
# It is the tolerance `docs/decisions/units-frames-and-inertia.md` sets on the norm
# of a case file's orientation quaternion, used here for the matrix form of the
# same statement. Rounding in this update puts the residual near the working
# precision and grows it like the square root of the step count, so a run long
# enough to reach this is a run this module refuses to continue rather than one it
# carries on producing numbers for.
GROUP_TOLERANCE = 1e-12

# The solve stops when the residual is this small relative to the right-hand side.
# It is not the accuracy of the step, which is set by the method and the step size;
# it is how completely the implicit equation was solved, and leaving it loose would
# put an unrecorded error inside a method whose properties are the reason it was
# chosen. RELATIVE TO THE RIGHT-HAND SIDE AND NEVER TO AN ABSOLUTE FLOOR: the
# right-hand side scales with the step, so a floor turns a smaller step into a
# looser solve, which is the direction that makes a convergence study report the
# solver rather than the method.
SOLVE_TOLERANCE = 1e-15

# The fixed-point iteration contracts at a rate that goes with the step size and
# the rotation rate, so a run needing more than this has a step too large for the
# method rather than a hard problem. Refused rather than truncated.
SOLVE_ITERATIONS = 64


class IntegrationRefused(ValueError):
    """Raised instead of returning a trajectory that is wrong in any way.

    It carries every problem found rather than the first, for the reason
    `casefile.CaseRefused` and `reference.answer.ReferenceRefused` carry: a reader
    that stops at the first one turns one review into several.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(self.problems))


def _refuse(problems: list[str]) -> None:
    if problems:
        raise IntegrationRefused(sorted(set(problems)))


def _is_finite_float(value: object) -> bool:
    """A float that is a number. A bool is not a float and an integer is not one.

    An integer where a float belongs is refused rather than widened, which is the
    rule `casefile` applies to every number in a case file, for the same reason: a
    conversion nobody sees is where this project's largest class of error lives.
    """
    return isinstance(value, float) and math.isfinite(value)


def _is_vector(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and len(value) == 3
        and all(_is_finite_float(entry) for entry in value)
    )


def _is_matrix(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and len(value) == 3
        and all(_is_vector(row) for row in value)
    )


def add(left: Vector, right: Vector) -> Vector:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def subtract(left: Vector, right: Vector) -> Vector:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def scale(vector: Vector, factor: float) -> Vector:
    return (vector[0] * factor, vector[1] * factor, vector[2] * factor)


def dot(left: Vector, right: Vector) -> float:
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def cross(left: Vector, right: Vector) -> Vector:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def norm(vector: Vector) -> float:
    """The length, through `hypot` rather than the square root of `dot`.

    The two agree to rounding on every vector this integrator produces in an
    ordinary run. They part on a diverging iterate, where the sum of squares
    overflows while the components are still finite, and the difference decides
    whether a step too large for the method is refused here or raises out of a
    trigonometric call in the standard library.
    """
    return math.hypot(*vector)


def transpose(matrix: Matrix) -> Matrix:
    return (
        (matrix[0][0], matrix[1][0], matrix[2][0]),
        (matrix[0][1], matrix[1][1], matrix[2][1]),
        (matrix[0][2], matrix[1][2], matrix[2][2]),
    )


def matvec(matrix: Matrix, vector: Vector) -> Vector:
    return (
        dot(matrix[0], vector),
        dot(matrix[1], vector),
        dot(matrix[2], vector),
    )


def matmul(left: Matrix, right: Matrix) -> Matrix:
    columns = transpose(right)
    return tuple(  # type: ignore[return-value]
        tuple(dot(row, column) for column in columns) for row in left
    )


def hat(vector: Vector) -> Matrix:
    """The skew-symmetric matrix with `hat(u) v == cross(u, v)`."""
    x, y, z = vector
    return (
        (0.0, -z, y),
        (z, 0.0, -x),
        (-y, x, 0.0),
    )


def determinant(matrix: Matrix) -> float:
    (a, b, c), (d, e, f), (g, h, i) = matrix
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def inverse(matrix: Matrix) -> Matrix:
    """The inverse by the adjugate, refused where the matrix is singular."""
    scaling = determinant(matrix)
    if scaling == 0.0:
        raise IntegrationRefused(["a singular matrix has no inverse"])
    (a, b, c), (d, e, f), (g, h, i) = matrix
    adjugate: Matrix = (
        (e * i - f * h, c * h - b * i, b * f - c * e),
        (f * g - d * i, a * i - c * g, c * d - a * f),
        (d * h - e * g, b * g - a * h, a * e - b * d),
    )
    return tuple(  # type: ignore[return-value]
        tuple(entry / scaling for entry in row) for row in adjugate
    )


def _sinc(angle: float) -> float:
    """`sin(x) / x`, which is one at zero and well conditioned everywhere else."""
    return 1.0 if angle == 0.0 else math.sin(angle) / angle


def _coefficients(angle: float) -> tuple[float, float]:
    """`a(phi)` and `b(phi)` of the update above.

    `b` is written through the half-angle identity

        (1 - cos(phi)) / phi^2 == (1 / 2) (sin(phi / 2) / (phi / 2))^2

    rather than from `1 - cos(phi)` directly. The direct form subtracts two nearly
    equal numbers for a small step, which is where every digit of the coefficient
    is lost, and the step sizes this reference runs at are exactly where that
    happens: at a rotation of a milliradian per step the direct form keeps about
    six significant digits and this one keeps them all.
    """
    half = _sinc(angle * 0.5)
    return _sinc(angle), 0.5 * half * half


def exponential(rotation_vector: Vector) -> Matrix:
    """Rodrigues' formula: the rotation by `|f|` about `f`.

    Orthogonal with determinant one for every finite argument, which is the
    property the whole configuration choice rests on. There is no series and no
    iteration in it, so it introduces no error beyond rounding.
    """
    if not _is_vector(rotation_vector):
        raise IntegrationRefused(
            [f"a rotation vector is three finite floats and this is "
             f"{rotation_vector!r}"]
        )
    angle = norm(rotation_vector)
    first, second = _coefficients(angle)
    skew = hat(rotation_vector)
    squared = matmul(skew, skew)
    return tuple(  # type: ignore[return-value]
        tuple(
            IDENTITY[row][column]
            + first * skew[row][column]
            + second * squared[row][column]
            for column in range(3)
        )
        for row in range(3)
    )


def off_the_group(orientation: Matrix) -> float:
    """How far a matrix is from being a rotation, as one number.

    The larger of the worst entry of `R^T R - I` and the deviation of the
    determinant from one. Both are needed: the first alone is satisfied by a
    reflection, which is orthogonal and is not a rotation, and a reference that
    silently reflected a body would mirror a rattleback, which is the one case in
    this suite where the mirror body is a different physical answer.
    """
    product = matmul(transpose(orientation), orientation)
    worst = max(
        abs(product[row][column] - IDENTITY[row][column])
        for row in range(3)
        for column in range(3)
    )
    return max(worst, abs(determinant(orientation) - 1.0))


def shifted_to_the_pivot(inertia: Matrix, mass: float, offset: Vector) -> Matrix:
    """The inertia about a pivot, from the inertia about the centre of mass.

    `offset` is the vector from the pivot to the centre of mass, in the body frame,
    which is the direction `docs/decisions/units-frames-and-inertia.md` fixes for a
    body frame whose origin is the centre of mass. The parallel-axis theorem adds
    `mass * (|d|^2 I - d d^T)`.

    It is here rather than in the caller because a heavy top's case file states the
    tensor about the centre of mass and this integrator turns the body about the
    pivot, so the shift happens once per case and every place it is written by hand
    is a place the sign of `offset` can be wrong without any number looking odd.
    """
    problems: list[str] = []
    if not _is_matrix(inertia):
        problems.append(f"an inertia tensor is a three by three of finite floats "
                        f"and this is {inertia!r}")
    if not _is_finite_float(mass) or mass < 0.0:
        problems.append(f"a mass is a finite float that is not negative and this "
                        f"is {mass!r}")
    if not _is_vector(offset):
        problems.append(f"an offset is three finite floats and this is {offset!r}")
    _refuse(problems)
    squared = dot(offset, offset)
    return tuple(  # type: ignore[return-value]
        tuple(
            inertia[row][column]
            + mass * (squared * IDENTITY[row][column] - offset[row] * offset[column])
            for column in range(3)
        )
        for row in range(3)
    )


@dataclass(frozen=True)
class Body:
    """What the reference turns: an inertia tensor, and optionally a weight.

    `inertia` is about the point the body turns about, in the body frame, and it is
    the full tensor. Three components read as a diagonal tensor is the refusal
    `docs/decisions/units-frames-and-inertia.md` asks for by name, and it is the
    rattleback that asks for it: its principal axes are skewed relative to its
    geometry, so a diagonal tensor is a different body.

    `mass`, `gravity` and `centre_of_mass` are the heavy top. `centre_of_mass` is
    the vector from the pivot to the centre of mass in the body frame, and it is
    zero for a body turning about its own centre of mass, where the weight does no
    turning and none of the three enters the motion.
    """

    inertia: Matrix
    mass: float = 0.0
    gravity: float = 0.0
    centre_of_mass: Vector = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not _is_matrix(self.inertia):
            problems.append(
                f"an inertia tensor is a three by three of finite floats and this "
                f"is {self.inertia!r}"
            )
        else:
            for row in range(3):
                for column in range(row + 1, 3):
                    if self.inertia[row][column] != self.inertia[column][row]:
                        problems.append(
                            "an inertia tensor is symmetric, and this one is not "
                            f"at ({row}, {column})"
                        )
            # Positive definite by the leading principal minors. An inertia that
            # is not is not invertible into an angular velocity, and the failure
            # would otherwise surface as a plausible trajectory rather than as a
            # refusal.
            first = self.inertia[0][0]
            second = (
                self.inertia[0][0] * self.inertia[1][1]
                - self.inertia[0][1] * self.inertia[1][0]
            )
            third = determinant(self.inertia)
            if not (first > 0.0 and second > 0.0 and third > 0.0):
                problems.append(
                    "an inertia tensor is positive definite, and the leading "
                    f"principal minors of this one are {first!r}, {second!r} and "
                    f"{third!r}"
                )
        if not _is_finite_float(self.mass) or self.mass < 0.0:
            problems.append(
                f"a mass is a finite float that is not negative and this is "
                f"{self.mass!r}"
            )
        if not _is_finite_float(self.gravity) or self.gravity < 0.0:
            problems.append(
                f"gravity is a finite float that is not negative and this is "
                f"{self.gravity!r}, with the direction fixed by the world frame "
                f"rather than by this sign"
            )
        if not _is_vector(self.centre_of_mass):
            problems.append(
                f"a centre of mass offset is three finite floats and this is "
                f"{self.centre_of_mass!r}"
            )
        _refuse(problems)

    @property
    def weight(self) -> float:
        return self.mass * self.gravity

    @property
    def _inverse_inertia(self) -> Matrix:
        return inverse(self.inertia)

    @property
    def _dual_inertia(self) -> Matrix:
        """`(trace(J) / 2) I - J`, the tensor the discrete update is written in."""
        trace = self.inertia[0][0] + self.inertia[1][1] + self.inertia[2][2]
        return tuple(  # type: ignore[return-value]
            tuple(
                0.5 * trace * IDENTITY[row][column] - self.inertia[row][column]
                for column in range(3)
            )
            for row in range(3)
        )


@dataclass(frozen=True)
class State:
    """The orientation and the body angular momentum, at one instant.

    The momentum carries `_body` in nothing but this sentence because there is no
    world-frame momentum field here to confuse it with; `spatial_momentum` is the
    world-frame quantity and it is computed rather than stored, so the two can
    never disagree.

    The orientation is refused if it is not a rotation to `GROUP_TOLERANCE`. That
    is a fail-closed reading of the property this whole module exists for: the
    update cannot leave the group by construction, so a state that is off it is
    either a caller's matrix that was never a rotation or a run long enough for
    rounding to have accumulated past the tolerance, and neither is a run whose
    numbers mean what they appear to.
    """

    orientation: Matrix
    momentum: Vector

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not _is_matrix(self.orientation):
            problems.append(
                f"an orientation is a three by three of finite floats and this is "
                f"{self.orientation!r}"
            )
        else:
            residual = off_the_group(self.orientation)
            if residual > GROUP_TOLERANCE:
                problems.append(
                    f"an orientation is a rotation, and this one is {residual!r} "
                    f"off the group against a tolerance of {GROUP_TOLERANCE!r}"
                )
        if not _is_vector(self.momentum):
            problems.append(
                f"a body angular momentum is three finite floats and this is "
                f"{self.momentum!r}"
            )
        _refuse(problems)


@dataclass(frozen=True)
class Sample:
    """One requested time and the state the run reached at it."""

    time: float
    state: State


def angular_velocity_body(body: Body, state: State) -> Vector:
    """The body-frame angular velocity, which is derived and never stored.

    Carrying it in the state instead of the momentum would put the inertia tensor
    between the integrator and the quantity the discrete conservation statements
    are about, which is the reason the design note fixes the state as it does.
    """
    return matvec(body._inverse_inertia, state.momentum)


def spatial_momentum(state: State) -> Vector:
    """The angular momentum in the world frame, `R Pi`."""
    return matvec(state.orientation, state.momentum)


def height(body: Body, state: State) -> float:
    """The height of the centre of mass above the pivot, along the vertical."""
    return dot(VERTICAL, matvec(state.orientation, body.centre_of_mass))


def energy(body: Body, state: State) -> float:
    """Kinetic plus potential, in joules.

    Computed from the state alone, and from no quantity the update carries along.
    A conserved quantity recomputed from the state is the only kind that can catch
    the integrator; one accumulated alongside it reports its own arithmetic.
    """
    kinetic = 0.5 * dot(state.momentum, angular_velocity_body(body, state))
    return kinetic + body.weight * height(body, state)


def _moment(body: Body, orientation: Matrix) -> Vector:
    """The moment of the weight about the pivot, in the body frame.

    `Gamma` is the vertical expressed in the body frame, which is the third row of
    `R` because `R` maps body components to world ones. The moment is
    `m g (Gamma x rho)`, and the order of that cross product is the sign that
    decides whether a top precesses or falls over; it is fixed by requiring the
    energy above to be constant on the exact motion, and it is what the heavy-top
    tests measure.
    """
    if body.weight == 0.0:
        return (0.0, 0.0, 0.0)
    vertical_in_body = orientation[2]
    return scale(cross(vertical_in_body, body.centre_of_mass), body.weight)


def _solve(body: Body, target: Vector) -> Vector:
    """The rotation vector `f` of one step, from the right-hand side of the solve.

    A fixed-point iteration rather than a Newton method, because the term it moves
    to the right is second order in the step and the iteration contracts at that
    rate, so the simpler code reaches the same fixed point. Non-convergence is
    refused rather than truncated: a step large enough to break the contraction is
    a step this method should not be run at, and returning the last iterate would
    put an unrecorded error inside every number downstream of it.
    """
    inertia = body.inertia
    dual = body._dual_inertia
    inverse_inertia = body._inverse_inertia
    tolerance = SOLVE_TOLERANCE * norm(target)

    rotation_vector = matvec(inverse_inertia, target)
    for _ in range(SOLVE_ITERATIONS):
        # A diverging iterate leaves the finite range within this many iterations
        # and every quantity below it becomes a nan, which compares false against
        # the tolerance, so the loop runs out and the refusal below is what a
        # caller sees. There is no separate finiteness guard here: one would
        # change nothing that can be observed, and a guard nothing can be shown
        # to trip is a guard this repository does not ship.
        angle = norm(rotation_vector)
        first, second = _coefficients(angle)
        coupling = cross(rotation_vector, matvec(dual, rotation_vector))
        residual = subtract(
            subtract(
                scale(matvec(inertia, rotation_vector), first),
                scale(coupling, second),
            ),
            target,
        )
        if norm(residual) <= tolerance:
            return rotation_vector
        rotation_vector = matvec(
            inverse_inertia, scale(add(target, scale(coupling, second)), 1.0 / first)
        )
    raise IntegrationRefused(
        [
            f"the step's implicit equation did not converge within "
            f"{SOLVE_ITERATIONS} iterations, which means the step is too large "
            f"for this method rather than that the problem is hard"
        ]
    )


def _refuse_step(step: object) -> None:
    """One step per run, and it is a positive finite float.

    A sequence of steps is refused here rather than accepted and iterated over,
    which is where a variable step would enter this module if it entered it at all.
    There is no other route: nothing below reads a second step and nothing shortens
    the one it was given.
    """
    if not _is_finite_float(step) or step <= 0.0:  # type: ignore[arg-type]
        raise IntegrationRefused(
            [
                f"a run has one step, which is a positive finite float, and this "
                f"is {step!r}"
            ]
        )


def advance(body: Body, state: State, step: float) -> State:
    """One step of the update at the top of this module."""
    _refuse_step(step)
    moment_here = _moment(body, state.orientation)
    target = add(scale(state.momentum, step), scale(moment_here, 0.5 * step * step))
    turn = exponential(_solve(body, target))
    orientation = matmul(state.orientation, turn)
    momentum = add(
        matvec(
            transpose(turn), add(state.momentum, scale(moment_here, 0.5 * step))
        ),
        scale(_moment(body, orientation), 0.5 * step),
    )
    return State(orientation, momentum)


def trajectory(
    body: Body, initial: State, step: float, at_times: tuple[float, ...]
) -> tuple[Sample, ...]:
    """The states at the requested times, reached by stepping and nothing else.

    Every requested time is on the grid the step defines, and one that is not is
    refused with the nearest grid time named. The two ways to honour an off-grid
    request are to interpolate between two states and to shorten one step, and both
    produce a trajectory whose accuracy varies along it, which is the thing this
    issue's fourth done-when forbids.

    The grid test allows a tolerance of half a rounding of the accumulated time,
    because a requested time is written by a person as a decimal and the grid is
    reached by multiplication.
    """
    _refuse_step(step)
    if not isinstance(initial, State):
        raise IntegrationRefused([f"a run starts from a State and this is "
                                  f"{initial!r}"])
    problems: list[str] = []
    if not isinstance(at_times, tuple) or not at_times:
        problems.append(
            f"a run names at least one time to report at and this is {at_times!r}"
        )
        _refuse(problems)
    steps: list[int] = []
    previous = -1
    for time in at_times:
        if not _is_finite_float(time) or time < 0.0:
            problems.append(
                f"a requested time is a finite float that is not negative and "
                f"this is {time!r}"
            )
            continue
        count = round(time / step)
        # The tolerance scales with the count because the grid time is reached by
        # accumulating, so the comparison has to admit the rounding that
        # accumulating costs and nothing more.
        if abs(count * step - time) > 1e-9 * step * max(count, 1):
            problems.append(
                f"the requested time {time!r} is not on the grid of the step "
                f"{step!r}; the nearest grid times are {(count - 1) * step!r} and "
                f"{count * step!r}, and this run neither interpolates between two "
                f"states nor shortens a step to land on one"
            )
            continue
        if count <= previous:
            problems.append(
                f"the requested times are strictly increasing, and {time!r} is "
                f"not after the one before it"
            )
            continue
        previous = count
        steps.append(count)
    _refuse(problems)

    samples: list[Sample] = []
    state = initial
    taken = 0
    for count in steps:
        while taken < count:
            state = advance(body, state, step)
            taken += 1
        samples.append(Sample(count * step, state))
    return tuple(samples)


def every_step(
    body: Body, initial: State, step: float, count: int
) -> tuple[State, ...]:
    """The state after each of `count` steps, starting from `initial`.

    The same run as `trajectory` over a grid of every step, without building the
    time grid, because the measurements this module is judged by look at every step
    rather than at reported times.
    """
    _refuse_step(step)
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise IntegrationRefused(
            [f"a run takes a whole number of steps, at least one, and this is "
             f"{count!r}"]
        )
    states = [initial]
    for _ in range(count):
        states.append(advance(body, states[-1], step))
    return tuple(states)
