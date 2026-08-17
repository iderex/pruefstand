"""Whether the numbers in a case are a rigid body, which the schema does not ask.

Issue #32. `casefile.py` refuses a case that is not a well-formed document: the
fields are present, typed, named and covered by provenance. It says in its own
words what it leaves open, and this is that:

    a tensor of six zeros is accepted by this schema and is not a body

So this module reads a case that already passed the schema and asks the questions
a schema cannot. It is deliberately a second pass rather than more code inside the
reader. The two are different kinds of judgement, they fail for different reasons,
and a case rejected here is a case somebody wrote out correctly and got the physics
wrong in, which is a different sentence to put in front of a reader.

## What it refuses, and what refuses the rest

Two conditions live here, and they are the two the issue says matter most:

The inertia tensor is positive definite. A tensor that is not cannot be inverted
into an angular velocity, and `reference/integrator.py` refuses one at
construction, so a case carrying one has no reference answer and never will. The
suite would report that as an engine disagreeing with nothing.

The principal moments satisfy the triangle inequalities. No rigid body has a
moment exceeding the sum of the other two, and this is the one a hand-written
rattleback file trips: its principal axes are deliberately skewed relative to its
geometry, so its tensor is the one nobody can check by looking at it.

Three of the issue's conditions are already refused, by the schema rather than
here, and they are not implemented twice:

    a mass that is not strictly positive     casefile._number(..., positive=True)
    a horizon of zero or negative length     the same, on horizon.seconds
    a quaternion that is not of unit norm     casefile.UNIT_NORM

One cannot be violated at all. The convention parameterises an inertia tensor by
six components rather than by nine, so a tensor that is not symmetric cannot be
written down, and a check for it here would be a check nothing could trip. That is
a property of the parameterisation and it is recorded rather than guarded.

Three have no field in the format to read, and they are named in the issue rather
than here. What each one waits for is in the comment on #32.

## The triangle inequalities, and why the deviatoric tensor is the way in

For principal moments `A`, `B` and `C`, the three conditions are `A <= B + C` and
its two rotations. Written against the tensor rather than against a sorted triple
they are one statement: the eigenvalues of `(trace(J) / 2) I - J` are not
negative, because that tensor's eigenvalue at `A` is `(B + C - A) / 2`. The same
tensor is what `reference/integrator.py` writes its step in, under the same name,
which is not a coincidence: it is the tensor the equations of a rigid body are
natural in.

Equality is admitted and it has to be. A flat body satisfies one of the three
exactly, which is why Euler's disk is in this suite at all, so a check that
refused equality would refuse #58 before it was written.

## The tolerance, and where its number comes from

One tolerance, relative to the trace, because an inertia tensor carries units and
a bound with units in it is a bound about one choice of them. Its size is measured
rather than rounded, in `tests/test_casephysics.py`, and the measurement is of this
module's own eigenvalue routine against tensors built from eigenvalues that are
known because they were chosen first.

## The means

Python and the standard library, beside `casefile.py`, which the same issue's
sibling put at the root under the same scope. The eigenvalues of a symmetric three
by three are a closed form, so there is no iteration here and no reason to add an
array library to a tree that carries none. The three rules survive it: every
condition is refused by code, each refusal is tripped by a fixture that is a valid
case with one number changed, and the tolerance is a number the tests compute.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import casefile

# How far a physics condition may be violated before it is a violation, as a
# fraction of the trace of the tensor it is about.
#
# The floor under it is this module's own arithmetic. `principal_moments` is a
# closed form, and over ten thousand tensors built from eigenvalues chosen in
# advance its worst error is 1.9e-13 of the trace, which is 860 times the working
# precision. The measurement is
# `test_the_worst_error_over_many_tensors_is_below_the_tolerance` and it is a
# measurement rather than a bound quoted from anywhere. A tolerance below it would
# refuse a body that satisfies a condition exactly, and the flat body is exactly
# that case: it sits on the triangle inequality with nothing to spare.
#
# The ceiling over it is what a violation this small would mean. An inertia tensor
# is sourced or chosen, and neither is quoted to nine significant figures, so a
# body whose moments fail a triangle inequality by less than a part in a billion
# of its own trace failed it by less than the number was ever known to.
INERTIA_TOLERANCE = 1e-9

INERTIA_COMPONENTS = casefile.INERTIA_COMPONENTS


def _tensor(inertia: dict[str, Any]) -> tuple[tuple[float, float, float], ...]:
    """The six components as the symmetric matrix they stand for."""
    return (
        (inertia["xx"], inertia["xy"], inertia["xz"]),
        (inertia["xy"], inertia["yy"], inertia["yz"]),
        (inertia["xz"], inertia["yz"], inertia["zz"]),
    )


def principal_moments(
    tensor: tuple[tuple[float, float, float], ...]
) -> tuple[float, float, float]:
    """The eigenvalues of a symmetric three by three, largest first.

    The closed form for the roots of a symmetric matrix's characteristic
    polynomial, by way of the trigonometric solution of the depressed cubic. It is
    exact arithmetic on paper and it is not on a machine, which is what the
    tolerance above is sized against.

    A diagonal tensor is returned by reading it rather than by going through the
    trigonometry, because the trigonometry divides by a quantity that is zero
    there. That is not a shortcut: it is the branch a case with an unskewed body
    takes, and it is the branch that makes a flat body's equality exact rather
    than exact to a rounding.
    """
    (xx, xy, xz), (_, yy, yz), (_, _, zz) = tensor
    off = xy * xy + xz * xz + yz * yz
    if off == 0.0:
        return tuple(sorted((xx, yy, zz), reverse=True))  # type: ignore[return-value]
    mean = (xx + yy + zz) / 3.0
    spread = math.sqrt(
        ((xx - mean) ** 2 + (yy - mean) ** 2 + (zz - mean) ** 2 + 2.0 * off) / 6.0
    )
    a, b, c = (xx - mean) / spread, (yy - mean) / spread, (zz - mean) / spread
    d, e, f = xy / spread, xz / spread, yz / spread
    half_determinant = (
        a * (b * c - f * f) - d * (d * c - f * e) + e * (d * f - b * e)
    ) / 2.0
    # Clamped rather than trusted. The determinant of the scaled tensor is between
    # minus one and one for every symmetric matrix, and rounding puts it a few
    # units in the last place outside that at a repeated eigenvalue, where the
    # unclamped call would raise instead of returning the repeated root.
    angle = math.acos(max(-1.0, min(1.0, half_determinant))) / 3.0
    largest = mean + 2.0 * spread * math.cos(angle)
    smallest = mean + 2.0 * spread * math.cos(angle + 2.0 * math.pi / 3.0)
    return (largest, 3.0 * mean - largest - smallest, smallest)


def deviatoric_moments(
    tensor: tuple[tuple[float, float, float], ...]
) -> tuple[float, float, float]:
    """`(B + C - A) / 2` and its two rotations, largest first.

    These are the eigenvalues of `(trace(J) / 2) I - J`, and each is half the slack
    in one triangle inequality. Negative means that inequality is broken, and by
    how much in the units of the tensor.
    """
    moments = principal_moments(tensor)
    half_trace = sum(moments) / 2.0
    return tuple(  # type: ignore[return-value]
        sorted((half_trace - moment for moment in moments), reverse=True)
    )


def problems(content: dict[str, Any]) -> list[str]:
    """Every way the numbers in a case are not a rigid body.

    Takes content that has already passed `casefile.problems`. It is not defended
    against content that has not: a caller that skipped the schema is a caller that
    would get a message about a missing key from here instead of a message about a
    missing key from there, and the second one is written to be read.
    """
    found: list[str] = []
    for body in content["body"]:
        found.extend(_body_problems(body))
    return found


def _body_problems(body: dict[str, Any]) -> list[str]:
    where = f"body.{body['id']}.inertia"
    tensor = _tensor(body["inertia"])
    trace = tensor[0][0] + tensor[1][1] + tensor[2][2]
    if trace <= 0.0:
        # Reported on its own, because every bound below is a fraction of it and a
        # fraction of a number that is not positive is not a bound.
        return [
            f"{where} has a trace of {trace!r}, and the trace of an inertia tensor "
            f"is twice the sum of three quantities that are not negative, so this "
            f"is not a body before any further condition is looked at"
        ]

    bound = INERTIA_TOLERANCE * trace
    moments = principal_moments(tensor)
    if moments[2] <= bound:
        # Returned alone rather than added to. A tensor with a moment at or below
        # zero also breaks a triangle inequality, always, and reporting both would
        # put two sentences in front of a reader about one number. The triangle
        # inequality is a statement about the moments of a body, and this is the
        # sentence saying these are not the moments of one.
        return [
            f"{where} has principal moments {moments[0]!r}, {moments[1]!r} and "
            f"{moments[2]!r}, and the smallest is not above {bound!r}, so the "
            f"tensor is not positive definite; the reference cannot invert it into "
            f"an angular velocity and refuses such a body at construction"
        ]
    slack = deviatoric_moments(tensor)
    if slack[2] < -bound:
        return [
            f"{where} has principal moments {moments[0]!r}, {moments[1]!r} and "
            f"{moments[2]!r}, and the largest exceeds the sum of the other two by "
            f"{-2.0 * slack[2]!r}, against a bound of {2.0 * bound!r}; no rigid "
            f"body has moments like that, whatever geometry is written beside them"
        ]
    return []


def refuse(content: dict[str, Any]) -> None:
    """Raise unless the numbers in a validated case are a rigid body."""
    found = problems(content)
    if found:
        raise casefile.CaseRefused(found)


def loads(text: str) -> casefile.Case:
    """A case that is both a well-formed document and a rigid body, or a refusal.

    The schema runs first and its verdict is final. A file that failed it is not
    handed to the physics, because every condition here reads a number the schema
    is what guarantees the presence and the type of, and a physics message about a
    field that is absent is a worse message than the one the schema already wrote.
    """
    case = casefile.loads(text)
    refuse(case.content)
    return case


def read(path: Path) -> casefile.Case:
    """The same, from a file on disk, with the path in front of every problem."""
    case = casefile.read(path)
    found = problems(case.content)
    if found:
        raise casefile.CaseRefused([f"{path}: {problem}" for problem in found])
    return case
