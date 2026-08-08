# How an uncertainty is reported, and what refuses a bare number

This answers issue #15. It names the terms an uncertainty on a metric value is
made of, says which are bounds and which are statistical, fixes that they are
reported separately rather than combined, names the fields that carry them,
states the rule for when two engines' numbers may be reported as different, and
names where a metric written without its uncertainty is refused.

It does not decide which metric a class is judged by, which is
[metric-per-class.md](metric-per-class.md), nor how a cell is rendered, which is
[report-card-shape.md](report-card-shape.md). It does not decide the estimators
whose own uncertainty is one of the terms below.

## Why a bare number is the problem

Two engines reported at 0.031 and 0.034 look ordered. Whether they are depends
entirely on a spread the two numbers do not carry, and the reader most likely to
quote them is the one least able to reconstruct it.

The tempting repair is a single symmetric interval on each number, which would
let a reader compare them at a glance. It is refused here, and the reason is that
the terms below do not combine the way a laboratory measurement's do. The largest
of them is not random, one of them is common to both engines and cancels in a
comparison between them, and one of them is not an uncertainty in the metric at
all. A single interval built out of those would be tidy, would be quoted, and
would be wrong in a way nobody could see from the number.

## The terms

Five, each with its kind, because a bound and a standard deviation are different
statements and adding them is a category error before it is an arithmetic one.

### Discretisation

A bound. The largest term for almost every case.

It is the error from the finite timestep, and it is not random: at a given step
the same engine on the same case makes the same error. What estimates it is the
resolution study of [resolution-study.md](resolution-study.md), from the observed
convergence over the ladder, and what it produces is a bound on how far the value
at a rung is from the value the same method would give at zero step.

For a study whose convergence conclusion is `not-established`, this term is not
estimated and the record says so. That is the case where a reduced study costs
what it costs, and it is why the reduced label travels with the number.

### Reference error

A bound. Computed by this project rather than estimated from the run, in #47, and
refused when absent by #49.

It has a property none of the others has and it is the one most likely to be
mishandled: it is common to every engine on that case, because every engine on
that case is compared against the same reference. It therefore shifts every
engine's value in the same direction by the same amount and cancels exactly in
the difference between two engines. It does not cancel in the distance between an
engine and the true answer.

Those are two different comparisons and they need two different intervals. Using
the one that includes the reference bound to compare two engines makes the suite
less able to tell them apart than it actually is; using the one that excludes it
to state how far an engine is from the truth claims more than the suite knows.
Both are stated below as separate rules for that reason.

### Run-to-run variation

Statistical, and the only term here that is.

It is real for engines whose solve is threaded or whose contact set depends on
ordering, and it is zero for a deterministic one, which is a finding rather than
an absence. It is reported as the sample standard deviation over a stated number
of repeats at identical inputs, with the number of repeats carried beside it,
because a standard deviation from three samples and one from thirty are not the
same evidence.

What determinism this suite promises and what it has measured is #14, and this
term is the place its answer arrives in a number.

### Estimator uncertainty

Statistical in shape, and it belongs to the estimator rather than to the engine.

For a metric that is read directly off a trajectory, such as the drift of a first
integral, it is negligible and is recorded as such rather than omitted. For a
largest Lyapunov exponent from a finite trajectory it is substantial, it has its
own literature, and it does not shrink by integrating more accurately. #75 is
where the estimator states it, and it states it as an interval with the method
that produced it named, because an interval whose method is unnamed cannot be
recomputed.

For a fitted exponent on a dissipative case it is the uncertainty of the fit over
the case's declared window, carried with the fit residual, since a small
uncertainty on a bad fit is a number about the fit and not about the engine.

### Sensitivity to the initial condition

Reported, and never part of the uncertainty.

For a chaotic case, the spread of the metric over perturbed initial conditions is
not an uncertainty in the metric. It is a property of the system, it is one of the
things the suite exists to show, and folding it into an interval on the engine's
value would attribute the physics to the measurement. It is carried in its own
field, with its own name, and no rule below adds it to anything.

For a qualitative case the same quantity is the outcome's stability across the
perturbations the case declares, and it is the evidence the outcome is an outcome
rather than an artefact. Same field, same refusal to be folded in.

## They stay separate

