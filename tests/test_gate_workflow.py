"""The gate workflow is a wrapper around the gate command and nothing else.

The failure this refuses is the one that makes a local green and a server green
mean different things: a step added to the workflow that does work the command
does not, so the command a contributor runs stops being the gate.

The rule is narrow on purpose. The gate workflow may carry exactly one `run:`
key, and its value must be the gate command written on the same line. A block
scalar, `run: |`, is refused whatever it contains, because that is where a
second procedure hides.

The bound on this check, stated so nobody reads more into a green than is there:
it is a text-level rule over one file. It does not parse YAML, it says nothing
about the other workflows in this tree, and it cannot see work done by an action
a step calls with `uses:` rather than by a shell line.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "gate.yml"
GATE_COMMAND = "python -m gate"

RUN_KEY = re.compile(r"^\s*(?:-\s+)?run:\s*(?P<value>.*?)\s*$")


def run_steps(text: str) -> list[str]:
    """Every shell line the workflow declares, in order.

    A comment cannot declare a step, so comment lines are not read. That is the
    only thing this function knows about YAML.
    """
    values = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        found = RUN_KEY.match(line)
        if found:
            values.append(found.group("value"))
    return values


def workflow_violations(text: str) -> list[str]:
    """Empty is the only passing verdict."""
    steps = run_steps(text)
    if not steps:
        return ["the gate workflow declares no run step, so it runs no gate"]
    violations = []
    if len(steps) > 1:
        violations.append(
            f"the gate workflow declares {len(steps)} run steps, and a wrapper "
            f"declares one"
        )
    for step in steps:
        if step != GATE_COMMAND:
            violations.append(
                f"the gate workflow runs {step!r} and the gate command is "
                f"{GATE_COMMAND!r}"
            )
    return violations


CLEAN = """\
name: gate
jobs:
  gate:
    steps:
      # run: something in a comment is not a step
      - uses: actions/checkout@0000000000000000000000000000000000000000
      - name: Run the gate
        run: python -m gate
"""


class TheCheckBites(unittest.TestCase):
    def test_a_wrapper_is_accepted(self) -> None:
        # The near-miss. Each fixture below is this text with one line changed.
        self.assertEqual(workflow_violations(CLEAN), [])

    def test_a_second_run_step_is_refused(self) -> None:
        text = CLEAN + "      - name: One more thing\n        run: python -m gate\n"
        self.assertEqual(len(workflow_violations(text)), 1)
        self.assertIn("2 run steps", workflow_violations(text)[0])

    def test_a_step_doing_other_work_is_refused(self) -> None:
        text = CLEAN.replace("run: python -m gate", "run: pytest tests/")
        self.assertEqual(len(workflow_violations(text)), 1)
        self.assertIn("pytest tests/", workflow_violations(text)[0])

    def test_a_block_scalar_is_refused(self) -> None:
        text = CLEAN.replace(
            "run: python -m gate",
            "run: |\n          python -m gate\n          echo also this",
        )
        self.assertTrue(workflow_violations(text))

    def test_a_workflow_with_no_run_step_is_refused(self) -> None:
        text = CLEAN.replace("        run: python -m gate\n", "")
        self.assertEqual(
            workflow_violations(text),
            ["the gate workflow declares no run step, so it runs no gate"],
        )


class TheWorkflowInThisTree(unittest.TestCase):
    def test_the_gate_workflow_exists(self) -> None:
        self.assertTrue(GATE_WORKFLOW.is_file(), f"{GATE_WORKFLOW} is missing")

    def test_the_gate_workflow_is_a_wrapper(self) -> None:
        self.assertEqual(
            workflow_violations(GATE_WORKFLOW.read_text(encoding="utf-8")), []
        )


if __name__ == "__main__":
    unittest.main()
