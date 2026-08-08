# cases

The case definitions, as data. A case carries the bodies, the initial condition,
the constraints and contact model the case intends, the horizon, the measured
quantity, the reference answer or the statement that it is computed, the
tolerance, and the provenance of every parameter. What shape that data takes and
which fields are required is issue #2, and the schema that refuses a case
missing one is issue #31.

Somebody who never runs this code should be able to read, cite and reuse what is
in here, so it holds no Python and no reference to any engine's parameter names.
