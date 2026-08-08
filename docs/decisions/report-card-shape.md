# The shape of the report card

This answers issue #17. It fixes the axes of the report card and what a cell
contains, names the four states a cell can be in and a rendering for each that
cannot be confused with another, declares the machine-readable form the primary
artefact with the rendered page derived from it, names where that direction is
enforced and where aggregation across classes is refused, and states the one
place this shape waits on a decision that is not its own.

It does not decide which metric a class is judged by, which is #7, nor how a
metric's uncertainty is stated, which is #15. It does not decide whether the card
carries a verdict word about a named engine, which is entry 6 of #1 and is
discussed below without an answer being assumed.

It is written before any result exists:

    git ls-files results/ report/
    report/README.md
    results/README.md

## What the shape has to survive

Four readers, and they pull in different directions.

Somebody deciding whether an engine can be trusted for one class of system, which
is the question people actually have and the reason the card is organised by
class at all.

Somebody choosing an engine for one specific system, who needs the individual
case rather than the class.

An engine's own maintainers, who will disagree with a number and need to reach
the case, the full configuration and the run behind it without asking anyone.

A machine, because the results are more useful as data somebody recomputes from
than as a page somebody screenshots.

The fourth is the one that decides the architecture, and it is why the ordering
below is what it is.

## The axes

Rows are cases. Columns are engines. Cases are grouped by class, and the group is
a heading rather than a row.

A class is not itself a row, and the argument for that is the same one that
refuses a single score, one level down. A class-level cell would have to combine
the cases in its class into one entry, and there is no combination that survives
what a class actually contains. The `qualitative` class holds whether a tippe top
inverted and how many times a rattleback reversed. Those have no common scale, no
common unit, and no defensible weighting between them, so a class cell would be
either a number with an invented weighting or a word standing in for one.

The same argument applied one level up is the refusal of an overall score, which
is the constraint the issue starts from and which
[what-this-is-not-for.md](../what-this-is-not-for.md) already states as a
property of the output. Making it structural rather than a rule is what this
decision is for: there is no field to put an overall score in, so refusing one is
not a matter of anybody remembering.

The card therefore has exactly one kind of cell, at one place: the intersection
of a case and an engine.

Two further axes exist inside that cell rather than beside it. The resolution
study of #11 gives every cell a curve rather than a point, and the configuration
of #5 gives it a set of settings. Neither becomes a column, because a table with
a column per rung is a table nobody reads; both are carried in the cell's own
record and reached from it.

## What a cell contains

Every cell carries, whatever state it is in:

The case it belongs to and the engine it belongs to, by identifier and by
version, so that a cell lifted out of the table on its own still says what it is
about.

A pointer to the run behind it, resolving to the result record, which carries the
full configuration, the machine, the suite's own commit and the reference with
its bound. That is the thing the third reader above needs and it is the reason it
is a required field rather than a convenience.

A state, one of the four below.

Whatever that state requires, and nothing else. The states do not share fields
they do not both mean.

## The four states

Named as the issue names them, each with a rendering that a reader cannot mistake
for another, and each with a required distinguishing mark that is not a colour,
because a card read in one colour, printed, or quoted as text has to keep the
distinction.

### measured

A number was produced and it is a measurement.

The cell carries the metric value, its unit, the uncertainty terms of #15 kept
separate rather than combined, the convergence conclusion of #11 and the study
kind, and the sign or direction the metric of #7 requires where it has one.

Rendered as the value with its unit and its uncertainty, followed by the study
kind where the study was reduced. A reduced study's number never appears without
that label, which is #11's requirement and is repeated here as a rendering rule
because this is the place it is most likely to be dropped.

### bounded

No value was established, but the metric is known to lie on one side of a number.

This is the state the reference produces when its own error bound is not smaller
than the case's tolerance, and the state an estimator produces when it returns an
interval rather than a point. The honest reading is that the engine is at least
this good, or at worst this bad, and no more.

Rendered as an inequality and never as a number: `< 3e-6` and not `3e-6`. A bound
rendered as a value is the single easiest way for this project to publish
something it did not measure, because the two look identical once somebody copies
them into a table of their own.

### refused

The run did not happen, and the reason is a property of the pair.

This is the state of a case refused for an engine at compilation, which is the
mechanism in
[one-description-per-engine.md](one-description-per-engine.md), and of a metric
the case's class does not admit, which is the trajectory-comparison refusal in
[metric-per-class.md](metric-per-class.md).

Rendered as the word refused, the situation, and the case field that could not be
carried. It is never rendered as a failure, a zero, or a worst-case value, and it
may not be ordered against a measured cell in either direction. An engine that
cannot express a non-holonomic constraint has told you something real about what
it is for and nothing at all about how accurately it would integrate the case if
it could.

