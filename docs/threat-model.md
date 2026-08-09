# Threat model

This answers issue #107. A benchmark suite looks like it has nothing to defend,
which is the reason to write this down rather than the reason not to.

Written at a point where most of what it describes does not exist yet. That is
deliberate and it is also its main limitation: several surfaces below are
undefended because they are absent, and absence is not a defence. Each one says
which it is.

## What is worth defending

The published numbers, and the trust somebody places in them. This project's
output is statements about other people's software. A number that is wrong, or
that changed without anybody noticing, is a failure of the thing this project
exists to produce, and it is worth more to an attacker than anything else here.

The reference trajectories and their bounds. Every published number is a
comparison against them, so an error there is invisible in every comparison that
uses it and is not detectable by looking at the engines.

The case definitions. They are meant to be reused by people who never run this
code, including by engine maintainers inside their own test suites, so a case
that has been altered travels further than this repository.

The operator's machine. Running this suite means running large native libraries
on inputs taken from a repository, which is a different exposure from reading a
document.

## Who would want to change one

Not a single adversary, and the interesting ones are not the loudest.

Somebody with an interest in a specific number. An engine's maintainers, a
competitor of theirs, or a party citing the result in an argument. What they want
is a number moved or a case removed, not a machine taken over, and moving a number
is quieter than breaking anything.

Somebody who wants code execution on the machines of people who run this. The
audience is researchers and engine developers, and the route is a case file or a
result record rather than a binary.

Somebody inside the dependency chain, which for this project eventually includes
the engines themselves. A change to a numerical library that alters a result in
the fifth digit is the highest-yield and lowest-noise attack available against
this project specifically.

And the adversary who is not one: a contributor who lands a case that is wrong.
The outcome is the same, the intent is not, and the defences are largely the
same, which is why they are counted here.

## The surfaces, and what stands behind each

**A case file from an untrusted source.** The point of publishing case definitions
is that other people write them, so the reader is a parsing surface and the runner
computes physics from a file somebody else wrote. There is no reader:

    git ls-files '*.py'
    gate.py
    tests/test_document_links.py
    tests/test_gate.py
    tests/test_gate_workflow.py
    tests/test_greppable_invariants.py
    tests/test_package_boundaries.py
    tests/test_two_test_sets.py
    tests/test_workflow_pipefail.py

So the surface is absent rather than defended. What will stand behind it when it
lands is the schema and the reader that returns a validated case or an error and
never a partially populated one, which is #31; the physics validation, which is
#32; and fuzzing, which is #91. The path handling is worth naming separately: a
case identifier reaches a filesystem path, and a case identifier is attacker
controlled.

**A result record from an untrusted source.** Only reachable if results computed
elsewhere are ever accepted, which is entry 2 of #1 and is the maintainer's. Every
issue in the plan assumes they are not. If that changes, this surface is a claim
about a measurement that this project would republish under its own name, which is
a trust problem the provenance work reduces and cannot remove, and the entry says
so itself.

**The published numbers, against a change nobody notices.** Undefended today and
nothing is published yet. The regression guard is #83, the reproducibility rerun
is #99, and the raw results that make a change diffable are #84. Until they exist
a number that moved would be found by somebody rerunning it themselves.

**The dependency chain.** The suite's own dependency surface is currently empty:
it is written against the standard library, and the only declared manifest is the
one that says what a hardware harness needs rather than what the suite imports.
What the workflows pull is not empty and is pinned to commit hashes:

    grep -hoE '^\s*(-\s+)?uses:\s*\S+' .github/workflows/*.yml | sed 's/.*uses:[[:space:]]*//' | sort -u
    actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
    actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294
    actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97
    actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a
    astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9
    github/codeql-action/upload-sarif@e4fba868fa4b1b91e1fdab776edc8cfbe6e9fb81
    ossf/scorecard-action@2d1146689b8cda280b9bc96326124645441f03bc

A reference that is not a commit pin is refused by
`tests/test_greppable_invariants.py`, and the near-miss it is built against is a
shortened hash, which looks pinned and is not. `zizmor.yml` installs its analyser
by version at run time rather than by digest, which is a gap in the same class and
belongs to #95 along with the lock file and the engine digests. Dependency review
runs on every pull request and gates nothing, which is the next section.

