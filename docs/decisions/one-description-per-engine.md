# One description, and how it reaches every engine

This answers issue #3. It fixes that a case is authored once rather than per
engine, what the compilation target is, what happens at each of the four edges
where a case and an engine do not fit, which fields carry a substitution or a
refusal into the result record, and what a reader may conclude from a case that
one engine was refused and another was run.

It does not decide how a rolling constraint is asked of an engine that cannot
express it, which is #12, nor which engines exist to compile for, which is #16
and waits on entry 3 of #1. It does not fix the adapter interface, which is #33,
nor the fields of the result record beyond the ones named here, which is #10. It
does not decide the configuration procedure, which is #5.

It is written before any adapter exists. At the commit this note landed in,
`adapters/` holds a README and nothing else:

    git ls-files adapters/
    adapters/README.md

    git ls-files cases/
    cases/README.md

That ordering is the point. The first adapter written without this decision
makes every part of it silently, and the second adapter copies whatever the
first did.

## The decision

One case file describes the physical system, and each engine is given that
description through the adapter that owns it. Nothing in this tree ever holds a
second description of the same system.

The reason is the one the issue states and it is worth keeping in the artefact.
A hand-written scene per engine makes every difference between two results a
difference between two scenes as much as between two engines, and the report
card then measures whoever wrote them. That failure is invisible in the output:
two scenes that differ in a contact stiffness produce two plausible numbers and
no error.

## The compilation target

The target is the engine's own construction calls, made in process by its
adapter, and not a scene file in a format the engine reads.

The engines under consideration accept text scene descriptions of their own, and
compiling into those is the route that looks tidiest: a file per engine per
case, diffable, inspectable, and reviewable beside the case it came from. It is
refused for three reasons.

A scene format is a second artefact that has to be kept in step with the case,
which is the cost the case file format note refuses for the same reason under
[case-file-format.md](case-file-format.md). A case regenerated and a scene file
not regenerated is a run against a stale description with a correct-looking
provenance.

A scene format is lossy in a direction nobody controls. What an engine's text
format can express is a subset of what its API can express, and the subset
differs per engine, so choosing the text route imports a second and undeclared
expressiveness boundary on top of the real one.

A scene format hides the substitutions. The whole of the next section is about
knowing exactly what an engine was told, and a text file written by this project
and read by the engine puts a parser this project does not own between the two.

What the API route costs, stated rather than glossed. There is no artefact a
reviewer can read to see what an engine was given, so what a reviewer reads is
the record instead, which is why the departure fields below are required rather
than advisory. And the construction calls are version-sensitive in a way a text
format partly is not, so an engine version floor becomes load-bearing, which is
#97.

The compilation is per engine and it lives in that engine's adapter package.
`adapters/README.md` already says an adapter holds no physics and no decision
about what a case means, and this note is what that sentence is protecting: the
translation is mechanical, and every place it cannot be mechanical is one of the
four situations below with a stated response.

## The four situations

The issue names four edges and three possible responses, which are refuse the
case for that engine, substitute and record the substitution, and let the engine
do what it does and record what it was told. Choosing once for all four is what
makes the answer indefensible, so each is answered separately.

### The engine cannot express what the case requires

Refuse, unless the case itself admits a named substitution.

An adapter that meets a constraint it cannot build and approximates it has made
a modelling decision, in the one place in this tree least able to argue for it,
and the result is then published as that engine's answer to that case. It is not
that engine's answer to that case. It is that engine's answer to a different
case that the adapter invented.

The route that is not a refusal is the case admitting the substitution in
advance: the case names the approximation it will accept, names the evidence
that the approximation was honoured, and the run carries that evidence. The
standing example is ideal rolling asked of an engine that has only friction, and
what evidence counts there is #12's to decide, with the slip measurement in #64.
This note fixes only the shape: the admission is in the case, never in the
adapter, and a case that admits nothing is refused rather than approximated.

Refusing is a statement about the pair rather than about the engine. The same
engine runs every case whose requirements it can meet.

### The engine can express it only through a parameter with no counterpart elsewhere

Substitute and record, and accept that the run is faithful and incomparable at
the same time.

Faithfulness wins here, because the alternative is worse in a way that is easy
to miss. Making two engines comparable by asking both a question neither was
built to answer produces two numbers that can be put in a row and that describe
nothing. The case was written to be a piece of physics, and an engine that can
carry that physics through an unusual parameter has carried it.

What is lost is the ordering between that cell and its neighbours, and that loss
is recovered by the record naming the parameter, so a reader comparing two cells
can see that the two runs are not the same experiment. A reader who is not shown
this compares them anyway.

### The engine has a default for a quantity the case never mentions

Refuse, and refuse the case rather than the engine.

This is the only one of the four where the fault is on this side. A quantity
that changes the answer and that the case does not set is a hole in the case,
and the engines are not disagreeing about it so much as each filling it in
differently. Publishing the spread as a difference between engines would be
publishing this project's own omission as somebody else's defect.

So the compilation refuses a case that leaves unset any quantity for which any
target engine carries a default, and the refusal names the quantity and the
engine whose default would have decided it. The list of such quantities is the
union over the engines rather than the intersection, which has a cost worth
stating plainly: adding an engine can red a case that has been green for a year,
because the new engine has a default for something nobody had to think about.

