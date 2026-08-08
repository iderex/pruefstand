# What a run records

This answers issue #10. It fixes the fields a result record carries and the
question each one answers, decides which of them identify the host and what
happens to those before anything is published, and names the checks that would
refuse a record with a required field it could not fill.

It does not choose the record's encoding or the store schema, which is #79. It
does not build the runner that writes one, which is #39, nor the check that
refuses one, which is #40, nor the scrub between the local record and the
published one, which is #103.

It is written before any run exists:

    git ls-files runner/ results/
    results/README.md
    runner/README.md

That ordering is the point of the issue. A record designed after the first runs
is a record assembled from whatever turned out to be convenient to log, and the
fields nobody thought to write are the ones a disputed number needs.

## The decision

One record per run, complete on its own, and no blanks.

Complete on its own means a reader holding one record can say which case at which
version, which engine at which version, which configuration was in force, which
reference it was compared against, what the machine was, what the suite was, what
the metric value is and what it was computed from. Not by resolving a pointer
into a store that may not travel with the record, and not by knowing which
directory it was found in.

No blanks means every required field is present in every record. A field that
could not be filled carries a value saying why, from a fixed vocabulary, and is
never empty and never zero. A missing field and a measured zero are opposite
statements, and the second one is usually a finding.

One record per run is the part that decides the rest. A run is one case, one
engine, one configuration, one rung of the resolution ladder, once. Everything
that is a property of a set of runs belongs to whatever assembles the set, and
the section on the resolution study below is where that bites.

## Most of the field set was fixed elsewhere, and is not restated here

Five decisions already fix parts of what a record carries, and each of them
states its part better than a summary would. They are referenced rather than
copied, because two statements of one field set drift and the drift is found by
somebody who trusted the wrong one.

The configuration in force, in full, including every setting the case never
mentioned and every setting nobody changed, with the absences and the deviations:
[configuration-procedure.md](configuration-procedure.md).

What happened when the engine could not be told something the case said, and the
record a refused run still produces:
[one-description-per-engine.md](one-description-per-engine.md).

The uncertainty terms, kept separate, each present on every metric value, with a
term that does not apply carrying the statement that it does not apply:
[uncertainty-reporting.md](uncertainty-reporting.md).

The resolution study and the convergence conclusion:
[resolution-study.md](resolution-study.md).

What the reference answer is per class and how far it is trusted:
[reference-answer-and-trust.md](reference-answer-and-trust.md).

## One run or one cell, and which one carries the study

[resolution-study.md](resolution-study.md) puts `study.kind`, the rung list, the
default point, the iteration slice and the convergence fields on the record. A
rung list is a property of a set of runs, and a single run sits at one rung, so
the two readings of the word record differ by whether it means one run's record
or the set behind one cell of the card.

This decision takes the first reading, and the consequence is stated rather than
left to be discovered. A record carries the rung it was run at and nothing about
the other rungs. The study and convergence fields are computed over the set of
records for one case and one engine, and they are carried by the assembly, which
is #80, and rendered by #17's cell.

The reason is that a set-level fact written onto every member can disagree
between members, and there is then no rule for which copy is right. It also makes
the study derivable from the records rather than asserted beside them, so a
record that was excluded from an assembly cannot leave a stale rung list behind
in the ones that were kept.

If the other reading was meant, the repair is a field on the assembly rather than
on the record, and it is #80's. Naming which reading this document takes is what
stops both from being assumed at once.

## The fields this decision fixes

Required unless the entry says otherwise. The second half of each entry is the
question the field answers, because a field nobody knows the question for is a
field that gets filled in to satisfy a schema.

### The file

`format`, an integer. The version of this record format.

It has to be readable without parsing the rest of the record, which is a
requirement on the encoding #79 chooses. A record from a format a reader does not
implement is refused by version, naming the version, rather than failing on the
first key that is not there. That is #40's last done-when and it only works if
the version is read first.

`id`, a string, unique in the store.

What #17's cell points at and what a published number resolves through, which is
#82. It is assigned rather than derived from the record's content. A
content-derived identifier would give two repeats of one run the same identifier,
and repeats differing in nothing but their outcome are exactly what #15's
run-to-run term is measured from, so deriving it would delete the measurement.

### `[case]`

`id`, `format`, `content_hash`, `rung`.

Which case, at which version of the case file, against which exact file, and at
which point of the ladder.

The hash is over the parsed content rather than over the file bytes, so
reformatting a case file is not a physics change and does not orphan every number
that names it. #31 defines the hash. Raising a case file's `format` does change
the hash, and what that means for published numbers is already decided in
[case-file-format.md](case-file-format.md).

### `[engine]`

`id`, `version`, `build`, `libraries`.

Which engine, at which version, built how, and what else was loaded that could
change a floating-point result.

