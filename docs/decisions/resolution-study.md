# The resolution study

This answers issue #11. It fixes the axes an engine is varied over, the sampling
on each and the reason for both, the rule that decides which cases get the full
study and which get a reduced one, what a reduced study may and may not claim,
the fields that carry the convergence conclusion into the result record, and the
single narrow route by which a case may declare that the study does not apply.

It does not decide the configuration procedure that fixes every setting other
than the ones varied here, which is #5. It does not decide how the uncertainty on
a metric value is stated, which is #15, and the order estimate below carries an
uncertainty whose shape that issue fixes. It does not decide which engines are
run, which is #16.

It is written before any runner or result record exists:

    git ls-files runner/ results/
    results/README.md
    runner/README.md

## Why a curve rather than a number

An engine evaluated at one timestep can be made to look good or bad by choosing
the timestep, and neither choice looks dishonest from the outside. Publishing one
number per engine per case would therefore be publishing a choice, and the
readers most able to check it are the ones who would be quoting it.

The curve is also where the most useful thing this suite can say comes from. An
error that falls as the step is refined is a discretisation error and it says the
engine is doing the right thing slowly. An error that stops falling is a
modelling error and it says the engine is doing a different thing accurately.
Those are opposite findings for anyone deciding whether to use the engine, and a
single point cannot tell them apart. Separating them is #57.

## The axes

Two, and a rule for a third.

The timestep, always, for every engine and every case. It is the axis every
engine has and the one the order of a method is defined against.

The solver iteration count, for an engine whose contact or constraint solve is
iterative and exposes the count. This is the axis on which an engine tuned for
robotics is most likely to differ from its own documentation, because a default
iteration count is chosen for a frame budget rather than for an answer. An engine
with no such setting simply has no second axis, which is recorded rather than
filled in.

Any third axis is admitted only by naming it in this document first. The reason
for that ceremony is arithmetic: axes multiply, the study already dominates the
machine time this project spends, and an axis added quietly is a cost nobody
agreed to. A solver tolerance, where an engine solves to a tolerance rather than
to a fixed count, is the most likely candidate and is not admitted here because
no adapter exists to say which engines have one.

## The sampling

The timestep ladder is geometric with ratio two, six rungs, and it is fixed by
the case in absolute seconds rather than derived from any engine.

Geometric because the order of convergence is a slope on a log-log plot, and a
slope needs points spread multiplicatively. Ratio two rather than ten because
with ratio ten there are too few points to fit a slope and to see it change,
while with ratio two the whole ladder costs a little under twice its finest rung,
so the ladder is nearly free once the finest rung is affordable.

Six rungs because five intervals give five local slope estimates, which is enough
to see a slope that changes across the ladder and enough to see the turnaround
described below. Fewer than four is a line through noise.

Fixed by the case and in absolute seconds because the alternative breaks the
comparison this project exists to make. A ladder anchored at each engine's own
default step would evaluate two engines at two different sets of timesteps, and
two numbers at two different steps are not a comparison. So every engine is asked
the same six steps.

The engine's own default step is run as well, as a seventh point, labelled as the
default rather than as a rung. It is not part of the ladder and no slope is
fitted through it. It is there because what a person gets when they install the
engine and use it is a real question, it is the condition most of the work this
suite worries about was done under, and dropping it would answer a question
nobody asked instead.

The iteration ladder, where it applies, is three points: the engine's default,
twice it, and four times it. Three because this axis answers a narrower question
than the first, which is whether the count matters for this case at all, and
three points separate no dependence from a dependence that has not saturated.

The two axes are not crossed. The timestep ladder is run at the engine's default
iteration count and the iteration ladder is run at one fixed timestep, the
second-finest rung of the timestep ladder. The full cross product would be
eighteen runs to answer a question that a slice answers, and the second-finest
rung is chosen rather than the finest so that the slice is affordable and still
sits in the part of the ladder where the timestep is not the dominant error.

Where the slice shows the metric moving with the iteration count by more than the
case's tolerance, the case is not answerable from the timestep ladder alone and
the record says so. That is a finding rather than a failure of the study.

## What the curve is asked to show

Four things, and each is a recorded value rather than something read off a
picture.

Whether the metric converges at all. Fitted as a slope over the rungs from the
turnaround downward in step size, with the fit's own residual recorded, because a
slope through points that are not on a line is a number with no meaning.

The observed order, against the order the engine's documentation claims. The
comparison is between two numbers this project can quote, and where the
documentation claims none, the record says the claim is absent rather than
leaving the field to be read as agreement.

Where the curve turns around. Below some step the accumulated rounding grows
faster than the discretisation error falls, and the metric starts rising again.
An engine that turns around early is saying something about its own arithmetic,
and the rung at which it happens is recorded.

What it cost. Wall-clock time per rung, so that an engine which is accurate only
at a step nobody would use is reported as such rather than reported as accurate.

## Full and reduced, and the rule that decides

The full study is all six timestep rungs, the default point, and the iteration
slice where the engine has one.

The rule is cost, and it is stated in the case rather than decided by whoever ran
it. The case declares a wall-clock budget for one engine's study. Where the
finest rung's measured cost would take the study past that budget, the study is
reduced, and the reduction drops rungs from the fine end.

