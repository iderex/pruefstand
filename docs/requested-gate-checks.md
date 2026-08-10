# The checks this repository asks to gate the mainline

This answers issue #27. It is the request and not the change. Changing the
ruleset is the maintainer's, and this document is what that decision can be made
from: the names to require, the failure each one refuses, where each name comes
from, and what is known and not known about each one having ever refused
anything.

[reference-gate-parity.md](reference-gate-parity.md) is the neighbouring
document. It records which elements of the reference gate this repository adopts,
adapts or drops, and it says of every adopted row that an issue is open rather
than that a check gates. This one takes the subset that exists here today and
writes it as a list somebody can paste.

Every list below is command output with the command above it, or it is the
request itself, which is the thing being asked for and has no earlier source to
be derived from. The distinction matters because #92 carries a candidate rule
that no document enumerates the checks. The parity document argues that
difference at length and this one relies on the same argument.

## What gates today

    gh api repos/iderex/pruefstand/rulesets --jq '.[] | "\(.id) \(.name)"'
    20521019 gate
    gh api repos/iderex/pruefstand/rulesets/20521019 --jq '{enforcement, bypass: .bypass_actors, types: [.rules[].type]}'
    {"bypass":[],"enforcement":"active","types":["deletion","non_fast_forward","pull_request"]}

No `required_status_checks` rule. So a change cannot be pushed straight to the
mainline and cannot force-push, and every workflow in this tree may red without
stopping a merge.

## What the check runs are actually called

A ruleset matches a required check by the literal check-run name, so the names
have to be read off a real change rather than guessed from the workflow files.
Taken from the head commit of the last merged pull request:

    gh api repos/iderex/pruefstand/commits/0f78b70d7f5dbd2fa914f2f3cfe4afd7730e9813/check-runs --jq '.check_runs[] | "\(.name)\t\(.app.slug)"' | sort
    Audit workflows (zizmor)	github-actions
    DCO sign-off	github-actions
    dependency-review	github-actions
    gate	github-actions
    Reject Trojan Source Unicode	github-actions
    Reject Trojan Source Unicode	github-actions
    zizmor	github-advanced-security

Two things in that output are not obvious and both change what should be asked
for.

`Reject Trojan Source Unicode` appears twice because two events each started the
workflow on that commit:

    gh api "repos/iderex/pruefstand/actions/runs?head_sha=0f78b70d7f5dbd2fa914f2f3cfe4afd7730e9813" --jq '.workflow_runs[] | "\(.name)\t\(.event)"' | sort
    DCO	pull_request
    Dependency review	pull_request
    gate	pull_request
    unicode-guard	pull_request
    unicode-guard	push
    Workflow Security Analysis	pull_request

`unicode-guard.yml` declares both `push` on every branch and `pull_request` on
every branch, so a branch pushed to this repository and then opened as a pull
request runs it twice. That is a duplicate rather than a defect, and it is worth
knowing before the name is required, because a reader watching one of the two
runs is not watching the one that has to be green.

`zizmor` from `github-advanced-security` is not a workflow job. It is the code
scanning check run that appears when the SARIF upload succeeds, and
`zizmor.yml` skips that upload on a fork pull request and on a Dependabot one.
A name that is absent for a whole class of contributor is a name that would
block those contributors permanently, so it is not in the list below.

## The list

Seven names to require, each with the failure it refuses and the file and job
that produce the name, and then the one name this tree produces that is
deliberately not among them.

`gate`. Refuses a tree whose suite reds, whose gate part could not start, or
whose collecting part found fewer items than its declared floor. `gate.yml`, job
`gate`, which sets `name: gate`. This is the only entry that covers the contents
of the repository rather than the shape of the change.

`DCO sign-off`. Refuses a non-merge commit in the change whose message carries no
`Signed-off-by:` trailer matching its author, so that the contributor's assertion
of origin is attached to every commit rather than to the pull request.
`dco.yml`, job `dco`, which sets `name: DCO sign-off`.

`dependency-review`. Refuses a newly introduced or upgraded dependency carrying a
known vulnerability at severity low or above. `dependency-review.yml`, job
`dependency-review`, which sets no `name:` and is named for its job id. The
comment in that file already records why the `name:` is absent.

`Reject Trojan Source Unicode`. Refuses a bidirectional override, isolate or mark
and a zero-width character in tracked text, so source cannot render to a reviewer
differently from how it is read by a machine. `unicode-guard.yml`, job `bidi`,
which sets `name: Reject Trojan Source Unicode`.

`Audit workflows (zizmor)`. Refuses an actionable workflow security finding at
low severity or above, over the workflow YAML itself. `zizmor.yml`, job `zizmor`,
which sets `name: Audit workflows (zizmor)`.

