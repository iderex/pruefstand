# tests

The suite that runs anywhere: no engine installed, no display, no elevation, no
network. A contributor who cannot install an engine still gets a meaningful green
from this directory, because most of what this project asserts is in code that
needs no engine.

The harness that needs real hardware or an installed engine is a separate set and
is not in here. Naming it, listing what each harness may require, and refusing a
test that belongs to neither set is issue #22.

`test_package_boundaries.py` is the check that refuses an import from the
numerical core into an adapter or an engine, and an adapter importing a second
engine. It is written against `unittest` from the standard library so that it
runs from a bare interpreter at the floor version, because the toolchain is not
pinned yet (#19) and the one gate command that will run it does not exist yet
(#20). Run it with:

    python -m unittest discover -s tests -v
