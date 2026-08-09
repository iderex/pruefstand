# adapters

One package per engine, and each package imports exactly one engine. An adapter
translates a case into whatever the engine it owns wants to be told, runs it,
and hands back what the engine actually did. It declares which engine it is for
in a module-level `ENGINE_MODULE` assignment in its `__init__.py`, and that
declaration is data the boundary check reads rather than a comment.

What does not belong in a package here: anything the numerical core needs,
anything a second adapter needs, and any decision about what a case means. An
adapter that starts holding physics is holding it once per engine, which is how
two engines end up being asked different questions.

Two modules sit beside the packages rather than inside one, and they are the
exception that sentence is drawn around. `interface.py` is what every adapter
implements and is the only place this project decides what an adapter is asked.
`conformance.py` is the suite an adapter has to pass, and it is what makes the
interface a mechanism rather than a description. Both are things every adapter
needs, which is exactly why neither is in an adapter: a contract that lived in the
first adapter would be whatever the first adapter did.

So a package here declares four names in its `__init__.py`, and all four are read
by code rather than by a person: `ENGINE_MODULE`, the one engine it imports;
`STATE_TOLERANCE`, how far a state read back from that engine may sit from the
case's own; `TOLERANCE_WHY`, the reason that number and not a looser one; and
`open_adapter()`, which returns something implementing the interface.
`interface.py` is where each of those is stated and `conformance.py` is what
refuses a package missing one.
