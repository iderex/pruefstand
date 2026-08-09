# Code of conduct

This answers part of issue #109. It covers this repository: its issues, its pull
requests, and anything else this project runs.

## What is expected

Argue with the work. A number, a method, a case, a document and a decision are
all things somebody can be wrong about, and saying so with the evidence is the
whole activity here. Disagreement is not a problem to be managed.

Bring the evidence. This project holds its own numbers to the rule that an
assertion carries the command that produced it, and it asks the same of a
disagreement. That is a standard about the argument and not about the person
making it, and it is the only standard applied.

Assume the other person is trying to get it right. Most wrong numbers here will
come from a case configured badly rather than from anybody's bad faith, and the
first response to a surprising result is to check this project's own work.

## What is not

Contempt for a person rather than an argument with their work. Harassment,
sustained or otherwise. Personal attacks, insults, and comments about somebody's
identity rather than their claim. Publishing somebody's private information.
Persisting with unwelcome attention after being asked to stop.

One thing is specific to what this project does. A published result saying that
a named piece of software gets a named physical system wrong is a measurement,
and it is not a verdict on the people who wrote that software. Writing it as one
is a breach of this document, and so is treating somebody who arrives to dispute
a result as an opponent rather than as the best-informed reader available.

## Reporting

Not the issue tracker. Use this repository's private vulnerability reporting, on
the Security tab, and say in the first line that this is a conduct report rather
than a vulnerability. It is enabled:

    gh api repos/iderex/pruefstand/private-vulnerability-reporting
    {"enabled":true}

That opens a private advisory that only the reporter and the maintainer can read.
It is a security channel used here for want of a separate one, which is stated
plainly rather than dressed up: the route is private and it is not purpose-built.

The limit of it is worth saying rather than leaving somebody to discover. There
is one maintainer and they are the only recipient, so a report about the
maintainer has no route inside this repository. GitHub's own abuse reporting is
outside this project and does not depend on the maintainer, and that is the route
in that case. This project cannot fix that gap from inside itself and does not
claim to have.

## What happens after a report

An acknowledgement, an answer saying what was decided and why, and where
something is asked of somebody, what is asked. If a report is not upheld, the
reason, in enough detail to argue with.

No timescale is promised. This is a small project with nobody on call, and a
report that arrives while nothing is happening waits. Saying so is better than a
promise a reporter finds out is empty, and it is the same thing
[SECURITY.md](SECURITY.md) says about a vulnerability report for the same reason.

What can actually be done here is limited to this repository: a comment can be
removed, a change can be refused, and somebody can be blocked from the
repository. Nothing here reaches further than that and no wording in this
document should be read as though it did.

## Why this is not a standard text

The Contributor Covenant is what a reader expects at this path, and it is not
what is here. The reason is that a text adopted unchanged would not carry the
paragraph above about results and disputes, which is the part of this document
most likely to be needed, and a standard text with a local addendum is two
documents that can disagree.

The cost is real and is stated rather than argued away: a contributor who knows
the Covenant knows what they are agreeing to, and has to read this one instead. A
maintainer who prefers the standard text can take it, and the paragraph about
results and disputes is what has to survive the swap.

## The mark

PROSE, NOT ENFORCEMENT, whole document. This is a rule about how people behave,
and there is nothing in this tree for a check to read. That is terminal rather
than a mechanism nobody has written yet.
