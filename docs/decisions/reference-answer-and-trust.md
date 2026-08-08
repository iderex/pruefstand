# The reference answer, per class, and how far it is trusted

This answers issue #9. It states, for each class in the vocabulary, whether the
answer an engine is compared against is a closed form, a computed integration or
both. It states the requirements a computed reference has to meet before anything
is compared against it, and where each is refused. It states how far a reference
that meets them is trusted, which is a narrower thing than being correct.

It does not restate the reference's design. The configuration variable, the
method class, the property that class preserves, the non-Hamiltonian cases with
the different property asked of them, and the list of what the reference is not,
are all fixed in [reference-integration.md](reference-integration.md) and are
referenced here rather than repeated. A list in a second document drifts against
the first, and this document is the second.

It is written before the reference exists:

    git ls-files reference/
    reference/README.md

## The reference is not the truth

The distinction this document is built on. A closed form evaluated to a stated
accuracy is the answer to the case. A computed integration is another program,
and a comparison between one program and several others is not what this project
claims to publish.

So a computed reference is admitted only with a bound attached, and the bound is
what makes the comparison a measurement rather than a preference for whichever
implementation this project happens to hold. Where the bound is not small enough
for the case, the honest report is that the engine's error is somewhere inside an
interval, which is the `bounded` cell state in
[report-card-shape.md](report-card-shape.md), and not a number.

## Per class

The classes are the five in [metric-per-class.md](metric-per-class.md).

### integrable

Both, and the closed form is the answer.

The torque-free asymmetric top and the heavy symmetric top have solutions in
elliptic functions, which is #44. The Kovalevskaya top is integrable and its
solution is hyperelliptic, which is a different practical proposition and is #45
for exactly that reason: what it costs to evaluate is part of what that issue has
to find out, and until it has, the Kovalevskaya case is one whose closed form is
named rather than available.

The computed integration is run beside the closed form rather than instead of it,
for two reasons that are not the same. It supplies the reference at the
resolutions the study of #11 needs, which a closed form supplies for free and a
comparison against the engine does not. And the agreement between the two is the
strongest check this project has on its own integrator, because the two share no
code and no method.

Where they disagree beyond the computed reference's own bound, neither is
published for that case until the disagreement is explained. A closed form is not
automatically right either: evaluating an elliptic function near a modulus of one
is where its accuracy goes, which is why the worked case in
[case-file-format.md](case-file-format.md) places its orbit away from the
separatrix on purpose.

### nonholonomic-conservative

Both for the Chaplygin sleigh, computed with a partial closed form for the
Chaplygin sphere.

The sleigh's reduced equations have an exact solution and the asymptotic
behaviour is known in closed form, which is #62. The sphere is integrable and its
solution reduces to quadratures rather than to a function anyone evaluates
directly, which is #63, so what is available there is the conserved quantities
and the invariant measure as exact statements rather than a trajectory.

That difference matters for what the reference is asked to do. For the sphere the
closed-form content is a set of invariants, so it constrains the reference
strongly and pins its trajectory not at all, and the computed integration is the
trajectory. The requirements below therefore carry the whole weight there.

### dissipative

Computed, with the asymptotic law as an independent partial check.

Euler's disk has no closed-form trajectory, and what is known in closed form is
the power law the motion approaches under a stated dissipation model, which is
#50's to name. That law checks the reference in the limit and says nothing about
the approach, so the reference is a computed integration whose late-time exponent
must agree with the law before the case is usable.

The tippe top is computed with no closed form at all.

A dissipative case whose file names no dissipation model has no reference, and
the reference refuses it rather than filling one in, which is the rule
[reference-integration.md](reference-integration.md) already states.

### qualitative

Computed, and the answer is an outcome rather than a trajectory.

The rattleback and the tippe top have no closed-form solution. What the reference
produces is the outcome of #7's metric, which is whether the inversion happened
and how many reversals occurred in which directions.

The requirements below are harder to satisfy here than anywhere else, and it is
worth saying why rather than letting the list look uniform. A discrete outcome
has no continuous error to bound, so a bound on the reference's trajectory does
not become a bound on its outcome. What stands in for it is stability: the
reference's outcome has to be the same across its own resolution ladder and
across the perturbations of the initial condition the case declares, and an
outcome that moves under either is not a reference outcome. Since #67 makes the
rattleback the case that decides this project, that is the requirement most worth
being strict about.

### chaotic

Computed, and the reference is a reference for the invariant rather than for the
trajectory.

The double pendulum has no closed form. A reference trajectory exists and is not
the answer to anything, because trajectory agreement is refused for this class,
so what the reference supplies is the largest Lyapunov exponent with its own
estimator uncertainty, which is #75.

The trap here is that the reference's exponent is itself an estimate from a
finite trajectory, so its uncertainty is not a bound in the sense the other
classes use and does not shrink by integrating more accurately. A reference
exponent quoted without that interval would be the tightest-looking and least
justified number in the whole suite.

