# The configuration procedure

This answers issue #5. It names the position taken on how an engine is
configured, writes the procedure out in enough detail to be applied by somebody
who did not write it, requires the full effective configuration in every result
record, states what happens when an engine has no setting the procedure names,
and names where a configuration that the procedure would not have produced is
refused.

It does not decide the timestep, which is
[resolution-study.md](resolution-study.md) and is deliberately not this
procedure's to choose. It does not decide what physics reaches the engine, which
is [one-description-per-engine.md](one-description-per-engine.md): a case's
contact model is the case's, and this document is about the settings that are
nobody's physics. It does not decide whether a configuration supplied by an
engine's own maintainers may appear at all, which is entry 5 of #1 and is not
assumed anywhere below.

It is written before any adapter exists:

    git ls-files adapters/
    adapters/README.md

## The position

A stated procedure, applied identically to every engine, with the engine's own
defaults carried as one labelled point rather than as a second column.

The issue offers three positions and the third, both as two full columns, doubles
the run matrix. It is not taken, because most of what it would buy is already
bought. The resolution study runs the engine's own default timestep as a labelled
seventh point beside the six-rung ladder, so the question of what a person gets
when they install the engine and use it is answered at the axis where the answer
differs most, without a second study.

What the defaults column would still have carried is the engine's own solver
settings at the default timestep, and that is added to the same labelled point:
the default point is run at the engine's defaults throughout rather than at the
procedure's settings. One extra run per case per engine, against a doubled
matrix.

Defaults alone is not taken either. It measures what a person gets, which is a
real question and is the one the labelled point answers, and as the only position
it reports several engines as worse than they are while giving their maintainers
an objection this project cannot answer.

## The procedure

Applied per engine, per case, per rung. It takes no input that is not in that
triple and the engine's own version, which is what makes it a function rather
than a habit.

1. Read the engine's effective configuration as the engine reports it, after
   construction and before the run. Not from its documentation, which is a
   statement about a version that may not be the installed one, and not from the
   adapter's own record of what it set, which is the thing being checked.

2. Set the integrator or solver family to the engine's own documented most
   accurate option, by the name the engine uses. The documentation version this
   name was read from is recorded beside it, so a later reader can see which
   document the choice came from.

3. Set the solver iteration count, where the engine has one, to the value the
   resolution study's axis fixes for the run being made. That is the engine's
   default for a timestep-ladder run and one of the three slice values for an
   iteration-slice run.

4. Set the solver tolerance, where the engine solves to one rather than to a
   fixed count, to the engine's documented tightest supported value.

5. Set the timestep from the case's ladder. It is the only setting this procedure
   does not choose, and it is stated here as a step so that the omission is
   visible rather than looking like a gap.

6. Leave every remaining setting at the engine's default, and record all of them.
   Not touching a setting is a decision, and the record carries it as one.

7. Change nothing after seeing a result.

Step seven is the one the issue exists for and it is worth stating why it is
written as a step in a mechanical procedure rather than as a warning. Everything
above is a function of the engine, its version, the case and the rung. The
runner derives that configuration and does not accept one, so there is no
argument through which a hand-set value can enter a run at all, which is a
stronger statement than a rule against setting one. Deriving rather than
accepting is a requirement on #39.

Where a step cannot be carried out, the run is not silently done without it. The
next two sections are what happens instead.

## The timestep is not in the procedure, on purpose

The issue's own example of a procedure was the finest timestep that finishes
within a wall-clock budget. It is not taken, and the reason is that it puts the
two largest levers in one place.

A procedure that chooses both the accuracy settings and the timestep can trade
them against each other, and the trade is invisible from the outside: a coarser
step with a tighter solver and a finer step with a looser one both look like the
procedure being applied. Splitting them means the timestep comes from the case's
ladder, identically for every engine, and this procedure has no way to move it.

The cost is that an engine which cannot finish the case's finest rung inside the
case's budget produces a reduced study rather than a configuration adjustment,
which is [resolution-study.md](resolution-study.md)'s outcome and carries its own
label. That is the honest place for that fact to appear.

## When an engine has no setting the procedure names

Recorded as absent, and never substituted.

The record carries the procedure's setting name and the statement that this
engine has no corresponding setting. The tempting alternative, mapping the
procedure's setting onto the nearest thing the engine has, is refused for the
reason the whole suite exists to avoid: a nearest-thing chosen per engine is a
judgement made by whoever wrote that adapter, and the differences between engines
then include the differences between those judgements.

    configuration.absent

