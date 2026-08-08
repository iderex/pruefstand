# The language and the toolchain

This answers issue #4. It fixes the means for each layer of the suite, states the
interpreter floor with the measurement that puts it there, names the cost of the
choice, and fixes the directory layout every later path follows.

Every number below was measured on 2026-08-08 with the command printed above it,
against the current release of each package on that day. Upstream releases move,
so re-run the command rather than quoting these numbers back later.

## The decision

Python for all three layers: the engine adapters, the numerical core and the
report assembly. One means, not two and not three.

Around it, named here and configured elsewhere:

- uv for the environment and the lock file. Issue #19 pins it.
- pytest for the suite and for the one gate command. Issues #20 and #21.
- ruff for both formatting and linting. Issue #24.
- mypy for type checking. Issue #25.

The interpreter floor is CPython 3.12.

## The adapter layer, where the means is forced

The engines are C++ libraries. Reaching them from anything other than their own
Python bindings means writing and maintaining a second set of bindings, and a
benchmark suite that did that would be measuring its own binding code alongside
the engine. That is the force, it is real, and it is held to the adapter layer
rather than being allowed to decide the rest of the tree by itself.

What is measured is that the bindings are distributed as ordinary Python
packages, so an adapter imports them and does not build them:

    for p in mujoco pybullet dartpy drake genesis-world; do curl -sS --max-time 25 "https://pypi.org/pypi/$p/json" | python -c "import json,sys; d=json.load(sys.stdin)['info']; print(d['name'], d['version'], d['requires_python'])"; done
    mujoco 3.11.0 >=3.10
    pybullet 3.2.7 None
    dartpy 6.19.4 >=3.7
    drake 1.55.0 >=3.12
    genesis-world 1.3.2 <3.14,>=3.10

One engine a reader would expect is absent from that list, and the absence has a
sharp edge. Project Chrono's bindings are not on the index under the obvious
name, and the obvious name belongs to an unrelated package:

    curl -sS --max-time 25 https://pypi.org/pypi/pychrono/json | python -c "import json,sys; d=json.load(sys.stdin)['info']; print(d['name'], d['version'], d['summary'][:60])"
    pychrono 1.1.0 A package for managing delays, scheduling tasks, timing

So an adapter for Chrono is not one import line and a pin, and the install route
for it has to be established before it is committed to. Which engines the first
release covers is issue #16, and this document does not decide it. The
observation belongs here because it is a fact about the means, and it is repeated
into #16 and #95 rather than left in one place.

Verified: the five packages above resolve on the index at the versions shown.
Not verified: that any of them, once installed, drives its engine correctly for
the cases this suite needs. That is what the adapters and their tests are for.

## The numerical core, where the means is chosen rather than forced

The reference integration and the metric estimators could be written in something
else. They are not, and this is the part of the decision that had a real
alternative.

Against the four things the answer has to satisfy:

The suite needs a test runner and a linter somebody else maintains, so a property
this project asserts can be refused by a check. pytest, ruff and mypy are that,
they are maintained outside this project, and they run on the same interpreter
the adapters already require.

A published number has to carry the command that produced it. One runtime means
one place that records versions, inputs and environment, and the versions it has
to record include the engine bindings, which are Python packages. A numerical
core in a second language would leave the run record straddling two environments,
and reconciling them is work that buys nothing a reader can check.

The suite has to run on a stock runner with no display and no elevation. Nothing
in this toolchain asks for either.

An operator installs it in one documented step. One toolchain is one step. Two
would be two, and issue #28 is the issue that would have to carry the second one.

What is given up by not adding a second language:

Speed. A reference integration written in a compiled language would be faster
than the same integration in Python, and the resolution study in issue #55 runs
each case at several timesteps, so the cost multiplies. The mitigation is that
NumPy and SciPy carry the inner arithmetic in compiled code and the reference is
integrated once per case per resolution rather than per engine step. That
mitigation is stated, not measured: no reference integrator exists yet, so
nothing here has been timed. The condition that reopens this decision is written
under "What would change this" below.

Compile-time guarantees. mypy is a checker over annotations, not a compiler, and
a Python program with a clean type check can still be given an array of the wrong
shape or a quantity in the wrong units. Shape and unit errors in the numerical
core are therefore caught by tests and by the case validation in issue #32, not
by the type checker, and issue #25 decides how strict the checker is rather than
whether it substitutes for those.

