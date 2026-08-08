"""The package boundary this tree exists to keep.

Two properties, both refused here rather than noticed in review:

1. The numerical core imports no adapter and no engine. If it does, the
   reference silently inherits an engine's conventions and the thing every
   engine is measured against is no longer independent of one of them.
2. An adapter imports exactly one engine, the one it declares. An adapter that
   reaches a second engine is a place where two engines can be asked different
   questions with nothing recording that they were.

The engine set is derived, never listed. An engine is whatever some adapter
package declares in its module-level ``ENGINE_MODULE`` assignment, so this file
names no engine and does not need editing when the engine list moves. An adapter
package that declares nothing is refused, so the rule cannot be dodged by
staying silent.

Written against ``unittest`` from the standard library so it runs from a bare
interpreter at the floor version fixed in
``docs/decisions/language-and-toolchain.md``. The toolchain is not pinned yet
(#19) and the one gate command that will run this does not exist yet (#20).

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The numerical core: the part that is measured against, so it stays independent
# of everything it measures.
CORE_DIRS = ("reference", "metrics")

ADAPTERS_DIR = "adapters"

# The name an adapter package assigns at module level to say which engine it is
# for.
ENGINE_DECLARATION = "ENGINE_MODULE"


def top_level_imports(source: str) -> set[str]:
    """The top-level module names one Python source file imports.

    A relative import cannot leave its own package, so it is not an import of
    anything this check judges and is skipped.
    """
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


def python_files(directory: Path) -> list[Path]:
    return sorted(p for p in directory.rglob("*.py") if p.is_file())


def adapter_packages(root: Path) -> list[Path]:
    """Every directory under ``adapters/`` that is a package."""
    adapters = root / ADAPTERS_DIR
    if not adapters.is_dir():
        return []
    return sorted(p for p in adapters.iterdir() if (p / "__init__.py").is_file())


def declared_engine(package: Path) -> str | None:
    """The engine module a package declares, or None if it declares nothing.

    Read out of the source rather than by importing it, because importing an
    adapter would import its engine, and this check has to run on a machine with
    no engine installed.
    """
    source = (package / "__init__.py").read_text(encoding="utf-8")
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(
            node.value.value, str
        ):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == ENGINE_DECLARATION:
                return node.value.value
    return None


def boundary_violations(root: Path) -> list[str]:
    """Every violation of the two properties, as sentences a reader can act on.

    An empty list is the only passing verdict.
    """
    violations: list[str] = []

    packages = adapter_packages(root)
    engines: set[str] = set()
    for package in packages:
        engine = declared_engine(package)
        if engine is None:
            violations.append(
                f"{package.relative_to(root).as_posix()} is an adapter package "
                f"and declares no {ENGINE_DECLARATION}"
            )
            continue
        engines.add(engine)

    for name in CORE_DIRS:
        directory = root / name
        if not directory.is_dir():
            continue
        for path in python_files(directory):
            imported = top_level_imports(path.read_text(encoding="utf-8"))
            where = path.relative_to(root).as_posix()
            if ADAPTERS_DIR in imported:
                violations.append(
                    f"{where} is in the numerical core and imports {ADAPTERS_DIR}"
                )
            for engine in sorted(imported & engines):
                violations.append(
                    f"{where} is in the numerical core and imports the engine "
                    f"{engine}"
                )

    for package in packages:
        own = declared_engine(package)
        if own is None:
            continue
        for path in python_files(package):
            imported = top_level_imports(path.read_text(encoding="utf-8"))
            for engine in sorted((imported & engines) - {own}):
                violations.append(
                    f"{path.relative_to(root).as_posix()} is in the adapter for "
                    f"{own} and imports the engine {engine}"
                )

    return sorted(violations)


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _clean_tree(root: Path) -> None:
    """A tree that satisfies both properties, and nearly does not.

    Every fixture below is this tree with one line changed, so what each test
    proves is that line and not the rest of the shape.
    """
    _write(root, "adapters/__init__.py", "")
    _write(root, "adapters/alpha/__init__.py", 'ENGINE_MODULE = "engine_alpha"\n')
    _write(
        root,
        "adapters/alpha/run.py",
        "import engine_alpha\nfrom . import helpers\n",
    )
    _write(root, "adapters/alpha/helpers.py", "")
    _write(root, "adapters/beta/__init__.py", 'ENGINE_MODULE = "engine_beta"\n')
    _write(root, "adapters/beta/run.py", "import engine_beta\n")
    _write(root, "reference/__init__.py", "")
    _write(root, "reference/integrate.py", "import math\n")
    _write(root, "metrics/__init__.py", "")
    _write(root, "metrics/drift.py", "from math import isclose\n")


class BoundaryCheckBites(unittest.TestCase):
    """Each test adds one import to a clean tree and expects a refusal."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        _clean_tree(self.root)

    def test_the_clean_tree_is_accepted(self) -> None:
        # The near-miss lives here. Each adapter imports its own engine, the
        # core imports the standard library, and a relative import crosses no
        # boundary. If this fixture were refused, every test below would pass
        # for the wrong reason.
        self.assertEqual(boundary_violations(self.root), [])

    def test_core_importing_an_adapter_is_refused(self) -> None:
        _write(self.root, "reference/integrate.py", "import adapters\n")
        self.assertEqual(
            boundary_violations(self.root),
            ["reference/integrate.py is in the numerical core and imports adapters"],
        )

    def test_core_importing_an_adapter_by_from_is_refused(self) -> None:
        _write(self.root, "metrics/drift.py", "from adapters.alpha import run\n")
        self.assertEqual(
            boundary_violations(self.root),
            ["metrics/drift.py is in the numerical core and imports adapters"],
        )

    def test_core_importing_an_engine_is_refused(self) -> None:
        _write(self.root, "reference/integrate.py", "import engine_beta\n")
        self.assertEqual(
            boundary_violations(self.root),
            [
                "reference/integrate.py is in the numerical core and imports "
                "the engine engine_beta"
            ],
        )

    def test_adapter_importing_a_second_engine_is_refused(self) -> None:
        _write(
            self.root,
            "adapters/alpha/run.py",
            "import engine_alpha\nimport engine_beta\n",
        )
        self.assertEqual(
            boundary_violations(self.root),
            [
                "adapters/alpha/run.py is in the adapter for engine_alpha and "
                "imports the engine engine_beta"
            ],
        )

    def test_adapter_declaring_no_engine_is_refused(self) -> None:
        # Fail closed. Without this, an adapter opts out of the second property
        # by deleting one line, and the engine it imports never joins the
        # derived engine set that the first property is enforced against.
        _write(self.root, "adapters/beta/__init__.py", "")
        self.assertEqual(
            boundary_violations(self.root),
            [
                "adapters/beta is an adapter package and declares no "
                "ENGINE_MODULE"
            ],
        )

    def test_a_declaration_that_is_not_a_plain_string_is_refused(self) -> None:
        # The one-character mistake: a declaration built at import time reads as
        # a declaration to a person and as nothing to this check, so this check
        # says nothing rather than saying it silently.
        _write(
            self.root,
            "adapters/beta/__init__.py",
            'ENGINE_MODULE = "engine" + "_beta"\n',
        )
        self.assertEqual(
            boundary_violations(self.root),
            [
                "adapters/beta is an adapter package and declares no "
                "ENGINE_MODULE"
            ],
        )


class ImportExtraction(unittest.TestCase):
    def test_relative_imports_are_not_counted(self) -> None:
        self.assertEqual(top_level_imports("from . import sibling\n"), set())
        self.assertEqual(top_level_imports("from .. import cousin\n"), set())

    def test_dotted_imports_reduce_to_their_top_level(self) -> None:
        self.assertEqual(
            top_level_imports("import adapters.alpha.run\n"), {"adapters"}
        )
        self.assertEqual(
            top_level_imports("from adapters.alpha import run\n"), {"adapters"}
        )


class TheTreeItself(unittest.TestCase):
    def test_this_repository_has_no_boundary_violations(self) -> None:
        self.assertEqual(boundary_violations(REPO_ROOT), [])

    def test_the_directories_this_check_judges_exist(self) -> None:
        # Without this, the check above passes on a tree where the numerical
        # core was renamed away and nothing is being read at all.
        for name in CORE_DIRS + (ADAPTERS_DIR,):
            with self.subTest(directory=name):
                self.assertTrue((REPO_ROOT / name).is_dir())


if __name__ == "__main__":
    unittest.main()
