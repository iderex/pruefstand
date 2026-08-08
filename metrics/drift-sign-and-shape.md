# The sign of a drift, and its shape

This answers issue #56. A conserved-quantity metric reports a signed value, and
beside it the two things a single value throws away: how fast the integral walks
away from its initial value, and how far it swings while doing it. This document
fixes both, the method that separates them, the conditions under which that
separation means anything, and what a run has to record for either to be
computable at all.

Nothing is implemented here:

    git ls-files metrics/
    metrics/README.md

## Why one number is not the measurement

An engine that loses energy and an engine that gains it are wrong in different
ways, and a magnitude reports them identically. Loss is what an integrator adds
on purpose for stability, and it is why a robotics simulation stays well behaved
over a long run. Gain is an instability, and a simulation that gains energy
eventually does something absurd. Those are not two sizes of the same fault.

The second thing a single value hides is the shape. A drift that grows steadily
with time and a drift that swings about a level are produced by different
integrators, and the difference is a property of the method rather than of the
step size. An engine can end the horizon close to its initial value having swung
a long way in between, and an engine with a small swing can walk steadily away.
Reporting the endpoint alone cannot tell those apart, and the endpoint is the
number most likely to be quoted.

So the metric for a conserved quantity is at least three numbers, and this
document says which three and how each is computed.

## The sign is already fixed and is not restated here

