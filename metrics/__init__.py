"""The metric estimators: the quantity a case is judged by, computed from a run.

`lyapunov.py` is the largest Lyapunov exponent, which is the metric for the
chaotic class, and it is written in the form that works from runs alone because
most engines will not hand out a linearisation. `known_exponents.py` is the small
set of systems whose exponent is published, which is what says the estimator
returns the right number rather than a plausible one.

Part of the numerical core, so nothing here imports an adapter or an engine, and
`tests/test_package_boundaries.py` refuses the import that would let it. An
estimator that could see which engine produced a run is an estimator that could
treat two engines differently.
"""
