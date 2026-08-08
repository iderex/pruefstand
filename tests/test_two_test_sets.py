"""There are exactly two sets of tests, and no third.

The suite that runs anywhere is `tests/`. The harnesses that need something are
`harness/<requirements>/`, where the directory name is a sorted, hyphen-joined
list of ids from `harness/requirements.toml`, so a reader knows what a harness
needs from its name and knows what a green from it does not cover.

Three refusals:

1. A test file in neither set. A test that belongs to no set is a test nobody
   knows the requirements of, and it is the shape both sets exist to make
   impossible.
2. A harness whose name does not decompose into declared requirement ids. A
   harness cannot invent a requirement, because the invented id would have to be
   added to the one file that lists them.
3. A harness importing something none of its own requirements permits. This is
   the one that catches a harness quietly acquiring a second requirement: the
   name still says `engine` while the code now also needs a device.

What this cannot do: it reads imports, so a harness that shells out to a tool,
reads a device file or reaches the network acquires that requirement without
this check seeing it. Refusing a network call in the suite that runs anywhere is
issue #23, and it is a different route from this one.
"""

from __future__ import annotations

import ast
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUITE_DIR = "tests"
HARNESS_DIR = "harness"
REQUIREMENTS_FILE = "requirements.toml"

# What every harness may import whatever it requires: the standard library, and
# the parts of this suite that themselves need nothing. `adapters` is
# deliberately absent, so reaching an engine is only legal for a harness whose
# name says `engine`.
ALWAYS_ALLOWED = frozenset(
    {"reference", "metrics", "runner", "report", "gate"}
) | frozenset(sys.stdlib_module_names)


def declared_requirements(root: Path) -> dict[str, list[str]]:
    """Requirement id to the extra module names it permits."""
    path = root / HARNESS_DIR / REQUIREMENTS_FILE
    if not path.is_file():
        return {}
    declared = tomllib.loads(path.read_text(encoding="utf-8"))
    return {key: list(value.get("permits", [])) for key, value in declared.items()}


def test_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("test_*.py")
        if path.is_file() and ".venv" not in path.parts
    )


def harness_directories(root: Path) -> list[Path]:
    harness = root / HARNESS_DIR
    if not harness.is_dir():
        return []
    return sorted(path for path in harness.iterdir() if path.is_dir())


