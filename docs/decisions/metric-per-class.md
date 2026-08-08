# The metric each class is judged by

This answers issue #7. It fixes the class vocabulary a case file may use, assigns
a metric to each class with the reason it is the right one there and what it is
blind to, states each metric's units, sign convention and failure direction,
names for each metric the way an engine could score well on it while being wrong,
and refuses trajectory comparison as the default with a named route by which a
case may opt into it.

It does not fix units, frames or the inertia parameterisation, which is #13, and
every quantity below is expressed in whatever that issue settles. It does not
decide how uncertainty is attached to any of these values, which is #15, nor how
a metric value is rendered on the report card, which is #17. It does not decide
which dissipation model a dissipative case names, which is #50, and it does not
implement any estimator.

It is written before any metric estimator exists. At the commit this note landed
in, `metrics/` holds a README and nothing else:

    git ls-files metrics/
    metrics/README.md

## Why the metric is per class and not per suite

One metric across the whole suite would have to be the distance between an
engine's trajectory and a reference trajectory, because that is the only quantity
every case has. For most of the systems here that number is dominated by phase
error rather than by anything a reader cares about, and for the chaotic cases it
is not a measurement at all: two trajectories from the same initial condition
separate exponentially even when both integrators are excellent, so what comes
out is a function of the horizon and the Lyapunov exponent and tells you almost
nothing about the engine.

So the metric is chosen from what the class of system actually preserves or does.
That is more work per class and it is the only version of this project worth
publishing.

## The class vocabulary

The `class` field of a case file takes one of exactly five values. This is the
vocabulary [case-file-format.md](case-file-format.md) leaves to this issue.

    integrable
    nonholonomic-conservative
    dissipative
    qualitative
    chaotic

A case declares one. The metric follows from the class, and the case's
`measured` block names which instance of that class's metric it means, for
example which first integral. A case that wants a metric its class does not
admit is a case in the wrong class or a request for a sixth class, and both are
arguments to have in the open rather than a field somebody widens.

The split between `integrable` and `nonholonomic-conservative` is the one worth
justifying, because both are conservative and it would be tidier to have one
class. They are separated because the primary metric differs. An integrable top
has first integrals and no constraint to violate. A rolling body has a
constraint that an engine can violate continuously while conserving energy
perfectly, and the violation is the first thing to measure there. Folding them
together would mean the sleigh and the sphere were scored on energy drift alone,
which is the number an engine with a frozen contact gets exactly right.

## integrable

The metric is the drift, over the horizon, of a first integral the continuous
system conserves exactly. Which integral is the case's to name: the spatial
angular momentum vector and the energy for the torque-free asymmetric top, those
two plus the vertical momentum for the heavy symmetric top, and the fourth
integral for Kovalevskaya, which is #54.

It is the right metric here because it needs no reference trajectory at all. The
continuous system conserves the quantity exactly, so every part of the change in
it was introduced by the integrator, and the measurement is against a theorem
rather than against another program. The closed form gives a second and
independent metric where one exists, which is #44 and #45.

Units are dimensionless. The value is the change in the integral over the
horizon divided by its value at the initial condition, and for a vector integral
it is reported as a vector of the same shape rather than as a norm, because a
momentum that drifts along its own direction and one that drifts across it are
different faults. Reporting the norm throws that away, and #56 is where the
report card is required to show the direction.

The sign convention is that a positive component means the integral grew. The
failure direction is therefore signed and is part of the result: an energy that
walks up and an energy that walks down come from different mechanisms, and an
engine that adds energy is failing in the direction that produces instability
rather than in the direction that produces a slow stop.

Larger magnitude is worse, with no threshold implied by the number itself. What
separates agreement from disagreement is the case's tolerance, which is derived
from the reference's own bound and from the resolution ladder in #11.

What it is blind to: any error in a direction the integral does not see. A body
rotating about entirely the wrong axis with exactly the right energy and the
right angular momentum scores zero, and so does a body running the correct orbit
on the wrong schedule, because phase is not a first integral. That is why a case
whose closed form is available carries the closed-form comparison as a second
metric rather than resting on the drift.

How an engine scores well here while being wrong: by correcting the integral
directly. An integrator that rescales the state each step to restore the energy
it lost reports a drift near the working precision and has moved the state in a
direction chosen by the correction rather than by the physics. This is not a
hypothetical failure mode, it is a thing implementations do on purpose, and the
tell is that the drift is small at every step size rather than falling with the
step size. The resolution study in #11 is what exposes it, and it is the reason
a single-point result is not admissible here.

The second route to a good score while wrong is a step so coarse that the body
barely turns. There is less motion to lose the integral through, and a curve over
step size rather than one number is again what catches it.

## nonholonomic-conservative

The primary metric is the constraint residual: the slip velocity at the rolling
contact, meaning the material velocity of the contact point of the body relative
to the surface, which the ideal rolling constraint holds at exactly zero.

Beside it, and required rather than optional, are the energy drift and, for a
system that has one, the drift of the invariant measure. The Chaplygin sphere has
an invariant measure. The Chaplygin sleigh does not, and the rattleback does not,
so asking for its preservation there would be asking for a property the dynamics
lacks, which is the direction [reference-integration.md](reference-integration.md)
warns about.

