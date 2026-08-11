# metrics

The metric estimators: the quantity a case is judged by, computed from a
trajectory. The Lyapunov exponent estimator, the reversal count, the drift of a
conserved quantity and its direction, and whatever a later case needs.

One thing in here is not an estimator. `trajectory.py` decides whether a
trajectory comparison may be made at all, because that is the metric this suite
refuses by default and the one somebody adding a case will reach for anyway.

Part of the numerical core, so it imports no adapter and no engine. An estimator
that could see which engine produced a trajectory is an estimator that could
treat two engines differently, and the boundary check in
`tests/test_package_boundaries.py` refuses the import that would let it.
