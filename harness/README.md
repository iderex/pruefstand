# harness

The second of exactly two sets of tests. `tests/` is the suite that runs
anywhere: no engine, no display, no elevation. This directory holds everything
that needs something, and what it needs is in its own name rather than in a
comment inside it.

A harness lives in `harness/<requirements>/`, where `<requirements>` is a
sorted, hyphen-joined list of ids from `requirements.toml`. So `harness/engine/`
needs an installed engine, and `harness/engine-gpu/` needs an engine and a
graphics device. A name that does not decompose into declared ids is refused, and
so is a harness that imports something none of its own requirements permits,
which is how a harness quietly acquires a second requirement while its name
still claims one. `tests/test_two_test_sets.py` is the check.

`requirements.toml` is the one place a requirement is declared. Adding an id
there is the deliberate act; a harness cannot invent one.

## What a green from here does and does not mean

A green from `tests/` covers the numerical core, the case validation, the report
assembly and the boundary rules, on any machine. It covers no engine.

A green from a harness covers what it covers on the machine that ran it, and
nothing about any other machine. A number produced only by a harness run is a
number nobody else can reproduce without the same requirements, so where the
report card carries one it says which harness produced it and on what. That
sentence is a rule about the report card and no check refuses a report card that
breaks it. PROSE, NOT ENFORCEMENT, and issue #83 is where the published numbers
are guarded against silent movement.

## The counts, so a later drift is visible

Measured on 2026-08-08 at the commit this file landed in:

    python -m unittest discover -s tests 2>&1 | grep -E '^Ran '
    Ran 44 tests in 3.460s

    git ls-files 'tests/test_*.py' | wc -l
    4

    git ls-files 'harness/*/test_*.py' | wc -l
    0

The third count has moved. One harness exists, `harness/engine/`, and the two
above have moved with the rest of the tree:

    python -m unittest discover -s tests 2>&1 | grep -E '^Ran '
    Ran 195 tests in 6.040s

    git ls-files 'tests/test_*.py' | wc -l
    10

    git ls-files 'harness/*/test_*.py' | wc -l
    1

`harness/engine/test_conformance.py` runs the adapter conformance suite against
every adapter package in the tree, which means importing an engine, which is what
puts it here. It covers no engine today, because there is no adapter package for
it to import:

    git ls-files 'adapters/*/__init__.py' | wc -l
    0

So it is written to fail rather than to pass when it is run against an empty
tree, and the gate does not run it at all: the engine part derives from the tree
and reports itself as not run, naming the absent adapter, which is a statement
about coverage rather than a green over nothing. The first adapter is issue #34
and the first case that needs one is issue #55.

A harness directory is a package, with an `__init__.py`. That is not decoration:
`unittest discover -s harness` skips a directory that is not one, silently, and
the engine part of the gate would then collect nothing and exit on the count
rather than on a test.
