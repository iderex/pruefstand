"""What can be decided about a change from facts, rather than from a judgement.

Issue #93. The reference gate requires a hygiene check as a named gate, and the
whole of its value is that it is deterministic: it either passes or fails on
facts about the change. A check that needs somebody to read the diff and form an
opinion is a review, and a review is a different thing that happens anyway.

Five conditions are decided here, each over inputs that are already written down
somewhere:

- The change names an issue. Nothing here starts without one.
- The changed paths fall inside the scope the issues it names declare, or the
  body names the ones that do not. A declared scope narrower than its own
  deliverable is a planning defect this repository has met twice and written
  down both times, in #29 and in #31, and both times the departure was said out
  loud in the pull request body. What is refused here is the departure nobody
  wrote down, and the run prints the admitted ones so a pass can never read as
  a change that stayed inside its scope.
- Where the change brings in a new tool, language or dependency, the body says
  which means it chose and why it fits.
- A result record is added and never modified. `results/README.md` fixes that a
  record which was corrected is a record that no longer describes the run it
  names.
- A published number does not move without a record arriving in the same change.

## What this cannot decide, said here and printed by every run

It cannot tell work that belongs to an issue from work that merely touches the
same paths. Two changes with identical path sets, one of them the issue's work
and one of them an unrelated edit that landed in the same directory, are the
same input to this module and get the same verdict. That bound is why the scope
condition is a floor under a review rather than a replacement for one.

Where no issue this change names declares a scope, the comparison is NOT MADE
and the run says so, in place of passing quietly. A silent pass over a
comparison that never happened is the failure this project spends most of its
words on: a run that covered less than everything read as one that covered
everything and found nothing.

The same holds one step further in, and it was found by running this check on
its own change rather than reasoned out in advance. Every issue named anywhere
in the body or the messages contributes its scope, so one incidental number
widens the union, and an issue declaring `Scope: .` widens it to everything. A
comparison against the whole tree refuses nothing and distinguishes nothing, so
it is reported as NOT DECIDED with the issue that declared it, rather than as a
pass. Narrowing which references contribute a scope would be the other repair
and it is not made here: reading only a closing reference would drop the change
that legitimately touches a second issue's paths, which is the case the union
exists for.

The published-number condition reads a subject that is not fixed yet. Where the
published artefacts live is #84's, and until it lands, anything under `report/`
that is not Python and not its README is treated as one. That is a floor chosen
so the condition has a subject today, and it will be narrowed or widened by the
issue that decides where the artefacts go.

## The scope value is not word-split

A scope is taken as the whole of what follows `Scope:` on the line, and it is
divided on commas alone. Splitting it on whitespace is the near-miss this
refuses by name: a gate elsewhere word-split its scope value and then refused
valid work, because a scope with a space in it became two scopes, neither of
which matched anything. A scope containing a space is one scope here.

## The means

The standard library, in the same Python the rest of this tree is written in.
The alternative was shell inside the workflow file, which is where a check like
this usually ends up, and it fails on the first of the three rules this project
works to: the conditions below are decided by functions a test can call with a
fixture and no repository, and a shell block inside a YAML file is reachable
only by pushing a change and watching what happens. It adds no language, no
runtime and no dependency, and the suite that already exists is what tests it.

The workflow that runs it in CI is `.github/workflows/hygiene.yml`, and it
carries no logic: it hands over the base and head commits and prints what this
says.

    python -m hygiene

Reading the change out of a repository and the issue bodies out of the tracker
is the one part that talks to anything, and it is kept in `collect` at the
bottom, apart from every function that decides. Nothing above it opens a socket
or runs a command, which is what lets the suite exercise all five conditions
without a network and without a checkout.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Mapping, Sequence, TextIO

PASSED = "PASSED"
REFUSED = "REFUSED"
NOT_DECIDED = "NOT DECIDED"

# NOT_DECIDED is not a failure and is not a pass either. It is printed with the
# reason the comparison could not be made, so a green run cannot be read as one
# where every condition was decided.
FAILING = (REFUSED,)

NAMES_AN_ISSUE = "names-an-issue"
INSIDE_SCOPE = "changed-paths-inside-scope"
MEANS_RECORDED = "means-recorded"
RECORD_ADDED_NOT_MODIFIED = "record-added-not-modified"
NUMBER_CARRIES_ITS_RECORD = "published-number-carries-its-record"

# An issue reference as this tracker spells it. A number with no `#` is not one,
# and `#` followed by anything but digits is not one either.
ISSUE_REFERENCE = re.compile(r"#(?P<number>\d+)\b")

# The one line of an issue body that any route here reads. Column zero, so a
# `Scope:` quoted inside a paragraph or indented in a block is not one.
SCOPE_LINE = re.compile(r"^Scope:(?P<value>.*)$", re.MULTILINE)

# Where result records live, and the one file in there that is not a record.
RESULTS_DIR = "results"
REPORT_DIR = "report"
DIRECTORY_NOTE = "README.md"

# The files whose arrival means a dependency, a tool or a packaging decision has
# been taken. Named rather than pattern-matched, because the cost of a name
# missing from this set is a means sentence nobody was asked for, and the cost
# of a pattern that over-matches is a change refused for a file that decides
# nothing.
DEPENDENCY_MANIFESTS = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements.in",
        "constraints.txt",
        "Pipfile",
        "Pipfile.lock",
        "poetry.lock",
        "uv.lock",
        "environment.yml",
        "package.json",
        "package-lock.json",
        "Cargo.toml",
        "go.mod",
    }
)

WORKFLOW_DIR = ".github/workflows"

# The shortest a means sentence may be. A body carrying the bare word `means` in
# a sentence about something else passes a test for the word and says nothing,
# and this is the cheapest thing that separates the two. It is a floor and not a
# judgement: whether the sentence names the right means is what the review is
# for, and no reading of a body decides it.
MEANS_SENTENCE_FLOOR = 40

MEANS_WORD = re.compile(r"\bmeans\b", re.IGNORECASE)


@dataclass(frozen=True)
class ChangedPath:
    """One path in the change, with the single letter git gave it.

    The letter is git's own status: `A` added, `M` modified, `D` deleted, `R`
    renamed and so on. A rename arrives as `R` with a similarity number after
    it, and only the letter is kept, because every condition below asks whether
    the path is new and none of them asks how similar it is to what it replaced.
    """

    status: str
    path: str


@dataclass(frozen=True)
class Change:
    """Everything the five conditions are decided from.

    Nothing in here is read from a repository or from the tracker. It is a
    value, so the suite constructs one and gets the same verdict CI would.
    """

    paths: tuple[ChangedPath, ...] = ()
    messages: tuple[str, ...] = ()
    body: str = ""
    # The bodies of the issues this change names, as far as they could be read.
    # An issue that could not be read is absent rather than present and empty,
    # so a scope that exists and was unreachable is not read as a scope that
    # does not exist.
    issue_bodies: Mapping[int, str] = None  # type: ignore[assignment]
    # The file suffixes the tree carried before this change. An added file whose
    # suffix is not in here is a language or a format arriving.
    known_suffixes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.issue_bodies is None:
            object.__setattr__(self, "issue_bodies", {})


@dataclass(frozen=True)
class Finding:
    """One condition and what this run decided about it."""

    condition: str
    outcome: str
    detail: str = ""


def referenced_issues(change: Change) -> tuple[int, ...]:
    """The issue numbers this change names, in the messages and in the body.

    Both are read, because the two spellings are both in use here: a commit
    message states the issue it is part of, and a pull-request body carries the
    closing reference. A change that names an issue in one and not the other has
    still named one.
    """
    found: set[int] = set()
    for text in (*change.messages, change.body):
        for match in ISSUE_REFERENCE.finditer(text):
            found.add(int(match.group("number")))
    return tuple(sorted(found))


def scopes_in(body: str) -> tuple[str, ...]:
    """The scopes an issue body declares, divided on commas and never on space.

    Every `Scope:` at column zero is read rather than only the first, so an
    issue that declares two lines is not silently reduced to one.
    """
    scopes: list[str] = []
    for match in SCOPE_LINE.finditer(body):
        for part in match.group("value").split(","):
            value = part.strip()
            if value:
                scopes.append(value)
    return tuple(scopes)


def inside(path: str, scope: str) -> bool:
    """Whether one changed path falls inside one declared scope.

    `.` is the whole tree. Anything else is a prefix, matched at a path
    separator, so a scope of `report` does not swallow a path in `reporting`.
    """
    scope = scope.strip()
    if scope in (".", "./"):
        return True
    prefix = scope.rstrip("/")
    return path == prefix or path.startswith(prefix + "/")


def names_an_issue(change: Change) -> Finding:
    numbers = referenced_issues(change)
    if not numbers:
        return Finding(
            NAMES_AN_ISSUE,
            REFUSED,
            "no commit message and no line of the body names an issue, and "
            "nothing in this repository starts without one",
        )
    named = ", ".join(f"#{number}" for number in numbers)
    return Finding(NAMES_AN_ISSUE, PASSED, f"names {named}")


def changed_paths_inside_scope(change: Change) -> Finding:
    numbers = referenced_issues(change)
    if not numbers:
        return Finding(
            INSIDE_SCOPE,
            NOT_DECIDED,
            "the change names no issue, so there is no scope to compare against",
        )

    unread = [number for number in numbers if number not in change.issue_bodies]
    declared: dict[int, tuple[str, ...]] = {}
    for number in numbers:
        body = change.issue_bodies.get(number)
        if body is None:
            continue
        scopes = scopes_in(body)
        if scopes:
            declared[number] = scopes

    if not declared:
        unreadable = (
            f", and {len(unread)} of them could not be read" if unread else ""
        )
        return Finding(
            INSIDE_SCOPE,
            NOT_DECIDED,
            "no issue this change names declares a Scope: line at column zero"
            f"{unreadable}, so THE PATH COMPARISON WAS NOT MADE",
        )

    allowed = tuple(scope for scopes in declared.values() for scope in scopes)
    scope_list = "; ".join(
        f"#{number}: {' '.join(scopes)}" for number, scopes in sorted(declared.items())
    )

    # A scope of `.` is the whole tree, so comparing against it refuses nothing
    # and distinguishes nothing. Measured on the first run of this check, where
    # a body quoting the gate's own output named ten issues, two of which
    # declare the whole tree, and the comparison passed having admitted every
    # path for a reason that had nothing to do with the change. Every issue
    # named anywhere contributes its scope, so one incidental number widens the
    # union, and a pass on a union like that is not a comparison.
    whole_tree = sorted(
        number
        for number, scopes in declared.items()
        if any(scope.strip() in (".", "./") for scope in scopes)
    )
    if whole_tree:
        named = ", ".join(f"#{number}" for number in whole_tree)
        return Finding(
            INSIDE_SCOPE,
            NOT_DECIDED,
            f"{named} declares the whole tree, so the union of scopes admits "
            f"every path and THE COMPARISON DISTINGUISHES NOTHING ({scope_list})",
        )

    outside = [
        changed.path
        for changed in change.paths
        if not any(inside(changed.path, scope) for scope in allowed)
    ]
    # A departure the body names is a departure somebody wrote down, which is
    # what this repository already does by hand when an issue's declared scope
    # cannot hold its own deliverable. What is refused is the SILENT departure.
    # The distinction is a fact about the body rather than a judgement: the path
    # is written there or it is not.
    silent = sorted(path for path in outside if path not in change.body)
    if silent:
        return Finding(
            INSIDE_SCOPE,
            REFUSED,
            f"{len(silent)} path(s) outside the declared scope ({scope_list}) and "
            "named nowhere in the body: " + ", ".join(silent),
        )
    partial = (
        f", and {len(unread)} named issue(s) could not be read" if unread else ""
    )
    if outside:
        # Reached only where `silent` was empty, so every path outside a scope
        # is one the body named. Listing them separately is what stops a pass
        # from reading as a change that stayed inside its scope.
        admitted = sorted(outside)
        return Finding(
            INSIDE_SCOPE,
            PASSED,
            f"{len(change.paths) - len(admitted)} path(s) inside "
            f"{scope_list}, and {len(admitted)} OUTSIDE IT that the "
            "body names: " + ", ".join(admitted) + partial,
        )
    return Finding(
        INSIDE_SCOPE,
        PASSED,
        f"{len(change.paths)} path(s) inside {scope_list}{partial}",
    )


def new_means_introduced(change: Change) -> tuple[str, ...]:
    """What in this change is a tool, a language or a dependency arriving.

    Only added paths are read. A dependency manifest that already existed and
    was edited is a version moving inside a means already chosen, which is a
    different question from choosing one.
    """
    reasons: list[str] = []
    for changed in change.paths:
        if changed.status != "A":
            continue
        path = changed.path
        name = PurePosixPath(path).name
        if name in DEPENDENCY_MANIFESTS:
            reasons.append(f"{path} declares dependencies or packaging")
        suffix = PurePosixPath(path).suffix
        if suffix and suffix not in change.known_suffixes:
            reasons.append(f"{path} carries {suffix}, which this tree did not")
        if path.startswith(WORKFLOW_DIR + "/"):
            reasons.append(f"{path} adds a workflow, and a workflow runs a tool")
    return tuple(reasons)


def means_sentence_in(body: str) -> str | None:
    """The line of the body that names the means, if there is one."""
    for line in body.splitlines():
        stripped = line.strip()
        if len(stripped) >= MEANS_SENTENCE_FLOOR and MEANS_WORD.search(stripped):
            return stripped
    return None


def means_recorded(change: Change) -> Finding:
    reasons = new_means_introduced(change)
    if not reasons:
        return Finding(
            MEANS_RECORDED,
            PASSED,
            "no added path brings in a tool, a language or a dependency",
        )
    sentence = means_sentence_in(change.body)
    if sentence is None:
        return Finding(
            MEANS_RECORDED,
            REFUSED,
            "this change chooses a means and the body does not name it: "
            + "; ".join(reasons),
        )
    return Finding(
        MEANS_RECORDED,
        PASSED,
        f"the body names the means ({len(reasons)} reason(s) it had to)",
    )


def _under(path: str, directory: str) -> bool:
    return path.startswith(directory + "/")


def record_added_not_modified(change: Change) -> Finding:
    touched = [
        changed
        for changed in change.paths
        if _under(changed.path, RESULTS_DIR)
        and PurePosixPath(changed.path).name != DIRECTORY_NOTE
    ]
    if not touched:
        return Finding(
            RECORD_ADDED_NOT_MODIFIED, PASSED, "no result record in this change"
        )
    offending = [changed for changed in touched if changed.status != "A"]
    if offending:
        return Finding(
            RECORD_ADDED_NOT_MODIFIED,
            REFUSED,
            "a record that was corrected is a record that no longer describes "
            "the run it names: "
            + ", ".join(
                f"{changed.path} ({changed.status})" for changed in sorted(
                    offending, key=lambda c: c.path
                )
            ),
        )
    return Finding(
        RECORD_ADDED_NOT_MODIFIED,
        PASSED,
        f"{len(touched)} record(s), all added",
    )


def published_artefacts(change: Change) -> tuple[ChangedPath, ...]:
    """The changed paths this reads as a published number.

    Python under `report/` is the assembly rather than its output, and the
    directory note is neither. Everything else there is read as an artefact,
    which is the floor this module's own docstring records against #84.
    """
    return tuple(
        changed
        for changed in change.paths
        if _under(changed.path, REPORT_DIR)
        and PurePosixPath(changed.path).suffix != ".py"
        and PurePosixPath(changed.path).name != DIRECTORY_NOTE
    )


def published_number_carries_its_record(change: Change) -> Finding:
    touched = published_artefacts(change)
    if not touched:
        return Finding(
            NUMBER_CARRIES_ITS_RECORD,
            PASSED,
            "no published artefact in this change",
        )
    records = [
        changed
        for changed in change.paths
        if _under(changed.path, RESULTS_DIR)
        and changed.status == "A"
        and PurePosixPath(changed.path).name != DIRECTORY_NOTE
    ]
    if not records:
        return Finding(
            NUMBER_CARRIES_ITS_RECORD,
            REFUSED,
            "a published number moved and no run arrived with it: "
            + ", ".join(sorted(changed.path for changed in touched))
            + ". A number edited without a new record is a correction that needs "
            "saying out loud or a mistake, and there is no third case",
        )
    return Finding(
        NUMBER_CARRIES_ITS_RECORD,
        PASSED,
        f"{len(touched)} artefact(s) with {len(records)} new record(s)",
    )


CONDITIONS = (
    names_an_issue,
    changed_paths_inside_scope,
    means_recorded,
    record_added_not_modified,
    published_number_carries_its_record,
)


def decide(change: Change) -> tuple[Finding, ...]:
    """Every condition, in a fixed order, all of them decided.

    It does not stop at the first refusal. The gate at the top of this tree
    stops, because its parts are expensive and ordered; these are five reads of
    the same value, and a contributor who has to push five times to be told
    five things is a contributor who stops reading the output.
    """
    return tuple(condition(change) for condition in CONDITIONS)


def report(findings: Sequence[Finding], out: TextIO) -> None:
    width = max((len(finding.condition) for finding in findings), default=0)
    print(f"hygiene: {len(findings)} condition(s)", file=out)
    print("", file=out)
    for finding in findings:
        print(f"  {finding.condition.ljust(width)}  {finding.outcome}", file=out)
        if finding.detail:
            print(f"  {' ' * width}  {finding.detail}", file=out)
        print("", file=out)

    undecided = [f for f in findings if f.outcome == NOT_DECIDED]
    refused = [f for f in findings if f.outcome in FAILING]
    print(
        f"hygiene: {len(findings) - len(undecided)} decided, "
        f"{len(refused)} refused, {len(undecided)} not decided",
        file=out,
    )
    print(
        "hygiene: this cannot tell work that belongs to an issue from work that "
        "merely touches the same paths.",
        file=out,
    )


def refused(findings: Sequence[Finding]) -> bool:
    return any(finding.outcome in FAILING for finding in findings)


# Everything below this line reads a repository or the tracker. Nothing above it
# does, which is why the suite can exercise all five conditions from a value.


def _git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments), check=True, capture_output=True, text=True
    ).stdout


def _issue_body(repository: str, number: int, token: str | None) -> str | None:
    """One issue body from the tracker, or None if it could not be read.

    None rather than an empty string. An issue that could not be read and an
    issue that declares no scope are different statements, and collapsing them
    would turn a network failure into a silent pass.
    """
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/issues/{number}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read()).get("body") or ""
    except (urllib.error.URLError, OSError, ValueError):
        return None


def collect(environment: Mapping[str, str]) -> Change:
    """The change this run is about, read from the workflow's own environment."""
    event_path = environment.get("GITHUB_EVENT_PATH", "")
    event = {}
    if event_path:
        with open(event_path, encoding="utf-8") as handle:
            event = json.load(handle)
    pull_request = event.get("pull_request") or {}
    base = pull_request.get("base", {}).get("sha", "")
    head = pull_request.get("head", {}).get("sha", "")
    body = pull_request.get("body") or ""

    merge_base = _git("merge-base", base, head).strip()
    paths = []
    for line in _git("diff", "--name-status", merge_base, head).splitlines():
        if not line.strip():
            continue
        status, _, rest = line.partition("\t")
        # A rename prints two paths; the second is where the file is now, and
        # that is the one every condition here asks about.
        paths.append(ChangedPath(status[0], rest.split("\t")[-1]))
    messages = tuple(
        _git("log", "--format=%B", f"{merge_base}..{head}").split("\n\n\n")
    )
    known_suffixes = frozenset(
        PurePosixPath(name).suffix
        for name in _git("ls-tree", "-r", "--name-only", merge_base).splitlines()
        if PurePosixPath(name).suffix
    )

    repository = environment.get("GITHUB_REPOSITORY", "")
    token = environment.get("GITHUB_TOKEN") or None
    issue_bodies: dict[int, str] = {}
    change = Change(
        paths=tuple(paths),
        messages=messages,
        body=body,
        known_suffixes=known_suffixes,
    )
    for number in referenced_issues(change):
        fetched = _issue_body(repository, number, token)
        if fetched is not None:
            issue_bodies[number] = fetched
    return Change(
        paths=tuple(paths),
        messages=messages,
        body=body,
        issue_bodies=issue_bodies,
        known_suffixes=known_suffixes,
    )


def main() -> int:
    findings = decide(collect(os.environ))
    report(findings, sys.stdout)
    return 1 if refused(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