Units for the slip are metres per second. It is a vector in the contact plane and
is reported as a vector, with the case naming the frame it is expressed in, so
that a slip along the direction of travel and a slip across it are distinguished.
Its magnitude has no sign convention because it has none, and the direction
carries what a sign would. Reported over the horizon as both the maximum and the
time integral, because a brief excursion and a steady creep are different faults
and a single summary hides one of them.

Units for the energy drift and the measure drift are dimensionless, relative,
with the same sign convention as the integrable class.

The failure direction for the slip is the direction of the slip itself. For the
energy the sign says whether the contact model is adding energy, which for a
constraint that should do no work is the more serious sign.

Larger is worse in all three.

What it is blind to: zero slip is necessary and nowhere near sufficient. An
engine can hold the contact point exactly still and integrate the reduced
dynamics badly, and the sleigh's asymptotic approach to uniform straight-line
motion is exactly the thing that would then be wrong while the primary metric
reads zero. That is why the case's own quantitative comparison against the exact
answer, which is #62 for the sleigh and #63 for the sphere, is carried beside the
residual rather than replaced by it.

How an engine scores well here while being wrong: by making the contact stiff and
the friction enormous. Slip goes to zero, the constraint looks honoured, and the
trajectory is dominated by a contact model nobody asked for. The extreme version
is an engine that welds the contact point, which reports exactly zero slip and no
rolling at all. The required energy drift beside the residual is what refuses
this, and #64 and #65 are where the slip is measured across engines and where
each engine's friction statement is mapped onto the case.

## dissipative

The metric is the exponent of the known asymptotic law, and the value scored is
the difference between the exponent measured from the engine's trajectory and the
exponent the case's stated dissipation model predicts.

Euler's disk is the case this class exists for, and it is #58. The measured
quantity there is the growth of the precession rate as the disk settles, which
under a stated dissipation model follows a power law in the time remaining before
the motion stops. Which model, and therefore which exponent, is #50's and is not
assumed here. A dissipative case that names no model is refused, for the same
reason the reference refuses one.

Units are dimensionless, since an exponent is. The value scored is the signed
difference between the measured exponent and the model's, so its sign says
whether the engine's approach is faster or slower than the model, and larger
magnitude is worse.

The failure direction matters more here than anywhere else in the suite, because
the two signs mean different things about the contact model. An engine whose
exponent is too steep is losing energy faster than the model, which points at
numerical damping. One whose exponent is too shallow is losing it more slowly,
which points at a contact that is not dissipating what the model says it should.

What it is blind to: the prefactor and the finishing time. An engine can produce
exactly the right power law on a timescale that is wrong by a factor of three and
score perfectly, so the case carries the finishing time as a second reported
quantity rather than folding it into the exponent.

It is also blind to the mechanism. The exponent is a property of a fit, and more
than one physical mechanism produces a similar one over a finite window, which is
why the exponent is reported with the window it was fitted over and the residual
of the fit, and why a fit whose residual exceeds the case's stated bound is not a
measurement of the exponent at all.

How an engine scores well here while being wrong: by the fitting window. A wide
window over a noisy signal fits a power law to almost anything, and a window
chosen after seeing the data fits the one you were hoping for. The window is
therefore fixed by the case rather than by whoever ran it, and it is stated in
the case file rather than in the estimator, so that the same window is applied to
every engine and to the reference.

Near the singularity the whole class of behaviour depends on what the engine does
when the contact geometry degenerates, and what a case is allowed to declare
there is #59.

## qualitative

The metric is a discrete outcome from a vocabulary the case declares, together
with the direction and the count where the outcome is a repeatable event.

The tippe top either inverts or does not, which is #60, and the rattleback
reverses some number of times in some directions, which is #69. The vocabulary is
the case's because the possible outcomes differ per case, and it is closed, with
one member always present for the run that produced no outcome because the engine
lost the contact or the state left the region the case is about.

There are no units. What is ordered is not the outcome but its agreement with the
reference outcome, so the scored value is the difference between the engine's
count and the reference's count, whose sign says whether the engine reversed too
often or too rarely, and for a binary outcome the scored value is agreement or
disagreement with no order between them at all.

The failure direction for the rattleback is the direction of the reversal, and it
is the part of this metric that decides the most. An engine that reverses in the
wrong sense has got the asymmetry backwards rather than got the magnitude wrong,
and #71 is where that is separated out.

What it is blind to: everything quantitative. An engine that inverts the tippe
top at four times the right time scores exactly what an engine that inverts it on
time scores. A continuous metric beside the discrete outcome is #61, and it
exists because this blindness is not acceptable on its own.

How an engine scores well here while being wrong: by chance. A binary outcome
from one run carries one bit and an engine with no relevant physics gets it right
half the time, so a single run is not evidence and the case states how many runs,
over which perturbations of the initial condition, an outcome is asserted from.
The second route is reversing for the wrong reason, where the reversal is driven
by solver noise rather than by the inertial asymmetry the case is about, and what
separates those is that the physical mechanism has a direction and noise does
not. Separating a failed reversal from a case the engine was never properly given
is #72.

