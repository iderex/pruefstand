"""The conformance suite against every real adapter, which needs the engine.

Issue #33. `adapters/conformance.py` is the suite. `tests/test_conformance.py`
runs it against adapters written in that file, which proves the refusals bite and
needs nothing installed. This runs the same operators against every adapter
package in the tree, which means importing that package, which means importing
its engine, and that is why it is here rather than in the suite that runs
anywhere.

It is the route by which the suite is run against every adapter in the gate.
`python -m gate` derives the engine part from the tree and runs
`unittest discover -s harness` on the day the first adapter package appears, so
nothing has to be remembered and no list has to be kept in step.

It fails closed on an empty tree. A harness that found no adapter and passed
would be a green from the engine part of the gate covering no engine, which reads
exactly like a green over every engine. THERE IS NO ADAPTER PACKAGE TODAY, so
this harness fails if it is run today, and the gate does not run it: the engine
part reports itself as not run, naming the absent adapter, rather than passing.
"""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

from adapters import conformance

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADAPTERS_DIR = "adapters"


def adapter_packages(root: Path) -> list[str]:
    """Every directory under `adapters/` that is a package, by name."""
    directory = root / ADAPTERS_DIR
    if not directory.is_dir():
        return []
    return sorted(path.parent.name for path in directory.glob("*/__init__.py"))


class EveryAdapterConforms(unittest.TestCase):
    def test_there_is_an_adapter_to_run_against(self) -> None:
        found = adapter_packages(REPO_ROOT)
        self.assertTrue(
            found,
            "there is no adapter package under adapters/, so this harness "
            "covers no engine. It is not a skip: a harness that passed here "
            "would be reporting the engine part of the gate as green over "
            "nothing. The first adapter is #34.",
        )

    def test_every_adapter_passes_the_conformance_suite(self) -> None:
        for name in adapter_packages(REPO_ROOT):
            with self.subTest(adapter=name):
                package = importlib.import_module(f"{ADAPTERS_DIR}.{name}")
                self.assertEqual(
                    conformance.conformance_violations(
                        f"{ADAPTERS_DIR}/{name}", package
                    ),
                    [],
                )


if __name__ == "__main__":
    unittest.main()