`Deterministic PR-hygiene checks`. Refuses a change that names no issue, whose
paths fall outside the scope its issues declare with the body naming none of
them, that brings in a tool, a language or a dependency without the body naming
the means, that modifies a result record instead of adding one, or that moves a
published number with no new record arriving beside it. `hygiene.yml`, job `hygiene`, which sets
`name: Deterministic PR-hygiene checks`. It is the only entry that decides
anything about the shape of a change rather than about the contents of the tree
or about one property of a commit, and it prints its own bounds on every run.
Where no named issue declares a scope, and where one of them declares the whole
tree, it says the comparison decided nothing in place of passing quietly.

`CodeQL`. Refuses a static analysis finding in the Python this repository is
written in, over the queries in the `security-and-quality` set. `codeql.yml`,
job `analyze`, which sets `name: CodeQL`. Its baseline is zero findings, which
is only cheap while the tree is small, and what keeps the baseline honest is
not in the workflow: a suppression comment lives in the source, and
`tests/test_code_scanning.py` refuses one that names no rule or gives no reason.
It runs on a schedule as well as on every change, because a scanner's rules
improve without the code changing.

`CodeQL` is produced twice on one commit, and only one of the two is the name
this list asks for. Read off the head of the change that added the workflow:

    gh api repos/iderex/pruefstand/commits/d3ab61380c08f6b21c28905786695849e590cd9a/check-runs --jq '.check_runs[] | "\(.name)\t\(.app.slug)"' | sort
    Audit workflows (zizmor)	github-actions
    CodeQL	github-actions
    CodeQL	github-advanced-security
    DCO sign-off	github-actions
    dependency-review	github-actions
    Deterministic PR-hygiene checks	github-actions
    gate	github-actions
    Reject Trojan Source Unicode	github-actions
    Reject Trojan Source Unicode	github-actions
    zizmor	github-advanced-security

The one from `github-actions` is the job, and it is the one being requested. The
one from `github-advanced-security` is the code scanning check run that appears
when the analysis uploads, which is the same shape as `zizmor` above and carries
the same caveat: a fork pull request runs with a read-only token and cannot
upload, so that check run is absent for a whole class of contributor. The two
share a literal name, so a ruleset entry cannot tell them apart, and what a
ruleset does when two check runs carry one name is not answered here and is not
something this repository's state can be read to answer without turning the rule
on. It is named because it is the difference between a required name that gates
and one that blocks an outside contributor permanently.

Two of the requested names are younger than the first check-run listing above,
which was read off a commit made before `hygiene.yml` and `codeql.yml` existed.
Both are requested from the files that produce them rather than from a run, and
the listing in this section is where both have since been observed.

`Scorecard analysis` is the one name this tree produces that is deliberately
not requested. `scorecard.yml` declares `branch_protection_rule`, `schedule` and
`push` on the mainline, and no `pull_request`, which is why it is absent from the
check-run listing above. It is a self-audit that publishes a score, and its job
carries `if: github.event.repository.default_branch == github.ref_name`, so on a
pull request there is nothing for a required name to match. Requiring it would be
requiring a name that never reports.

So the request is seven names, and the paragraph above is the reason the eighth
is not among them.

## One of them has refused something, and six have not

    gh api --paginate "repos/iderex/pruefstand/actions/runs?per_page=100" --jq '.workflow_runs[] | "\(.name)\t\(.conclusion)"' | sort | uniq -c
          5 CodeQL	success
          2 DCO	failure
         40 DCO	success
         42 Dependency review	success
         73 gate	success
          6 hygiene	success
         37 Scorecard supply-chain security	success
        120 unicode-guard	success
         78 Workflow Security Analysis	success

That counts workflow runs, and what a ruleset holds is a check-run name. The two
coincide here because every workflow producing a requested name declares one job,
which is what the check-run listing above shows: one line per workflow apart from
the `unicode-guard` duplicate that section explains. Counted by the name a
ruleset would hold:

    gh api --paginate "repos/iderex/pruefstand/actions/runs?per_page=100" --jq '.workflow_runs[] | select(.conclusion=="failure") | .id' | while read -r id; do gh api "repos/iderex/pruefstand/actions/runs/$id/jobs" --jq '.jobs[] | select(.conclusion=="failure") | .name'; done | sort | uniq -c
          2 DCO sign-off

So `DCO sign-off` has refused twice, and `gate`, `dependency-review`, `Reject
Trojan Source Unicode`, `Audit workflows (zizmor)`, `Deterministic PR-hygiene
checks` and `CodeQL` have refused nothing here. Each of those six is a guard
whose bite is argued from its source rather than observed from a run, and #27
asks for the opposite.

Neither red was arranged. Both are a branch whose commit carried no
`Signed-off-by:` trailer, which is the failure `DCO sign-off` is in the list for:

    gh api --paginate "repos/iderex/pruefstand/actions/runs?per_page=100" --jq '.workflow_runs[] | select(.conclusion=="failure") | "\(.head_sha[0:12])\t\(.head_branch)\t\(.created_at)"' | sort
    00f5d2edb79d	issue-46-order-of-convergence	2026-08-09T16:04:26Z
    d1b7a83666da	issue-23-refuse-network	2026-08-09T06:04:50Z

