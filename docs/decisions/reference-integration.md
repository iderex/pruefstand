# The reference integration

This answers issue #42. It says what the reference is, what it is not, which
configuration variable it carries, which method class it belongs to and which
property that class preserves, and it names where its correctness is established
rather than establishing it here.

It is written before the integrator exists. `reference/` holds a README and
nothing else at the commit this note landed in:

    git ls-files reference/
    reference/README.md

That ordering is the point of the issue. A note written afterwards is a
justification of whatever was built, and the two decisions below are exactly the
ones a working implementation makes silently.

## What the reference is

The answer the engines are compared against, computed in this tree, for the cases
in this suite only. For a case with a closed-form solution the closed form is the
answer and the reference is the thing checked against it. For a case with no
closed form the reference is the answer, and it is only usable at all once it
carries an error bound, which is issue #49's refusal and issue #47's computation.

## The configuration variable

The orientation is carried as a rotation matrix constrained to the rotation
group, and it is advanced by a group operation rather than by adding a
derivative to it. It is never renormalised, because there is nothing to
renormalise: an update of the form

    R_next = R * exp(hat(w) * h)

lands in the group by construction, since the exponential of a skew-symmetric
matrix is orthogonal with determinant one. The state is the pair of the
orientation and the body angular momentum, on the cotangent bundle of the
rotation group, rather than the orientation and the angular velocity. The
momentum is what the discrete conservation statements below are about, and
deriving it from a velocity each step puts the inertia tensor between the
integrator and the quantity it is meant to conserve.

The alternative, and the reason it is refused, is a unit quaternion advanced by a
derivative and divided by its norm each step. That works and is what most of the
engines under test do. The renormalisation is a projection, it moves the state by
an amount that scales with the step size and the local rotation rate, and it
moves it in a direction fixed by the method rather than by the physics. A
systematic per-step correction in a fixed direction is a secular drift, and slow
secular drift is precisely the quantity this suite exists to measure. A reference
whose own drift comes from the same mechanism as the drift it is measuring cannot
separate the two.

What the group representation costs is nine stored numbers per body instead of
four, plus one matrix exponential per step. The exponential of a 3x3
skew-symmetric matrix is a closed form, Rodrigues' formula, so the cost is a
handful of trigonometric calls and not a series.

What it does not buy is freedom from rounding. Orthogonality holds to the working
precision and not beyond it, and the working precision on this machine is:

    python -c "import sys; print(sys.float_info.mant_dig, sys.float_info.epsilon)"
    53 2.220446049250313e-16

So the residual of R transpose times R against the identity is expected to sit
near that number and to grow like the square root of the step count rather than
like the step count, because rounding is not systematic. That expectation is a
claim in this note. Measuring it, and refusing a run whose residual exceeds a
stated bound, belongs to #43 and #47.

## The class of method, for the Hamiltonian cases

The integrable canon in milestone M4, which is the torque-free asymmetric top,
the heavy symmetric top and the Kovalevskaya top, is Hamiltonian. For those cases
the reference is a variational integrator on the rotation group, of the discrete
Hamilton principle class that Moser and Veselov constructed for the free rigid
body and that Lee, Leok and McClamroch extended to the heavy top.

What that class preserves, and what it does not:

The group structure, exactly, in the sense above. This is a property of the
update and not of the case.

The symplectic form on the cotangent bundle, exactly. This is what the word
symplectic means here and it is used for these cases only.

The momentum map of every exact symmetry of the discrete Lagrangian, exactly, by
the discrete form of Noether's theorem. Which momentum that is differs per case
and is worth naming, because a reader checking the reference will check the wrong
quantity otherwise. For the torque-free top the symmetry is the whole rotation
group and the spatial angular momentum vector is preserved. For the heavy
symmetric top gravity breaks that to rotations about the vertical, so the
vertical component of the spatial angular momentum is preserved, and the body
component about the symmetry axis is preserved for the separate reason that the
symmetric top's own axis is a symmetry of its inertia tensor. For the
Kovalevskaya top only the vertical component survives as a momentum map.

Energy, not exactly. A symplectic method with a constant step size has an energy
error that oscillates within a band and does not walk, over horizons that are
exponentially long in the inverse step size. That is the standard backward error
analysis result for this class and it is cited rather than proved here. It is the
reason the class was chosen: the suite's own metric on the integrable cases is
energy drift, so the reference needs an energy error that is bounded and does not
accumulate, not one that is small on the first step.

