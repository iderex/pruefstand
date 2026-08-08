# reference

The reference integration: the answer the engines are compared against, computed
here rather than taken from any of them, together with the error bound that says
how far it is trusted.

Part of the numerical core, so it imports no adapter and no engine. That is the
property this directory exists for. A reference that imported an engine would
inherit that engine's conventions for frames, units or contact, and the thing
every engine is measured against would no longer be independent of one of them.
The boundary check in `tests/test_package_boundaries.py` refuses the import.
