# Parity with the reference gate

This answers issue #86. It records, element by element, whether this repository
adopts, adapts or drops what the reference gate requires, and what this
repository needs that the reference has no counterpart for.

Parity is not copying. The reference gate is for a plugin loaded into somebody
else's process, in another language, shipped through a package catalogue. This is
a numerical benchmark suite whose output is published numbers about other
people's software. Some of it does not apply, some applies differently, and some
of what this project needs is not there at all.

This is a record of a comparison made at one commit, not a live list. Both sides
move. Re-run the commands rather than quoting the outputs back later.

## The two rulesets, at this commit

The reference gate, github.com/Flowfin/jellyfin-plugin-sso, which is public and
whose ruleset is readable:

    gh api repos/Flowfin/jellyfin-plugin-sso/rulesets --jq '.[] | select(.name=="Protect main and 5.0") | .id'
    18802863
    gh api repos/Flowfin/jellyfin-plugin-sso/rulesets/18802863 --jq '{enforcement, bypass: .bypass_actors, required: [.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context]}'
    {"bypass":[],"enforcement":"active","required":["build","ABI floor build","Package (JPRM) / Build package","Package (JPRM) / Generate SBOM","CodeQL","Analyze (csharp)","DCO sign-off","Deterministic PR-hygiene checks","Enforce greppable invariants","Reject Trojan Source Unicode","Audit workflows (zizmor)","prettier","dependency-review"]}

This repository:

    gh api repos/iderex/pruefstand/rulesets/20521019 --jq '{enforcement, bypass: .bypass_actors, types: [.rules[].type]}'
    {"bypass":[],"enforcement":"active","types":["deletion","non_fast_forward","pull_request"]}

`required_status_checks` is absent from the second output. So no check gates a
merge here at all, and the distance is the whole list rather than some of it.
That is the state this document is measured against and it is not softened
anywhere below: every "adopted" row means an issue is open for it, not that it
gates today. Asking for the list is #27.

What does run here, unrequired, on the mainline commit this document was written
against:

    gh api "repos/iderex/pruefstand/commits/$(git rev-parse HEAD)/check-runs" --jq '[.check_runs[].name] | unique | join(", ")'
    Audit workflows (zizmor), Reject Trojan Source Unicode, Scorecard analysis, gate

That is the set a push to the mainline produces. It is not the set a change
produces: two of the six workflows run only on a pull request, so the list above
is shorter than what a merge is actually preceded by, and neither list is
required by anything.

The issue that opened this work quoted five workflow files. There are six now:

    git ls-files .github/workflows
    .github/workflows/dco.yml
    .github/workflows/dependency-review.yml
    .github/workflows/gate.yml
    .github/workflows/scorecard.yml
    .github/workflows/unicode-guard.yml
    .github/workflows/zizmor.yml

`gate.yml` arrived with #20 after that quote was taken. The drift is small and it
is the reason this document pastes command output rather than restating it.

## The required checks, one row each

Each row names the delivering issue in this repository. Every issue number
written anywhere in this document exists on this tracker, derived from the file
rather than asserted:

    gh issue list --state all --limit 300 --json number --jq '.[].number' | sort -u > /tmp/exist.txt
    grep -oE '#[0-9]+' docs/reference-gate-parity.md | tr -d '#' | sort -u > /tmp/named.txt
    wc -l < /tmp/named.txt
    26
    comm -23 /tmp/named.txt /tmp/exist.txt | wc -l
    0

An empty second output is the whole claim. It says every number named resolves;
it does not say the issue named is the right one for the row, which is a
judgement and is what a reader of this document checks.

`build`. Adapted. The reference compiles a plugin; this project's equivalent of
"it builds" is the gate command, which is #20 and has landed, plus the
distributable and its bill of materials, which is #29.

`ABI floor build`. Adapted, to a different dependency. The reference proves it
still builds against the oldest host version it claims to support. Here the
oldest thing claimed is an engine version rather than a host ABI, and #97 is
where that floor lives.

`Package (JPRM) / Build package`. Dropped as a route, adapted as an idea. Nothing
here is published through a plugin catalogue, so the catalogue packager goes; the
requirement that a distributable is built reproducibly stays and is #29.

`Package (JPRM) / Generate SBOM`. Adapted. The bill of materials is #29 for the
build side and #105 for the notices an operator reads. Split because the two
readers are different: one is a supply-chain tool, the other is a person deciding
whether they may run this.

`CodeQL` and `Analyze (csharp)`. Adapted. The second is the first's per-language
job, so they are one element and the language is the thing that changes. #87.

`DCO sign-off`. Adopted unchanged, and it already runs here in `dco.yml`. The
argument for it does not depend on the language or on what is published.

`Deterministic PR-hygiene checks`. Adopted. #93.

`Enforce greppable invariants`. Adapted, because the invariants differ. The
reference greps for its own rules; the rules here are about engine imports,
tolerance literals, aggregation across classes and pinned actions, and #92 holds
them.