## The report assembly

The same means again. The report assembly reads result records and writes text
and data files, which is the least demanding of the three layers and the one with
the weakest case for a toolchain of its own. Giving it a second means would add
every cost listed below to the layer that benefits least.

## What a second language would cost

Named so that if it is ever added, it is added knowingly. Against the same four
requirements:

Refusable properties. A second test runner, a second linter and a second coverage
story, so the gate command in issue #20 has two sets of parts to report on rather
than one, and a part that silently fails to start in the second toolchain is a
new way for the gate to pass while covering less.

Commands behind claims. A second version-recording route in the result record of
issue #10, because a record that names one toolchain's versions and not the
other's cannot explain a disagreement that came from the other.

A stock runner. A second toolchain installed in CI, which is a second thing that
can be unavailable for a platform, and the wheel table below already shows this
project has platform gaps without one.

One documented install step. Two toolchains is two steps, or one step that
installs a compiler, which is the same thing with the cost hidden.

No surface in this tree forces a second means today. The surface most likely to
force one later is the inner loop of the reference integrator. If it does, the
smallest form is a compiled kernel behind the same interface the pure-Python
integrator already has, with the pure-Python one kept as the thing the kernel is
tested against, and not a rewrite of the numerical core. That is the shape to
argue for, not a general permission.

## The interpreter floor

CPython 3.12, and the floor is where the packages put it rather than where a
preference put it:

    for p in mujoco pybullet dartpy drake genesis-world numpy scipy; do curl -sS --max-time 25 "https://pypi.org/pypi/$p/json" | python -c "import json,sys; d=json.load(sys.stdin)['info']; print(d['name'], d['version'], d['requires_python'])"; done
    mujoco 3.11.0 >=3.10
    pybullet 3.2.7 None
    dartpy 6.19.4 >=3.7
    drake 1.55.0 >=3.12
    genesis-world 1.3.2 <3.14,>=3.10
    numpy 2.5.1 >=3.12
    scipy 1.18.0 >=3.12

The current releases of NumPy, SciPy and Drake each require 3.12 or later, and
this decision builds the numerical core on the first two. Nothing measured here
argues for a floor lower than 3.12, and a lower floor would mean holding those
three at older releases for no stated gain.

There is a ceiling in the same output and it is worth reading before it is met.
The current release of genesis-world excludes 3.14, so an environment that
installs it is 3.12 or 3.13 today. The interpreter on the machine this was
measured from is above that ceiling:

    python --version
    Python 3.14.6

That is not a defect in the floor. It means an environment that has to hold
genesis-world cannot be created from the interpreter that happens to be on the
host, and the pinned interpreter in issue #19 is what settles which version the
suite actually runs on. Which engines are in scope at all is issue #16, so this
document records the constraint and does not resolve it.

The floor is a sentence in a document and nothing refuses a change that breaks
it. PROSE, NOT ENFORCEMENT, issue #19, which is where the pinned interpreter and
the lock file that would refuse a drifting environment are owed.

## Where it runs

The engines do not all ship a wheel for every platform, which decides where the
gate runs rather than being a detail of it:

    for p in mujoco pybullet dartpy drake genesis-world; do curl -sS --max-time 25 "https://pypi.org/pypi/$p/json" | python -c "
    import json,sys
    d=json.load(sys.stdin)
    t=sorted({f['filename'].removesuffix('.whl').split('-')[-1] for f in d['urls'] if f['packagetype']=='bdist_wheel'})
    print(d['info']['name'], d['info']['version'], ' '.join(t))"; done
    mujoco 3.11.0 macosx_11_0_arm64 manylinux_2_27_aarch64.manylinux_2_28_aarch64 manylinux_2_27_x86_64.manylinux_2_28_x86_64 win_amd64
    pybullet 3.2.7 manylinux_2_17_x86_64.manylinux2014_x86_64
    dartpy 6.19.4 macosx_15_0_arm64 manylinux_2_27_x86_64.manylinux_2_28_x86_64 win_amd64
    drake 1.55.0 macosx_15_0_arm64 manylinux_2_34_aarch64 manylinux_2_34_x86_64
    genesis-world 1.3.2 any

