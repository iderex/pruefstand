# What a wrong Lyapunov exponent means, and what it does not

This answers issue #78. The largest Lyapunov exponent is the number in this
project most likely to be misread, the misreadings are predictable, and this is
where they are headed off before there is a number for anybody to misread.

It is written for somebody about to quote a figure from the chaotic class, and it
fixes the rule the report card applies when it says two engines differ.

Nothing computes an exponent yet. `metrics/` holds a README and nothing else at
the commit this note landed in:

    git ls-files metrics/
    metrics/README.md

## What a difference in the exponent does mean

The exponent measures how fast nearby states separate. A system with a larger
exponent forgets its initial condition faster, and the rate is a property of the
system rather than of any particular trajectory through it.

So an engine whose exponent differs from the reference's is an engine whose
trajectories explore the phase space at a different rate than the true system
does. That is a statement about the statistics of everything the engine produces
for that system, not about one run. For anything that consumes simulated
trajectories in bulk, training data being the case that matters most today, it
says the distribution of generated behaviour is wrong in a way that more data
does not fix, because the extra data is drawn from the same wrong rate.

That is the whole of what it says, and it is worth having. It is also much less
than what people will read into it.

## What it does not mean

**It is not a bound on any trajectory error.** An engine can match the exponent
closely and put a particular double pendulum somewhere completely different after
ten seconds. In a chaotic system that is expected rather than a defect, which is
why the chaotic class is judged by the exponent instead of by comparing
trajectories, and why comparing trajectories there is refused in the code (#76).

**It is not comparable across systems.** The exponent has the dimension of
inverse time and its size is set by the system, so a number from the double
pendulum and a number from any other case are two different quantities that share
a name. No aggregate over cases in this class is meaningful and none is rendered.

**It is not a quality score.** Two engines with the same exponent can be
different in every other respect measured in this suite, and an engine with a
worse exponent than another may be better on every other class. There is no
ranking in this project by design, which is
[what a number from this suite does not support](what-this-is-not-for.md).

**A closer exponent is not evidence of a better solver.** The exponent is an
estimate from a finite trajectory, and an engine can land near the reference by a
cancellation of errors. The resolution study is what separates those, and it is
#11 and #55.

## Where the estimate is weak

The estimator does not return a number. It returns an interval, because the
estimate is made from a finite trajectory and depends on which trajectory it was
made from, on the length of the run, and on the separation over which the growth
was fitted. How the interval is produced is #75's, and it is the part of this
measurement that carries the uncertainty rather than an afterthought attached to
it.

The consequence governs how the whole table is read, so it is written here as the
sentence the report card carries beside the numbers rather than in a method
section a reader reaches by a link:

    Two engines whose intervals overlap are not distinguished by this
    measurement.

Not "are equivalent", and not "agree". Nothing was shown in either direction. The
sentence is negative on purpose and it does not become a positive one when the
intervals are narrow.

## The rule for when two exponents may be called different

This is the rule the report card applies. It is mechanical, so an argument about
a published claim is an argument about the rule rather than about somebody's
judgement, and the rule is here where it can be argued with.

Two exponents may be called different when all of the following hold:

- They are for the same case. Never across cases, for the units reason above.
- They are at the same rung of the resolution ladder, and the ladder covered the
  same range for both. A comparison across rungs is a comparison of two
  discretisations as well as two engines.
- They were computed by the same version of the estimator, against the same
  version of the reference and its error bound.
- Their intervals are disjoint.
- The separation between the intervals is larger than the error bound on the
  reference's own exponent, where the comparison is against the reference. Two
  engines compared with each other do not use that term, and the card says which
  comparison it made.

Where any of those fails, the card says the two are not distinguished, and that
is a statement about the measurement rather than about the engines.

The rule is deliberately one-sided. Disjoint intervals licence the word
different. Overlapping intervals licence nothing, in particular not the claim
that two engines agree.

What the rule does not do, said plainly because a mechanical rule invites being
read as more than it is:

- Disjointness is not a hypothesis test at a stated level, and it does not become
  one by being applied consistently. Whether the interval #75 produces supports a
  stronger statement is #75's to say, and if it does then this rule tightens to
  it.
- The intervals of two engines on one case are not independent. They share the
  case, the reference and the estimator, so a systematic error in any of the
  three moves both, and it can move them apart as easily as together. Two
  disjoint intervals can both be wrong.
- One case is one initial condition in one system. A difference established under
  this rule is established for that case, and this project publishes it that way
  or not at all.

## The regular-motion result, and why it is published beside the chaotic one

An estimator applied to a case whose motion is regular has to return an interval
containing zero. That is the control, and it is the evidence that the other
number is worth reading at all: an estimator with a positive bias reports chaos
everywhere, including where there is none, and it looks entirely convincing doing
it.

So the regular case's result is rendered beside the chaotic one for every engine,
in the same table rather than in an appendix. An engine whose regular-motion
interval excludes zero has not earned a reading of its chaotic number, and the
card says so instead of printing the chaotic number on its own.

Which regular case plays that role, and whether it is a separate case file or the
same system at a non-chaotic energy, is #74's, because it is a property of the
case rather than of this document.

## What is owed before this document is finished

Two of this issue's four conditions are requirements on artefacts that do not
exist, and this note cannot meet them by describing them.

The report card has to carry the interval beside every exponent, and a rendering
without one has to be refused. There is no report card. The assembly is #80, the
rendering is #81 and the provenance on every number is #82, and the refusal
belongs with whichever of those renders a cell.

The regular-motion result has to be shown beside the chaotic one. There is no
estimator to produce either, which is #75, and no case to run it on, which is
#74.

Until then the rule above is a rule nothing applies, and the sentence about
overlapping intervals is a sentence nothing prints.

## The mark

PROSE, NOT ENFORCEMENT, whole document.

No check reads this file, no check refuses a rendering that omits an interval,
and no check refuses a comparison made outside the rule above, because there is
nothing in the tree that renders or compares anything. The mechanism is owed and
#81 is where the rendering half of it lands.

One narrower absence, named so a green is not read as covering it. The rule above
constrains what the card may say and nothing constrains what a person quoting the
card says. That half has no mechanism available to it at all, in this tree or any
other, and this document plus
[what a number from this suite does not support](what-this-is-not-for.md) is the
whole of what this project does about it.