**The engines.** The dependency whose change matters most, the largest, the least
inspectable, and the one loaded into the same process as everything else. Nothing
verifies an engine download against a recorded digest today; #95 is where that
lands, and #19 is where the engine versions get a manifest separate from the
suite's own so that updating a linter and updating an engine do not look the same
in a diff.

**The operator's machine.** Engine code executes in the same process as this
project's code, which is the arrangement every one of these libraries expects and
is not something this project can change. What reduces the exposure is that the
suite that runs anywhere needs no engine at all, which is already true and is what
the gate reports when it says the engine part did not run. Headless execution is
#21 and is not built. The network is refused, in `no_network.py`, as a property of
the process that runs the tests rather than as a rule somebody follows, and its
reach is stated where it is implemented: it covers connection and name resolution
through the socket module, and it does not reach a child process or a call that
leaves by another route. What an engine fetches on first use is therefore a
register in `tests/test_no_network.py` that reds when an adapter lands without an
entry, rather than something this refusal observes.

**The repository itself.** The ruleset refuses a direct push and a force-push to
the mainline and requires a pull request, with no bypass actors. It requires no
status check, so every workflow here may red without stopping a merge, and it does
not require verified signatures. Both are measured in
[the checks this repository asks to gate the mainline](requested-gate-checks.md),
which is also where the request to change it is written. The sign-off gate runs
and asserts authorship rather than proving it.

**The workflow definitions.** Release-critical in any project that has a release,
and audited by `zizmor.yml` at low severity and above, which also uploads its
findings to code scanning. It gates nothing, for the same reason as everything
else above.

**Tracked text, against source that reads differently from how it executes.**
`unicode-guard.yml` refuses bidirectional overrides, isolates, marks and
zero-width characters, and fails closed on a scanner error rather than reading a
broken scan as a clean tree. It gates nothing.

## What is not defended, plainly

An engine that detects this suite and behaves differently while it is being
measured. It is possible, it would be undetectable from inside a run, and no
amount of provenance in a record would surface it. The honest response is to say
so rather than to imply a guarantee. What reduces the value of doing it is that
the case definitions and the reference trajectories are published, so somebody can
run the same case from outside this project, which is a reason #51 and #84 are
worth more than they look.

Every guard in the list above, today. None of them is a required check, so each is
advice that a merge may ignore. That is one setting and it is the maintainer's,
and until it changes this document describes intent wherever it names a workflow.

A case that is wrong rather than malicious. Nothing refuses a case whose physics
is wrong but whose shape is right, and #32 is where the physics half lands. Until
then a wrong case is caught by a reviewer, and a wrong case produces a wrong
number about somebody else's software, which is the outcome this whole document is
about.

The identity of a contributor beyond their own assertion. The sign-off says the
author asserted the origin of their work. It is not evidence, and verified
signatures are not required, which is #96.

The maintainer's account and machine. Anything that reaches either reaches
everything here, and nothing in this repository can defend against that.

An engine's own vulnerabilities. This suite points unusual inputs at large native
libraries and will eventually find one. That is theirs to fix and this project's
to report, and [SECURITY.md](../SECURITY.md) has the route and the rule that
nothing is published here about it, including the case that triggers it, until
their process has run.

## Revisiting this when a new surface arrives

#107's fourth done-when asks that a new input surface force this document to
change, enforced by a check over the directories that hold readers. It is not
met.

The directories that would hold them are `cases/`, `results/`, `report/` and
`runner/`, and every one of them holds a README and nothing else. The shape of the
check already exists in this tree: `tests/test_greppable_invariants.py` carries
entries whose subject does not exist yet, naming the directories that would be
their subject, and the suite reds the day one of them holds Python. A rule
requiring this document to name a reader is another entry of exactly that kind,
which makes it a pattern over the tree, which puts it in #92's register rather
than in a document under this issue's declared scope of `docs/`.

So it is owed and it is named, here and in #107, and until it lands this document
is revisited because somebody remembered.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing reads it. Every defence it names
is a workflow that gates nothing or an issue that has not landed, and the one
mechanism that would make the document itself hard to forget is the entry
described above, which is not written. The distinction this document is most at
risk of blurring is between a surface that is defended and one that is absent, and
each entry states which of the two it is for that reason.
