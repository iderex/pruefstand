"""The reference integration and the trust statement that travels with it.

`answer.py` is the type a reference value is carried in, and it cannot hold a
value without holding how far that value is trusted. Everything else here is the
computation that produces one, and none of it exists yet: the integrator is #43,
the closed forms are #44 and #45, the measured order is #46, the independent bound
is #47 and the non-holonomic reference is #48.

Part of the numerical core, so nothing here imports an adapter or an engine, and
`tests/test_package_boundaries.py` refuses the import that would let it.
"""