The Kovalevskaya fourth integral, not at all as a construction. It is a quartic
first integral rather than a momentum map, so no symmetry of the discrete
Lagrangian protects it and a symplectic method does not preserve it exactly. This
matters because issue #54 makes that integral the metric for the Kovalevskaya
case. The reference's own drift in it therefore has to be bounded before an
engine's drift in it means anything, which is #47's job and is named here so that
#54 does not inherit an unstated assumption.

The order of the method is not fixed here. The base update in this class is
second order and time-reversible, and higher order is reached by symmetric
composition of it, which keeps both the symplecticity and the reversibility.
Which order the reference ships at is decided by the convergence measurement in
#46 against the cost measurement in the same issue, and asserting a number here
would be asserting the answer to that issue.

What is refused, and why it is worth writing down: a general-purpose explicit
Runge-Kutta method of any order. Those are not symplectic, their energy error
walks rather than oscillating, and the walk is smooth and slow. Used as the
reference it would produce a plausible-looking drift in every integrable case,
and the report card would be reporting the reference.

## The non-Hamiltonian cases, and the word that must not travel

Five cases in this suite are not Hamiltonian, and the property asked of the
reference there is a different property. Euler's disk is #58, the tippe top is
#60, the Chaplygin sleigh is #62, the Chaplygin sphere is #63 and the rattleback
is #68.

They split into two groups and the split is not cosmetic.

The ideal rolling cases, which are the sleigh, the sphere and the rattleback, are
nonholonomic. Their equations come from the Lagrange-d'Alembert principle, which
is not a variational principle in the sense the previous section uses, and their
flow does not preserve a symplectic form. There is no symplectic form to preserve
and asking for a symplectic method there is a category error, not a lesser
guarantee. The word symplectic must not be written about the non-Hamiltonian half
of the reference. That rule is greppable and nothing greps it today, so it is
PROSE, NOT ENFORCEMENT, and issue #92 is where a check over greppable invariants
would hold it.

What is asked instead, in order:

The constraint is satisfied exactly at every step, to working precision, rather
than being violated and projected back. The rolling constraint is what makes
these cases what they are, and a reference that drifts off it and is pulled back
has the same defect the renormalised quaternion has, one rung down.

Energy is conserved. For workless, time-independent constraints the constraint
forces do no work, so the continuous system conserves energy exactly, and the
reference is expected to conserve it with a bounded and non-accumulating error.
That expectation is weaker than the Hamiltonian one: it does not follow from a
backward error analysis of the same strength, and it is written here as a claim
that #48 measures rather than as a property the method class delivers.

The invariant measure is preserved where the continuous system has one, and is
not imposed where it does not. The Chaplygin sphere has an invariant measure. The
Chaplygin sleigh does not, and the rattleback does not. This is the direction that
is easy to get backwards. A method chosen because it preserves phase volume would
give the sleigh and the rattleback a property their own dynamics lack, and the
rattleback's reversal appears in the reduced dynamics as a passage between spin
states that a measure-preserving reduced flow does not produce. Since #67 makes
the rattleback the case that decides this project, a reference that suppressed the
mechanism would be a reference that could not see the deciding result. Stated as an
argument from the literature, not measured on this route.

The construction that fits is the discrete Lagrange-d'Alembert class, on the same
group representation as above, which enforces the discrete constraint exactly and
is not symplectic and does not claim to be. Which member of that class the
reference uses is #48.

The dissipative cases, which are Euler's disk and the tippe top, are a third
thing again. Their interesting behaviour exists because energy leaves the system,
so no conservation statement is the right ask. There the reference solves a model
somebody chose, the choice is arguable, and saying which model and what follows
from that is issue #50. This note does not choose it and the reference has no
default: a dissipative case whose file names no model is a case the reference
refuses rather than one it fills in.

## What the reference is not

A list a later change can be held against.

It is not fast. It is run once per case per resolution rather than per engine
step, and the resolution ladder in #55 is what its cost multiplies against.

It is not general. It integrates the cases in this suite, with the bodies and
constraints those cases declare, and nothing else.

