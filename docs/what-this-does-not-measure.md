# What this suite does not measure

This answers issue #85. It is the limits of the measurement.
[What this project is not for](what-this-is-not-for.md) is the limits of the
conclusion, and that document names this one as the separate statement rather
than folding the two together. A reader weighing a number needs both and they
fail differently: one is about what a number cannot support, this one is about
what was never put on the scale.

Everything here is a small number of rigid bodies with clean constraints, chosen
because the answer is known. That is a long way from what these engines are mostly
used for, and being explicit about the distance is what makes the findings usable.

## What is out of scope

Articulated systems with many bodies and many joints. The solver's behaviour there
is dominated by how a chain of constraints is assembled and factorised, which is a
different concern from how one body's rotation is integrated, and nothing here
exercises it.

Soft bodies, cloth, fluids and deformable contact. Every body in this suite is
rigid by assumption, and the assumption is in the reference as much as in the
cases, so there is nothing here to compare a deformable result against.

Speed, throughput and simulations per second. This is what the existing benchmarks
measure and this project does not, and the cost of a run is recorded only so that
an engine accurate at an unusable step is reported as such rather than as
accurate.

Many simultaneous contacts. Each case here has zero or one contact point, so
nothing measures how an engine behaves when a solve has to distribute forces over
many of them at once, which is where most of these engines spend their time in
real use.

Impacts and restitution. The canon here is smooth sustained motion, and a collision
model is not exercised by any of it.

Stability under the aggressive settings robotics work actually uses. Configurations
here are derived by a stated procedure aimed at getting the physics right, which is
not the same as the large steps and stiff contacts a controller runs against.

Behaviour under control inputs and actuation. Every case is a passive system left
to itself, and an actuated joint is a torque source this suite never turns on.

Gradients, differentiability and anything about training through a simulator. A
simulator can be differentiable and wrong, or correct and opaque, and nothing here
tells the two apart.

Anything about an engine that is not its numerical behaviour. Its API, its
documentation, its build, its platform coverage and its licence terms are all real
reasons to choose or reject one, and none of them is measured here.

## What a poor result does legitimately imply

The honest inversion, stated as specifically as the list above, because a document
that only says no gives a reader nothing to do with it.

A poor result here means that this engine's treatment of rotation, of constraints
or of contact departs from the physics in a measurable way, on a case where the
right answer is known and the departure cannot be argued to be a modelling choice
about something harder. Behaviour built on top of that treatment inherits the
departure, whether or not it is visible in the thing being built.

The per-class structure is what makes the implication specific. A drift in a
conserved quantity on the integrable cases is a statement about how rotation is
advanced. A slip beyond the rolling threshold is a statement about the contact
model rather than about the solver's accuracy. A rattleback that does not reverse
is a statement about the non-holonomic constraint. Those are different findings
and the report card keeps them apart for that reason.

And the honest limit on the implication. An engine whose error falls as the step
is refined is integrating the right equations imprecisely, which computer time
fixes; an engine whose error stops falling is integrating something else, which no
step size fixes. What separates those is `metrics/error_source.py`, and the limit
has moved rather than gone: the estimator exists and has never been given a curve
from an engine, because the resolution study that produces one is #55 and the
runner under it is #39. So a poor number here still does not say which of the two
it is, and the reason is now that nothing has run the separation rather than that
nothing could.

Two things it will not say even then, and they are the reason that estimator
carries a third verdict rather than two. A step range too narrow to decide returns
undecided, which is a statement about the study and not about the engine. And what
it attributes to the engine is what is left after the run's own rounding and the
reference's bound are taken out, both of which are declared by whoever ran the
study, so the verdict is only as good as that declaration.

## What is not met

Two of this issue's four done-when items, stated rather than softened.

The document has to be linked from the report card itself, so a reader meets it
with the numbers rather than after them. There is no report card: the assembly is
#80 and the rendering is #81, and neither exists. Being linked from `docs/` is not
the same requirement and is not a substitute for it.

A case added later that reaches outside this scope has to force this document to
change in the same pull request, enforced by a check over the case directory.
There is no such check, and there is nothing yet for it to read:

    git ls-files cases/
    cases/README.md

The shape it would take is a pattern over the tree of the kind
`tests/test_greppable_invariants.py` already carries for a subject that does not
exist yet, which puts it in #92's register rather than in a document under this
issue's declared scope of `docs/`. It is owed and it is named here and in #85.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing reads it. A case reaching outside
the scope above is refused by nobody, the link this document owes has no page to
be on, and both are recorded above rather than left to be discovered by whoever
adds the first case that does not belong.
