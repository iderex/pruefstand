"""The one command that runs the gate.

    python -m gate

The same command locally and in CI. `.github/workflows/gate.yml` calls it and
does nothing else, because two procedures meant to be one procedure drift, and
the drift is found by a merge that was green on a laptop and reds on the server.

What this command promises:

- The parts run in a stated order and it stops at the first failure, so the
  output ends at the thing that needs fixing.
- Every part is printed with its outcome. A part that did not run says why and
  what asking for it would cost, so a run that covered less than everything
  cannot be read as one that covered everything and found nothing.
- A part that could not start is a failure, not a pass and not a skip. That
  distinction is the whole point: a skip is a decision this tree made, and a
  part that could not start is a decision nobody made.
- It runs on a machine with no engine installed. Most of what this project
  asserts is in code that needs no engine, and a contributor who cannot install
  one still gets a meaningful green.

Whether a part runs is derived from the tree rather than declared here, so a
skip cannot go stale: the formatting part starts running on the day a formatter
configuration lands, and the engine part on the day an adapter does.

Written against the standard library so it runs from a bare interpreter at the
floor version in `docs/decisions/language-and-toolchain.md`. The toolchain is
not pinned yet (#19).
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

REPO_ROOT = Path(__file__).resolve().parent

PASSED = "PASSED"
FAILED = "FAILED"
COULD_NOT_START = "COULD NOT START"
NOT_RUN = "NOT RUN"
NOT_REACHED = "NOT REACHED"

# The outcomes that mean the command fails. NOT_RUN is not among them, and
# neither is NOT_REACHED: a part that never ran covered nothing, which the
# report says in words rather than in an exit code.
FAILING = (FAILED, COULD_NOT_START)


@dataclass(frozen=True)
class Part:
    """One leg of the gate."""

    name: str
    what: str
    command: tuple[str, ...]
    # None means the part runs here. A string is the reason it does not, and it
    # is derived from the tree by build_parts rather than written by hand.
    not_run_because: str | None = None
    would_cost: str | None = None


@dataclass(frozen=True)
class Result:
    part: Part
    outcome: str
    detail: str = ""


def build_parts(root: Path) -> list[Part]:
    """The parts, in the order they run, with the skips derived from the tree."""
    formatter_config = [
        name for name in ("pyproject.toml", "ruff.toml", ".ruff.toml")
        if (root / name).is_file()
    ]
    adapters = [
        path.name
        for path in sorted((root / "adapters").iterdir())
        if (path / "__init__.py").is_file()
    ] if (root / "adapters").is_dir() else []

    parts = [
        Part(
            name="suite",
            what="the tests that need no engine, no display and no network",
            command=(sys.executable, "-m", "unittest", "discover", "-s", "tests"),
        )
    ]

    if formatter_config:
        parts.append(
            Part(
                name="format",
                what="the formatter and the linter, in check mode",
                command=("ruff", "format", "--check", "."),
            )
        )
    else:
        parts.append(
            Part(
                name="format",
                what="the formatter and the linter, in check mode",
                command=("ruff", "format", "--check", "."),
                not_run_because=(
                    "no formatter configuration in this tree "
                    "(looked for pyproject.toml, ruff.toml, .ruff.toml)"
                ),
                would_cost="pinning ruff (#19) and writing its configuration (#24)",
            )
        )

    if adapters:
        parts.append(
            Part(
                name="engine-harness",
                what="the cases that need an installed engine",
                command=(sys.executable, "-m", "unittest", "discover", "-s", "harness"),
            )
        )
    else:
        parts.append(
            Part(
                name="engine-harness",
                what="the cases that need an installed engine",
                command=(sys.executable, "-m", "unittest", "discover", "-s", "harness"),
                not_run_because="no adapter package under adapters/",
                would_cost=(
                    "writing an adapter (#33, #34) and installing its engine "
                    "in the run (#26)"
                ),
            )
        )

    return parts


def run_part(part: Part, root: Path) -> Result:
    """Run one part. Anything that is not a clean exit 0 is said out loud."""
    if part.not_run_because is not None:
        return Result(part, NOT_RUN, part.not_run_because)
    try:
        completed = subprocess.run(part.command, cwd=root, check=False)
    except OSError as error:
        # The case this whole module exists to get right. A part whose command
        # is missing, unreadable or not executable has covered nothing, and
        # reporting it as a skip would be a green that means nothing.
        return Result(part, COULD_NOT_START, f"{type(error).__name__}: {error}")
    if completed.returncode == 0:
        return Result(part, PASSED)
    return Result(part, FAILED, f"exit {completed.returncode}")


def run(parts: list[Part], root: Path) -> list[Result]:
    """Run the parts in order, stopping at the first failure."""
    results: list[Result] = []
    stopped = False
    for part in parts:
        if stopped:
            results.append(
                Result(part, NOT_REACHED, "the run stopped at an earlier failure")
            )
            continue
        result = run_part(part, root)
        results.append(result)
        if result.outcome in FAILING:
            stopped = True
    return results


def report(results: list[Result], out: TextIO) -> None:
    width = max((len(r.part.name) for r in results), default=0)
    print(f"gate: {len(results)} part(s)", file=out)
    print("", file=out)
    for result in results:
        line = f"  {result.part.name.ljust(width)}  {result.outcome}"
        if result.detail:
            line += f"  {result.detail}"
        print(line, file=out)
        print(f"  {' ' * width}  {result.part.what}", file=out)
        if result.outcome == NOT_RUN and result.part.would_cost:
            print(
                f"  {' ' * width}  to run it: {result.part.would_cost}",
                file=out,
            )
        print("", file=out)

    ran = [r for r in results if r.outcome in (PASSED, FAILED, COULD_NOT_START)]
    passed = [r for r in results if r.outcome == PASSED]
    absent = [r for r in results if r.outcome in (NOT_RUN, NOT_REACHED)]
    print(
        f"gate: {len(ran)} part(s) ran, {len(passed)} passed, "
        f"{len(absent)} did not run and therefore covered nothing",
        file=out,
    )


def main() -> int:
    root = REPO_ROOT
    results = run(build_parts(root), root)
    report(results, sys.stdout)
    return 1 if any(r.outcome in FAILING for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
