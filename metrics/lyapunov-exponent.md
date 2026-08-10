# The largest Lyapunov exponent: the rule, and what it measured

Issue #75. [The estimator](lyapunov.py) computes the metric for the chaotic
class. This document is the half of that issue a document has to carry: the rule
by which the two free parameters are chosen, the measurement of how much the
answer depends on them, and the published numbers the estimator was checked
against.

Everything below is printed by one command, and the numbers are quoted from its
output rather than retyped:

    python -m metrics.lyapunov

It takes about two minutes. The suite runs the same measurements over shorter
horizons, in `tests/test_lyapunov.py`, which is where a change that costs the
estimator its accuracy reds.

## What is estimated, and from what

Two trajectories, started a small distance apart, advanced by the same flow.
Each renormalisation interval the separation reached is recorded, the logarithm
of its growth is one sample, and the second trajectory is pulled back onto the
line to the first at the starting distance again. The exponent is the mean of
those samples over the intervals that are kept.

The construction needs no linearised equations and no derivative. It needs a
flow: something that advances a state by a duration. That is what an engine
offers and what an engine's linearisation does not, and it is the whole reason
this construction was chosen over the tangent-map one.

Two recorded trajectories and nothing else would not be enough, and it is worth
saying why, because "works from trajectories alone" reads as if it were. Without
the pull-back the samples telescope: the sum of the logarithms is the logarithm
of the last separation over the first, the separation saturates at the size of
the attractor, and what comes back falls like one over the horizon whatever the
system does.

## The rule for the separation

The separation has a floor and a ceiling, and neither is a preference.

Below the floor the two runs differ by their own noise rather than by the
system's instability. The floor is the larger of two things, both measured on the
flow in hand: what two runs of the same state produce, which is zero for a
deterministic flow and is not zero for an engine reached through a runner, and
the rounding of the run's own excursion.

Above the ceiling the perturbation is no longer small compared with the run's
excursion, so the separation is bent by the shape of the attractor rather than by
its instability, and the growth saturates.

**The rule is the geometric mean of the two.** That is the point as many decades
above the floor as below the ceiling, and it is the widest margin available
against both failures at once.

On the Lorenz system at these parameters, the run's excursion is 14.7288 about
its own mean, its reproducibility floor is 0.0e+00, so the floor is the rounding
of the excursion and the rule lands at 2.1948e-07.

## The rule for the interval

The interval wants the separation to grow by about one factor of e before it is
pulled back. Shorter and each sample is the rounding of a growth that barely
happened; longer and the perturbation leaves the linear regime inside the
interval, which is the ceiling failure again.

One factor of e per interval is one over the exponent, and the exponent is what
is being measured, so **the rule is a bootstrap**: run a pilot, take the exponent
it reports, and set the interval from it. Two bounds sit on the answer and both
are the horizon rather than the system:

- A pilot exponent of zero or less has no growth rate to invert. That is what a
  regular system reports, and the rule keeps the pilot interval there rather than
  dividing by a number that is not there.
- An interval long enough to leave fewer intervals than the blocks can be cut
  from would buy a well-placed interval at the cost of the uncertainty, so it is
  cut back to the longest the horizon carries. The pendulum reaches this bound
  rather than the first: its pilot exponent is small and positive, being the
  shear that has not finished decaying, and one over it is longer than any
  horizon.

Then the interval is snapped to a whole number of whatever the flow advances by.
That last step is not tidiness and the cost of skipping it is measured below.

## The uncertainty

The per-interval samples are correlated: an orbit crossing a strongly separating
region gives several large ones in a row. Dividing their standard deviation by
the square root of their count would report an uncertainty too small by whatever
the correlation length is.

So the samples are cut into contiguous blocks, each block is averaged, and the
uncertainty is the standard error over the block means. The estimator refuses a
run that cannot give it blocks long enough for that, with the floor in the
message, and it refuses a run whose block means are all identical rather than
reporting an uncertainty of zero. No number leaves that module claiming to be
exact.

## What the rule produced, against the published numbers

    ## The rule, and what it produced

    plane pendulum, amplitude one radian
        horizon 6400, separation 1.4526e-08, interval 39.875 (the growth rule asked for 39.8750)
                     +0.0010  +/- 0.0006   published +0.00000    1.89 uncertainties away

    Lorenz, sigma 10, rho 28, beta 8/3
        horizon 1000, separation 2.1948e-07, interval 1.11 (the growth rule asked for 1.1105)
                     +0.8997  +/- 0.0099   published +0.90560    0.60 uncertainties away

    Henon map, a 1.4, b 0.3
        horizon 40000, separation 1.1203e-08, interval 2 (the growth rule asked for 2.3864)
                     +0.4190  +/- 0.0021   published +0.41922    0.09 uncertainties away

Where each published number comes from is in
[the systems themselves](known_exponents.py), one sentence per entry, so a reader
can go and check it rather than take this file's word for it.

## The sensitivity to the separation

    separation    exponent   uncertainty
    1.0e-14       refused: the two runs met exactly at interval 38
    1.0e-13       refused: the two runs met exactly at interval 376
    1.0e-12       +0.8942    0.0106
    1.0e-11       +0.8997    0.0100
    1.0e-10       +0.8997    0.0099
    1.0e-09       +0.8997    0.0099
    1.0e-08       +0.8997    0.0099
    1.0e-07       +0.8997    0.0099
    1.0e-06       +0.8997    0.0099
    1.0e-05       +0.8997    0.0099
    1.0e-04       +0.8995    0.0100
    1.0e-03       +0.8929    0.0134
    1.0e-02       +0.9071    0.0110
    1.0e-01       +0.8887    0.0157
    1.0e+00       +0.9842    0.0240
    1.0e+01       +0.4031    0.0172

