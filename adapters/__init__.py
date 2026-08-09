"""The adapter layer: one interface, one conformance suite, one package per engine.

`interface.py` is the contract every adapter implements and is the only place
this project decides what an adapter owes its callers. `conformance.py` is the
suite an adapter has to pass, and it is what turns that contract from a
description into something a run can refuse.

Neither of them imports an engine, and this package declares no `ENGINE_MODULE`,
because it is not an adapter. The packages beneath it are, and each of those
imports exactly one engine and declares which. `tests/test_package_boundaries.py`
refuses a package here that declares nothing.
"""
