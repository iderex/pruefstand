# Units, frames and the inertia parameterisation

This answers issue #13. It fixes the unit system, the frames, the orientation
representation the case file uses and the one the result record uses, the inertia
parameterisation, and the direction of the vertical.

Its identifier is

    pruefstand-units-frames-inertia-1

and that string is the first legal value of the `convention` field
[the case file format](case-file-format.md) requires. Until this landed there was
no legal value, so no case file could be added, which
[cases/README.md](../../cases/README.md) says in place. A case naming any other
identifier is refused rather than read under a guess.

Six documents already defer to this one rather than restating any part of it, and
that is why the list below appears once:

    git grep -l '#13\b' -- '*.md'
    cases/README.md
    docs/decisions/case-file-format.md
    docs/decisions/metric-per-class.md
    docs/decisions/run-record.md
    reference/dissipation-models.md
    reference/nonholonomic-reference.md

The mistakes it prevents are
ordinary. An inertia tensor given about the centre of mass in one place and about
the contact point in another. A quaternion stored scalar-first here and
scalar-last there. An angular velocity in the body frame compared against one in
the world frame. Each produces a plausible wrong number rather than an error.

## Units

SI base and derived units, without prefixes, and no case may use another. A
length is in metres, a mass in kilograms, a time in seconds, an angle in radians,
an angular velocity in radians per second, a velocity in metres per second, an
acceleration in metres per second squared, a moment of inertia in kilogram metres
squared, a force in newtons, a torque in newton metres, an energy in joules, a
linear momentum in kilogram metres per second and an angular momentum in kilogram
metres squared per second. A friction coefficient, a restitution and a ratio are
dimensionless.

The unit is a property of the field and is never written beside the number. A
number in a case file carries no unit string, and a reader that met one would be
reading a file this convention does not cover.

What that gives up is a case written in the units of the paper it came from. The
alternative was a per-quantity unit declaration with a converter behind it, and
the converter is exactly where this class of error goes: a conversion applied
twice, or in the wrong direction, produces a number that is plausible and wrong,
which is the failure the whole issue is about. Converting once, by hand, while
writing the case, with the source cited beside it, puts the conversion where a
reviewer can see it.

`[measured].units` is a different field and keeps its own meaning. It says what
the measured quantity is in, including `dimensionless`, and it describes a metric
rather than an input.

## Frames

The world frame. Right-handed, Cartesian, inertial, and fixed for the whole run.
Its z axis points opposite to gravity. Where the case has a supporting plane, that
plane is z equals zero and the origin lies in it. Where it has none, the origin is
wherever the case's own initial placements put the bodies, which they state
exactly in any event.

The body frame, one per body, named by that body's `id`. Its origin is at that
body's centre of mass. Its axes are fixed in the body and are the axes the body's
geometry is written in, so the geometry is what declares them.

The body frame is not required to be a principal frame of the inertia tensor, and
for the rattleback it must not be. That freedom is the reason the parameterisation
below is what it is.

The contact normal. At a contact, the normal direction is the outward unit normal
of the supporting surface at the contact point, which for a horizontal plane is
the world z direction. A slip velocity is a world-frame vector whose component
along that normal is zero by construction, so a slip reported with a normal
component is a diagnostic about the engine rather than a measurement of slip.

## Which frame a quantity is in, and what it is called when it is in two

Every vector-valued quantity in a case file is in the world frame, with one
exception, and the exception is the inertia tensor, which is in the body frame.
There is no world-frame spelling of an inertia in a case file at all, so the
exception cannot be got wrong by writing the other one.

Where a quantity genuinely exists in both frames anywhere in this project, the
bare name is the world one and the body one carries `_body` in its name. So
`angular_velocity` is in the world frame and `angular_velocity_body` is the
body-frame quantity, and nothing in this project may carry a body-frame angular
velocity under the bare name. Engines report the body-frame one and some report
only that, so this is the conversion an adapter performs on every step and the
place a sign or a transpose is most likely to be wrong.

The rule is stated as a naming rule rather than as a note because a note is
checked by a reader and a name is checked by whoever reads the field.

## Orientation in a case file

The orientation of a body is a unit quaternion, written as a table with named
components rather than as an ordered list:

    orientation = { w = 1.0, x = 0.0, y = 0.0, z = 0.0 }

Naming the components removes the scalar-first against scalar-last question from
the file entirely. It survives at the adapter boundary, where an engine has its
own ordering, and that is one conversion in one place rather than a convention a
case author has to remember.

The convention in full. It is a Hamilton quaternion, so `ij = k`. It represents
the rotation that maps components in the body frame to components in the world
frame, meaning `v_world = q v_body q*` with `v` embedded as a pure quaternion, so
the equivalent matrix `R` in `v_world = R v_body` is the body-to-world rotation.
Its norm is 1 to within `1e-12`, which is the tolerance a double-precision value
written to seventeen significant digits and read back survives with room to
spare, and a case outside it is refused rather than normalised.