The sign convention, and the rule that a vector integral is reported as a vector
of the same shape rather than as a norm, are settled in
[the metric each class is judged by](../docs/decisions/metric-per-class.md#integrable).
That document names this issue as where the requirement to show the direction
lands, so what follows is the requirement rather than a second statement of the
convention.

Everything below applies per component for a vector integral, for the same
reason: a momentum that walks along its own direction and one that walks across
it are different faults, and a component that is steady while another swings is
a third.

## The three numbers

Write `I(t)` for the integral the case names and `g(t)` for its relative change,

    g(t) = (I(t) - I(0)) / |I(0)|

sampled at the instants the run recorded over the horizon. `g` is the quantity
the class already scores, so this document introduces no new physical quantity
and only says what is read out of it.

The secular rate is the slope of the least-squares straight line fitted to `g`
over the whole horizon, in units of relative change per second of simulated time.
It carries the sign, and the sign is the whole point of it: positive is an
integral that grew.

The oscillation amplitude is the largest absolute residual about that line. It is
non-negative by construction and therefore carries no sign, and a reader must not
read a positive amplitude as growth. It is the largest excursion rather than a
root-mean-square, because the fault it exists to show is a single large swing and
an average understates exactly that.

The oscillation growth is the amplitude computed over the second half of the
horizon divided by the amplitude computed over the first half. A bounded
oscillation gives roughly one. A swing that is opening gives more, and that is a
third shape which belongs in the result rather than folded into either of the
other two. It is reported as a ratio and no threshold is set on it here: what
separates agreement from disagreement is the case's tolerance, which is not this
document's to write.

Two choices inside that, made deliberately rather than by default.

The fit is over the whole horizon and no transient is discarded. Discarding an
opening segment is a choice that hides a start-up kick, which is one of the
faults this measurement exists to find, and a rule that says how much to discard
would be a second place for a judgement to hide.

The model is a straight line and not something higher order. A straight line is
the smallest model that separates an integral that walks from one that does not,
and any further term would be fitting a shape nobody asked for. The cost is real
and is paid below rather than by adding terms: a drift growing faster than
linearly is not described by these numbers, and the third condition in the next
section is what refuses to report them as if it were.

## When the separation is not made

Three conditions, all readable from the same samples, and where any of them fails
the result says which one and the two components are absent rather than zero. A
blank that reads as a measurement is worse than an admission, which is the same
rule the record is written under.

The first is that there is an oscillation to measure. The residual about the
fitted line has to change sign at least twice over the horizon. A residual that
does not is not swinging about the line, and an amplitude taken from it is the
size of a systematic departure from the straight-line model rather than the size
of a swing.

The second is resolution. The oscillation is at the frequency of the system's own
motion, so a run sampled too coarsely reports an amplitude that is an artefact of
where the samples fell. The period is read from the residual's own sign changes
rather than declared anywhere, so this condition needs nothing from the case file.
At least sixteen samples per residual period are required. The number comes from
what coarse sampling costs at the peak: a sample can fall up to half a sampling
interval away from the true extremum, so a sinusoid sampled `n` times per period
has its peak underestimated by at most `1 - cos(pi/n)`,

    python -c "import math; [print(n, f'{100*(1-math.cos(math.pi/n)):.2f}') for n in (4, 8, 16, 32)]"
    4 29.29
    8 7.61
    16 1.92
    32 0.48

on CPython 3.14.6. Sixteen puts the worst case under two per cent, which is below
the precision anything else in this project is quoted to, and eight does not.
Thirty-two would buy another factor of four in a quantity nobody reads to that
precision, at four times the samples in every record.

The third is the floor. Where the residual is the size of the computation's own
rounding, the fitted slope is fitting noise and the amplitude is the noise's
excursion. The floor is not invented here: it is the run-to-run term from
[how an uncertainty is reported](../docs/decisions/uncertainty-reporting.md#run-to-run-variation),
and an amplitude that does not exceed it is reported as not distinguished from
zero rather than as a number. A secular rate whose change over the whole horizon
does not exceed the same term is reported the same way.

The conditions compose in the direction that matters. A residual made of rounding
noise changes sign at nearly every sample, so it fails the second condition as
well as the third, and neither of them alone would have caught both a badly
sampled run and a quiet one.

## What the report card has to render

The sign travels with the value and with the rate, everywhere, including in a
cell that has room for one number. A rendering that shows a magnitude where this
document requires a signed value is refused. That refusal belongs to the renderer
and there is no renderer, so it is owed rather than in force, and
[the metric each class is judged by](../docs/decisions/metric-per-class.md#the-mark)
already names the same absence against itself.

The two components are rendered beside the value rather than behind a link, for
the same reason the sign is: a reader who has to go somewhere else for them is a
reader who will quote the value alone.

Where the separation was not made, the cell says which condition failed. It does
not show a blank, and it does not show the value with the components quietly
missing, because that is indistinguishable from a run whose swing was zero.

## What this requires of a run record

None of the three numbers can be computed from an endpoint. A record carrying
only `I(0)` and `I(T)` yields the value the class already scores and nothing
else, and no later reader can recover what this document asks for from it.

So the record carries either the sampled integral over the horizon, or the three
numbers computed while the run was in progress together with the sample count and
the sampling interval that produced them. The second is far smaller and cannot be
recomputed or checked by anybody who did not run it, and the first is a
trajectory-sized field on every record. Which one, and what the choice costs in
the size of a published record, is #10's, and the runner that writes it is #39.
This document does not choose between them and does require that one of them
exists, because the alternative is discovering after the first run that the
measurement was never possible.

The sampling interval is required in either case. The resolution condition above
is a statement about samples per period, and a record that does not say how often
it sampled cannot support it.

## What is not decided here

- Which integral each case names, and which classes are scored on one at all.
  That is the class vocabulary in
  [the metric each class is judged by](../docs/decisions/metric-per-class.md#the-class-vocabulary).
- The estimators that compute any of this. They start at #75.
- What a run records and how, which is #10, and the runner that writes it, #39.
- How a metric value and its components are rendered, which is #81, and the
  provenance beside them, which is #82.
- The tolerance that separates agreement from disagreement, which belongs to the
  case and is derived over the resolution ladder rather than from any of the
  numbers above.
- Whether a case whose integral is a vector is scored on all components or on a
  subset. The vector shape is fixed elsewhere and which components a case names
  is the case's.

## The mark

PROSE, NOT ENFORCEMENT, whole document.

Nothing in this tree reads this file. There is no estimator to compute a secular
rate, no record to carry a sampling interval, and no card to refuse a magnitude
where a signed value is required. Each of those is owed by an issue named in the
section above.

One narrower absence, so that the absence of a red is not read as agreement.
Nothing checks that the conditions in this document are the conditions an
estimator actually applies, and nothing will until an estimator exists. Until
then the three numbers are a specification and the conditions are a promise about
a computation nobody has written.
