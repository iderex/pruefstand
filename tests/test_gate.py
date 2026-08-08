"""What the gate command promises, proved rather than described.

The property that matters most here is the one a reader would not think to test:
a part that could NOT START is a failure. A skip is a decision this tree made
and says so with its reason; a part whose command was missing is a decision
nobody made, and reporting it as a skip is a green that covered nothing. The
one-character version of that mistake is catching OSError and returning NOT_RUN,
so that outcome is asserted by name below and not merely as "the gate failed".
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import gate  # noqa: E402  (the path insert above has to happen first)

# A name no executable on any machine has. Deliberately not a plausible typo of
# a real tool, so a machine that happens to have that tool cannot pass this test
# for the wrong reason.
MISSING_EXECUTABLE = "pruefstand-no-such-executable-af38"


def part(name: str, command: tuple[str, ...]) -> gate.Part:
    return gate.Part(name=name, what="a fixture part", command=command)


def exits_with(code: int) -> tuple[str, ...]:
    return (sys.executable, "-c", f"raise SystemExit({code})")


class APartThatCouldNotStart(unittest.TestCase):
    def test_is_reported_as_could_not_start_and_not_as_not_run(self) -> None:
        results = gate.run([part("broken", (MISSING_EXECUTABLE,))], REPO_ROOT)
        self.assertEqual([r.outcome for r in results], [gate.COULD_NOT_START])

    def test_fails_the_command(self) -> None:
        results = gate.run([part("broken", (MISSING_EXECUTABLE,))], REPO_ROOT)
        self.assertTrue(any(r.outcome in gate.FAILING for r in results))

    def test_carries_the_reason_it_could_not_start(self) -> None:
        results = gate.run([part("broken", (MISSING_EXECUTABLE,))], REPO_ROOT)
        self.assertIn("Error", results[0].detail)


class APartThatRan(unittest.TestCase):
    def test_exit_zero_passes(self) -> None:
        # The near-miss. Without this the tests above could pass because every
        # part fails, which would prove nothing about the outcomes they name.
        results = gate.run([part("fine", exits_with(0))], REPO_ROOT)
        self.assertEqual([r.outcome for r in results], [gate.PASSED])

    def test_a_non_zero_exit_fails_and_quotes_the_code(self) -> None:
        results = gate.run([part("bad", exits_with(3))], REPO_ROOT)
        self.assertEqual(results[0].outcome, gate.FAILED)
        self.assertEqual(results[0].detail, "exit 3")


class TheRunStopsAtTheFirstFailure(unittest.TestCase):
    def test_a_later_part_is_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "the-later-part-ran"
            later = part(
                "later",
                (
                    sys.executable,
                    "-c",
                    f"open({str(marker)!r}, 'w').close()",
                ),
            )
            results = gate.run([part("bad", exits_with(1)), later], REPO_ROOT)
            self.assertEqual(
                [r.outcome for r in results], [gate.FAILED, gate.NOT_REACHED]
            )
            self.assertFalse(
                marker.exists(), "the run continued past a failing part"
            )


class ASkip(unittest.TestCase):
    def setUp(self) -> None:
        self.skipped = gate.Part(
            name="format",
            what="a fixture part",
            command=("ruff", "format", "--check", "."),
            not_run_because="no formatter configuration in this tree",
            would_cost="pinning ruff and writing its configuration",
        )

    def test_is_not_a_pass(self) -> None:
        results = gate.run([self.skipped], REPO_ROOT)
        self.assertEqual(results[0].outcome, gate.NOT_RUN)
        self.assertNotEqual(results[0].outcome, gate.PASSED)

    def test_does_not_fail_the_command(self) -> None:
        results = gate.run([self.skipped], REPO_ROOT)
        self.assertFalse(any(r.outcome in gate.FAILING for r in results))

    def test_prints_its_reason_and_what_asking_would_cost(self) -> None:
        out = io.StringIO()
        gate.report(gate.run([self.skipped], REPO_ROOT), out)
        printed = out.getvalue()
        self.assertIn("no formatter configuration in this tree", printed)
        self.assertIn("pinning ruff and writing its configuration", printed)

    def test_the_summary_says_the_part_covered_nothing(self) -> None:
        out = io.StringIO()
        gate.report(gate.run([self.skipped], REPO_ROOT), out)
        self.assertIn("covered nothing", out.getvalue())


class TheReport(unittest.TestCase):
    def test_names_every_part_and_its_outcome(self) -> None:
        parts = [part("one", exits_with(0)), part("two", exits_with(0))]
        out = io.StringIO()
        gate.report(gate.run(parts, REPO_ROOT), out)
        printed = out.getvalue()
        for name in ("one", "two"):
            self.assertIn(name, printed)
        self.assertEqual(printed.count(gate.PASSED), 2)


class APartThatCollectedTooLittle(unittest.TestCase):
    """A runner that finds nothing exits zero, and that green looks real.

    The floor is what makes it not look real. These tests are what stops the
    floor from being decoration.
    """

    def counting_part(self, prints: str, floor: int) -> gate.Part:
        return gate.Part(
            name="counted",
            what="a fixture part that reports a count",
            command=(sys.executable, "-c", f"print({prints!r})"),
            counts="tests",
            count_pattern=gate.UNITTEST_COUNT,
            floor=floor,
        )

    def test_a_count_below_the_floor_fails(self) -> None:
        part = self.counting_part("Ran 0 tests in 0.000s", floor=1)
        results = gate.run([part], REPO_ROOT)
        self.assertEqual(results[0].outcome, gate.COLLECTED_NOTHING)
        self.assertTrue(any(r.outcome in gate.FAILING for r in results))

    def test_the_failure_carries_the_count(self) -> None:
        part = self.counting_part("Ran 3 tests in 0.000s", floor=40)
        results = gate.run([part], REPO_ROOT)
        self.assertEqual(results[0].detail, "collected 3 tests, and the floor is 40")
        self.assertEqual(results[0].count, 3)

    def test_a_count_at_the_floor_passes(self) -> None:
        # The near-miss, and an off-by-one here would be the whole defect.
        part = self.counting_part("Ran 40 tests in 0.000s", floor=40)
        self.assertEqual(gate.run([part], REPO_ROOT)[0].outcome, gate.PASSED)

    def test_no_count_at_all_is_not_treated_as_fine(self) -> None:
        # A part that exits 0 and says nothing about what it collected has told
        # this gate nothing. Reading that as a pass is the same mistake as
        # reading a skip as a pass.
        part = self.counting_part("nothing to report", floor=1)
        results = gate.run([part], REPO_ROOT)
        self.assertEqual(results[0].outcome, gate.COLLECTED_NOTHING)
        self.assertIn("reported no count", results[0].detail)

    def test_the_count_is_printed_when_the_part_passes(self) -> None:
        # A reader has to see what was covered, not infer it from the absence
        # of failures.
        out = io.StringIO()
        part = self.counting_part("Ran 41 tests in 0.000s", floor=40)
        gate.report(gate.run([part], REPO_ROOT), out)
        self.assertIn("41 tests, floor 40", out.getvalue())

    def test_the_output_of_a_part_that_failed_is_printed_in_full(self) -> None:
        out = io.StringIO()
        part = self.counting_part("Ran 1 tests in 0.000s", floor=40)
        gate.report(gate.run([part], REPO_ROOT), out)
        self.assertIn("Ran 1 tests in 0.000s", out.getvalue())

    def test_the_suite_part_declares_a_floor_above_zero(self) -> None:
        # Without this, the floor mechanism is present and the one part that
        # collects opts out of it.
        suite = [p for p in gate.build_parts(REPO_ROOT) if p.name == "suite"][0]
        self.assertIsNotNone(suite.floor)
        self.assertGreater(suite.floor, 0)


class WhichPartsRunIsDerivedFromTheTree(unittest.TestCase):
    """A skip written by hand goes stale in silence. These do not."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "adapters").mkdir()

    def named(self, name: str) -> gate.Part:
        found = [p for p in gate.build_parts(self.root) if p.name == name]
        self.assertEqual(len(found), 1, f"expected exactly one {name} part")
        return found[0]

    def test_the_format_part_is_skipped_with_no_configuration(self) -> None:
        self.assertIsNotNone(self.named("format").not_run_because)

    def test_the_format_part_runs_once_a_configuration_exists(self) -> None:
        (self.root / "ruff.toml").write_text("", encoding="utf-8")
        self.assertIsNone(self.named("format").not_run_because)

    def test_the_engine_part_is_skipped_with_no_adapter(self) -> None:
        self.assertIsNotNone(self.named("engine-harness").not_run_because)

    def test_the_engine_part_runs_once_an_adapter_exists(self) -> None:
        package = self.root / "adapters" / "alpha"
        package.mkdir()
        (package / "__init__.py").write_text(
            'ENGINE_MODULE = "engine_alpha"\n', encoding="utf-8"
        )
        self.assertIsNone(self.named("engine-harness").not_run_because)

    def test_the_suite_part_always_runs(self) -> None:
        self.assertIsNone(self.named("suite").not_run_because)


if __name__ == "__main__":
    unittest.main()
