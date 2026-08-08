# The dissipation the reference models

This answers issue #50. It names, per dissipative case, which dissipation model
the reference solves and where that model comes from, says what the model leaves
out, fixes what follows for the report card, and names the outcomes that survive
a reasonable disagreement about the model.

The last of those is the part that has to be written now rather than later. An
outcome named after the runs are made is an outcome chosen with the results in
front of it, and no reader can tell the difference afterwards.

It does not implement anything. The reference integration is #43, its class of
method and the property asked of the non-Hamiltonian half are settled in
[the reference integration note](../docs/decisions/reference-integration.md),
which names this issue as the thing it does not decide. The disk's case file is
#58 and the tippe top's is #60, and neither can be written until #13 fixes the
units, frames and inertia parameterisation every case names, for the reason
[the case file format](../docs/decisions/case-file-format.md) gives.

Nothing is implemented here at all:

    git ls-files reference/
    reference/README.md

## Why these two cases are different in kind

Everywhere else in this suite the reference computes a solution of a system
nobody disputes. A torque-free top conserves its angular momentum and its
energy, the Chaplygin sleigh has an exact solution, and a disagreement between
an engine and the reference is a statement about the engine.

Euler's disk and the tippe top are not like that. Both of them only do the
interesting thing because energy leaves the system, so the reference cannot solve
the system without first choosing how it leaves. That choice is arguable in the
literature for the disk and settled but incomplete for the top, and either way
the reference is then solving a model somebody chose rather than a system
everybody agrees on.

The consequence is a third possible explanation for a disagreement, beside the
engine being wrong and the case being mis-specified: the engine implements a
different and equally defensible dissipation. A report card that cannot separate
those three is a report card that publishes the third as the first.

## Euler's disk

### The dispute, named rather than settled

A rigid disk rolling on a plane, in the ideal non-holonomic model, keeps its
inclination and its motion persists. A real disk settles in a short and
strikingly abrupt time while its precession rate rises. What removes the energy
has been argued about, and the argument is between mechanisms rather than between
coefficients.

Three entries fix the shape of it. H. K. Moffatt, "Euler's disk and its
finite-time singularity", Nature 404, 833 to 834, 2000, attributes the
abruptness to viscous dissipation in the film of air between the disk and the
table and derives a finite-time singularity from it. G. van den Engh, P. Nelson
and J. Roach, "Numismatic gyrations", Nature 408, 540, 2000, report that removing
the air changes the final motion very little and point at the contact instead,
with a reply from Moffatt in the same place. "Does the Euler Disk slip during its
motion?", American Journal of Physics 70, 1025, 2002, is where the contact half
of that question is put directly, by asking whether the contact rolls or slides.

This note takes none of those sides, and it is worth being explicit that it
cannot: settling the question needs an experiment, and this project runs
simulations. What follows is a decision about what the reference solves, argued
on grounds that do not require the dispute to be resolved first.

### The model the reference solves

Linear rolling resistance at a rolling contact, with no air.

The resistive moment opposes the rolling motion and is proportional to the normal
force, with a coefficient carrying the dimension of length. The rolling
constraint itself is the one the non-Hamiltonian half of the reference already
enforces exactly, so the dissipation is a moment added to a constrained system
rather than a relaxation of the constraint.

The reason is not that rolling resistance won the argument. It is that this suite
exists to compare engines, and the comparison decides which model is worth
solving:

- Every engine in scope can be asked for friction at a contact. None of them can
  be asked for a viscous air film, because none of them models the air. A
  reference solving Moffatt's mechanism would differ from every engine for a
  reason that has nothing to do with any engine's solver, and the whole column
  would measure the absence of a fluid model.
- The mechanism the engines do implement is the one worth measuring them on. An
  engine given a rolling disk and a contact dissipation is being asked a question
  it is built to answer, and its answer is about its contact and constraint
  handling, which is what this suite is for.
- Rolling resistance is expressible in the case file as physics rather than as
  any engine's parameter, which is what
  [the case file format](../docs/decisions/case-file-format.md) requires of the
  `[contact]` table.

The cost is stated plainly rather than buried. This suite cannot contribute
anything to the Moffatt dispute, and a number from the disk case must never be
quoted as evidence about it. The reference's disk is a disk in a vacuum with a
lossy contact, which is one of the candidate physical pictures and is chosen here
for a reason about engines.

### What the model does not include

- The air. No fluid, no boundary layer, no film.
- Sliding at the contact. The reference solves the rolling case, and a run whose
  measured slip exceeds the threshold is an invalid run rather than a bad result,
  which is #12's rule and #64's measurement.
- Deformation of the disk or the table, and therefore any dependence of the
  resistance on the contact patch.
- Anything at or after the end of the fall. As the inclination goes to zero the
  rigid-body model stops describing a disk, and where the case stops is a
  decision this note does not take: it is #59, and it has to be taken before an
  engine takes it by default.
- Any dependence of the coefficient on the rolling speed, the inclination or the
  normal force beyond the proportionality above.

### The value a case file carries

    dissipation = "rolling-resistance-linear"

with the coefficient and its provenance in the case file, as a value covered by a
`[[provenance]]` entry like every other number. Whether the coefficient is
sourced or chosen is #58's to answer, and if it is chosen then the entry says so.

## The tippe top

### The model the reference solves

Sliding Coulomb friction at a single contact point, with a constant coefficient,
on the eccentric sphere the case describes.

