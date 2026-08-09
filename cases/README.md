# cases

The case definitions, as data. A case carries the bodies, the initial condition,
the constraints and contact model the case intends, the horizon, the measured
quantity, the reference answer or the statement that it is computed, the
tolerance, and the provenance of every parameter. What shape that data takes and
which fields are required is fixed in
[docs/decisions/case-file-format.md](../docs/decisions/case-file-format.md), and
`casefile.py` is the schema that refuses a case missing one.

Two things refuse a file here and they ask different questions. `casefile.py` asks
whether it is a well-formed document: the fields are present, typed, named and
covered by provenance. `casephysics.py` asks whether the numbers in it are a rigid
body, which no schema can see: an inertia tensor that is not positive definite, or
principal moments where one exceeds the sum of the other two. Both run over every
file in here on every gate run, and what neither of them can ask yet is issue #32.

Nothing is in here yet. Nothing is missing that stops one being written either,
which was not true when this directory was created: the convention every case
names is fixed, in
[docs/decisions/units-frames-and-inertia.md](../docs/decisions/units-frames-and-inertia.md),
and the reader implements it.

Somebody who never runs this code should be able to read, cite and reuse what is
in here, so it holds no Python and no reference to any engine's parameter names.
