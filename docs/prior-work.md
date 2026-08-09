# The prior work, and where this disagrees with it

This answers issue #111. It describes the existing comparisons of these engines,
states the gap this project fills, and says what this suite measures instead. It
does not argue that the prior work is wrong, because it is not, and a document
that overreached there would weaken the part that is strong.

Both works below were read for this document rather than cited from a summary of
them. Where a sentence of theirs is quoted, it is quoted because a paraphrase of
it would be the thing this project is arguing with.

## The standard comparison

Tom Erez, Yuval Tassa and Emanuel Todorov. Simulation tools for model-based
robotics: Comparison of Bullet, Havok, MuJoCo, ODE and PhysX. 2015 IEEE
International Conference on Robotics and Automation (ICRA), IEEE, 2015, pages
4397 to 4404. DOI 10.1109/ICRA.2015.7139807.

What it does. It puts one model into five engines through a common interface,
runs the same four systems in each, and reports a speed-accuracy curve per engine
per system: a grasping hand of 35 degrees of freedom, a 25 degree-of-freedom
humanoid, a five-body planar kinematic chain, and 27 capsules falling on a floor.
It measures raw speed separately, and it measures grasp stability as the largest
timestep at which the hand still holds the object.

Its accuracy measure is self-consistency. The paper integrates the same system at
a very small timestep, 1/64 of a millisecond, calls that the reference
trajectory, then increases the timestep and measures how far the result departs
from it, averaged over ten short pieces of trajectory so that a system near chaos
does not have its divergence counted as error.

Why it chose that rather than a conservation law, in its own words, from section
III:

> We seek to develop universal tests and performance metrics that can be applied
> to any model system. This is in contrast with benchmarks such as single
> rigid-body motion or energy and momentum conservation which rely on analytical
> solutions. Although we include the latter when applicable, typical robotic
> systems do not preserve energy, momentum, symplectic forms or any other known
> quantity. Furthermore it is unclear if the ability to do well on simple systems
> generalizes to more complex systems, where the primary challenges are multiple
> interacting contacts, poor conditioning of large matrices and other
> scaling-related phenomena.

That is correct, and it is correct for the reason it gives. A robot is actuated,
it has joint limits, it makes and breaks contact, and none of those conserve
anything. A metric that only exists on systems without them is a metric that does
not apply to the thing being built. The paper is explicit about the boundary of
its own measure as well: it separates numerical integration error from model
error, and puts the second outside its scope because addressing it is system
identification rather than simulation.

And the clause that is easy to miss is the one that matters most here. The paper
does run energy and momentum tests, in section IV.E, on the two of its systems
where they apply. It gets them to apply by removing the ground plane, disabling
gravity, and disabling joint limits, contacts and actuators, which turns the
humanoid into what the paper calls an astronaut. On the planar chain, which
preserves energy and angular momentum without modification, it reports that the
Runge-Kutta integrator wins by orders of magnitude, as it should.

The authors state that they are MuJoCo's developers and that identifying MuJoCo's
strengths and weaknesses is a secondary goal, and they offer their comparison code
so that others can validate and extend the results. That disclosure is the
practice this project inherits rather than something to hold against the paper.

## The other benchmark

SimBenchmark, by Dongho Kang and Jemin Hwangbo, published as a site and a
repository rather than as a paper: https://leggedrobotics.github.io/SimBenchmark/
and https://github.com/leggedrobotics/SimBenchmark. It compares RaiSim, Bullet,
ODE, MuJoCo and DART.

What it measures is stated on its own front page: total kinetic energy, linear
momentum, and penetration error, which it defines as the position-level error a
contact solver or the discretisation leaves and which it says should be zero for
rigid-body simulation with hard contacts. It reports the whole speed-accuracy
curve rather than a point, over tests it names rolling, bouncing, 666 balls,
elastic 666 balls, and PD-control, momentum and energy tests on the ANYmal robot.

It is robotics-centred in the same way and for the same reasons, and its authors
are also RaiSim's, which it states.

## The gap

Both works take the answer they compare against from the engines themselves. The
ICRA comparison's reference trajectory is the engine under test run at a smaller
timestep, which measures whether an engine agrees with itself as the step
shrinks. An error that the engine's model makes at every timestep is in the
reference too, so it cancels; the paper says as much when it names its measure
self-consistency and puts model error outside its scope. SimBenchmark compares
against quantities that are conserved by construction in the systems it built,
which is a real check and a weaker one than an answer known independently. So on
the systems where a right answer exists and is known in closed form, nobody in
this field is checking the engines against it, and the systems where it exists are
exactly the ones the ICRA comparison reaches by switching contact, gravity, joint
limits and actuators off. A roboticist should accept that sentence without
accepting that it makes their benchmarks worse, because their benchmarks are
answering a question about robots and this one is not.