It is not a contact solver. It handles the contact each case declares in the form
that case declares it, and it does not do collision detection, impact resolution,
contact set discovery, or anything with more than the contacts a case names.

It is not articulated. There are no joints, no kinematic trees and no closed
loops in it.

It is not a physics engine, and it must never become the sixth entry on the
report card. It is the thing the entries are measured against, and an artefact
that is both the ruler and a thing being measured is neither.

It is not authoritative where a closed form exists. For the two classical tops and
for Kovalevskaya the closed form is the answer, and #44 and #45 are where those
are evaluated.

It is not an answer without a bound. A reference trajectory with no error bound
attached is refused rather than published, which is #49.

## The precision it works in

Binary64 for the ordinary run, at the precision measured above, 53 bits of
significand.

The same code is expected to run at higher precision for the error bound in #47,
and that expectation shapes the code rather than following it: the integrator is
written against a numeric type rather than against the float literal, so the
higher precision run is the same algorithm and not a second implementation. A
second implementation would make the bound a comparison of two programs instead
of a comparison of two precisions.

Which higher precision route is used is #47's to decide, and one route is ruled
out here for a reason that belongs to the means rather than to the bound. NumPy's
extended float type has a platform-dependent width, so a bound computed with it
on one machine and quoted on another is a bound about neither. Not evaluated on
this route: NumPy is not installed on the machine this note was written on, so
the width was not measured here.

    python -c "import numpy"
    ModuleNotFoundError: No module named 'numpy'

The command that would settle it on a machine that has it is

    python -c "import numpy; print(numpy.finfo(numpy.longdouble).bits, numpy.finfo(numpy.longdouble).eps)"

and #47 is where the answer is recorded. The standard library carries an
arbitrary-precision decimal type with no trigonometric functions, which the
Rodrigues formula needs, so that route costs either a series for those functions
or a dependency. Both are #47's cost to weigh and neither is chosen here.

## How its correctness is established

Not here, and that is deliberate. This note asserts no correctness for the
reference, and every claim in it about what a method class preserves is a claim
about the class rather than a measurement of any code, because there is no code.

Where it is established: the closed forms for the two classical tops are #44, the
Kovalevskaya solution and what evaluating it costs are #45, the measured order of
convergence is #46, the independent error bound is #47, the non-holonomic
reference and its property are #48, the refusal of an unbounded answer is #49,
and the published trajectories with their bounds are #51.

The constructions named above are cited from the literature by author and by
construction rather than by reference. None of those references was fetched for
this note, and giving them exactly, with the disagreements between them, is #111.

## What would change this

Written so that reopening this is an event with a trigger rather than a
preference expressed later.

The group representation is reconsidered if the orthogonality residual measured in
#43 grows like the step count rather than like its square root, because that would
mean the update is not doing what the section above says it does.

The method class for the Hamiltonian cases is reconsidered if #46 finds that
reaching the accuracy #47's bound needs costs a wall-clock time an operator will
not accept, and the first thing to try then is a higher composition order rather
than a different class.

The claim that the nonholonomic energy error is bounded and non-accumulating is
reconsidered the moment #48 measures otherwise, and the honest outcome there is a
stated bound on the reference's own energy walk rather than a different word for
the same behaviour.

## What is not decided here

- The integrator itself, its interface and its step size control: #43.
- The resolution ladder every case is run at: #55.
- Which dissipation model each dissipative case solves: #50.
- The error bound and the precision it is computed in: #47.
- The case file format, including the timescale a case states it intends to
  show: #31.
- Which engines any of this is compared against: #16.

## The means

Python, the same means as the rest of the numerical core, for the reasons in
[language-and-toolchain.md](language-and-toolchain.md). Nothing in this note
forces a different one: the group representation is nine floats and a matrix
exponential, and the composition is arithmetic. The one place that decision is
under pressure is the inner loop of the integrator at the resolutions #55 needs,
which is the trigger already written into the language decision and is not
retriggered by anything here.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree refuses a reference
implementation that departs from any of it, because there is no reference
implementation to refuse and no check that reads this file. The two places a
mechanism is owed are named at the rules they belong to: the word symplectic on
the non-Hamiltonian half is #92, and the answer published without a bound is #49.
The rest of this note is a specification a reviewer holds #43 against, and a
reviewer is what stands behind it.
