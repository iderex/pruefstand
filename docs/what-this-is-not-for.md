# What this project is not for

This answers issue #108. [NOTICE.md](../NOTICE.md) is the generic notice and it
says what any project says. This is the specific one, because the ways a report
card about other people's software gets misused are particular to what a report
card is.

It is written before there is a report card to misuse. That is on purpose: a
document like this written after the first number is published is a document
written in response to how somebody already used it.

## This is not a procurement scorecard

A poor result on one class says something about that class. It says nothing about
work that has nothing to do with it. An engine that drifts badly on a torque-free
top may be the right engine for a walking robot, because a contact-rich control
problem is not a conservation problem and the qualities that make an engine good
at one are not the qualities that make it good at the other.

The cases here were chosen because their answers are known, not because they are
representative of what anybody simulates for a living. That is what makes them
useful as a test and what disqualifies them as a shortlist.

## The numbers certify nothing

This project certifies nothing and is not in a position to. There is no
assessment body behind it, no scheme it operates under, and no statement here is
a conformity statement. A number produced by this suite is a measurement made by
a method that is written down, which is a different and smaller thing.

## There is no ranking and no overall winner

Refusing a single score is a design constraint rather than an omission, and it is
argued in #17. A number that ranks engines across classes would be an average
over quantities with different units, different tolerances and different meanings,
and the ranking would then be a property of the weighting rather than of the
engines.

The report card is per class, per case and per engine, and the assembly refuses an
aggregate across classes. Somebody who wants one line will have to compute it
themselves, and they should have to, because the choice of weighting is the whole
argument and it belongs to whoever is making the decision.

## A result is about a version at a configuration

Every number this project publishes is about a specific version of an engine, run
at a specific configuration, on a specific case at a specific version, against a
reference with a stated bound. Quoting one without those is quoting something this
project did not say.

That is not a formality. Engines change their contact solvers between releases,
and a configuration that was derived by this project's procedure is not the
configuration an engine ships with. A number lifted out of its qualifiers is a
number about a thing that may no longer exist.

## This does not replace validating your own system

The most useful thing anyone can do with a simulation they depend on is check it
against the system they actually care about. This suite cannot do that for
anybody. It checks engines against classical mechanics problems with known
answers, which is a floor: an engine that fails these is unlikely to do better on
something harder, and an engine that passes them has told you nothing about your
geometry, your materials, your controller or your timestep.

## What the numbers are good for

The positive half, stated as specifically as the negative half, because a document
that only says no is a document nobody reads.

Choosing between engines for a system that resembles one of these cases. If the
thing being simulated is a spinning body whose interesting behaviour is a slow
drift or a reversal, then an engine's result on the corresponding case here is
close to direct evidence, and that is the narrow claim this suite makes well.

Knowing what to check when a simulation behaves oddly. A drift with a direction, a
constraint that is quietly being satisfied by friction rather than by rolling, an
energy error that walks rather than oscillating: these are named failure shapes
with cases attached, and recognising one in your own run is faster than
rediscovering it.

Giving an engine's maintainers a reproducible failing case. This is the outcome
worth the most. A case file, a configuration, a reference answer with a bound and
a run record is a bug report somebody can act on, and every case here is intended
to be usable that way by the people who maintain the engine it was run against.

Reusing the case definitions and the reference trajectories. They are published as
data so that somebody who never runs this code can cite them, check them or build
on them.

## What is not covered here

What this suite does not measure, as opposed to what it is not for, is a separate
statement and it is #85. The two are different questions: one is about the limits
of the measurement, this one is about the limits of the conclusion.

## Where this is linked from

The readme links here. The report card is required to link here as well, and it
does not, because there is no report card: the assembly is #80 and the rendering
is #81. That half of this issue's done-when is not met and is not softened
anywhere in this document.

The related requirement, that every number on the report card carries its version
and configuration qualifier so that quoting one without them takes deliberate
effort, is also unmet for the same reason. It is a requirement on the rendering,
it is recorded in #108, and #81 and #82 are where it lands.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing refuses a use of this project's
numbers, and nothing could: the misuse happens in somebody else's document. The
one half of this that a machine can reach is the qualifier on a rendered number,
which is #82, and it is unbuilt.