The version and the build identifier come from asking the engine after
construction, never from a package manifest, which is #26's second done-when and
the same read-back the configuration procedure's first step makes. An engine that
cannot be asked what it is produces no measured record at all: that is the one
absence the configuration procedure refuses, and the case reports not attempted
with the reason.

`libraries` is the inventory of loaded native modules with their versions, taken
after the run rather than before. An engine can load a backend on first use, so
an inventory taken before the run misses exactly the library that decided the
result.

What this cannot do is stated so the field is not read as more than it is. The
inventory is what the process reports it has loaded, and a library loaded and
unloaded inside the run is not in it.

### `[reference]`

`id`, `version`, `bound`, `bound_units`.

Which reference the value was compared against, at which version, and with which
error bound.

A reference answer carrying no bound is refused by #49, and the field is here so
the refusal has something to read. Where the bound is computed with the run
rather than stated in advance, the field carries the computed value and says so,
which is the case [case-file-format.md](case-file-format.md) already allows a
case to declare.

### `[machine]`

`os`, `os_version`, `architecture`, `processor`, `isa_advertised`, `isa_targeted`,
`accelerator`, `threads`.

What the machine was, in the terms a reader uses to explain a difference between
two hosts.

`threads` is the thread count the engine actually ran with. A parallel reduction
over floating-point numbers is order dependent, so two runs on one host that
disagree cannot be explained without it, and #14's promise about determinism is a
promise about a population this field defines.

`accelerator` says whether anything ran on a graphics device and which one, or
carries the statement that nothing did.

The two instruction-set fields are the subject of the next section.

### `[suite]`

`commit`, `tree_clean`, `gate`.

What this project itself was when the number was produced.

`tree_clean` is what makes a number publishable or not. A record from an unclean
tree names a commit that does not describe the code that ran, and #82 refuses
publication of one.

`gate` carries which parts of the gate ran, which did not, and why, in the words
the gate command already prints. A record asserting that the suite was green
without saying which parts ran is the same defect the gate itself refuses, and
recording only an exit status would reintroduce it one artefact later.

### `[invocation]`

`argv`, `base`.

The command that reproduces the run.

It is the argument vector rather than a shell string. A shell string is a second
parser between the record and the reproduction, and the quoting is where the
attempt fails and the number gets called irreproducible. `base` is the placeholder
the paths in `argv` are relative to, never an absolute path, for the reason in the
next section.

### `[metric]`

`quantity`, `units`, `value`, `estimator`, `estimator_version`, `raw`,
`sample_interval`.

What was measured, what it came out as, what computed it, and what it was
computed from.

`quantity` and `units` are the case's own, from its `[measured]` table. Which
quantities a class admits at all is #7.

`estimator_version` is required because #80 refuses an assembly whose cells came
from different estimator versions, and a changed estimator moves a number without
moving the run.

`raw` is the quantities the value was computed from. This is the field most
likely to be dropped as bulk and it is the one that decides whether a corrected
estimator costs a recomputation or a re-run of every engine. Without it, fixing an
estimator invalidates every published number it produced.

`sample_interval`, with the sampled series or with the summary computed from it,
is a requirement [drift-sign-and-shape.md](../../metrics/drift-sign-and-shape.md)
places on this issue: none of the signed rate, the oscillation amplitude or the
opening ratio can be recovered from a conserved quantity's endpoints, so a record
carrying only the start and end values makes that measurement impossible on runs
already made.

The uncertainty terms are #15's five fields. They are required on every metric
value and they are not restated here.

### Timing

Not a new field. The duration is `cost.wall_clock_seconds` from
[resolution-study.md](resolution-study.md), which is per rung and therefore per
run under the reading above.

What this document adds is `date`, and its coarseness is in the next section.

## The host, and what leaves it

This is the decision the issue says belongs here rather than in the legal
milestone, and it is decided by asking one question of each field: can a reader
explain a number with it.

Kept, because a reader cannot interpret a disagreement between two hosts without
them: the processor model, the instruction-set fields, the architecture, the
operating system family and version, the thread count and the accelerator.

Removed or replaced, because they identify a machine or a person and explain
nothing about any number: the host name, the user name, absolute paths, and clock
time finer than a day.

The split falls exactly there and not by taste. Every kept field is one a reader
computes with. No number in this project is explained by whose machine it was or
by what time of day somebody ran it, and a full set of second-resolution
timestamps across a long run describes when a person was at their desk.

So `date` is a date. The record carries the day, not the clock time. The local
record may carry more, because the scrub runs on the way out rather than on the
way in and the operator's own record stays complete for the operator's own
debugging. #103 implements the scrub and its list is this list.

### The instruction-set fields, and what neither of them is