Dropping from the fine end is the direction the arithmetic forces and it costs
exactly the thing the study is for, so it is worth stating plainly rather than
presenting as a tidy compromise. A geometric ladder's cost is dominated by its
finest rung, so dropping coarse rungs saves nearly nothing and dropping fine ones
is the only reduction that is a reduction. The information that is lost is the
part of the curve where the discretisation error has become small enough for the
modelling error to show, which is the distinction the section above calls the
most useful thing this suite can report.

So a reduced study is worth much less, and what it may claim is limited to match.

A reduced study may report the metric value at each rung it ran, with the rungs
it ran, and it may report that the metric was still falling at its finest rung.

A reduced study may not report an observed order, may not report a turnaround,
and may not conclude either that the metric converged or that it did not. Its
convergence conclusion is `not-established`, which is a third value and not a
polite spelling of `not-converged`. An engine whose study was cut short and an
engine whose error stopped falling are opposite findings and must not share a
cell.

Which cases get the full study is therefore not a list. It is whichever cases can
afford one, measured rather than assumed, and the budget is per case in the case
file. Two cases are exempt from the budget and get the full study regardless,
because a reduced study there would make the case pointless: every case in the
integrable canon, where the metric is the drift's scaling with the step and there
is nothing else to report, and the rattleback, which #67 makes the case that
decides this project.

## Where the study does not apply

One route, and it is narrow.

A case declares `study.not_applicable` with a reason, and the reason has to be
that the metric is not a function of the timestep at all. Today that is true of
exactly two things: an entry produced by evaluating a closed form, which has no
timestep, and the stub engine of #38, whose answer is known by construction.

Being a discrete outcome is not a reason. It is tempting, because there is no
slope to fit for a case whose metric is whether the tippe top inverted, and it is
wrong: an outcome that appears at one timestep and not at the next is not an
outcome, it is an artefact, and the ladder is the only thing that tells them
apart. So a qualitative case runs the full ladder and what its curve shows is the
outcome's stability across the rungs rather than a slope. The convergence
conclusion for such a case is `converged` when the outcome is the same at every
rung from the turnaround downward, and `not-converged` when it is not, which is a
finding worth publishing on its own.

Cost is not a reason either. Cost produces a reduced study, which is a different
state with a different label, and collapsing the two would let an expensive case
be reported as one the study did not apply to.

## What the record carries

Requirements on #10 and #40 rather than a schema, and #79 is where the result
store holds them.

    study.kind

One of `full`, `reduced` and `not-applicable`.

    study.rungs
    study.default_point
    study.iteration_slice

The timesteps actually run, the engine's own default step and the metric at it,
and the three iteration counts with their metric values or the statement that the
engine has no such setting.

    convergence.conclusion

One of `converged`, `not-converged` and `not-established`. This is the field the
issue asks for and the reason it is a field rather than a picture: a reader
inferring convergence from a plot is a reader inferring it from the axis limits
somebody chose.

    convergence.order
    convergence.order_residual
    convergence.claimed_order
    convergence.turnaround_step

Present when the conclusion is `converged` or `not-converged`, absent when it is
`not-established`, and `claimed_order` carries the explicit statement that the
engine's documentation claims none where that is the case.

    cost.wall_clock_seconds

Per rung, so the cost of accuracy is reported rather than assumed.

A number that came from a reduced study carries `study.kind` with it everywhere
it is reproduced. That is a requirement on the report card and on the published
data rather than a hope: the label travels with the number, so a value lifted out
of the data by somebody building their own table cannot lose it. #17 fixes the
rendering and #84 the published form.

## What refuses a single-point result

Nothing at this commit, and it is worth saying plainly rather than letting the
paragraph above read as a mechanism. There is no runner, no result record and no
report card in this tree, so a single-point result is refused today by a
reviewer, which is not a mechanism.

Where it lands: the check reads the set of records for one case and one engine
and refuses a report card cell built from fewer than two rungs unless the case
declares `study.not_applicable` with its reason. That is an assembly-time
refusal, so it belongs to #80, whose subject is already refusing an assembly it
should not make. The record fields it reads are #40's, the store it reads them
from is #79's, and running the study over the integrable canon is #55.

## The means

Markdown in `docs/decisions/`, beside the decisions it is read with. The artefact
is an argument about how much machine time is spent and what may be claimed from
it, and it is held against #55 and #80 when those are written. Nothing here is a
program. The arithmetic behind the ratio and the rung count is stated in the text
rather than computed, because the quantities it is about, the cost of a rung and
the budget of a case, do not exist yet and a number computed from invented inputs
would be a claim wearing a command.

## What is not decided here

- Everything the engine is configured with other than the two axes above: #5.
- The uncertainty attached to the order estimate and to each metric value: #15.
- Which metric each class is judged by, and therefore what the curve is a curve
  of: #7.
- Separating a discretisation error from a modelling error once the curve
  exists: #57.
- The full result record and what refuses one that omits a field: #10, #40.
- The report card cell states, and how a reduced study is rendered: #17.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree refuses a run at one
timestep, a reduced study reported as a full one, an order fitted through a
reduced ladder, or a case claiming the study does not apply for a reason this
document rules out. Every mechanism is owed and each is named above.

One absence is narrower and is named so a later green is not read as covering it.
Nothing checks that a number reproduced outside the result store still carries
its `study.kind`, and that is the requirement above most likely to be lost,
because losing it takes no action at all: a table built by copying values is a
table with the label left behind.