## What a computed reference must meet

Six requirements. A computed reference that fails any of them is not a weaker
reference, it is not a reference, and the case it was for reports `bounded` or
nothing rather than a number against it. There is no downgraded state and no
adjective that admits one.

It carries an error bound over the case's horizon, in the units of that case's
metric, and the bound is smaller than the case's tolerance. Where it is not
smaller, the case is still runnable and its cell is `bounded` by the reference's
own bound rather than by the engine's error. Refused by #49, computed by #47.

Its measured order of convergence agrees with the order its method class claims,
within a stated tolerance. An integrator that does not converge at the order its
construction implies has a defect somewhere between the construction and the
code, and the measurement is the only thing that finds it. Measured by #46.

It agrees with an independent second computation, at higher precision or by a
different route, to a stated tolerance. A single implementation checked against
itself proves nothing, and the independence is the whole content of the
requirement. Computed by #47.

Its configuration stays on the manifold it claims, with the residual measured and
recorded rather than assumed. For the rotation group that is the orthogonality
residual, expected near working precision and expected to grow like the square
root of the step count; for the rolling cases it is the constraint residual, held
at working precision rather than projected back. Measured by #43 and #48.

It preserves the property its class names, measured rather than asserted. Bounded
and non-accumulating energy error for the Hamiltonian cases, exact constraint
satisfaction with conserved energy for the nonholonomic ones, and the invariant
measure only where the continuous system has one. Which property belongs to which
case is fixed in [reference-integration.md](reference-integration.md), including
the two systems that have no invariant measure and must not be given one.

It is reproducible from its own record: the method, the composition order, the
step, the precision and the commit, so that a reader who doubts a reference value
can produce it again rather than argue about it. The record is #10's shape and
the published trajectories with their bounds are #51.

For a qualitative case, the first requirement is replaced rather than dropped, by
the stability statement in that class's section above. Replaced rather than
dropped is the load-bearing word: an outcome with no continuous error is not an
outcome that needs no evidence.

## How far it is trusted

Three limits, stated so that a later reader can hold a number against them.

A reference is trusted for the case it was computed for, at the resolutions it
was computed at, and nowhere else. A reference trajectory reused for a case with
a different initial condition is a new computation with a new bound.

A reference is trusted to the size of its bound and not beyond it. Two engines
whose difference from the reference is smaller than the bound are not ordered by
it, which is the comparison rule in
[uncertainty-reporting.md](uncertainty-reporting.md) and is the place that limit
becomes a rule rather than a caution.

A reference is never trusted to say an engine is wrong about a quantity the
reference does not itself preserve. The Kovalevskaya fourth integral is the
standing example: the reference's method class does not protect it, so the
reference's own drift in it has to be bounded before an engine's drift in it
means anything, which is #47's and is named in
[reference-integration.md](reference-integration.md) so that #54 does not inherit
it silently.

## What refuses a reference answer with no bound

Nothing at this commit. There is no reference, no result record and no store, so
a reference answer without a bound is refused today by a reviewer, which is not a
mechanism.

Where it lands: #49, whose declared subject is exactly that refusal, reading the
bound that #47 computes out of the record that #10 shapes. This document adds one
thing to #49's subject, which is that the refusal applies to the qualitative
classes through the stability statement rather than through a numeric bound, so
that a case with no continuous error cannot pass the check by having nothing to
bound.

The requirements above are refused in the places named at each one: #46 for the
order, #47 for the independent computation, #43 and #48 for the residuals. None
of those checks exists at this commit either, and each is named at its issue
rather than assumed here.

## The means

Markdown in `docs/decisions/`, beside the decision it references. The artefact is
an argument about what may be compared against what, and the only reason it is a
separate document from the reference design note is that the two answer different
questions: that one says what the reference is, this one says which cases have
one and what makes it usable. Where the two would say the same thing, this one
links instead, because a list restated in a second file drifts against the first
and the drift is silent.

## What is not decided here

- The reference's configuration variable, method class and preserved properties:
  #42, already answered.
- The integrator itself: #43.
- The closed forms and what evaluating them costs: #44 and #45.
- The measured order and the independent bound: #46 and #47.
- The non-holonomic reference: #48.
- Which dissipation model a dissipative case names: #50.
- How the terms of an uncertainty are reported and combined: #15.
- The prior work these constructions come from, given exactly: #111.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree refuses a reference
without a bound, a reference whose order was never measured, a reference checked
only against itself, or a qualitative reference whose outcome moves across its own
ladder, because there is no reference. Each refusal is named at the issue that
owes it above.

One absence is narrower and is named so a later green is not read as covering it.
The per-class table above is a statement about which cases have closed forms,
made from the literature rather than from anything in this tree, and no command
backs it. It is written as a claim for that reason, and #111 is where those
claims acquire their sources.
