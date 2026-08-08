# runner

The one route from a case, an engine and a configuration to a result record. It
selects an adapter, hands it a case, collects what came back, and writes a record
that describes its own run well enough for the number to be reproduced from the
record alone.

The runner is allowed to import adapters, because selecting one is its job. It is
the only place other than an adapter that may. What does not belong here is
physics: a quantity computed in the runner is a quantity computed outside the
numerical core, where no test of the numerical core reaches it.
