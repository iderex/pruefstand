# Sovereignty

This answers issue #101. It states the position, says what personal data means
in a benchmark suite, says what deliberate federation means, and puts each claim
next to the mechanism that makes it true or marks it as a claim.

The position, in one sentence:

**Nothing about the operator or the operator's machine leaves that machine unless
the operator takes an explicit action to send it.**

The rest of this document exists because that sentence is worth nothing on its
own. A statement about where data goes is either falsifiable or it is
advertising, and the difference is whether anything in the tree refuses the
opposite.

## What personal data means here

The temptation for a benchmark suite is to say there is none. There is.

A result record identifies the machine it was produced on, because reproducing a
number needs to know what produced it.
[The run record](decisions/run-record.md) is where those fields are fixed, which
of them identify a host, and which are removed before anything is published. That
list appears there and not here: two statements of one list drift, and the one
that matters is the one the scrub reads. The scrub itself is #103.

Beyond the record, three things carry a person and are worth naming because they
are easy to forget:

A file path in a log or a traceback carries a user name. This suite writes no log
today and a traceback is printed rather than stored, so there is nothing to
scrub yet and nothing to promise about it either.

The commit history carries the names and addresses of everybody who has
contributed. That is ordinary for a public repository and it is deliberate: the
sign-off gate requires each commit to carry a `Signed-off-by` line matching its
author, so the identity is the point of the field rather than a leak. Nothing
removes it and nothing should.

A result computed on somebody else's machine and submitted here would carry all
of the above from that machine. Whether results are ever submitted from elsewhere
is not decided, and it is entry 2 of #1.

## What deliberate federation means

One thing only. The operator takes an explicit action whose purpose is to send a
result somewhere.

It is not a default. It is not a setting that ships enabled. It is not a prompt
with an answer already filled in. It is not an update check that happens to
reach a server, and it is not a first-run fetch of an asset that an engine
performs inside a call that looks local, which is the shape this project is most
likely to meet.

Nothing in this repository federates anything today, because there is nothing to
send and nothing that could send it:

    git ls-files results/ runner/ report/
    report/README.md
    results/README.md
    runner/README.md

## The claims, each with what stands behind it

**The suite that runs anywhere makes no outbound network call.** This is the one
claim with a mechanism rather than an argument. `no_network.py` replaces the
outbound calls on `socket.socket` and the whole of name resolution in the process
that runs the tests, and `tests/test_no_network.py` installs it before any test
runs and shows it refusing a connection, a datagram and a name lookup. Deleting
the install reds nine tests and takes the run from 2.3 seconds to 69.9 seconds,
because an outbound call that is not refused does not fail, it waits.

Its reach is stated where it is implemented and is repeated here because a
sovereignty statement is the wrong place to overclaim. The refusal lives in that
process and not in the kernel, so a child process is not covered, and it covers
what goes through `socket`, so an extension module opening its own descriptor is
invisible to it. An engine is the most likely thing to take that second route,
which is why what an engine fetches on first use is a register in
`tests/test_no_network.py` that fails closed rather than an assurance here.

**No result is transmitted anywhere.** A claim, and true for the reason that
there is no result and no transmitter, shown by the command above. It becomes a
mechanism when there is something to refuse, which is #102.

**No telemetry of any kind is collected.** A claim. What supports it is that the
suite imports nothing outside the standard library, which is measurable, and that
the one standard library module capable of reaching the network is the one the
refusal above replaces. What it is not is a check that would refuse telemetry
added tomorrow.

**The only outbound connections a run makes are the ones an operator asked for.**
A claim, and today an empty one: there is no dependency to fetch and no engine to
install, so a run makes no outbound connection of any kind. The honest version of
this sentence arrives with the first engine, and what it will have to say is what
that engine does on first use.

## What this repository's own automation does, which is not what an operator runs

Worth separating, because a reader who finds uploads in the workflow files and no
mention of them here would be right to distrust the rest.

The workflows in this repository run on this repository's changes, on a hosted
runner, and two of them send something outward: the workflow auditor and the
supply-chain scorecard upload their findings to code scanning. That is analysis
of this repository's own text, it happens on a machine the operator does not own,
and it is not part of anything an operator runs. An operator who clones this
repository and runs the gate triggers none of it.

## The test that guards the central sentence

`tests/test_no_network.py`. It is the only thing in this tree that refuses the
opposite of the sentence at the top, and it guards the part of it that exists:
the suite makes no outbound call, so nothing about the machine can leave through
one. It does not guard a runner, a result store or a publication route, because
there are none, and #102 is where the guard over those lands.

## The mark

`PROSE, NOT ENFORCEMENT` for everything except the first claim.

The first claim is enforced, by name, by the test above. The rest are claims in
the sense this project uses the word: statements true today for a reason that is
visible in the tree, with nothing refusing the change that would make them false.
That is a weaker thing than a mechanism and it is written as the weaker thing.

Two absences, so a later green is not read as covering them. Nothing refuses a
new outbound route added to this suite outside the socket module. And nothing
places this statement in front of an operator before they run anything, which is
this issue's fourth done-when: the README is where that lands and it is being
rewritten under #110.
