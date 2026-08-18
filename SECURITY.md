# Security policy

There are two kinds of problem in this project and they are reported by
different routes. Sending one down the other route is not a mistake anybody
should have to avoid, so both are written out below.

A vulnerability in this software is the ordinary kind. A case file that executes
something when it is parsed, a path traversal through a case identifier, a result
record that does something unpleasant when it is read.

A wrong published number is the other kind, and it is the more likely one. This
project publishes numbers about other people's software, so a number that is
wrong is a defect in the thing this project exists to produce.

## Reporting a vulnerability

Use this repository's private vulnerability reporting, on the Security tab, which
opens a private advisory only the reporter and the maintainer can read. It is
enabled:

The form is here, without navigating:

<https://github.com/iderex/pruefstand/security/advisories/new>

    gh api repos/iderex/pruefstand/private-vulnerability-reporting
    {"enabled":true}

Do not open a public issue for a vulnerability. Do not send a proof of concept
into the issue tracker.

What to expect. An acknowledgement within seven days. An assessment within thirty
days saying whether the report is accepted, and if it is, what the fix is and
roughly when. If the report is not accepted, the reason, in enough detail to
argue with.

Those are targets rather than guarantees. This is a small project with nobody on
call, and a report that arrives while nothing is happening waits. Saying so here
is better than a promise a reporter finds out is empty.

What happens after. An accepted report gets a fix, a published advisory naming
the versions affected, and credit to the reporter unless they ask otherwise. A
report that turns out to describe intended behaviour gets that written down,
because the next person will report it again.

## Reporting a wrong number

A number in the report card that you can show is wrong is not a security issue
and should not go through the route above. It also should not have to become an
argument before it becomes a correction.

Open an issue with the `bug` label and put the evidence in it: which case, which
engine and version, which configuration, the command you ran, the number you got,
the number the report card carries, and the machine you ran it on. A number
without the command that produced it cannot be checked, and this project holds
its own numbers to that rule, so it holds a disagreement to the same one.

If you would rather not be public before there is an answer, use the private
route above and say in the first line that this is a number and not a
vulnerability. It will be moved.

The response is a correction with the reason, not a patch. Either the number
moves and the correction says why, or it does not and the answer says why not,
with the command behind it either way.

## What a correction does to the published artefact

A published number is not edited in place. The failure that rule exists against
is a reader who quoted a number, came back, found a different one, and has no way
to tell whether it was corrected or has always been that.

So a correction is an addition. The corrected number is published as a new
version of the result data and the report card. The superseded number stays
readable, marked as superseded, and carries what replaced it. A correction note
says what was wrong, how it was found, what changed and what else the same
mistake could have reached, and it is dated. Anything derived from a superseded
number, including the rendered page, is regenerated from the corrected data
rather than edited to match.

A correction never turns into a quiet improvement. If the old number was wrong,
the record says it was wrong.

No number is published yet. This procedure is written before the first one rather
than after the first disagreement, which is the only time it can be written
without a result in view. Guarding the published numbers against movement that
nobody announced is #83, and publishing the raw results as data so a correction
is diffable is #84. Until those land, the procedure above is what a person
follows and no check refuses a departure from it. PROSE, NOT ENFORCEMENT, and #83
is where the mechanism is owed.

## A vulnerability in an engine

This suite runs other people's physics engines and points unusual inputs at them.
Something it finds may be a defect in an engine rather than in this project.

That is theirs to fix and this project's to report responsibly. It goes to that
engine's own security process first, at whatever address they publish. Nothing is
published here about it, including the case that triggers it, until their process
has run or they decline to run one. If an engine publishes no security process at
all, the report goes to their public tracker after a reasonable wait, and the
wait is recorded.

While that is outstanding, a case withheld for this reason is recorded here as
withheld, with the date and the engine, and without the detail. An absent case
that says nothing about why is indistinguishable from a case nobody wrote, and
those are different statements.

This project publishes no exploit for anybody else's software.

## Scope

This policy covers this repository. It does not cover the engines, which have
their own maintainers and their own policies, and it does not cover anything an
operator builds on top of the results.

Nothing here is a warranty. See [NOTICE.md](NOTICE.md) for the intended-use
notice.