### not attempted

No run exists, and the reason is not a property of the pair.

The engine was not installed on the machine that produced the card, the budget
ran out, the case is newer than the last full run, or nobody has got to it. Each
of those is a fact about this project rather than about the engine, and the cell
says which.

Rendered as the words not attempted and the reason. It is never rendered as an
empty cell, a dash, a blank, or anything else that a reader's eye passes over.
This is the state the issue is really about: an empty cell reads as an absence of
a problem and it is an absence of a measurement, and those are opposite
statements. So the renderer emits no cell without a state, and a case and engine
pair with no record is `not attempted` with the reason `no record`, rather than a
gap in the table.

## The machine-readable form is the primary artefact

The card is a data file. The page a person reads is generated from that file and
from nothing else.

The ordering is the decision, not a preference about formats. A page written
first and a data file exported afterwards is a data file nobody checks, whose
fields drift from the page, and whose first serious use is by somebody who finds
out it disagrees. Making the page derived means the data file is exercised by
every render.

The direction is enforced by re-rendering. The check regenerates the page from
the data file at the commit being pushed and refuses a difference against the
published page. A page edited by hand, a number corrected in the page and not in
the data, and a renderer whose output has moved without the data moving all red
the same way, and the failure message is a diff. That check belongs to #81, which
is where the renderer lands, and the guard against the published numbers moving
for any other reason is #83.

Nothing enforces it at this commit. There is no data file, no renderer and no
page, so the direction is held today by this document and by a reviewer, which is
not a mechanism.

## What refuses an aggregation

The check reads the card's data file and refuses any field whose value is a
function of more than one class. That is the whole rule and it is checkable
because the data file's shape makes the dependency visible: a cell names one case,
a case names one class, and a field that is not inside a cell and not one of the
declared header fields is an aggregation by construction.

It refuses an overall score per engine, a per-class score, a rank, a count of
classes passed, and a percentage. It refuses them by shape rather than by name, so
a new name for the same thing is refused too, which is the point of putting the
rule on the structure rather than on a list of forbidden words.

That check belongs to #80, whose subject is already refusing an assembly it
should not make, and it is the second thing that issue refuses beside an assembly
from mismatched runs. Nothing refuses it at this commit, for the same reason as
above.

The one aggregation that is not refused is counting: how many cells in a class
are in each of the four states is a statement about this project's coverage
rather than about an engine, and it is required rather than merely allowed,
because a class where most cells are `not attempted` and the rest are measured is
a class whose measured cells are easy to over-read. It is rendered beside the
class heading and never inside a cell.

## What this waits on

Entry 6 of issue #1 asks whether the report card ever uses a verdict word about a
named engine, and it is open. This document does not assume an answer and does
not need one to be written, which is deliberate: the shape above is the same
under all three of that entry's options.

If the answer is numbers only, nothing here changes. If it is numbers with a
stated mechanical verdict per class, the verdict is a field computed from the
cells of that class by a published rule, which is an addition to the data file
and a rendering beside the class heading, and it is the one aggregation across
cases within a class that this document would have to admit. If it is a written
assessment per engine, that is prose beside the card rather than a field in it,
and the card is unchanged.

No field for a verdict exists in the shape above, and none is reserved. Reserving
one would be assuming the answer quietly, which is what the entry exists to stop.

## The means

Markdown in `docs/decisions/`, beside the decisions it is read with. This
document argues a shape rather than implementing one, so it is prose, and the
artefact it decides about, the data file itself, has its means chosen where it is
built rather than here: #79 is the result store and #84 the published raw
results, and each answers the means question for what it writes. Naming the
format here would be choosing it for two issues from the outside and carrying it
over from habit, which is exactly what the means check exists to stop.

## What is not decided here

- Which metric each class is judged by, and what a cell's value is a value of:
  #7.
- How the uncertainty terms are stated and which are bounds: #15.
- The result store and its schema: #79.
- Assembling the card and refusing a mismatched assembly: #80.
- The renderer, the page and the re-render check: #81.
- Provenance on every number down to the command: #82.
- Guarding the published numbers against silent movement: #83.
- The published raw results as data: #84.
- Whether a verdict word is used at all: entry 6 of #1.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree refuses an
aggregation, a hand-edited page, a bound rendered as a value, or an empty cell,
because there is no data file, no renderer and no page. The mechanisms are owed
and are named at #80 and #81 above.

One absence is narrower and is named so a later green is not read as covering it.
The rule that refuses aggregation reads the card's own data file, so it says
nothing about a table somebody else builds by copying cells out of it. A
published number that has lost its state, its uncertainty or its study kind on
the way into somebody's slide is outside every mechanism this project can have,
and the only thing that reduces it is that each cell carries enough to be quoted
alone.
