# metrics

The metric estimators: the quantity a case is judged by, computed from a
trajectory. The Lyapunov exponent estimator, the reversal count, the drift of a
conserved quantity and its direction, and whatever a later case needs.

Part of the numerical core, so it imports no adapter and no engine. An estimator
that could see which engine produced a trajectory is an estimator that could
treat two engines differently, and the boundary check in
`tests/test_package_boundaries.py` refuses the import that would let it.