A list, one entry per procedure step the engine had nothing for, each with the
step, the setting name and the engine's own vocabulary where a related setting
exists and was deliberately not used.

An absence does not refuse the run and it travels with the number. A cell whose
engine had no accuracy setting is `measured`, and the absence is carried with it,
because the engine ran the case and produced a value; what a reader has to know
is that the value is at whatever accuracy that engine does by default. Rendering
it as anything other than measured would be claiming the run did not happen.

The one absence that does refuse is step one. An engine that cannot be asked what
it holds cannot be configured by a procedure that reads back, and a run against
it would be a run whose configuration is what the adapter believes rather than
what is true. That is refused, and the case reports `not attempted` with the
reason.

## The full effective configuration in every record

Every result record carries every setting the engine holds after construction, as
the engine reports it, including the settings the case never mentions and the
settings nobody changed.

Including the unmentioned ones is the point. A hand-set value shows up only as a
value the procedure would not have produced, and that comparison is impossible
against a record that carries only what somebody chose to write down. The
read-back is the same mechanism as #41's, which asks each engine what it actually
did rather than what it was told, and this is one of the things it is asking.

    configuration.effective
    configuration.source
    configuration.absent
    configuration.deviation

The effective set is what the engine reports, by the engine's own setting names.
The source names, per setting, which step of the procedure produced it or that it
is the engine's default. The deviation list is empty for a run the procedure
produced, and an entry in it carries the setting, the value the procedure would
have produced, the value used, why, and what admitted it.

A deviation admitted by nothing is not a deviation, it is the thing this issue
refuses. The `admitted_by` field has no free-text option: it names either the
case, where the case declares the deviation, or the engine's own refusal, where
the engine rejected the procedure's value and reported what it took instead.

## What refuses a configuration the procedure would not have produced

Nothing at this commit. There is no adapter, no runner and no record, so a
hand-tuned configuration is refused today by a reviewer, which is not a
mechanism.

Where it lands, in two parts that are not the same.

The first is that the runner derives the configuration rather than accepting one,
so a hand-set value has no route into a run. That is #39, and it is a property of
the code rather than a check over its output.

The second is the check the issue asks for, which re-derives the procedure's
output from the record's own inputs, being the engine and its version, the case
and the rung, and reds on any difference from `configuration.effective` that the
`deviation` list does not explain. It reads the record and needs no engine, which
is what makes it a check rather than a second run. Its home is #40, whose subject
is refusing a result record that does not describe its own run: a record whose
configuration is not the one its own inputs produce describes a different run
from the one it names. This decision adds that clause to #40's subject, and if
#40 is read more narrowly than that the check needs an issue of its own, which is
said here so the gap is visible rather than assumed closed.

## The means

Markdown in `docs/decisions/`, beside the decisions it is read with. The
procedure above is written as numbered prose rather than as code because the
things it reads, an engine's effective configuration and its documented setting
names, do not exist in this tree and cannot exist until an adapter does. Written
as code it would be a second implementation living in a document, drifting
against the runner that #39 builds, which is the failure this repository already
names against itself. What is checkable is that the steps are stated in an order
somebody else can apply, and the review is where a wrong step is caught.

## What is not decided here

- The timestep and the iteration ladder every run is made at: #11.
- What physics reaches the engine, as distinct from what settings it runs under:
  #3.
- The adapter interface the read-back is made through: #33.
- Asking each engine what it actually did: #41.
- The runner that derives the configuration: #39.
- The record's full field list and what refuses one missing a field: #10, #40.
- Whether a configuration supplied by an engine's own maintainers may appear in
  the report card at all: entry 5 of #1.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree refuses a run whose
settings somebody chose by hand, a record that omits the settings nobody touched,
a nearest-thing substitution for an absent setting, or a deviation admitted by
nobody. The mechanisms are owed and are named at #39, #40 and #41 above.

Two narrower absences, so a later green is not read as covering them. Step seven
is a rule about conduct rather than about an artefact: the derivation in #39 makes
the ordinary route impossible and nothing in a tree can refuse somebody who edits
a record afterwards, which is why records are append-only and why the
re-derivation check reads the record rather than trusting it. And the choice of
each engine's most accurate documented option is a judgement about somebody
else's documentation, so no check can tell a right reading of it from a wrong
one; what is checkable is that the name and the documentation version are
recorded, and the review is where a wrong reading is caught.
