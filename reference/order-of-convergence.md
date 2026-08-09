# The order this reference reaches

Issue #46. [The reference integration](../docs/decisions/reference-integration.md)
fixes the class of method, says the base update in that class is second order, and
leaves what this implementation reaches to be measured. This is the measurement.
Everything below is output of a command that is written above it, run at the
commit this file landed in.

The observed order is two. The three ladders below overlap, and together they run
from a step of 2.5e-1 down to 4.9e-6, which is close to five decades, with every
interval inside that range at two to within 0.08. Above it there is one interval
at 2.34, where the leading term does not yet dominate, and then the run is
refused. Below it rounding takes over, at a step this file names. The order is two
on both halves of the update, the free one and the one carrying the moment.

Nothing was fixed as a result, because nothing was found to be out of order. What
the study did turn up is in the section on what bounds the fine end, and it is
about how long a run may be rather than about the order.

## The command

    python -m reference.convergence

It prints three ladders. The first two refine the torque-free symmetric body
against its elementary closed form, over a long horizon and a short one. The third
refines a heavy top against itself, because the heavy symmetric top's closed form
is elliptic and is #45's, and the moment term has to be reached by something.

## The free body, against a known answer

    the orientation, against the free symmetric top's closed form, horizon 2.0
      N=4         h=5.0000e-01  error=3.138110e-01  order=
      N=8         h=2.5000e-01  error=6.186435e-02  order= 2.343
      N=16        h=1.2500e-01  error=1.470972e-02  order= 2.072
      N=32        h=6.2500e-02  error=3.633221e-03  order= 2.017
      N=64        h=3.1250e-02  error=9.055866e-04  order= 2.004
      N=128       h=1.5625e-02  error=2.262274e-04  order= 2.001
      N=256       h=7.8125e-03  error=5.654629e-05  order= 2.000
      N=512       h=3.9062e-03  error=1.413591e-05  order= 2.000
      order two from h=2.5000e-01 to h=3.9062e-03, over 6 interval(s), worst departure 0.072
      rounding does not take over anywhere on this ladder, so the floor is below its finest step and is not measured here

The coarse end of this ladder is where the range ends and not where the method
does. Above it the leading term does not yet dominate, which is the 2.343, and
above that the step's implicit equation stops contracting and the run is refused
rather than truncated:

    python -c "
    from reference.convergence import against_the_closed_form
    from reference.integrator import IntegrationRefused
    try:
        against_the_closed_form(2.0, (2, 4, 8))
    except IntegrationRefused as refused:
        print(refused)
    "
    the step's implicit equation did not converge within 64 iterations, which means the step is too large for this method rather than that the problem is hard

So for this body the usable coarse end is a step of about a quarter of a second,
which is a rotation of roughly a fifth of a radian per step, and there is no range
between the last rung and the refusal in which the method runs and is not second
order.

## The same body, refined until rounding takes over

    the orientation, against the free symmetric top's closed form, horizon 0.005
      N=16        h=3.1250e-04  error=2.341463e-10  order=
      N=32        h=1.5625e-04  error=5.853662e-11  order= 2.000
      N=64        h=7.8125e-05  error=1.463407e-11  order= 2.000
      N=128       h=3.9063e-05  error=3.658435e-12  order= 2.000
      N=256       h=1.9531e-05  error=9.149626e-13  order= 1.999
      N=512       h=9.7656e-06  error=2.279565e-13  order= 2.005
      N=1024      h=4.8828e-06  error=5.537237e-14  order= 2.042
      N=2048      h=2.4414e-06  error=8.393286e-14  order=-0.600
      N=4096      h=1.2207e-06  error=1.761924e-13  order=-1.070
      order two from h=3.1250e-04 to h=4.8828e-06, over 6 interval(s), worst departure 0.042
      rounding takes over at h=2.4414e-06, where the error is 8.393286e-14 after 2048 steps

The horizon is short here for one reason: the floor is reached by taking many
steps, and taking many steps at a long horizon runs into the limit the next
section is about before it runs into rounding.

The floor is 5.5e-14 in the worst entry of the orientation, at a step of 4.9e-6
over 1024 steps. Below that, halving the step costs accuracy rather than buying
it, and the two rungs past the floor show the error rising rather than levelling,
which is the accumulated rounding of twice as many steps.