The sign is fixed. A quaternion and its negation are the same rotation, so a case
file requires `w` greater than zero, and where `w` is zero the first non-zero of
`x`, `y`, `z` is positive. Without that rule two case files describing one
physical state differ in their bytes, differ in the content hash #31 defines over
the parsed content, and read as a physical change in a diff.

`orientation = "identity"` is permitted as the one shorthand, and it means `w`
equals one with the rest zero. It is in the worked example in the case file
format document, so a convention refusing it would refuse the document that
introduced it.

## Orientation in a result record

The result record carries the three by three rotation matrix, row-major, nine
floats, and it is the same `R` above. It is not the quaternion.

They differ because the two are written and read by different things. A case file
is written by a person, where four numbers with named components are readable and
the sign rule is something a person can follow. A record is written and read by a
program, where a matrix has no sign ambiguity to normalise away, no ordering
question at all, and where whether the orientation stayed on the rotation group is
a statement about a matrix that #43 measures directly.

The cost is size, which is nine numbers per body per sample instead of four, and
that cost lands on #51 and #84 where trajectories are published. It is paid
knowingly and it is the reason to state it here rather than to discover it there.

## The inertia parameterisation

The `inertia` field carries the inertia tensor of the body about that body's own
centre of mass, expressed in that body's frame, as six named components:

    inertia = { xx = 1.0, yy = 2.0, zz = 3.0, xy = 0.0, xz = 0.0, yz = 0.0 }

All six are required, always, including where three of them are zero. A case
carrying three is refused rather than read as a diagonal tensor, because a reader
that filled the missing ones with zero would accept a rattleback whose skew
somebody forgot to write and would run it as a body with no chirality.

The tensor those components form is

    [ xx  xy  xz ]
    [ xy  yy  yz ]
    [ xz  yz  zz ]

and it is the inertia tensor itself, the one defined by integrating
`|r|^2 * identity - r r^T` over the body's mass. That is worth stating in this
form because of what follows from it: `xy` equals minus the integral of `x y`
over the mass, so the off-diagonal components are the negatives of the products of
inertia as several textbooks and tables define that phrase.

Getting that sign wrong is not a small error here. For a rattleback the sign of
`xy` is the chirality, so a value copied out of a table under the other definition
produces the mirror body, which reverses from the other spin sense. That is the
fourth outcome in #71, the one that reads as a finding about an engine and is a
defect in this repository, and it is reachable from one sign in one field.

Whether a given tensor is physically admissible, meaning symmetric, positive
definite and with eigenvalues satisfying the triangle inequalities, is a check
over the numbers rather than a statement about the format, and it is #32's.

## The rattleback's skew, written in this parameterisation

The demonstration #13 asks for. The numbers below illustrate the format and are
not the case's parameters, which are sourced rather than invented and are #68's.

Take a body whose principal moments are `A`, `B` and `C` and whose principal
frame is the body frame rotated by an angle `theta` about the body z axis. Then
the tensor in the body frame is `Rz(theta) diag(A, B, C) Rz(theta)^T`, which is

    xx = A cos^2 theta + B sin^2 theta
    yy = A sin^2 theta + B cos^2 theta
    zz = C
    xy = (A - B) sin theta cos theta
    xz = yz = 0

For `A = 1.0e-5`, `B = 4.0e-5`, `C = 4.5e-5` and `theta = 0.15`, and for the
mirror body at `theta = -0.15`:

    python -c "
    import math
    A, B, C = 1.0e-5, 4.0e-5, 4.5e-5
    for th in (0.15, -0.15):
        c, s = math.cos(th), math.sin(th)
        print('theta =', th, '-> xx =', A*c*c + B*s*s, 'yy =', A*s*s + B*c*c, 'zz =', C, 'xy =', (A - B)*c*s)
    "
    theta = 0.15 -> xx = 1.0669952663115909e-05 yy = 3.933004733688409e-05 zz = 4.5e-05 xy = -4.432803099920094e-06
    theta = -0.15 -> xx = 1.0669952663115909e-05 yy = 3.933004733688409e-05 zz = 4.5e-05 xy = 4.432803099920094e-06

Which is the point. The two bodies differ in the sign of `xy` and in nothing
else, and they are the two chiralities. So the case file for the rattleback is

    [[body]]
    id = "rattleback"
    mass = 0.02
    inertia = { xx = 1.0669952663115909e-05, yy = 3.933004733688409e-05, zz = 4.5e-05, xy = -4.432803099920094e-06, xz = 0.0, yz = 0.0 }