That cost is accepted and the direction is deliberate. A red on the day an
engine is added is a question asked once, in the open, by somebody who is already
looking at the case. The alternative is the same case silently acquiring an
uncontrolled variable, and a published number that moved for a reason nobody
recorded.

The effective configuration that every record carries, which is the other half
of this, is #5's, and it is a different thing from this refusal: #5 is about the
settings the procedure chose, this is about the physics the case forgot.

### The engine silently clamps or rounds a value the case gave it

Let the engine do what it does, and read back what it holds.

Nothing at compilation time can know this happened, so neither refusing nor
substituting is available at the moment of the write. What is available is
asking afterwards. After construction and before the run, the adapter reads back
every quantity the case set, compares it against what the case said, and a
difference beyond a stated tolerance refuses the run rather than reporting it.
That mechanism is #41 and this note is the requirement it implements.

The clamp is the failure this whole issue exists to prevent. An engine that was
never told the value the case specified, whose result is then published as that
engine's answer to that case, is a wrong number wearing a correct provenance,
and it is wrong in the direction that flatters the engine, because a clamped
value is usually a value clamped into the range the engine is stable in.

Where an engine offers no read-back for a quantity, the run is not refused and
the record says the quantity was not read back. That is a negative disclosure
and it stays negative: not read back is not the same statement as read back and
agreed, and the record has to be able to say the first without it looking like
the second.

## What the result record carries

Each of the responses above is worth nothing if it does not reach the record, so
the fields are named here rather than left to the record's own design. These are
requirements on #10 and #40 rather than a schema, and #37 is where the adapter
side of them lands.

A run that was refused still produces a record. This is the part that is easy to
get wrong: a refusal that produces no record is an absence, an absence renders
as an empty cell, and an empty cell reads as no problem found. The record for a
refusal carries no metric value and carries the reason instead.

    run.outcome

One of `ran` and `refused-at-compilation`. Nothing else, and no third value that
means partly.

    refusal.situation
    refusal.field
    refusal.why

Present exactly when `run.outcome` is `refused-at-compilation`. The situation is
which of the four above it was, the field is the case field that could not be
carried, and the why is a sentence naming what the engine could not express or
which quantity the case left unset.

    [[departure]]
    kind
    field
    asked
    given
    why
    admitted_by

Zero or more, on a record whose outcome is `ran`. The kind is one of
`substitution`, `unmatched-parameter`, `clamped` and `not-read-back`. The
`asked` and `given` fields carry the value the case stated and the value the
engine holds, which for `not-read-back` means `given` is absent rather than
equal to `asked`. The `admitted_by` field names the case's own admission for a
`substitution` and is absent for the other three, so a substitution nobody
admitted cannot be written down as though somebody had.

A record with an empty `departure` list is a record asserting that the engine
holds exactly what the case said, on every quantity the case set. That is a
strong claim and it is the one this project wants to be able to make.

## A case refused for one engine and run for another

The reader concludes that the first engine could not be asked the question. Not
that the second engine is better, and not that the first engine got it wrong.

Those are different statements and only the first is supported. An engine with
no non-holonomic constraint that is refused the Chaplygin sleigh has told you
something real about what it is for, and it has told you nothing about how
accurately it would integrate the sleigh if it could express it. Reporting the
refusal as a failure would be reporting the second thing.

So the report card is required to render a refused cell as refused, carrying the
situation and the field from the record, distinctly from a cell that was
measured and distinctly from a cell nobody attempted. Three states that a reader
must not be able to confuse, and #17 is where the four cell states and their
renderings are fixed. This note adds one constraint to that issue: a refused
cell may not be ordered against a measured one, in either direction, because
there is no order between them.

## The means

Markdown in `docs/decisions/`, beside the two decisions already there, because
the artefact is an argument a person reads and holds a later change against.
Nothing here is a program, so the means carries the three rules in the only way
prose can: the claims about the tree above are commands, and the claims about
what an engine does are written as claims. The mechanisms this document asks for
are named at the issues that own them rather than asserted here, and the section
below is where that is recorded rather than implied.

## What is not decided here

- How ideal rolling is asked of an engine that has only friction, and what
  evidence counts that the approximation was honoured: #12.
- Which engines are compilation targets at all: #16, which waits on entry 3
  of #1.
- The adapter interface these compilations are written against: #33.
- The full field list of the result record, and what refuses one that is missing
  a field: #10 and #40.
- The read-back mechanism and its tolerance per quantity: #41.
- The configuration the engine is run at, as opposed to the physics the case
  states: #5.
- The four report card cell states and how each is rendered: #17.
- The engine version floor that the API compilation route makes load-bearing:
  #97.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree refuses an adapter
that writes a scene file, an adapter that approximates a constraint the case did
not admit, a compilation that runs a case with an unset quantity, or a record
that omits a departure, because there is no adapter, no compilation and no
record. Every mechanism this note asks for is owed, and each is named above at
the issue that owes it.

One absence is narrower than the rest and is named separately so a later green
is not read as covering it. Nothing checks that the departure fields above and
the record schema in #10 agree once both exist. That is the same drift
[case-file-format.md](case-file-format.md) names against itself, and it has the
same repair, which is that the schema is the authority and this document is
corrected against it rather than the other way round.
