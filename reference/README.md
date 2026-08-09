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

The computation that produces an answer does not exist yet. The integrator is
issue #43, the closed forms are #44 and #45, the measured order is #46, the
independent bound is #47 and the non-holonomic reference is #48.

Part of the numerical core, so it imports no adapter and no engine. That is the
property this directory exists for. A reference that imported an engine would
inherit that engine's conventions for frames, units or contact, and the thing
every engine is measured against would no longer be independent of one of them.
The boundary check in `tests/test_package_boundaries.py` refuses the import.