Read from both ends rather than from the middle. The two finest separations are
refused rather than answered: the perturbation is below the rounding of a state
of that size, the two runs land on the same float, and the estimator says so
instead of taking the logarithm of zero. The two coarsest are answered and wrong:
at a separation of 1 the exponent is eight per cent high and at 10, which is of
the order of the excursion, it is less than half the published value and carries
an uncertainty that says nothing about the error.

Between 1.0e-11 and 1.0e-05 the answer moves in the fourth decimal. The rule's
2.1948e-07 sits in the middle of that plateau, which is what the rule is for.

## The sensitivity to the interval

    interval      exponent   uncertainty
    0.05          +0.9005    0.0073
    0.1           +0.9005    0.0073
    0.25          +0.9005    0.0073
    0.5           +0.9005    0.0073
    1             +0.9005    0.0073
    2             +0.9018    0.0048
    4             +0.9018    0.0048

Flatter than expected, and the reason is worth writing down rather than leaving
to be rediscovered. The mean of the samples is the total accumulated growth
divided by the total time, and the blocks partition the same total time whatever
the interval is, so both the value and the block means are nearly independent of
it while the perturbation stays inside the linear regime. Where the interval
would matter is where it is long enough for the separation to leave that regime
inside one interval, and at this separation the horizon runs out first.

So on this system the interval is the parameter the answer is least sensitive to,
and the rule that chooses it earns its place for a different reason: the snapping
below, and the horizon bound that keeps the blocks fillable.

## The regular system

    horizon       exponent   uncertainty   log(T/settling)/(T-settling)
    400           +0.00805   0.00222       0.00788
    1600          +0.00290   0.00111       0.00277
    6400          +0.00104   0.00055       0.00090

A regular system's exponent is zero, and no finite horizon prints zero. What a
finite horizon prints is the separation that is linear in time, read as a rate,
and the third column is that shape written out. The measured value tracks it
within a few per cent over a factor of sixteen in horizon.

That is the claim the suite makes about the pendulum, and it is a much stronger
one than a small number would be: a small number is what an estimator returns
when it has quietly given up, and this one has the shape linear separation has
and shrinks when the horizon grows.

It also says what a reader may not do with a regular case. At a horizon of 400
the estimate is 3.6 uncertainties from zero. Read as a hypothesis test that says
the pendulum is chaotic, which it is not: the uncertainty is the spread of the
measurement and the distance from zero is a bias that falls with the horizon, and
the two are different quantities. Whether the report card is allowed to say
anything at all about a class whose exponent is zero is #78's, and it is named
here because this table is where somebody would otherwise decide it by accident.

## What rounding the interval costs

    snapped 2    +0.4190  +/- 0.0021   published +0.41922    0.09 uncertainties away
    asked 2.3864 +0.3501  +/- 0.0015   published +0.41922   45.90 uncertainties away
        the ratio of the two intervals is 1.1932 and the ratio of the two exponents is 1.1968

This is the mistake somebody will actually make, and it is why the interval is
snapped rather than passed through. The rule asks for 2.3864 iterations. A map
cannot advance by that, and a flow that rounds the request silently advances by 2
and reports the growth over 2 divided by 2.3864. Nothing about the result looks
wrong. It is positive, it is stable to four figures, it agrees with itself on
every rerun, and it is sixteen per cent low.

The two ratios agreeing to three figures is what says the cause is the rounding
and not something else. In this tree the flows advance by exactly the duration
asked, cutting it into equal substeps, and the map refuses a duration that is not
a whole number of iterations. `tests/test_lyapunov.py::TheSnappingBites` holds
both halves.

## What this does not measure, and what it cannot

Only the largest exponent. The rest of the spectrum needs either the tangent map
or a set of perturbations kept orthogonal, and the first is unavailable through
an engine while the second multiplies the cost by the dimension.

The phase space is whatever the caller's state holds, and the distance is
Euclidean over those coordinates as given. An estimator that knew an orientation
from an angular velocity could weigh them, and one that could weigh them could
weigh two engines differently, so it does not know. What follows is that the
number depends on the coordinates the state is expressed in, and a case comparing
engines has to hand all of them the same ones. That is the run record's job and
it is #10 and #40.

The uncertainty is the spread of this measurement over this trajectory. It is not
a bound on the difference between this estimate and the true exponent of the
system: the block-means construction estimates the spread of the finite-time
exponent, and a bias shared by every block is invisible to it. The regular
system's table above is exactly that case, and it is shown rather than argued.

Nothing here has been run against an engine. There is no adapter:

    git ls-files 'adapters/*/__init__.py' | wc -l
    0

so every number in this document is the estimator against a system this tree
integrates itself. What an engine's trajectory does to it is #74's case and
#76's refusal of trajectory comparison for this class.

PROSE, NOT ENFORCEMENT for the choice of the two placement constants. That the
rule was applied is refused by code: the estimator takes the separation and the
interval it was given, records both on the estimate, and `by_the_rule` is the one
callable that derives them. Whether the geometric mean is the right point between
the floor and the ceiling, and whether one factor of e is the right growth per
interval, are judgements this tree has no way to read. The tables above are the
evidence offered in place of a mechanism, and they are the reason the constants
are named and recorded rather than written inline.