def top_level_imports(source: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def set_violations(root: Path) -> list[str]:
    """Every violation of the three rules. Empty is the only passing verdict."""
    violations: list[str] = []
    requirements = declared_requirements(root)

    for path in test_files(root):
        parts = path.relative_to(root).parts
        if parts[0] not in (SUITE_DIR, HARNESS_DIR):
            violations.append(
                f"{path.relative_to(root).as_posix()} is a test in neither "
                f"{SUITE_DIR}/ nor {HARNESS_DIR}/"
            )

    for directory in harness_directories(root):
        name = directory.name
        ids = name.split("-")
        unknown = [i for i in ids if i not in requirements]
        if unknown:
            violations.append(
                f"{HARNESS_DIR}/{name} names {', '.join(unknown)}, which "
                f"{HARNESS_DIR}/{REQUIREMENTS_FILE} does not declare"
            )
            continue
        if ids != sorted(ids):
            violations.append(
                f"{HARNESS_DIR}/{name} lists its requirements out of order, so "
                f"one harness could be written under two names"
            )
            continue
        allowed = set(ALWAYS_ALLOWED)
        for requirement in ids:
            allowed.update(requirements[requirement])
        for path in sorted(directory.rglob("*.py")):
            for imported in sorted(top_level_imports(path.read_text(encoding="utf-8"))):
                if imported not in allowed:
                    violations.append(
                        f"{path.relative_to(root).as_posix()} imports "
                        f"{imported}, which none of the requirements in its "
                        f"name ({name}) permits"
                    )

    return sorted(violations)


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


CLEAN_REQUIREMENTS = """\
[engine]
description = "an installed engine"
permits = ["adapters"]

[gpu]
description = "a graphics device"
permits = []
"""


def _clean_tree(root: Path) -> None:
    """Both sets, correctly populated. Every fixture below changes one line."""
    _write(root, f"{HARNESS_DIR}/{REQUIREMENTS_FILE}", CLEAN_REQUIREMENTS)
    _write(root, "tests/test_anywhere.py", "import math\n")
    _write(root, "harness/engine/__init__.py", "")
    _write(root, "harness/engine/test_with_an_engine.py", "import adapters\nimport json\n")
    _write(root, "harness/engine-gpu/__init__.py", "")
    _write(root, "harness/engine-gpu/test_on_a_device.py", "import adapters\n")


class TheCheckBites(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        _clean_tree(self.root)

    def test_the_clean_tree_is_accepted(self) -> None:
        # The near-miss. A harness named `engine` importing `adapters` is legal,
        # a harness importing the standard library is legal, and `engine-gpu` is
        # in sorted order. Without this every refusal below could be passing for
        # the wrong reason.
        self.assertEqual(set_violations(self.root), [])

    def test_a_test_in_neither_set_is_refused(self) -> None:
        _write(self.root, "reference/test_sneaked_in.py", "import math\n")
        self.assertEqual(
            set_violations(self.root),
            ["reference/test_sneaked_in.py is a test in neither tests/ nor harness/"],
        )

    def test_a_harness_naming_an_undeclared_requirement_is_refused(self) -> None:
        _write(self.root, "harness/network/test_it.py", "import math\n")
        self.assertEqual(
            set_violations(self.root),
            [
                "harness/network names network, which harness/requirements.toml "
                "does not declare"
            ],
        )

    def test_a_harness_name_out_of_order_is_refused(self) -> None:
        # Without this, `engine-gpu` and `gpu-engine` are two names for one
        # harness and the count in harness/README.md means nothing.
        _write(self.root, "harness/gpu-engine/test_it.py", "import adapters\n")
        self.assertEqual(len(set_violations(self.root)), 1)
        self.assertIn("out of order", set_violations(self.root)[0])

    def test_a_harness_acquiring_a_second_requirement_is_refused(self) -> None:
        # The shape the rule exists for. The name still says engine; the code
        # now reaches a device library nothing in that name permits.
        _write(
            self.root,
            "harness/engine/test_with_an_engine.py",
            "import adapters\nimport some_device_library\n",
        )
        self.assertEqual(
            set_violations(self.root),
            [
                "harness/engine/test_with_an_engine.py imports "
                "some_device_library, which none of the requirements in its "
                "name (engine) permits"
            ],
        )

    def test_a_harness_reaching_an_engine_without_saying_so_is_refused(self) -> None:
        _write(self.root, "harness/gpu/__init__.py", "")
        _write(self.root, "harness/gpu/test_on_a_device.py", "import adapters\n")
        self.assertEqual(
            set_violations(self.root),
            [
                "harness/gpu/test_on_a_device.py imports adapters, which none "
                "of the requirements in its name (gpu) permits"
            ],
        )


class TheTreeItself(unittest.TestCase):
    def test_this_repository_has_no_violations(self) -> None:
        self.assertEqual(set_violations(REPO_ROOT), [])

    def test_both_sets_exist(self) -> None:
        self.assertTrue((REPO_ROOT / SUITE_DIR).is_dir())
        self.assertTrue((REPO_ROOT / HARNESS_DIR).is_dir())

    def test_the_requirement_list_exists_and_declares_something(self) -> None:
        # Without this, an empty or deleted requirements file makes rule 2
        # vacuous: no harness could ever be named legally, and a tree with no
        # harness would still pass.
        self.assertTrue(declared_requirements(REPO_ROOT))

    def test_the_suite_that_runs_anywhere_is_not_empty(self) -> None:
        # A count of zero here would make every green in this file a green over
        # nothing. The floor is deliberately low; asserting a real one per
        # collection step is issue #30.
        self.assertGreater(len(test_files(REPO_ROOT / SUITE_DIR)), 0)


if __name__ == "__main__":
    unittest.main()