The issue asks for the extensions actually used. Nothing here measures that, and
the honest response is two fields and a sentence rather than one field that would
be read as an answer.

`isa_advertised` is what the machine reports it supports. `isa_targeted` is what
the engine's build says it was compiled for, from asking the engine, which is the
same read-back as its version.

Neither is what executed. A build compiled for a wide set dispatches at run time
on what it finds, an engine that reports nothing about its build leaves the second
field carrying that statement, and no route in this project observes the
instruction actually issued.

The consequence is stated rather than left implied: two hosts whose advertised and
targeted sets agree and whose numbers disagree are a disagreement this record
cannot explain, and #14's promise may not be written as though it could. Recording
both fields narrows where the explanation is. It does not supply one.

## No blanks, and what a field carries when it cannot be filled

A required field that could not be filled carries a value from a fixed vocabulary
saying why. Three such vocabularies already exist and this document adds no
fourth: the absent list in [configuration-procedure.md](configuration-procedure.md),
the outcome and refusal fields in
[one-description-per-engine.md](one-description-per-engine.md), and #15's
statement that a term does not apply.

Every field above takes the same treatment. The rule is that the record says which
of three things is true of a value: it was measured, it does not apply here for a
stated reason, or it could not be obtained for a stated reason. Writing a zero, an
empty string or nothing at all collapses those three into one, and the third is the
one a reader most needs to see.

Where the thing that could not be obtained is the engine's own identity or its
effective configuration, there is no record with a metric value at all. The run is
not attempted or refused, in the vocabulary
[report-card-shape.md](report-card-shape.md) fixes, and the record it produces
carries the reason instead of a number.

## The list above is a second source of truth, and it is temporary

This document fixes the fields, so today it is the source. When #79 lands the
store schema, the schema is the authority for which fields exist and this document
keeps the reasons and points at it for the list.

Between now and then there are two statements of the field set and they can drift.
That is a defect this document creates rather than one it inherits, it is the shape
`restated-not-referenced` names, and #79 is what closes it. Naming it here is not
the same as fixing it.

## What refuses an incomplete record

Nothing at this commit, said plainly because the issue asks for the check to be
named rather than assumed. There is no writer, no store and no reader:

    git ls-files runner/ results/
    results/README.md
    runner/README.md

At this commit a record with a blank required field is refused by a reviewer,
which is not a mechanism.

Where it lands, in three parts that are not the same. The runner writes a record or
fails, and does not write a partial one, which is #39 and is a property of the code
rather than a check over its output. The store schema refuses a record whose
required fields are not all present, which is #79. The check that reads a record
and refuses one whose fields disagree with each other, including a configuration
that is not the one its own inputs would produce, is #40, and
[configuration-procedure.md](configuration-procedure.md) already adds that clause to
it.

This issue declares `Scope: docs/`, so the check it names is written elsewhere by
construction. This document can name it and cannot be it.

## The means

Markdown in `docs/decisions/`, beside the decisions it is read with.

The field set is written as named prose rather than as a schema. A schema here
would be a second declaration of the same fields, in a file no route reads,
drifting against the one #79 lands, which is the failure this tree already names
against itself. What is checkable is that each field is stated with the question it
answers, and the review is where a wrong field is caught.

The record's encoding is deliberately not chosen. A case file is TOML because a
person writes it and a schema refuses it, which is
[case-file-format.md](case-file-format.md)'s argument. A record is written by a
program and read by a program, so the trade is a different one, and answering it
here would be choosing #79's means from outside it.

## What is not decided here

- The record's encoding, the store schema and what refuses a record whose required
  fields are absent: #79.
- The runner that writes one, and the derivation that leaves no route for a
  hand-set configuration: #39.
- The check that refuses a record whose fields disagree: #40.
- The scrub between the local record and the published one: #103.
- What is published, at what size, and what is dropped: #84.
- The content hash of a case file: #31.
- Units, frames and the inertia parameterisation, and therefore what any number in
  a record means: #13.
- Which engines are in scope, and therefore the population every field above is
  filled for: #16.
- Which quantity each class is judged by: #7.
- What determinism this suite promises, which is a statement about the fields above
  rather than a field: #14.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree reads it and nothing
refuses a record that departs from it, because there is no record and no reader to
refuse one. The mechanisms are owed and are named at #39, #40 and #79 above.

Three narrower absences, named so a later green is not read as covering them.
Nothing checks that the field list above and #79's schema agree once both exist,
which is the drift this document names against itself. Nothing checks that the
fields kept about the host are the ones #103 keeps, so the two lists can part
without anything noticing. And the reading taken above, that a record is one run
rather than one cell, is stated in two documents that no route compares, so a
divergence between this one and [resolution-study.md](resolution-study.md) is
found by a person or not at all.