Each was repaired by cherry-picking the commit onto a fresh branch with the
trailer rather than by rewriting the branch, and each original pull request was
closed with the reason in its body: #139 replaced by #140, and #148 replaced by
#149.

For the other six this is the one requirement of #27 that a document cannot meet,
because it is a fact about the repository's history rather than about what is
written down. It is recorded here as unmet rather than softened, it is written
into #27 as the reason that issue stays open, and the two spellings that would
meet it are a deliberately broken change pushed on purpose or a red arriving in
the ordinary course of the work. The first has a cost this document is not the
place to spend: it puts a knowingly broken pull request on a public tracker for no
reason a reader could infer. The second is what produced the two above, and it
cannot be arranged for a particular name.

What is separable, and is met for the whole list, is that all seven names exist
and are produced by a job in this tree. The check-run listing above is that half.

## A rename removes a check from the gate

A ruleset stores the required check by its literal name. The name is the job id
unless the job sets `name:`, and every requested name above except
`dependency-review` comes from a `name:` its job sets. Renaming a job,
or adding a `name:` to `dependency-review`, changes the check-run name, and the
required entry then matches nothing while the workflow goes on passing. The
merge waits on a name nothing produces, or, where the ruleset is later tidied to
remove the stale entry, passes with one guard fewer than the list says.

Two of the seven are caught and five are not:

    git grep -l 'DCO sign-off\|Reject Trojan Source Unicode\|Audit workflows' -- tests/ ; echo "exit=$?"
    exit=1
    git grep -l 'Deterministic PR-hygiene checks' -- tests/
    tests/test_hygiene.py
    git grep -l 'CHECK_RUN_NAME = ' -- tests/
    tests/test_code_scanning.py

`tests/test_hygiene.py` asserts that `hygiene.yml` carries the literal name and
that this document carries the same string, so renaming that one job reds the
suite and moving the name in one of the two places without the other reds it as
well. `tests/test_code_scanning.py` holds `CodeQL` the same way against
`codeql.yml` and against this document, and it is grepped for by its constant
rather than by the name, because the name is three characters of ordinary prose
and a grep for it finds this document, the workflow and every sentence that
mentions the tool. That is the shape the rest of the list needs and it covers
two names, because each was written beside the workflow it names rather than
over the set.

No test names any of the other five strings the ruleset would hold. The check
that would catch those reads the workflow files, derives the check-run name each
job produces, and refuses a set that differs from the requested list, which is a
pattern over the tree and therefore belongs in #92's register rather than in this
document. It is owed and it does not exist. Until it does, a rename of one of the
other five is caught by whoever notices the ruleset and the workflow disagreeing.

## Verified signatures, and what they cost here

#27 asks that this be raised in the same place as the list, so that it is decided
alongside it rather than separately. #96 is the issue that holds it.

A signature is a different claim from the DCO sign-off already in the list. The
sign-off is an assertion the author writes into the message and anybody can type;
the signature is evidence a key held by the author produced the commit. For a
project whose output is published statements about other people's software, a
commit nobody can attribute is a poor foundation, and that argument is in #96.

The cost is measurable rather than guessed. Across the mainline history:

    gh api --paginate "repos/iderex/pruefstand/commits?sha=main&per_page=100" --jq '.[] | .commit.verification.reason' | sort | uniq -c
          1 unsigned
         39 valid

Thirty-nine of forty verify. So requiring signatures asks for something the work
already does, and the ongoing cost is a contributor whose clone is not configured
to sign, who is refused at the merge rather than at the push and who then has to
rewrite the branch. That cost falls on an outside contributor and not on the
person who set the rule, which is worth saying before the rule is set.

One commit does not verify:

    gh api --paginate "repos/iderex/pruefstand/commits?sha=main&per_page=100" --jq '.[] | select(.commit.verification.reason=="unsigned") | "\(.sha[0:12]) \(.commit.author.date)"'
    7e6ada44b5c3 2026-08-08T01:53:49Z

It is already merged. Whether an unsigned commit sitting in the mainline's
history refuses a later merge, or whether the rule reaches only the commits a
push introduces, is not answered here and is not something this repository's
state can be read to answer without turning the rule on. It is named because it
is the thing that would turn a two-minute settings change into a rewritten
history, and finding it afterwards is much worse than finding it now.

## The mark

PROSE, NOT ENFORCEMENT, whole document, with two strings excepted. Nothing reads
it. The ruleset is not in this tree, so no check here can compare what is
required against what is asked for. The rename half is refused for exactly two
of the seven names, by `tests/test_hygiene.py` and `tests/test_code_scanning.py`
holding their names against the workflows that produce them and against the
entries above, and it is refused for none of the other five. #92 is
where the half that covers the set would live and it is not written. Until the
ruleset carries the list, the seven names above are workflows that may red
without stopping anything, which is what the parity document means when it says
the guards here are advice.