The record carries the terms as separate fields and there is no field for a
combined interval. As in [report-card-shape.md](report-card-shape.md), the shape
is what enforces the decision: there is nowhere to write the tidy number, so
refusing it is not a matter of anybody remembering.

    uncertainty.discretisation        kind = bound
    uncertainty.reference             kind = bound
    uncertainty.run_to_run            kind = statistical, with repeats
    uncertainty.estimator             kind = statistical, with method
    sensitivity.initial_condition     not an uncertainty, never combined

Each field is present on every metric value, and a term that does not apply
carries the statement that it does not apply rather than being absent. A missing
field and a term measured at zero are opposite statements, and the second one is
a finding.

What this costs is the report card's simplicity, and the cost is real: a cell
carries five things instead of one and no reader can order two cells by eye. That
is the correct outcome rather than an unfortunate side effect, because ordering
two cells by eye is the thing this decision exists to prevent.

## When two engines may be reported as different

Two values, on the same case, at the same rung of the ladder, from two engines.
They are reported as different when

    |m_A - m_B|  >  d_A + d_B + k * sqrt(s_A^2 + s_B^2)

where `d` is the discretisation bound, `s` is the run-to-run standard deviation
combined in quadrature with the estimator uncertainty where the estimator has
one, and `k` is a coverage factor fixed at 2.

Three things about that rule are decisions rather than arithmetic.

The bounds add and the statistical terms combine in quadrature, because that is
what the two kinds of term mean. Adding a bound to a standard deviation, or
putting a bound in quadrature, would be treating one as the other.

The reference bound is absent, for the reason given at that term: it is common to
both engines on the same case and cancels. A comparison between an engine and the
true answer is a different statement, and there the reference bound is added and
the rule becomes that an engine's value is distinguishable from zero error only
when it exceeds `d + r + k*s`, with `r` the reference bound.

The coverage factor is 2 and that is a convention, not a derivation. It is
recorded in the card's data alongside the comparison so a reader who wants
another factor can recompute rather than argue, and it is the same factor for
every case so it cannot be chosen per comparison.

Where the rule is not satisfied the two engines are reported as not
distinguished, which is its own statement and not a tie, not equal, and not a
shared rank. Where either study's convergence conclusion is `not-established`,
the discretisation term is not estimated and no comparison is made at all, which
is the second place a reduced study costs what it costs.

For a qualitative metric none of this applies, because the values are not
numbers. Two engines are reported as different there when their outcomes differ
in every run of the set the case declares, and as not distinguished otherwise. A
majority is not a difference.

For the chaotic class the rule above is used on the exponent, and the sensitivity
term is not in it. #78 holds the reading of what a difference in exponent means
and what it does not, and this document fixes only when one may be called a
difference at all.

The report card follows this rule rather than a reader's eye, which is a
requirement on #81: two cells are shown as distinguished or not distinguished by
the rule, computed from the fields above, and never by their rendered order.

## What refuses a bare number

Nothing at this commit. There is no result record, no store and no report card,
so a metric value written without its uncertainty is refused today by a reviewer,
which is not a mechanism.

Where it lands: the store schema refuses a metric value whose five fields are not
all present, which is #79, and the record that does not describe its own run is
#40. The renderer refusing to draw a value without them, and refusing to show two
cells as ordered when the rule above does not distinguish them, is #81.

## The means

Markdown in `docs/decisions/`, beside the decisions it is read with. The rule in
the middle of this document is arithmetic and is written as arithmetic rather
than as code, because the quantities it operates on do not exist yet and the
place it will be implemented is #81, whose means is chosen there. Writing it here
as a function would be choosing that issue's means from outside it and would put
a second implementation in a document, which is the drift this tree already names
against itself.

## What is not decided here

- Which metric each class is judged by: #7.
- The resolution study that estimates the discretisation bound: #11.
- What determinism this suite promises, and what it has: #14.
- The reference's own bound: #47, refused when absent by #49.
- The estimators that state their own uncertainty: #75 and the per-case issues.
- The result store schema and the renderer: #79 and #81.
- What a difference in Lyapunov exponent means once one may be called a
  difference: #78.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree refuses a metric
value with no uncertainty, a combined interval, a sensitivity folded into one, or
two cells shown as ordered when the rule does not distinguish them. The
mechanisms are owed and are named at #79, #40 and #81 above.

One absence is narrower and is named so a later green is not read as covering it.
The rule for calling two engines different is a rule about published cells, so it
reaches nothing a reader computes from the raw data themselves. Every term needed
to apply it is published for that reason, which reduces the problem and does not
remove it.
