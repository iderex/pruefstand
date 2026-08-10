# Telling a discretisation error from a modelling error

Issue #57. This is the statement that makes a result useful to an engine's
maintainers rather than merely embarrassing, so it is worth being precise about
what is claimed and what stands behind it.

An engine whose error falls as the step is refined is integrating the right
equations imprecisely. The fix is computer time. An engine whose error stops
falling is integrating something other than the right equations, and no step size
will fix it. [The estimator](error_source.py) decides which of those a resolution
ladder shows, or says that the ladder does not decide.

## The method, in the order it is applied

**The study's own error comes off first.** Three things can put a floor under an
error curve: the engine integrating the wrong equations, the arithmetic running
out of significant digits, and the reference the error was measured against being
itself known only to a bound. Only the first is a finding. The second and third
are declared by the caller as an `Excluded`, they add, and every rung is reduced
by their sum before anything is fitted.

**A rung not clear of that sum is dropped rather than reduced.** The threshold is
a factor, `MARGIN_ABOVE_EXCLUDED`, and it is a factor rather than a difference
because both excluded contributions are themselves estimates. A rung level with
them carries no statement about the engine in either direction, and subtracting
one estimate from another of the same size produces a number whose sign is
arbitrary. Each dropped rung is recorded on the conclusion with the reason, so a
verdict drawn from three rungs of an eight-rung study cannot be read as one drawn
from eight.

**The verdict is read from the local orders, not from the fit.** One slope over a
curve that is second order at the coarse end and flat at the fine end is a number
near one, and a number near one is the shape of a ladder that is neither. So the
order between each neighbouring pair is computed, and:

- every interval at or above `ORDER_CONVERGENCE_HOLDS` is **converging**
- the coarse end at or above it and the fine end below
  `ORDER_A_FLOOR_HAS_FALLEN_BELOW` is **floored**
- anything else, and any ladder with too few rungs left, is **undecided**

The gap between the two bands is deliberate. A ladder whose orders sit inside it
is one where the evidence points neither way, and that is what the third verdict
is for.

**The fit is carried, and it decided nothing.** The least-squares slope and scale
over the surviving rungs are on every decided conclusion, because the order is
the number a reader compares against what an engine documents. They are recorded
rather than consulted.

## What each conclusion carries

The verdict, the reason in a sentence naming which route produced it, the range
of steps the fit used, how many rungs reached it, the local order of every
interval, the fitted order and scale, the floor the error settled at where it
settled, one sentence per dropped rung, and the exclusions as declared. A verdict
without the range it was fitted over is refused at construction, and so is a
fourth word for a verdict.

## Undecided is produced rather than avoided

Three routes reach it and no two of them say the same sentence: a ladder with
fewer rungs than the floor left after the exclusions, a ladder whose local orders
sit between the bands, and a ladder entirely inside the exclusions.
`tests/test_error_source.py::UndecidedIsProducedRatherThanAvoided` holds all
three, including the near-miss where exactly one rung too few survives and a
module willing to conclude from two would have reported converging on the
strength of a single interval.

## What this does not do

It has not been run on an engine. There is no adapter and no resolution study:

    git ls-files 'adapters/*/__init__.py' 'runner/*.py' | wc -l
    0

so every ladder it has seen is one `tests/test_error_source.py` built with the
answer known in advance. The study that produces real ones is #55 and the runner
under it is #39.

It does not estimate the rounding floor. That number is an input here, and where
it comes from is the study that produced the ladder: `reference/convergence.py`
measures one for the reference's own refinement and prints where rounding takes
over, and the corresponding number for an engine's run is the study's to measure.
Taking a guess at it inside this module would be the module deciding how much of
an engine's error to forgive.

It says nothing about which of several floors is the engine's when more than one
is present. What it reports is that what remains after the declared exclusions
stopped falling, and the declaration is carried on the conclusion so that a
reader disputing the verdict can dispute the input.

PROSE, NOT ENFORCEMENT for the two order bands and the margin. That the verdict
follows from them is refused by code, and each of the three verdicts has a
fixture that reaches it and a neighbour that does not. Whether half an order is
the right place to say convergence holds, and a quarter the right place to say a
floor has arrived, are judgements no reading of a tree makes. They are named
constants rather than numbers inside an expression so that a disagreement is with
a value a reader can find, and the tests are written against the constants rather
than against their values so that moving one moves the fixtures with it.
