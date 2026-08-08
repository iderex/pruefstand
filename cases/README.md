# cases

The case definitions, as data. A case carries the bodies, the initial condition,
the constraints and contact model the case intends, the horizon, the measured
quantity, the reference answer or the statement that it is computed, the
tolerance, and the provenance of every parameter. What shape that data takes and
which fields are required is fixed in
[docs/decisions/case-file-format.md](../docs/decisions/case-file-format.md), and
the schema that refuses a case missing one is issue #31.

Nothing is in here yet, and one field is why. Every case names the units, frames
and inertia convention it is written against, that vocabulary is issue #13, and
until it exists the field has no legal value.

Somebody who never runs this code should be able to read, cite and reuse what is
in here, so it holds no Python and no reference to any engine's parameter names.