## What this suite measures instead

An answer computed here, from the equations of motion, with an error bound
attached, on systems whose behaviour is known: the integrable tops, the
non-holonomic rolling cases, and the rattleback, whose reversal is a qualitative
outcome an engine either reproduces or does not.

That is a narrower question than either work above asks, and it is narrower on
purpose. It does not measure speed, throughput, articulated systems, contact-rich
manipulation, or stability under the settings robotics work actually uses, and
[what this suite does not measure](what-this-does-not-measure.md) says so at
greater length. What a poor result here supports, and what it does not, is
[what this project is not for](what-this-is-not-for.md).

Nothing here says an engine that does badly on a rattleback is unsuitable for
robotics. The two works above measure what an engine does on the systems it is
used for; this one measures whether it can do rigid-body mechanics where the
answer is known. Both are worth knowing and neither substitutes for the other.

## The constructions the reference is built from

[The reference integration](decisions/reference-integration.md) names these by
author and by construction and states that none of the references was fetched for
it. They are given here.

The discrete rigid body on the rotation group, which is the update
`reference/integrator.py` implements: Jürgen Moser and Alexander P. Veselov.
Discrete versions of some classical integrable systems and factorization of matrix
polynomials. Communications in Mathematical Physics, volume 139, 1991, pages 217
to 243. DOI 10.1007/BF02352494.

Its extension to a body under gravity about a fixed point, and the Lie group form
the code is written in: Taeyoung Lee, Melvin Leok and N. Harris McClamroch. Lie
group variational integrators for the full body problem. Computer Methods in
Applied Mechanics and Engineering, volume 196, issues 29 and 30, 2007, pages 2907
to 2924. DOI 10.1016/j.cma.2007.01.017.

The general theory, including the discrete Noether theorem that says which
momentum map each case preserves exactly: J. E. Marsden and M. West. Discrete
mechanics and variational integrators. Acta Numerica, volume 10, 2001, pages 357
to 514. DOI 10.1017/S096249290100006X.

The non-holonomic half, which is a different construction and not a weaker version
of the same one: J. Cortés and S. Martínez. Non-holonomic integrators.
Nonlinearity, volume 14, issue 5, 2001, pages 1365 to 1392.
DOI 10.1088/0951-7715/14/5/322.

Where these disagree is one place and it is worth naming, because it is the place
this suite's deciding case lives. The variational construction of the first three
rests on a discrete Hamilton principle, and the non-holonomic cases have no such
principle: their equations come from the Lagrange-d'Alembert principle, their flow
preserves no symplectic form, and asking for a symplectic method there is a
category error rather than a lesser guarantee. That is why the fourth reference is
a separate construction and why the reference integration note refuses the word
symplectic on the non-Hamiltonian half.

`PROSE, NOT ENFORCEMENT` for that refusal. Nothing greps the word, which the
reference integration note already states and places at #92.

Which member of the non-holonomic class this project uses is #48, and it is not
decided here. The order the reference ships at is #46's measurement rather than a
number any of these references fixes.

## The citations a case carries

Every number in a case file says where it came from, and the reader refuses one
that does not. A case with no provenance block at all is refused, a value no entry
covers is refused, an entry naming a value the file does not contain is refused,
and a `sourced` value with no citation is refused:

    python -m unittest discover -s tests -k casefile
    Ran 54 tests in 0.054s
    OK

    git grep -n 'is a value of this case and no provenance entry covers it' -- casefile.py
    casefile.py:513:                f"{path} is a value of this case and no provenance entry covers it"

That refusal is enforced rather than prose, and it is the reason the citations for
a case's parameters and its physics belong in the case file rather than in this
document. There is no case file yet:

    git ls-files 'cases/*.toml' | wc -l
    0

and the emptiness is asserted rather than passed over, by
`tests/test_casefile.py::TheCasesInThisTree::test_there_is_still_no_case_file`,
which reds the day the first one lands.

## The mark

`PROSE, NOT ENFORCEMENT` for everything above except the last section. Nothing in
this tree refuses a document that describes the prior work unfairly, that
overstates the gap, or that lets a reference go stale, and no reading of the tree
could: whether a description is fair is a judgement about meaning, and a reviewer
is what stands behind it. The link checker in `tests/test_document_links.py`
refuses a broken link to a file in this repository and says nothing about an
external one, which is its own stated bound and is #94's remaining half.
