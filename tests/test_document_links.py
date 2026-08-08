"""Every link inside a document resolves, and so does every heading it names.

Part of #94. Most of this repository's output is prose, and prose that has gone
stale is the same defect as code that has gone stale with less chance of being
noticed. A link to a file that moved is the cheapest instance of it to refuse.

Two rules, both over the tracked Markdown:

1. A link to something inside this repository resolves to a file or a directory
   that exists. A link that climbs out of the repository root is refused whether
   or not something happens to be there, because what is there is not this
   project's to promise.
2. A link naming a heading resolves to a heading in the file it points at,
   including a bare `#heading` link inside one document.

What this deliberately does not do, so a green is not read as more than it is.

It reads inline Markdown links, `[text](target)`, and nothing else. A reference
style link, an autolink and a bare URL in prose are invisible to it.

It says nothing about an external link. Whether `https://` resolves is a
question with a network on the other end of it, it belongs on a schedule rather
than in a gate that must run offline, and #94 holds that half.

It does not check paths named in prose or in a pasted command. That looks like
the same rule and is not: this tree's documents quote commands whose arguments
are paths that never existed here, `/tmp/exist.txt` among them, and a checker
that read those would refuse the documents that are doing exactly what the rules
ask. Telling a path somebody promised from a path somebody typed into an example
needs a marking convention this repository does not have, and inventing one here
would put a mark in every document to serve a check. Recorded rather than
approximated, and #94 is where the marking is decided if it is ever wanted.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# `[text](target)`, with the target taken up to the first closing bracket. A
# target carrying a title in quotes is not used in this tree and is not read.
INLINE_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

# An ATX heading. Setext headings are not used in this tree.
HEADING = re.compile(r"^#{1,6}\s+(?P<text>.+?)\s*$", re.MULTILINE)

EXTERNAL = ("http://", "https://", "mailto:", "//")

SKIP_DIRS = {".git", ".venv", "__pycache__"}

# Floors, so a reader that found nothing cannot pass as a tree with nothing
# wrong. Measured at the commit these landed in:
#
#     git ls-files '*.md' | wc -l
#     18
#     grep -ohE '\[[^]]*\]\([^)]*\)' $(git ls-files '*.md') | wc -l
#     7
DOCUMENT_FLOOR = 15
LINK_FLOOR = 5


def documents(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file() and not SKIP_DIRS.intersection(path.parts)
    )


def anchor(text: str) -> str:
    """A heading reduced to the fragment a Markdown renderer links it by."""
    kept = [c for c in text.lower() if c.isalnum() or c in " -_"]
    return "".join(kept).strip().replace(" ", "-")


def anchors(text: str) -> set[str]:
    return {anchor(found.group("text")) for found in HEADING.finditer(text)}


def links(text: str) -> list[str]:
    return INLINE_LINK.findall(text)


def link_violations(root: Path) -> list[str]:
    """Every link that does not resolve. Empty is the only passing verdict."""
    violations: list[str] = []
    for path in documents(root):
        name = path.relative_to(root).as_posix()
        for target in links(path.read_text(encoding="utf-8")):
            if target.startswith(EXTERNAL):
                continue
            file_part, _, fragment = target.partition("#")
            if file_part:
                resolved = (path.parent / file_part).resolve()
                try:
                    resolved.relative_to(root.resolve())
                except ValueError:
                    violations.append(
                        f"{name} links to {target}, which is outside this "
                        f"repository, and what is there is not this project's to "
                        f"promise"
                    )
                    continue
                if not resolved.exists():
                    violations.append(
                        f"{name} links to {target}, and there is nothing at "
                        f"{resolved.relative_to(root.resolve()).as_posix()}"
                    )
                    continue
            else:
                resolved = path
            if not fragment:
                continue
            if resolved.is_dir() or resolved.suffix != ".md":
                violations.append(
                    f"{name} links to the heading {fragment} in {file_part or name}, "
                    f"which is not a document with headings"
                )
                continue
            if fragment.lower() not in anchors(resolved.read_text(encoding="utf-8")):
                violations.append(
                    f"{name} links to the heading {fragment} in "
                    f"{file_part or name}, and no heading there has that name"
                )
    return sorted(violations)


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _clean_tree(root: Path) -> None:
    """Every fixture below is this tree with one line changed."""
    _write(
        root,
        "README.md",
        "# Readme\n\n"
        "See [the notice](NOTICE.md) and [a decision](docs/decisions/one.md).\n"
        "It has [a section](docs/decisions/one.md#what-was-given-up) too, and\n"
        "[a heading here](#readme), and [a directory](docs/).\n"
        "An external link is not read: [somewhere](https://example.invalid/x).\n",
    )
    _write(root, "NOTICE.md", "# Notice\n")
    _write(root, "docs/decisions/one.md", "# One\n\n## What was given up\n\ntext\n")


class TheCheckBites(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        _clean_tree(self.root)

    def test_the_clean_tree_is_accepted(self) -> None:
        # The near-miss. A relative link, a link into a subdirectory, a heading
        # in another file, a heading in this one, a link to a directory and an
        # external link are all legal. Without this every refusal below could be
        # passing for the wrong reason.
        self.assertEqual(link_violations(self.root), [])

    def test_a_link_to_a_missing_file_is_refused(self) -> None:
        _write(self.root, "README.md", "# Readme\n\n[gone](docs/decisions/two.md)\n")
        violations = link_violations(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("docs/decisions/two.md", violations[0])

    def test_a_link_to_a_missing_heading_is_refused(self) -> None:
        # The one-character mistake somebody will actually make: the file is
        # right and the section was renamed.
        _write(
            self.root,
            "README.md",
            "# Readme\n\n[section](docs/decisions/one.md#what-was-given-away)\n",
        )
        violations = link_violations(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("what-was-given-away", violations[0])

    def test_a_link_to_a_heading_in_this_file_is_refused_when_absent(self) -> None:
        _write(self.root, "README.md", "# Readme\n\n[here](#no-such-section)\n")
        self.assertEqual(len(link_violations(self.root)), 1)

    def test_a_link_out_of_the_repository_is_refused(self) -> None:
        _write(self.root, "README.md", "# Readme\n\n[up](../../etc/passwd)\n")
        violations = link_violations(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("outside this repository", violations[0])

    def test_a_document_in_a_subdirectory_is_read_too(self) -> None:
        # Without this, a reader that stopped at the top level would pass a tree
        # whose nested document links at nothing.
        _write(self.root, "docs/notes.md", "# Notes\n\n[gone](../missing.md)\n")
        violations = link_violations(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("docs/notes.md", violations[0])

    def test_a_relative_link_resolves_from_its_own_document(self) -> None:
        # The refusal this guards against is a checker that resolves every link
        # from the repository root, which passes a broken link in a nested file
        # and refuses a good one.
        _write(self.root, "docs/notes.md", "# Notes\n\n[notice](../NOTICE.md)\n")
        self.assertEqual(link_violations(self.root), [])


class TheDocumentsInThisTree(unittest.TestCase):
    def test_every_link_resolves(self) -> None:
        self.assertEqual(link_violations(REPO_ROOT), [])

    def test_the_reader_found_the_documents(self) -> None:
        # A green over an empty file list is the shape #30 is about.
        found = len(documents(REPO_ROOT))
        self.assertGreaterEqual(
            found, DOCUMENT_FLOOR, f"found {found} documents, floor {DOCUMENT_FLOOR}"
        )

    def test_the_reader_found_the_links(self) -> None:
        found = sum(
            len(links(path.read_text(encoding="utf-8"))) for path in documents(REPO_ROOT)
        )
        self.assertGreaterEqual(
            found, LINK_FLOOR, f"found {found} links, floor {LINK_FLOOR}"
        )


if __name__ == "__main__":
    unittest.main()