## chaotic

The metric is the largest Lyapunov exponent, estimated from the engine's own
trajectory, and the value scored is its relative difference from the reference
exponent.

It is the right metric because it is the thing that is comparable. The exponent
is an invariant of the dynamics rather than a property of one trajectory, so it
survives the exponential separation that makes trajectory comparison meaningless
here, and it is the quantity that says whether the engine has the right dynamics
at all. The double pendulum is #74 and the estimator with its uncertainty is #75.

Units of the exponent are inverse seconds. The scored value is dimensionless,
being a relative difference, and its sign says whether the engine's dynamics
diverges faster or slower than the reference's. Larger magnitude is worse, and a
larger exponent on its own is not worse: it is more chaotic, and worse is only
the distance from the reference.

The failure direction is informative in both signs. An exponent that is too large
points at an engine generating divergence numerically, from solver noise or from
a contact that fires inconsistently. One that is too small points at damping,
numerical or modelled, which flattens the dynamics.

What it is blind to: the specific trajectory, by construction and on purpose, and
also the structure of the attractor. Two systems can share a largest exponent and
differ in everything else about their phase space, which is why the Poincare
section is carried as a second and independent view in #77.

How an engine scores well here while being wrong: by producing the right amount
of divergence from the wrong source. Numerical noise generates a positive
exponent, and a finite-time estimator applied without care cannot distinguish
that from dynamical divergence. What distinguishes them is the scaling of the
separation with the size of the initial perturbation, so the estimator records
that scaling rather than a single number, and an estimate whose separation does
not scale with the perturbation is refused rather than reported. That requirement
belongs to #75 and is stated here as the thing #75 has to deliver.

The second route is the horizon. An exponent estimated over too short a window is
dominated by the transient before the trajectory reaches the attractor, and the
window is fixed by the case rather than chosen per engine, for the same reason
the dissipative fitting window is.

## Trajectory comparison

Refused by default, in every class.

A case may ask for it, and the route is a block in the case file rather than a
setting anywhere else, because the horizon over which agreement is expected is a
statement about the physics of that case and not about a run:

    [measured.trajectory]
    horizon_seconds = <number>
    why = """<the reason agreement is expected over that horizon>"""

Three properties of that block are the whole of the mechanism. The horizon is
required, so there is no way to ask for trajectory comparison over the case's own
horizon by omission. The horizon has to be shorter than the case's horizon, so
the request is visibly a request about an early window rather than about the
whole run. And the `why` is required and is prose, so the request carries an
argument a reviewer can refuse.

For a case whose class is `chaotic` the block is refused even when it is present,
and the refusal is not overridable. There is no horizon over which trajectory
agreement is a statement about the engine there, so a case declaring one is
asking for a number that would be quoted and would mean nothing. That refusal is
#76.

Nothing refuses any of this today, and it is worth saying plainly rather than
letting the paragraph above be read as a mechanism. There is no case reader, no
metric dispatch and no runner in this tree, so at this commit trajectory
comparison is refused by a reviewer, which is not a mechanism. The reader and the
schema that hold the block's shape are #31, the dispatch that selects a metric
from a class and refuses one the class does not admit is #39, and the
unoverridable chaotic refusal is #76. That is the same state
[case-file-format.md](case-file-format.md) records for the field list it fixes,
for the same reason, at the same point in the plan.

## The means

Markdown in `docs/decisions/`, beside the decisions it is read with. The artefact
is an argument about what may be measured, held against the estimators when they
are written, and no part of it is a program. Every claim above about this tree is
a command, every claim about what a class of system preserves is written as a
claim about the class, and each mechanism the document asks for is named at the
issue that owes it rather than asserted here.

## What is not decided here

- Units, frames and the inertia parameterisation every quantity above is
  expressed in: #13.
- How each metric's uncertainty is stated, and what refuses a bare number: #15.
- The resolution ladder each metric is evaluated over, and what refuses a
  single-point result: #11.
- Which dissipation model a dissipative case names, and therefore which exponent
  its metric compares against: #50.
- The estimators themselves, one issue per class: #54, #58, #61, #62, #63, #64,
  #69, #75, #77.
- How a metric value, an outcome and a refusal are each rendered: #17.
- Whether a class cell also carries a verdict word about a named engine, which
  is entry 6 of #1 and is not assumed anywhere above.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree refuses a case
declaring a class outside the vocabulary, a case asking for a metric its class
does not admit, a trajectory comparison without a horizon, or a chaotic case
asking for one at all. The mechanisms are owed and are named at #31, #39 and #76
above.

Two narrower absences, so a later green is not read as covering them. Nothing
checks that the class vocabulary here and the schema's own enumeration agree once
both exist, which is the drift this document names against itself and whose
repair is that the schema is the authority. And nothing refuses an estimator that
reports a magnitude where this document requires a signed value or a vector,
which is the requirement most likely to be lost in the writing of the estimators,
because a norm is the easier thing to return.