That number is the useful bound and it is not a bound on this suite's cases. It
says a reference run refined past about 1e-5 seconds per step is spending time to
get a worse answer. Where a case's tolerance sits relative to it is a question for
the case, and no case exists yet.

## The heavy top, where the moment enters

    the orientation, against the run at the next step down, horizon 0.5
      N=32        h=1.5625e-02  error=6.487136e-03  order=
      N=64        h=7.8125e-03  error=1.603979e-03  order= 2.016
      N=128       h=3.9062e-03  error=3.998925e-04  order= 2.004
      N=256       h=1.9531e-03  error=9.990440e-05  order= 2.001
      N=512       h=9.7656e-04  error=2.497181e-05  order= 2.000
      N=1024      h=4.8828e-04  error=6.242684e-06  order= 2.000
      N=2048      h=2.4414e-04  error=1.560654e-06  order= 2.000
      order two from h=1.5625e-02 to h=2.4414e-04, over 6 interval(s), worst departure 0.016
      rounding does not take over anywhere on this ladder, so the floor is below its finest step and is not measured here

What this ladder proves is narrower than what the two above it prove, and the
difference matters. It compares each run against the run at half its step, so it
measures the rate at which refinements agree with each other. A method converging
steadily onto the wrong answer produces a clean slope here. What says this update
converges onto the right answer at all is the closed form, and the closed form
reaches only the torque-free half.

Closing that gap is #45, whose closed form is the one this body would be measured
against.

## What bounds the fine end, and it is not the same for every body

The orientation is never renormalised, so its distance from the rotation group is
rounding and nothing else, and a state further off the group than `GROUP_TOLERANCE`
is refused at construction rather than integrated further. How many steps that
allows is not a property of the method alone:

    python -c "
    from reference.convergence import SYMMETRIC
    from reference.integrator import IDENTITY, Body, State, every_step, matvec, off_the_group
    SKEWED = ((2.0, 0.3, -0.7), (0.3, 3.5, 0.11), (-0.7, 0.11, 4.25))
    for name, inertia, spin in (('symmetric', SYMMETRIC, (0.7, 0.0, 1.3)), ('skewed', SKEWED, (1.1, -0.4, 0.9))):
        states = every_step(Body(inertia=inertia), State(IDENTITY, matvec(inertia, spin)), 2e-3, 16000)
        worst = [max(off_the_group(s.orientation) for s in states[:n + 1]) for n in (1000, 16000)]
        print(f'{name:10s} 1000 steps {worst[0]:.3e}   16000 steps {worst[1]:.3e}   ratio {worst[1] / worst[0]:5.2f}')
    "
    symmetric  1000 steps 4.396e-14   16000 steps 7.216e-13   ratio 16.41
    skewed     1000 steps 7.550e-15   16000 steps 2.331e-14   ratio  3.09

Sixteen times the steps. For the skewed body the residual grows by a factor of
three, which is the square root of the step count the design note expects and
which `tests/test_integrator.py` measures. For the symmetric body it grows by a
factor of sixteen, which is the step count itself.

The difference tracks a quantity the two runs do not share. A torque-free
symmetric body turns through the same angle every step, because the size of its
body angular velocity is constant, while an asymmetric one does not:

    python -c "
    from reference.convergence import SYMMETRIC
    from reference.integrator import IDENTITY, Body, State, angular_velocity_body, every_step, matvec, norm
    SKEWED = ((2.0, 0.3, -0.7), (0.3, 3.5, 0.11), (-0.7, 0.11, 4.25))
    for name, inertia, spin in (('symmetric', SYMMETRIC, (0.7, 0.0, 1.3)), ('skewed', SKEWED, (1.1, -0.4, 0.9))):
        body = Body(inertia=inertia)
        states = every_step(body, State(IDENTITY, matvec(inertia, spin)), 2e-3, 16000)
        sizes = [norm(angular_velocity_body(body, s)) for s in states]
        print(f'{name:10s} |omega| from {min(sizes):.6f} to {max(sizes):.6f}')
    "
    symmetric  |omega| from 1.476482 to 1.476482
    skewed     |omega| from 1.434910 to 1.478653

A rounding error that is the same size and the same sign every step adds up like
the step count. One whose size and sign move adds up like a random walk. So the
square-root growth already measured is a property of the body that was measured
and not of the update, and the case where it is linear is the case with a closed
form, which is the one the reference is checked against and the one #53 makes a
case of this suite.

