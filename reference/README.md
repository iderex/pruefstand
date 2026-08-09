# reference

The reference integration: the answer the engines are compared against, computed
here rather than taken from any of them, together with the error bound that says
how far it is trusted.

`answer.py` is the type a reference value is carried in, and it holds the value and
the trust statement as one thing: there is no constructor that takes a value
without saying how far it is trusted, so the comparison code cannot be written
without one. The three trust statements are a numeric bound, the stability
statement that replaces a bound where the answer is an outcome rather than a
number, and an explicit unbounded state that carries the reason no bound could be
produced. Each is refused for the class it does not belong to. Which of them a case
has is
[the reference answer and how far it is trusted](../docs/decisions/reference-answer-and-trust.md).

`integrator.py` is the computation that produces an answer for a rigid body,
either free or under gravity about a fixed point. The orientation is a rotation
matrix advanced by a group operation and never renormalised, the state is the
orientation together with the body angular momentum, and the step is fixed: a
requested time that is not on the step's grid is refused rather than reached by
interpolating between two states or by shortening a step. Which method class that
is, and what it preserves for which case, is
[the reference integration](../docs/decisions/reference-integration.md). What it
keeps is measured in `tests/test_integrator.py` rather than asserted here: the
residual off the rotation group over a long horizon and how that residual grows,
the free rotation of a symmetric body against its elementary closed form, the two
momentum maps a heavy symmetric top has, and an energy band that does not walk and
shrinks with the square of the step.

The rest of the computation does not exist yet. The closed forms are #44 and #45,
the measured order of convergence is #46, the independent error bound is #47 and
the non-holonomic reference is #48. `integrator.py` carries one precision,
binary64, and the higher-precision run the design note anticipates for the bound is
#47's to weigh rather than something built here.

Part of the numerical core, so it imports no adapter and no engine. That is the
property this directory exists for. A reference that imported an engine would
inherit that engine's conventions for frames, units or contact, and the thing
every engine is measured against would no longer be independent of one of them.
The boundary check in `tests/test_package_boundaries.py` refuses the import.