Linux on x86-64 is the only platform every one of these publishes a wheel for, so
that is where the full run happens. On Windows, mujoco and dartpy install and
pybullet and drake do not, so a contributor on Windows runs the numerical core,
the case validation, the report assembly and the adapters whose engine installed,
and reports the rest as not run rather than as passed. That split is exactly the
distinction issue #20 asks the gate command to print, and it is the reason that
requirement is not decoration.

The genesis-world wheel is tagged `any`, which says the distribution is pure
Python and says nothing about what it loads at import time. Not evaluated on this
route.

## The layout this decision implies

One installable Python distribution, with the packages at the top of the tree
rather than under a `src/` directory, and the data directories beside them:

    adapters/    one package per engine, each importing exactly one engine
    cases/       case definitions, as data
    metrics/     the metric estimators
    reference/   the reference integration
    report/      the report card assembly
    results/     result records, as data
    runner/      case plus engine plus configuration to a result record
    tests/       the suite that runs anywhere
    docs/        documents, including this one

The reason for a flat layout rather than `src/` is that four of those directories
are data a reader should be able to find, cite and reuse without installing
anything, and burying `cases/` and `results/` inside a package directory to
satisfy a packaging convention would make the least code-like part of this project
the hardest to reach. The cost of the flat layout is the one that convention
exists to prevent: with the repository root on the import path, a test can import
the working tree instead of the installed distribution and an install-time defect
goes unnoticed. The answer is that the distribution is installed into the
environment and the suite is run against the installed package, which is a
property of the gate command in issue #20 and of the clean-clone route in issue
#28, and neither is decided here.

The layout is not invented here. It is the one every open issue on this tracker
already names, and choosing anything else would have made those Scope lines point
at a tree that does not exist:

    gh issue list -R iderex/pruefstand --state open --limit 200 --json number,body --jq '.[] | "\(.number) \(.body | capture("(?m)^Scope: (?<s>.*)$").s)"' | awk '{print $2}' | sort | uniq -c | sort -rn
         32 docs/
         16 .github/workflows/
         14 .
         12 cases/
          9 reference/
          9 adapters/
          8 metrics/
          7 report/
          4 runner/
          3 results/
          2 tests/
          1 README.md

Every open issue carries a Scope line, and none of them names a path outside that
set:

    gh issue list -R iderex/pruefstand --state open --limit 200 --json number,body --jq '.[] | "\(.number) \(.body | capture("(?m)^Scope: (?<s>.*)$").s)"' | grep -vE ' (\.|docs/|cases/|adapters/|reference/|metrics/|runner/|report/|results/|tests/|\.github/workflows/|README\.md)$' | wc -l
    0

That command is the whole check on the last condition in #4, and its bound should
be read: it compares the Scope line of each open issue against the set above. It
does not read paths written in the prose of an issue body, and it says nothing
about issues opened after it ran. Creating the directories and refusing an import
that crosses between them is issue #18. PROSE, NOT ENFORCEMENT until then: today
nothing in this tree refuses a file written into a directory this document did not
name.

## What is not decided here

- The pinned interpreter version, the lock file and the dependency floors: #19.
- The one command that runs the gate, and what it prints: #20.
- The formatter and linter configuration, and the suppression rule: #24.
- How strict the type checker is: #25.
- Which engines get an adapter at all: #16, which is itself provisional on entry 3
  of #1.
- The licence, which decides whether any of this may be redistributed: entry 1
  of #1.

## What would change this

The means is reconsidered, in writing and not silently, if any of these becomes
true:

- The reference integration at the resolutions issue #55 needs cannot be run in a
  time an operator will accept, measured rather than estimated. The measurement
  that would show it is the wall-clock leg of #46.
- An engine that the first release has to cover has no Python route at all, so the
  adapter layer's forced means stops being forced for that engine.
- The single-toolchain claim in this document turns out to cost more in pinning
  than two toolchains would, which would show up as issue #19 being unable to
  produce a lock that resolves on the platforms named above.

None of the three has been measured. They are stated so that reopening this is a
recorded event with a trigger, rather than a preference expressed later.
