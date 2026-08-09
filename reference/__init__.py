"""The reference integration and the trust statement that travels with it.

`answer.py` is the type a reference value is carried in, and it cannot hold a
value without holding how far that value is trusted. `integrator.py` is the
computation that produces one for a rigid body, free or under gravity about a
fixed point, advanced on the rotation group rather than onto it. `convergence.py`
is the refinement study that says what order that computation reaches, and
`order-of-convergence.md` is what it measured. What is still missing: the closed
forms are #44 and #45, the independent bound is #47 and the non-holonomic
reference is #48.

Part of the numerical core, so nothing here imports an adapter or an engine, and
`tests/test_package_boundaries.py` refuses the import that would let it.
"""
