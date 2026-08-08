# The non-holonomic reference, and the property asked of it

This answers issue #48 as far as a document can. It picks the member of the
method class the reference integration note fixed, says per case which physical
system the reference solves and which case-file fields carry the same statement,
separates what is measured from what is claimed, and names what cannot be settled
until the integrator exists.

Nothing is implemented here:

    git ls-files 'reference/*.py' | wc -l
    0

The integrator is #43, its error bound is #47, and the order it achieves is #46.
This note decides none of those and is written before them for the same reason
[the reference integration note](../docs/decisions/reference-integration.md) was
written before the integrator: a choice recorded afterwards is a justification of
whatever was built.

## What is already fixed, and is not fixed again here

The class of method for these cases, the configuration variable, the rule that
the constraint is satisfied exactly rather than projected back, and the rule that
the word symplectic must not be written about this half of the reference are all
settled in
[the reference integration note](../docs/decisions/reference-integration.md#the-non-hamiltonian-cases-and-the-word-that-must-not-travel).
That note ends the section by saying which member of the class the reference uses
is this issue's. So what follows is the member and the measurements, not a second
statement of the class.

## Which cases this covers, and the one that sits in two places

The ideal rolling cases are the Chaplygin sleigh, the Chaplygin sphere and the
rattleback. They roll without slipping, their constraint is workless and
time-independent, and no energy leaves them.

Euler's disk rolls too, and this issue's body counts it among the four. It is
handled here in the construction and not in the conservation statement, and
saying which half it is in matters more than the count. Its constraint is the
same rolling constraint and it is built by the same discrete construction below.
Its energy is not conserved, because
[the dissipation the reference models](dissipation-models.md#eulers-disk) puts a
resistive moment on the constrained system, so the energy measurement below does
not apply to it and the qualitative outcomes named there are what it is judged
against instead. The tippe top is not in this document at all: its contact
slides, so it is not a rolling case in the sense used here.

Leaving the disk in both groups is how a reference ends up asked for a
conservation property that its own model denies it.

## The member of the class

The midpoint discrete Lagrange-d'Alembert step, on the group representation the
reference already carries.

The discrete Lagrangian is the midpoint one, the discrete constraint is imposed
at the midpoint of the step in the same quasi-velocity the continuous constraint
is written in, and the step is therefore implicit and is solved rather than
evaluated. The literature this member comes from is J. Cortes and S. Martinez,
"Non-holonomic integrators", Nonlinearity 14, 1365, 2001, where the discrete
Lagrange-d'Alembert principle and its discrete constraint distribution are set
out, and R. McLachlan and M. Perlmutter, "Integrators for nonholonomic mechanical
systems", Journal of Nonlinear Science 16, 283, 2006, which is where the
behaviour of the members of that class is compared, including which of them
preserve a measure and which do not.

Three reasons for the midpoint member rather than the simpler explicit one, in
the order they matter here.

It is second order and symmetric, and the first-order member is not. Order is
what decides the cost of a reference at a stated accuracy, because to reach a
target error a method of order `p` needs a step going like the error to the power
`1/p`, so the step count goes like the error to the power `-1/p`:

    python -c "
    for e in (1e-8, 1e-10, 1e-12):
        print(f'{e:.0e}', f'{e**-1.0:.0e}', f'{e**-0.5:.0e}')
    "
    1e-08 1e+08 1e+04
    1e-10 1e+10 1e+05
    1e-12 1e+12 1e+06

Read as target error, then the step count at order one, then at order two, at the
same constant. The gap is five orders of magnitude at a relative error of `1e-10`,
and a reference nobody can afford to run at the accuracy its own bound needs is a
reference that gets run at a coarser one.

It is symmetric, and symmetry is the property associated with a bounded rather
than an accumulating energy error for a reversible flow. The reduced flows of
these three cases are reversible, so the argument applies to them. It is an
argument from the literature and not a theorem of the strength the Hamiltonian
half has, which is the next section's subject and is why this issue measures
rather than asserts.

It does not impose an invariant measure, and that is a requirement rather than an
absence of one. The sphere has an invariant measure and the sleigh and the
rattleback do not, and a method chosen because it preserves phase-space volume
would hand the sleigh and the rattleback a property their own dynamics lack. The
rattleback's reversal is the case this project is built around, so a construction
that suppressed the mechanism would be a reference unable to see the deciding
result.

What the choice costs, stated rather than left to be discovered. The step is
implicit, so every step is a small nonlinear solve, and the solve carries its own
tolerance. A solve stopped early is an error term nobody accounted for and it
does not fall with the step size, so it would sit under the convergence
measurement in #46 as a floor and look like the method's own order breaking down.
The rule that follows is that the solve is iterated to working precision, its
residual is recorded per step and reported as its maximum over the horizon, and a
step whose solve did not reach that is a refusal rather than a step taken with
whatever the iteration had reached.

## What is asked of it, and what is measured

Three properties, and the difference between measuring one and claiming it is the
point of this section.

The constraint residual. The discrete constraint is satisfied exactly at every
step, so what is measurable is that it holds to working precision and no worse.
Reported as the maximum over the horizon of the constraint function evaluated on
the discrete state. This is the one property the construction delivers rather
than approximates, so a residual that grows with the step count is a defect in
the implementation and not a property of the method.

Energy. For workless, time-independent constraints the constraint forces do no
work, so the sleigh, the sphere and the rattleback conserve energy exactly and
the reference is expected to conserve it with a bounded, non-accumulating error.
Expected, not guaranteed. Reported over the horizon exactly as an engine's energy
drift is, by
[the sign of a drift, and its shape](../metrics/drift-sign-and-shape.md), so the
reference is held to the measurement it is used to make. That reuse is
deliberate: a reference whose own drift is described by a different quantity than
the drift it measures cannot be compared with what it is measuring.

If that measurement shows an accumulating rate rather than a bounded swing, the
expectation in the reference integration note is what moves, and the honest
outcome is a weaker statement about the reference rather than a different
statement about the engines. The note says the same about itself.

The invariant measure, for the sphere. Reported as the relative change over the
horizon of the density-weighted phase-space volume of a small ensemble of initial
conditions started near the case's own, with the density being the one the
continuous system's measure carries. The method of measurement is named here so
that a later result cannot be read as a property of the method: an ensemble is
a measurement with its own convergence in the ensemble size, and the size used is
reported beside the number.

The negative half, that no measure is imposed on the sleigh and the rattleback,
is not measured by a second test. The sleigh's reduced flow contracts phase-space
volume as it approaches uniform straight motion, and that contraction is in its
exact solution, so a method that suppressed it fails the sleigh's comparison
against the exact solution directly. Checking the negative through the case that
has an exact answer is cheaper than an ensemble and is a stronger statement.

## Per case, what the reference solves and what the case file says

Each entry names the physical system in the same terms the case file is required
to use, so the two can be compared without either being read through the other.
The fields are the ones
[the case file format](../docs/decisions/case-file-format.md) already fixes:
`[[constraint]].kind` carries the constraint in physical terms, `[contact].model`
carries the contact and friction model, and `[contact].dissipation` is required
even when the answer is none.

The Chaplygin sleigh. A rigid body in the plane carrying a knife edge at a point
of the body, constrained so that the velocity of that point has no component
perpendicular to the edge. No friction and no dissipation anywhere else. It has
an exact solution, which is why it is the first target: the implementation is
checked against an answer before it is pointed at anything whose answer is not
known. `[contact].dissipation` names none.

The Chaplygin sphere. A sphere rolling without slipping on a horizontal plane,
whose geometric centre and centre of mass coincide and whose inertia tensor is
not isotropic. Integrable, and it has an invariant measure, which is what makes
it the second and independent check rather than a second case of the same kind.
`[contact].dissipation` names none.

The rattleback. A convex body rolling without slipping on a horizontal plane,
with the principal axes of its inertia tensor rotated relative to the geometric
axes of its contact surface. This is the case where the physics itself is
contested, between this ideal rolling model and a model in which the contact
slips and dissipates, and the reference has to say which one it solves. It solves
the ideal rolling model, with `[contact].dissipation` naming none and
`[[constraint]].kind` naming rolling without slipping at a single contact point.
A rattleback case naming a dissipative contact is a different system and is not
what this reference computes.

Euler's disk. The rolling constraint of this document plus the resistive moment
[the dissipation the reference models](dissipation-models.md#eulers-disk) fixes.
It is in the construction and out of the energy statement, as above.

The check that the case file and this document agree is the schema's, which is
#31, and it does not exist. Until it does, the agreement is a reviewer's, and no
case file exists to disagree:

    git ls-files cases/
    cases/README.md

## What is not decided here

- The integrator itself, and its error bound: #43 and #47, with the refusal of a
  reference answer carrying no bound at #49.
- The order it actually achieves, measured rather than claimed: #46.
- The dissipation the disk's reference models, which is settled next door in
  [the dissipation the reference models](dissipation-models.md), and where the
  disk's case stops as its inclination goes to zero, which is #59.
- The case files themselves, which are #62, #63 and #68, and which cannot be
  written until #13 fixes the units, frames and inertia parameterisation every
  case names.
- How the same constraint is asked of an engine, what evidence is recorded that
  it was honoured, and the slip threshold that separates a rolling run from an
  invalid one: #12, with the measurement at #64 and the mapping at #65. None of
  that reaches the reference, which is not an engine and is not configured like
  one.
- The ensemble size the measure measurement uses, which is a number that belongs
  with the implementation and its cost rather than with this choice.

## The mark

PROSE, NOT ENFORCEMENT, whole document.

Nothing in this tree reads this file. There is no integrator to carry the step,
no case file to compare against the per-case statements above, and no route that
measures a constraint residual, an energy drift or a phase-space volume. Each of
those is owed by an issue named above.

Two narrower absences, so that the absence of a red is not read as agreement. The
rule that the word symplectic must not be written about this half is greppable
and is not grepped; it is recorded in the register #92 keeps rather than here.
And nothing refuses a reference that reports a bounded energy error without
having measured one, which is this document's central distinction and has no
mechanism at all until the measurement exists.
