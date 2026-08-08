# adapters

One package per engine, and each package imports exactly one engine. An adapter
translates a case into whatever the engine it owns wants to be told, runs it,
and hands back what the engine actually did. It declares which engine it is for
in a module-level `ENGINE_MODULE` assignment in its `__init__.py`, and that
declaration is data the boundary check reads rather than a comment.

What does not belong here: anything the numerical core needs, anything a second
adapter needs, and any decision about what a case means. An adapter that starts
holding physics is holding it once per engine, which is how two engines end up
being asked different questions.
