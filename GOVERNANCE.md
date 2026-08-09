# Governance

This answers issue #109. It says who decides, how a change and a case get in,
and what happens when somebody disagrees with a number this project published.

The last one is the reason this exists now rather than after the first report
card. This project publishes statements about other people's software. Some of
the people best placed to find an error in one of those statements maintain the
software it is about, and they are also the people most interested in seeing it
changed. Both of those are true at once and the process has to work with both.

## Who decides

One maintainer, who is the repository owner. There is no committee and pretending
otherwise would be worse than saying it.

A decision that shapes the architecture is written down before the code that
depends on it exists, as a file in `docs/decisions/`, stating what was chosen,
the reason, what was given up and what would change it. That is where a
disagreement about a decision is argued, because arguing with a written reason is
possible and arguing with a preference is not.

Decisions that are the maintainer's and have not been taken are parked in #1,
with the options and what each one costs, and no issue elsewhere assumes an
answer. An issue blocked on one of them names the entry it waits on and stops
there. If something you want to work on is blocked that way, say so on #1 rather
than working around it.

Disagreement about a decision that has been taken goes on the issue that took it,
with what changed since. The decision notes each carry a line saying what would
change them, and that line is the shortest route to a reversal.

## How a change gets in

Every change starts as an issue and lands as a pull request. An issue says what
is wrong, what the evidence is, and what done means, and where the evidence is a
number it carries the command that produced it. The same rule applies to the
change: an assertion in a pull request body carries the command behind it, run at
the commit being pushed.

The gate is one command and it is the same one everywhere:

    python -m gate

Every commit carries a `Signed-off-by:` trailer matching its author, which is the
Developer Certificate of Origin, and `.github/workflows/dco.yml` refuses a commit
without one. `git commit -s` writes it.

Two things a contributor is pointed at do not exist:

    git ls-files DCO CONTRIBUTING.md | wc -l
    0

The sign-off check's own failure message names `CONTRIBUTING.md` and `./DCO`, so
somebody who trips that gate is sent to two files that are not in this
repository. It is recorded here rather than fixed here, because the fix belongs
to whoever lands the contributor documentation, and a governance document that
quietly described a route nobody can follow would be the more expensive mistake.

## How a case gets in

A case is a stricter contribution than a change to the code, because a case that
is wrong produces numbers that look right about somebody else's software.

What a case carries is fixed by
[the case file format](docs/decisions/case-file-format.md) and is not restated
here. What governance adds to it is provenance: the parameters come from a source
that is named, the physical statement is in physical terms rather than in any
engine's parameters, the tolerance carries the derivation that justifies it, and
the reference answer carries its bound. A case whose parameters were invented is
a case whose result cannot be argued with, and #111 is where the check that
refuses a case with no provenance is owed.

A contributed case is reviewed for the physics before it is reviewed for the
format. The format is the cheaper of the two to check and it is not the one that
produces a wrong number.

## How a disputed number is handled

The route and the procedure are in [SECURITY.md](SECURITY.md), under reporting a
wrong number and what a correction does to the published artefact, and they are
referenced rather than repeated so that there is one statement of them. In short:
a disagreement is an issue with the evidence in it, the answer is a correction
with its reason or a refusal with its reason, and either way the command is
behind it. A published number is never edited in place.

What this document adds is who may raise one, which is anybody, and what is asked
of them, which is the same thing that is asked of this project.

## Conflict of interest

Somebody who maintains an engine this project has published a result about may
dispute that result, and should. Excluding them would remove the best-informed
reader this project has.

The position is that the evidence standard does not move. A dispute is answered
on its evidence: which case, which engine and version, which configuration, the
command, the number produced and the number published, and the machine it ran on.
That is the same list this project holds its own numbers to. A report from an
engine's maintainer is not given extra weight because they know the engine, and
it is not given less because they have an interest in the answer.

The interest is stated rather than managed. Where a dispute is raised by somebody
with an interest in the outcome, the interest is named in the issue, by them or
by the maintainer, and it stays visible in whatever comes out. A reader weighing
a correction needs to know who asked for it. Naming an interest is not an
accusation and it does not weaken the report; a correction that is right is right
whoever asked for it.

The same rule points back at this project. This project has an interest in its
own numbers being correct and a smaller one in them being interesting, and the
second is the one to watch. A result that is dropped, softened or left unpublished
after a dispute is recorded as such with the reason, exactly as a corrected one
is.

Money is the other place an interest can arrive from, and whether this project
takes any, and by what route, is entry 8 of #1 and is not decided here. Whatever
is decided, a funder with an interest in a published number is disclosed or
refused, and that is the entry's own wording rather than this document's.

## What happens when this project is wrong

It is corrected visibly. The procedure is the one in
[SECURITY.md](SECURITY.md), which publishes the correction as an addition, leaves
the superseded number readable and marked, and says what was wrong, how it was
found and what else the same mistake could have reached. It is referenced here
and not restated, because two statements of a correction procedure drift and the
drift is found by whoever followed the wrong one.

A correction never becomes a quiet improvement.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree reads it. The
sign-off half is refused by a workflow and that is the only mechanism named here;
everything else is a person following a written rule. No check notices a case
without provenance, no check notices an undisclosed interest, and none could read
the second one at all. #111 holds the provenance half.
