"""A workflow step whose failure is swallowed by a pipe.

In a POSIX shell the exit status of a pipeline is the status of its LAST
command, so `git rev-list ... | head` reports success when the first command
failed. A step written that way is green over a command that did not work, which
is the same class of defect as a runner that collected no tests: the green is
indistinguishable at a glance from a real one.

The rule: a shell block in any workflow in this tree that contains a pipeline
must set `pipefail` in the same block. Not in a neighbouring step, because the
shell is a new process per step and a setting made elsewhere does not reach it.

This is a property of how a step is WRITTEN, which is why it is checked over the
workflow files rather than by running them.

What this cannot do, stated so nobody reads more into a green than is there. It
does not parse YAML; it finds block scalars by indentation and single-line
`run:` values by pattern. It reads the text of a shell block rather than
executing it, so a pipeline built at run time out of a variable is invisible to
it. It says nothing about a step whose work is done by an action called with
`uses:`. And it judges pipefail by the presence of the word in the block, not by
whether that line is reached.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

BLOCK_RUN = re.compile(r"^(?P<indent>\s*)(?:-\s+)?run:\s*[|>][+-]?\s*$")
INLINE_RUN = re.compile(r"^(?P<indent>\s*)(?:-\s+)?run:\s*(?P<value>[^|>].*?)\s*$")

# A pipe, and not the `||` of a shell or, and not a `|` inside a character
# class or a quoted regex we cannot see. The first two are what actually occurs.
PIPE = re.compile(r"(?<!\|)\|(?!\|)")

PIPEFAIL = "pipefail"


def shell_blocks(text: str) -> list[str]:
    """Every shell block a workflow declares, as one string each."""
    blocks: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.lstrip().startswith("#"):
            index += 1
            continue
        block_start = BLOCK_RUN.match(line)
        if block_start:
            indent = len(block_start.group("indent"))
            body: list[str] = []
            index += 1
            while index < len(lines):
                following = lines[index]
                if following.strip() and (
                    len(following) - len(following.lstrip())
                ) <= indent:
                    break
                body.append(following)
                index += 1
            blocks.append("\n".join(body))
            continue
        inline = INLINE_RUN.match(line)
        if inline:
            blocks.append(inline.group("value"))
        index += 1
    return blocks


def pipefail_violations(text: str, where: str) -> list[str]:
    """Every shell block that pipes without pipefail. Empty is the only pass."""
    violations = []
    for number, block in enumerate(shell_blocks(text), start=1):
        stripped = "\n".join(
            line for line in block.splitlines() if not line.lstrip().startswith("#")
        )
        if PIPE.search(stripped) and PIPEFAIL not in stripped:
            violations.append(
                f"{where}: shell block {number} contains a pipeline and does "
                f"not set {PIPEFAIL}, so a failure in it would be reported as "
                f"success"
            )
    return violations


def tree_violations(root: Path) -> list[str]:
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return [".github/workflows/ does not exist, so nothing was examined"]
    files = sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml"))
    if not files:
        return ["no workflow files were found, so nothing was examined"]
    violations: list[str] = []
    for path in files:
        violations.extend(
            pipefail_violations(
                path.read_text(encoding="utf-8"),
                path.relative_to(root).as_posix(),
            )
        )
    return violations


CLEAN = """\
jobs:
  one:
    steps:
      - name: A pipeline that fails closed
        run: |
          set -euo pipefail
          git rev-list HEAD | head -1
      - name: No pipeline at all
        run: python -m gate
      - name: A shell or, which is not a pipeline
        run: |
          command-a || echo "fell back"
"""


class TheCheckBites(unittest.TestCase):
    def test_the_clean_fixture_is_accepted(self) -> None:
        # The near-miss, and it holds three shapes that are legal and look
        # illegal: a pipeline that does set pipefail, a step with no pipeline,
        # and `||`, which is a shell or and not a pipe. Without this every
        # refusal below could be passing for the wrong reason.
        self.assertEqual(pipefail_violations(CLEAN, "fixture"), [])

    def test_a_pipeline_without_pipefail_is_refused(self) -> None:
        text = CLEAN.replace("          set -euo pipefail\n", "")
        violations = pipefail_violations(text, "fixture")
        self.assertEqual(len(violations), 1)
        self.assertIn("contains a pipeline", violations[0])

    def test_pipefail_in_a_neighbouring_step_does_not_count(self) -> None:
        # Each step is a new shell. A setting made in one does not reach the
        # next, and a check that scanned the whole file rather than the block
        # would call this clean.
        text = """\
jobs:
  one:
    steps:
      - name: Sets it here
        run: |
          set -euo pipefail
          echo fine
      - name: And pipes over there
        run: |
          git rev-list HEAD | head -1
"""
        self.assertEqual(len(pipefail_violations(text, "fixture")), 1)

    def test_an_inline_pipeline_without_pipefail_is_refused(self) -> None:
        text = CLEAN.replace("run: python -m gate", "run: cat x | wc -l")
        self.assertEqual(len(pipefail_violations(text, "fixture")), 1)

    def test_a_pipe_inside_a_comment_is_not_a_pipeline(self) -> None:
        text = CLEAN.replace(
            "        run: python -m gate",
            "        run: |\n          # a | b would be a pipeline\n          echo fine",
        )
        self.assertEqual(pipefail_violations(text, "fixture"), [])


class TheWorkflowsInThisTree(unittest.TestCase):
    def test_every_workflow_that_pipes_sets_pipefail(self) -> None:
        self.assertEqual(tree_violations(REPO_ROOT), [])

    def test_something_was_actually_examined(self) -> None:
        # Without this the test above is green over an empty file list, which is
        # the exact shape this whole file exists to refuse.
        self.assertGreater(len(sorted(WORKFLOWS.glob("*.yml"))), 0)

    def test_shell_blocks_are_actually_being_found(self) -> None:
        # And without this, a parser that returned no blocks at all would make
        # every workflow above pass without being read.
        found = sum(
            len(shell_blocks(path.read_text(encoding="utf-8")))
            for path in sorted(WORKFLOWS.glob("*.yml"))
        )
        self.assertGreater(found, 0)


if __name__ == "__main__":
    unittest.main()