and its mirror is the same file with one sign changed.

Nothing is lost by writing the skew this way rather than as a separate rotation
beside three principal moments. The principal moments and the skew come back out:

    python -c "
    import math
    xx, yy, zz, xy = 1.0669952663115909e-05, 3.933004733688409e-05, 4.5e-05, -4.432803099920094e-06
    mid, half = (xx + yy) / 2, math.hypot((xx - yy) / 2, xy)
    lo, hi = mid - half, mid + half
    axis = math.atan2(xy, lo - yy)
    axis = (axis + math.pi / 2) % math.pi - math.pi / 2
    print('principal moments:', lo, hi, zz)
    print('skew of the smallest in-plane principal axis from body x, rad:', axis)
    "
    principal moments: 1e-05 4e-05 4.5e-05
    skew of the smallest in-plane principal axis from body x, rad: 0.1499999999999999

The alternative was three principal moments plus a rotation from the geometric
frame to the principal frame. It is more readable and it puts the rattleback's
defining quantity in two fields that can disagree with each other and with the
geometry, and a case whose stated skew contradicts its own geometry is a case
nothing in this format could refuse. Six components in one field cannot
contradict themselves.

The cost is that a body with a diagonal tensor still writes three zeros, and that
a reader who wants the principal moments computes them, as above, rather than
reading them.

## Gravity and the vertical

The world z axis points opposite to gravity. The gravitational acceleration is
`(0, 0, -g)` in world components with `g` the positive standard value

    g = 9.80665

in metres per second squared, which is the defined standard value rather than a
local one. Fixing it rather than leaving it to each engine's default is
deliberate: engines default to different values near this one, and an engine at
9.81 against a reference at 9.80665 is a modelling difference of a few parts in
ten thousand that nobody recorded and that would be attributed to the solver. An
adapter sets the engine's gravity to this value rather than accepting its default,
and where an engine will not take it, that is a substitution and #37 is where it
is recorded.

A case that needs a different value of `g` is not expressible. The case file
format carries no gravity field, so there is nowhere to write one, and this
document does not invent a field in another issue's territory. If such a case is
ever wanted, the field is #2's to add and the value becomes a second convention
identifier rather than a change to this one.

Where a case has no gravity, as a torque-free top does, the case says so through
its own fields and this section does not apply to it. There is no case in which
gravity points sideways, because the vertical is defined by gravity rather than
the other way round.

## What would change this

An engine that cannot accept a non-diagonal inertia tensor at all, which is a
real shape: some derive inertia from geometry and density and some take principal
moments plus a frame. That is not a reason to change the parameterisation, it is a
substitution to record under #37, and changing the convention to suit one engine
would put the rattleback's defining property out of reach of every engine.

A case needing a non-inertial world frame, a rotating support for instance. The
world frame's inertial claim is used by every reference computation and moving it
is not a small edit.

A case needing units this list does not carry, which would be an addition rather
than a change, and a case needing a different `g`, which is a second identifier.

In each of those the identifier moves to `-2` and the old one keeps meaning what
it means, because a published number names the convention it was produced under
and that name may not change meaning after the fact.

## What is not fixed here

The field names, the file shape and the versioning: #2, in
[the case file format](case-file-format.md). The schema, the reader and the
content hash: #31. Whether a tensor is physically admissible and whether a case is
physics rather than only a document: #32. The record's encoding and store schema:
#79, and [the run record](run-record.md) is what defers to this document for what
its numbers mean. Which quantity each class is judged by: #7.

## What #13 asks for and does not have

The first item is met. This document fixes the unit system, the frames, the
orientation representation on both sides, the inertia parameterisation and the
vertical, and no other document restates them. The six listed at the top deferred
to it before it existed, which is the same property arrived at from the other
side.

The fourth is met in the sense a document can meet it and no further. The
rattleback's skewed principal axes are expressible and are written out above, with
the numbers and the command behind them. They are an illustration of the format
rather than that case's parameters, which are sourced and are #68's.

The second and third are not met and cannot be met here.

A case using a unit or a frame this document does not name is refused by nothing.
There is no reader and no schema:

    git ls-files cases/
    cases/README.md

The refusal is #31's and the physics half of it is #32's.

Round-tripping a case through each engine's representation and back is not shown,
because there is no adapter to round-trip through:

    git ls-files adapters/
    adapters/README.md

That belongs to #33 for the interface and #34 and #35 for the two adapters, and
the tolerance it would be shown within is a number this document cannot derive
without one of them to measure.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree reads it. Every
statement above is a rule a case author follows and a reviewer checks, the
`convention` field it gives a legal value to is read by no code, and the two
done-when items above are the mechanisms it is owed. #31 and #32 are where they
land.