`Reject Trojan Source Unicode`. Adopted unchanged, already running here in
`unicode-guard.yml`. The attack does not care what the source compiles to.

`Audit workflows (zizmor)`. Adopted unchanged, already running here in
`zizmor.yml`. Workflow YAML is attack surface in any language.

`prettier`. Adapted to whichever formatter this project's language uses, which is
#24. The argument was adopted rather than adapted and is written in that issue:
what a formatter buys is that a diff shows the change and nothing else, which is
what makes reviewing numerical code possible.

`dependency-review`. Adopted unchanged, already running here in
`dependency-review.yml`.

## The elements that do not gate there either

Derived from the reference gate's own workflow directory rather than from
memory:

    gh api repos/Flowfin/jellyfin-plugin-sso/contents/.github/workflows --jq '.[].name'

The coverage bar. Adapted, and the subject is what changes. The reference pins a
high line bar on the modules that decide security outcomes rather than on the
whole codebase:

    gh api repos/Flowfin/jellyfin-plugin-sso/contents/scripts/check-coverage.py --jq .content | base64 -d | grep -n 'SECURITY_LINE_BAR' | head -1
    68:SECURITY_LINE_BAR = 92.0

Here the code that decides an outcome is the reference integration, the metric
estimators and the report assembly, and #89 is where the bar and its subject are
pinned. The number is not carried over; a bar copied from another repository's
risk surface is a number with no derivation.

Mutation testing, reporting rather than gating. Adopted with the same posture.
#90.

Fuzzing and property-based testing. Adapted to the surfaces that read other
people's bytes, which here are the case file reader and the result record reader
rather than an authentication callback. #91.

The end-to-end login harness. Adapted. Its counterpart is the set of tests that
need a real engine, which #22 named and separated and which the gate reports as
not run when no adapter is present.

The second analyser with a different lens. Adopted. #88.

The documentation lint. Adopted. This project is mostly documents, so it has more
to gain from it than the reference does. #94.

The manifest freshness and manifest regeneration jobs. Dropped. They exist to
keep a plugin catalogue entry in step with a release, and there is no catalogue
here.

The publish and beta-publish jobs. Adapted into the release route, which is #112
for what a version number promises, #113 for reproducibility from a tag and #114
for signing and publishing the artefacts.

Scorecard. Adopted unchanged, already running here in `scorecard.yml`.

The language's own test and lint job. Adapted into the one gate command, #20,
with the type checker at #25 and the formatter at #24.

## What the reference gate does not require, and this repository does

The reference ruleset carries four rule types:

    gh api repos/Flowfin/jellyfin-plugin-sso/rulesets/18802863 --jq '[.rules[].type]'
    ["deletion","non_fast_forward","required_status_checks","pull_request"]

Verified signatures are not among them. So #96 is an addition here rather than an
adoption, and it is argued on this project's own grounds: the artefact this
project publishes is a set of numbers about other people's software, and a commit
nobody can attribute is a poor foundation for that.

Reproducibility of a published number as a gate. #99. The reference gate has no
counterpart because its output is a binary, and a binary that behaves is a
different claim from a number that comes back the same. This is the deviation
upward, and it is the one that most justifies the whole comparison.

A refusal of aggregation across classes. #17 makes the refusal of a single score
a design constraint and #92 is where the pattern that refuses it would live. The
reference gate has nothing of the kind because it publishes no scores.

A floor under a green over nothing. #30, partly landed. Every collecting part of
the gate declares a minimum and fails below it. No required check name on the
reference gate corresponds to this, from the output pasted above; whether that
gate has the property by some other route was not evaluated here.

A proof that every test runs with no display, no elevation and no special
hardware. #98. The reference has an end-to-end harness that needs a running
service; what it does not have, and what a suite publishing numbers needs, is the
audit that says every test is in exactly one of two sets.

A refusal of a reference answer carrying no error bound. #49. There is nothing to
compare it against, because the reference gate publishes no measurements.

The engine version floor. #97, listed above as the adaptation of the ABI floor
check, and repeated here because it is also an addition in substance: the thing
being floored is somebody else's release cadence rather than a platform.

## The mark

PROSE, NOT ENFORCEMENT. Nothing reads this document. It records a comparison and
does not enforce one, no check notices when either ruleset moves underneath it,
and every "adopted" row above describes an open issue rather than a running
check. #27 is where the required list is asked for on this side, and until that
lands the whole of this document describes intent.

There is a second thing to say about this file rather than to leave for somebody
to notice. #92 carries a candidate rule that no document enumerates the checks,
because a list in a document is a second source of truth that drifts. This
document is an enumeration of checks. The difference it relies on is that every
list in it is pasted command output with the command above it, taken at one
commit and dated by that, rather than a list written from memory; the drift note
about five workflows against six is that difference doing its work. Whether a
pattern check can tell a pasted output from a hand-written list is a bound #92
has to decide, and it is named here rather than discovered there.