This is not a choice between mechanisms in the way the disk is. The top inverts
because the friction force at a sliding contact does work, and the inversion is
an instability that dissipation creates rather than one it merely permits. N. M.
Bou-Rabee, J. E. Marsden and L. A. Romero, "Tippe top inversion as a
dissipation-induced instability", SIAM Journal on Applied Dynamical Systems,
2004, is where that is put in those terms. S. Rauch-Wojciechowski, M. Sköldstam
and T. Glad, "Mathematical analysis of the tippe top", Regular and Chaotic
Dynamics, 2005, is the analysis of the same model. The sliding Coulomb law
itself, as the thing that accounts for inversion, is older than both.

So the model is settled and it is incomplete, which is a different position from
the disk's and needs saying differently. What is disputed is not which mechanism
inverts the top but how much the terms left out change the inversion, and at
least one of them changes it: the effect of a rolling resistance model on tippe
top inversion is the subject of "The influence of the first integrals and the
rolling resistance model on tippe top inversion", Nonlinear Dynamics, 2020.

### What the model does not include

- Rolling resistance, which the 2020 entry above shows is not a small correction
  to the inversion.
- Any dependence of the friction coefficient on the sliding speed, including a
  distinct static value.
- Deformation of the peg, the sphere or the surface, and therefore any contact
  patch.
- Air.
- More than one contact at a time. The top is treated as touching at a point
  throughout, and a run in which it leaves the surface is outside what the
  reference solves.

### The value a case file carries

    dissipation = "sliding-coulomb-constant"

with the coefficient and its provenance in the case file. The coefficient is the
number most worth sourcing in this case rather than choosing, because the
inversion has a threshold in it and a chosen coefficient puts the threshold
wherever the person choosing wanted it.

## What the report card may say about these two cases

For every other class, a difference between an engine and the reference beyond
the case tolerance is a statement about the engine. For these two it is not, and
the rendering has to carry that.

The rule, which is the third thing #50 asks to be written down:

- A quantitative difference on a dissipative case is rendered with the name of
  the dissipation model the reference solved attached to it, in the cell, not in
  a methods section somebody reaches by a link.
- The sentence the card is entitled to is that the engine differs from this
  model by this much. It is not entitled to the sentence that the engine is
  wrong, and no aggregate over a dissipative case may reach a column that is read
  as an engine's score.
- Where an engine's own documentation names a different dissipation model, that
  is recorded beside the number as a substitution, which is #37's register rather
  than a note in the card.
- A qualitative outcome from the list below is rendered as a finding without the
  model dependence attached, because it does not depend on the model.

Whether the card ever uses a verdict word about a named engine is entry 6 of #1
and is unanswered, so the second item above is the floor rather than the final
shape. It gets tighter if that entry is answered with numbers only, and it does
not get looser.

## The outcomes that survive disagreement about the model

Named now, before the reference exists and before any engine has been run, so
that the list cannot be fitted to a result. Each one is a statement no reasonable
change of dissipation model makes false.

For Euler's disk:

1. The disk settles. The inclination decreases to the point where the case stops
   it, within the horizon. An engine in which the inclination is still near its
   initial value at the end of the horizon has not produced a slow settle, it has
   produced a different motion.
2. The precession rate rises as the inclination falls. An engine in which the
   precession rate falls while the disk settles has the qualitative behaviour
   backwards, and this is the outcome most worth having in the list, because a
   plausible-looking settle with a falling precession rate is exactly what a
   number alone would not show.
3. The total mechanical energy does not rise over the run. No candidate
   dissipation model adds energy, so an increase is a statement about the
   integrator or the contact handling rather than about the model.

For the tippe top:

4. A top launched clearly above the threshold the model gives inverts within the
   horizon. Clearly above is a property of the case file rather than of this
   note, and #60 has to place it far enough above the threshold that the
   qualitative statement does not turn on the threshold's exact value.
5. The same top launched with the friction coefficient set to zero does not
   invert. This is the sharper of the two and it is the reason the pair is worth
   running: an engine that inverts a frictionless tippe top has produced the
   right answer from the wrong cause, and no comparison of inversion times would
   have found it.
6. Once inverted and still spinning above the threshold, it stays inverted for
   the rest of the horizon. A spontaneous re-inversion is a finding.

What this list is worth, stated so a green over it is not read as more: an engine
can satisfy all six and still be quantitatively far from the reference, and the
disk's exponent is where that shows. The list is a floor under the qualitative
behaviour, and #58's exponent and #61's continuous metric are the measurement.

## What is not decided here

- The reference implementation and its error bound: #43 and #47.
- Where the disk's case stops as the inclination goes to zero: #59.
- The disk's exponent as its metric, and the coefficient the case carries: #58.
- The tippe top's case file, its threshold placement and its coefficient: #60,
  with the continuous metric beside the discrete outcome in #61.
- How the case's friction statement is mapped onto each engine's parameters, and
  where the mapping is recorded as a substitution: #65 and #37.
- Whether the report card uses a verdict word at all: entry 6 of #1.
- How the literature above is cited in this repository. There is no citation
  convention in this tree yet and #111 holds it, so the entries above name
  author, title, venue and year and nothing more, which is enough for a reader to
  find them and not a claim about a style.

## The mark

PROSE, NOT ENFORCEMENT, whole document.

Nothing in this tree reads this file. There is no case file to carry
`dissipation`, no reader to refuse one that names a model this document does not
list, no reference to solve either model, and no report card to render the rule
above. Each of those is owed by an issue named in the section before this one.

Two narrower absences, named so that the absence of a red is not read as
agreement. Nothing checks that the value a case file carries in `dissipation` is
one of the two strings above, which is the schema's job and is #31's. And nothing
checks that the six outcomes above are the ones the report card actually renders
as findings, which cannot exist before the card does and belongs with #66 and
#72.