Where that leaves the run length, measured rather than extrapolated:

    python -c "
    from reference.convergence import SYMMETRIC
    from reference.integrator import IDENTITY, Body, State, advance, matvec, IntegrationRefused
    body = Body(inertia=SYMMETRIC)
    for step in (2e-3, 3.125e-7):
        state = State(IDENTITY, matvec(SYMMETRIC, (0.7, 0.0, 1.3)))
        for taken in range(1, 60001):
            try:
                state = advance(body, state, step)
            except IntegrationRefused:
                print(f'step {step:.3e}  refused after {taken} steps'); break
        else:
            print(f'step {step:.3e}  not refused within 60000 steps')
    "
    step 2.000e-03  refused after 22520 steps
    step 3.125e-07  refused after 9044 steps

Twenty-two thousand steps, which at that step is a horizon of forty-five seconds,
and nine thousand at a step small enough that each rotation is below the rounding
of the one it is added to. The refusal is the fail-closed behaviour the state's
own docstring describes and it is not a fault. What it is is a run length, and it
is short enough to reach: a free symmetric body asked for a horizon of a minute at
a step of 2e-3 stops rather than answering, and the ladder that reaches the
rounding floor above uses a short horizon for the same reason.

What follows beyond this issue is not decided here. The design note writes growth
like the step count as the trigger for reconsidering the configuration variable,
and whether that trigger is met by a body rather than by the method is a reading
of the note, not a measurement.

PROSE, NOT ENFORCEMENT for the paragraph above. Nothing measures the residual
growth for a symmetric body: `test_the_residual_grows_like_the_square_root_of_the_step_count`
runs the skewed body only, and it would fail on the symmetric one, so the
measurement above is made by a command a reader runs and by nothing else.

## A change that costs an order reds

Four one-line changes to `integrator.py`, each a mistake somebody makes, each run
as `python -m unittest discover -s tests -k convergence` and then reverted:

- The moment read at the start of the step where the update reads it at the end,
  which is the term evaluated at the wrong point that costs exactly one order.
  `TheOrderWhereTheMomentEnters.test_every_interval_sits_at_order_two` fails with
  no stretch of the ladder at order two.
- The second-order term dropped from the right-hand side of the step's solve.
  Same failure.
- That term's factor changed from a half to one. Same failure.
- The coupling term dropped from the solve's residual. The free ladder fails.

The first of those is the one the heavy top's initial condition was chosen for,
and choosing it took a measurement rather than a guess. Run against a fast top
tilted a little, which is the condition `tests/test_integrator.py` turns, the same
mistake is invisible: the fast motion's own second-order error is large enough to
hide the first-order term it introduces down to a step of 1.2e-5, which is a
hundred times finer than any rung a study would run at. Slowing the spin and
tilting the body over shrinks the second-order term and leaves the moment varying,
and the mistake then moves every interval of the ladder to order one.

Stated plainly rather than left out: none of these four changes is caught by this
study alone. Each of them also reds `tests/test_integrator.py`, because each
breaks a conservation statement that file already measures. What this study adds
is the order itself, which nothing else in this tree measures, and a failure that
names the order rather than naming an invariant.

The mirror case is worth recording too, because it is what stops the study being
read as a general accuracy check. Loosening the solve's tolerance from 1e-15 to
1e-7 reds `tests/test_integrator.py` and leaves this study green, correctly: a
looser solve raises the floor and does not change the slope.

## What this does not say

The order of the non-holonomic reference, which does not exist. Its member of the
method class is fixed in `nonholonomic-reference.md` and is second order by the
same argument, and #48 is where it is built and measured.

Anything about a case's tolerance. The last done-when item of #44 asks for an
accuracy bound smaller than the tolerance of any case that uses it, and no case
file exists, so the comparison has nothing on its right-hand side. The floor above
is a number about the reference and not about a case.

Anything about cost. The design note says which order the reference ships at is
decided by this measurement against a cost measurement in the same issue, and
#46's own body asks for neither a cost measurement nor a choice of order. The
implementation measured here is the base update at order two, a higher order in
this class is reached by symmetric composition of it, and whether to compose is a
choice about what a reference should cost. Not made here.

Whether the same order holds on another machine. Every number above is from one
host and one interpreter, and the reduced study in the gate is what would show a
number that did not travel.
