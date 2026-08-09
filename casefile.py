"""The case file schema, the reader, and the content hash over a case.

Issue #31. The shape was decided first, in
`docs/decisions/case-file-format.md`, and what every number in a case means was
decided in `docs/decisions/units-frames-and-inertia.md`. This is the mechanism
both of those documents say they are owed, and from here the schema below is the
authority for which fields exist while the documents keep the reasons.

The reader is a boundary. Case definitions are published so that other people
write them, so a case file is one of the few surfaces in this project where a
hostile or simply wrong input is a real category rather than a formality. Three
properties follow from that and are worth stating before the code:

It returns a fully validated case or it raises, never a partially populated one.
Every problem it can find is found in one pass and reported together, because a
reader that stops at the first missing field turns one review into six.

An unknown field is refused. A field name nobody reads is a field somebody
misspelled, and the value they meant to set is then silently absent. This is
where the units rule is enforced in practice: units are a property of the field
and are never written beside a number, so a case that writes one has either put
a string where a float belongs, which is refused by type, or added a key nobody
declared, which is refused by name.

The convention is refused rather than guessed. A file naming a convention this
reader does not implement is refused on that field alone, and so is a file whose
`format` this reader does not implement. That is the difference between "this
suite is too old for this case" and a stack trace about a missing key.

## What this does not decide

Whether a case is physics rather than only a well-formed document is #32. A
symmetric, positive definite inertia tensor whose eigenvalues satisfy the
triangle inequalities is a check over the numbers, and nothing here does it: a
tensor of six zeros is accepted by this schema and is not a body.

Whether a chaotic case may ask for trajectory comparison is #76. The shape of
the `[measured.trajectory]` block is held here, its horizon is required and is
required to be shorter than the case's own, and the refusal that is not
overridable for one class is not written here.

Two vocabularies are enumerated here and one is not. `class` takes one of the
five values `docs/decisions/metric-per-class.md` fixes, and `provenance.kind`
takes one of the two the format document spells out. `reference.kind` names
three kinds in prose and spells exactly one of them, `closed-form`, in its worked
example, so this schema requires a non-empty string there and enumerates nothing.
Inventing the two missing spellings would be fixing a vocabulary in a document's
place, and the enumeration is owed rather than absent.

## The means

Python and the standard library. `tomllib` reads the format the decision fixed,
`hashlib` supplies the digest, and no dependency is added to a tree that carries
none. The three rules survive it: every property here is refused by code rather
than asserted in prose, every refusal is tripped by a fixture in
`tests/test_casefile.py`, and the numbers in this module's own docstrings are
the ones its tests compute.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# The version of the file format this reader implements. A file naming another
# is refused by version rather than by discovering a missing key.
FORMAT = 1

# The units, frames and inertia convention this reader implements, from
# `docs/decisions/units-frames-and-inertia.md`. A file naming another is refused
# rather than read under a guess, which is the whole point of the field: every
# number in a case means what that document says and nothing else.
CONVENTION = "pruefstand-units-frames-inertia-1"

# The class vocabulary, from `docs/decisions/metric-per-class.md`.
CLASSES = (
    "integrable",
    "nonholonomic-conservative",
    "dissipative",
    "qualitative",
    "chaotic",
)

PROVENANCE_KINDS = ("sourced", "chosen")

# All six, always, including where three of them are zero. A case carrying three
# is refused rather than read as a diagonal tensor: a reader filling the missing
# ones with zero would accept a rattleback whose skew somebody forgot to write
# and would run it as a body with no chirality.
INERTIA_COMPONENTS = ("xx", "yy", "zz", "xy", "xz", "yz")

QUATERNION_COMPONENTS = ("w", "x", "y", "z")

# The one shorthand the convention permits for an orientation.
IDENTITY = "identity"

# How far a quaternion's norm may sit from one. It is the tolerance a
# double-precision value written to seventeen significant digits and read back
# survives with room to spare, and a case outside it is refused rather than
# normalised.
UNIT_NORM = 1e-12

# The three-vector fields of an initial state, and the whole of that block.
VECTOR_FIELDS = ("placement", "velocity", "angular_velocity")
INITIAL_FIELDS = ("placement", "orientation", "velocity", "angular_velocity")

# `format` is the version of the format rather than a value of the case, so it
# is the one number a provenance entry does not cover. Every other number in a
# file is covered by exactly one entry.
UNCOVERED_BY_PROVENANCE = ("format",)


class CaseRefused(ValueError):
    """Raised instead of returning a case that is wrong in any way.

    It carries every problem found rather than the first, because a reader that
    stops at the first missing field turns one review into six.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(self.problems))


@dataclass(frozen=True)
class Case:
    """A case that passed every check in this module."""

    content: dict[str, Any]

    @property
    def id(self) -> str:
        return self.content["id"]

    @property
    def case_class(self) -> str:
        return self.content["class"]

    @property
    def body_ids(self) -> tuple[str, ...]:
        return tuple(body["id"] for body in self.content["body"])

    @property
    def content_hash(self) -> str:
        return content_hash(self.content)


def _is_float(value: Any) -> bool:
    """A TOML float. A TOML integer is not one, and neither is a boolean.

    An integer literal where a float belongs is refused rather than widened. The
    numbers in a case file are binary64, a reader that widened an integer would
    be performing a conversion, and a conversion nobody sees is where this
    project's largest class of error lives.
    """
    return isinstance(value, float)


def _keys(problems: list[str], where: str, table: Any, required: tuple[str, ...],
          optional: tuple[str, ...] = ()) -> bool:
    """Refuse a missing key and an undeclared one. False if it is not a table."""
    if not isinstance(table, dict):
        problems.append(f"{where} is {type(table).__name__} and has to be a table")
        return False
    for key in required:
        if key not in table:
            problems.append(f"{where}.{key} is missing")
    allowed = set(required) | set(optional)
    for key in sorted(table):
        if key not in allowed:
            problems.append(
                f"{where}.{key} is not a field of this format, and a field "
                f"nobody reads is a value somebody meant to set"
            )
    return True


def _text(problems: list[str], where: str, table: dict[str, Any], key: str,
          one_line: bool = False) -> None:
    if key not in table:
        return
    value = table[key]
    if not isinstance(value, str):
        problems.append(
            f"{where}.{key} is {type(value).__name__} and has to be a string"
        )
        return
    if not value.strip():
        problems.append(f"{where}.{key} is empty")
        return
    if one_line and "\n" in value.strip():
        problems.append(f"{where}.{key} has to be one line")


def _number(problems: list[str], where: str, table: dict[str, Any], key: str,
            positive: bool = False) -> None:
    if key not in table:
        return
    value = table[key]
    if not _is_float(value):
        problems.append(
            f"{where}.{key} is {type(value).__name__} and has to be a float, "
            f"written with a decimal point"
        )
        return
    if positive and not value > 0.0:
        problems.append(f"{where}.{key} is {value!r} and has to be greater than zero")


def _vector(problems: list[str], where: str, table: dict[str, Any], key: str) -> None:
    if key not in table:
        return
    value = table[key]
    if not isinstance(value, list) or len(value) != 3:
        problems.append(f"{where}.{key} has to be three floats in the world frame")
        return
    for index, component in enumerate(value):
        if not _is_float(component):
            problems.append(
                f"{where}.{key}[{index}] is {type(component).__name__} and has "
                f"to be a float"
            )


def _orientation(problems: list[str], where: str, value: Any) -> None:
    """A unit quaternion with named components, or the one permitted shorthand.

    Named components rather than an ordered list, so the scalar-first against
    scalar-last question is not in the file at all. The sign rule is enforced
    because a quaternion and its negation are the same rotation: without it two
    case files describing one physical state differ in their bytes and in their
    content hash, and read as a physical change in a diff.
    """
    if value == IDENTITY:
        return
    if not _keys(problems, where, value, QUATERNION_COMPONENTS):
        return
    for key in QUATERNION_COMPONENTS:
        _number(problems, where, value, key)
    if any(not _is_float(value.get(key)) for key in QUATERNION_COMPONENTS):
        return

    w, x, y, z = (value[key] for key in QUATERNION_COMPONENTS)
    norm = (w * w + x * x + y * y + z * z) ** 0.5
    if abs(norm - 1.0) > UNIT_NORM:
        problems.append(
            f"{where} has norm {norm!r}, which is further than {UNIT_NORM!r} "
            f"from one, and it is refused rather than normalised"
        )
    if w < 0.0:
        problems.append(
            f"{where}.w is negative, and a quaternion and its negation are the "
            f"same rotation, so this format requires the positive one"
        )
    elif w == 0.0:
        leading = next((c for c in (x, y, z) if c != 0.0), None)
        if leading is not None and leading < 0.0:
            problems.append(
                f"{where} has w equal to zero and the first non-zero of x, y, z "
                f"negative, and this format requires the positive one"
            )


def _bodies(problems: list[str], content: dict[str, Any]) -> list[str]:
    """Validate `[[body]]` and return the body ids that were well formed."""
    bodies = content.get("body")
    if not isinstance(bodies, list) or not bodies:
        problems.append("body is missing, and a case has one or more bodies")
        return []

    ids: list[str] = []
    for index, body in enumerate(bodies):
        where = f"body[{index}]"
        if not _keys(problems, where, body, ("id", "mass", "inertia", "geometry")):
            continue

        # Named by its id from here on, so every path this reports is the path a
        # provenance entry would have to use. A body whose id is unusable keeps
        # its index, because there is nothing better to call it.
        identifier = body.get("id")
        if isinstance(identifier, str) and identifier.strip():
            if identifier in ids:
                problems.append(
                    f"{where}.id is {identifier!r}, which another body in this "
                    f"file already uses, and the initial state names bodies by id"
                )
            else:
                ids.append(identifier)
            where = f"body.{identifier}"

        _text(problems, where, body, "id", one_line=True)
        _number(problems, where, body, "mass", positive=True)

        if "inertia" in body:
            if _keys(problems, f"{where}.inertia", body["inertia"],
                     INERTIA_COMPONENTS):
                for component in INERTIA_COMPONENTS:
                    _number(problems, f"{where}.inertia", body["inertia"], component)

        geometry = body.get("geometry")
        if geometry is not None:
            if not isinstance(geometry, list) or not geometry:
                problems.append(
                    f"{where}.geometry is missing, and a body with no geometry "
                    f"touches nothing, which is a statement a case has to make"
                )
            else:
                for position, shape in enumerate(geometry):
                    place = f"{where}.geometry[{position}]"
                    if _keys(problems, place, shape, ("kind",),
                             ("why", "dimensions", "placement")):
                        _text(problems, place, shape, "kind", one_line=True)
                        _text(problems, place, shape, "why")
    return ids


def _initial(problems: list[str], content: dict[str, Any], ids: list[str]) -> None:
    """The state at time zero, per body, given exactly rather than described."""
    initial = content.get("initial")
    if not isinstance(initial, dict):
        problems.append("initial is missing, and every body starts somewhere")
        return

    for identifier in ids:
        if identifier not in initial:
            problems.append(
                f"initial.{identifier} is missing, and body {identifier!r} has "
                f"no state at time zero"
            )
    for name in sorted(initial):
        if name not in ids:
            problems.append(
                f"initial.{name} names no body in this file"
            )
            continue
        where = f"initial.{name}"
        if not _keys(problems, where, initial[name], INITIAL_FIELDS):
            continue
        for field in VECTOR_FIELDS:
            _vector(problems, where, initial[name], field)
        if "orientation" in initial[name]:
            _orientation(problems, f"{where}.orientation",
                         initial[name]["orientation"])


def _measured(problems: list[str], content: dict[str, Any]) -> None:
    measured = content.get("measured")
    if not _keys(problems, "measured", measured, ("quantity", "units", "why"),
                 ("trajectory",)):
        return
    _text(problems, "measured", measured, "quantity")
    _text(problems, "measured", measured, "units", one_line=True)
    _text(problems, "measured", measured, "why")

    if "trajectory" not in measured:
        return
    where = "measured.trajectory"
    block = measured["trajectory"]
    if not _keys(problems, where, block, ("horizon_seconds", "why")):
        return
    _number(problems, where, block, "horizon_seconds", positive=True)
    _text(problems, where, block, "why")

    # Shorter than the case's own horizon, so asking for trajectory comparison
    # is visibly a request about an early window rather than about the whole
    # run. Refusing the block outright for one class is #76 and is not here.
    horizon = content.get("horizon")
    if isinstance(horizon, dict) and _is_float(horizon.get("seconds")):
        if _is_float(block.get("horizon_seconds")):
            if block["horizon_seconds"] >= horizon["seconds"]:
                problems.append(
                    f"{where}.horizon_seconds is {block['horizon_seconds']!r} "
                    f"and the case's horizon is {horizon['seconds']!r}, so this "
                    f"asks for trajectory agreement over the whole run"
                )


def numeric_paths(content: dict[str, Any]) -> list[str]:
    """Every value in a case a provenance entry has to cover, as a dotted path.

    A quantity is one path even where it is several numbers: an inertia tensor
    is six components of one tensor and an angular velocity is three components
    of one vector, and a provenance entry is about the quantity.

    `format` is excluded, and it is the only exclusion. It is the version of the
    format rather than a value of the case, so there is nothing to source and
    nothing to have chosen.
    """
    paths: list[str] = []

    horizon = content.get("horizon")
    if isinstance(horizon, dict) and "seconds" in horizon:
        paths.append("horizon.seconds")

    for body in content.get("body", []) or []:
        if not isinstance(body, dict) or not isinstance(body.get("id"), str):
            continue
        where = f"body.{body['id']}"
        if "mass" in body:
            paths.append(f"{where}.mass")
        if "inertia" in body:
            paths.append(f"{where}.inertia")
        geometry = body.get("geometry")
        if isinstance(geometry, list):
            for index, shape in enumerate(geometry):
                if not isinstance(shape, dict):
                    continue
                for key in sorted(shape):
                    if _is_float(shape[key]) or _is_list_of_floats(shape[key]):
                        paths.append(f"{where}.geometry.{index}.{key}")

    initial = content.get("initial")
    if isinstance(initial, dict):
        for name in sorted(initial):
            state = initial[name]
            if not isinstance(state, dict):
                continue
            for field in INITIAL_FIELDS:
                if field not in state:
                    continue
                if field == "orientation" and state[field] == IDENTITY:
                    # The shorthand carries no number to account for.
                    continue
                paths.append(f"initial.{name}.{field}")

    for index, constraint in enumerate(content.get("constraint", []) or []):
        if not isinstance(constraint, dict):
            continue
        for key in sorted(constraint):
            if _is_float(constraint[key]) or _is_list_of_floats(constraint[key]):
                paths.append(f"constraint.{index}.{key}")

    measured = content.get("measured")
    if isinstance(measured, dict) and isinstance(measured.get("trajectory"), dict):
        if "horizon_seconds" in measured["trajectory"]:
            paths.append("measured.trajectory.horizon_seconds")

    tolerance = content.get("tolerance")
    if isinstance(tolerance, dict) and "value" in tolerance:
        paths.append("tolerance.value")

    return paths


def _is_list_of_floats(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        _is_float(item) for item in value
    )


def _provenance(problems: list[str], content: dict[str, Any]) -> None:
    """Every number covered by exactly one entry, and every entry about a number.

    This is what makes an invented parameter visible instead of absent. A case
    that made up its inertia says so, with the reason, in the file that
    publishes it, and a case that quietly left a number unaccounted for is
    refused rather than published.

    It fails closed in both directions. An uncovered number is a value nobody
    said where it came from, and an entry naming no value in this file is a
    citation that has come loose from the thing it was citing.
    """
    entries = content.get("provenance")
    if not isinstance(entries, list) or not entries:
        problems.append(
            "provenance is missing, and every number in a case says where it "
            "came from"
        )
        return

    covered: dict[str, int] = {}
    for index, entry in enumerate(entries):
        where = f"provenance[{index}]"
        if not _keys(problems, where, entry, ("field", "kind"), ("citation", "why")):
            continue
        _text(problems, where, entry, "field", one_line=True)
        _text(problems, where, entry, "kind", one_line=True)

        kind = entry.get("kind")
        if isinstance(kind, str) and kind not in PROVENANCE_KINDS:
            problems.append(
                f"{where}.kind is {kind!r}, and this format has "
                f"{' and '.join(repr(k) for k in PROVENANCE_KINDS)}"
            )
        if kind == "sourced":
            if "citation" not in entry:
                problems.append(
                    f"{where}.citation is missing, and a sourced value says "
                    f"precisely enough where it came from that a reader can "
                    f"check it"
                )
            _text(problems, where, entry, "citation")
        if kind == "chosen":
            if "why" not in entry:
                problems.append(
                    f"{where}.why is missing, and a value nobody published "
                    f"carries the reason it is this value"
                )
            _text(problems, where, entry, "why")

        field = entry.get("field")
        if isinstance(field, str):
            covered[field] = covered.get(field, 0) + 1

    paths = numeric_paths(content)
    for path in paths:
        count = covered.get(path, 0)
        if count == 0:
            problems.append(
                f"{path} is a value of this case and no provenance entry covers it"
            )
        elif count > 1:
            problems.append(
                f"{path} is covered by {count} provenance entries, and the rule "
                f"is exactly one"
            )
    for field in sorted(covered):
        if field not in paths:
            problems.append(
                f"provenance names {field}, and there is no such value in this "
                f"file"
            )


def problems(content: Any) -> list[str]:
    """Every way this content is not a case. Empty is the only passing verdict.

    `format` and `convention` short-circuit. A file this reader cannot read at
    all is refused on the field that says so, rather than reported as a heap of
    missing keys that would send a reader looking for the wrong thing.
    """
    found: list[str] = []
    if not isinstance(content, dict):
        return [f"a case is a table and this is {type(content).__name__}"]

    if "format" not in content:
        return ["format is missing, and it is the field that says whether this "
                "reader can read the file at all"]
    if content["format"] != FORMAT or isinstance(content["format"], bool):
        return [f"format is {content['format']!r} and this reader implements "
                f"{FORMAT!r}"]

    if "convention" not in content:
        found.append("convention is missing")
    elif content["convention"] != CONVENTION:
        return [f"convention is {content['convention']!r} and this reader "
                f"implements {CONVENTION!r}, so every number in this file would "
                f"be read under a guess"]

    _keys(
        found,
        "case",
        content,
        ("format", "id", "title", "class", "convention", "summary", "horizon",
         "body", "initial", "contact", "measured", "reference", "tolerance",
         "provenance"),
        ("constraint",),
    )
    _text(found, "case", content, "id", one_line=True)
    _text(found, "case", content, "title", one_line=True)
    _text(found, "case", content, "summary")

    declared = content.get("class")
    if isinstance(declared, str) and declared not in CLASSES:
        found.append(
            f"case.class is {declared!r}, and the vocabulary is "
            f"{', '.join(CLASSES)}"
        )
    elif "class" in content and not isinstance(declared, str):
        found.append(f"case.class is {type(declared).__name__} and has to be a string")

    if "horizon" in content and _keys(found, "horizon", content["horizon"],
                                      ("seconds", "why")):
        _number(found, "horizon", content["horizon"], "seconds", positive=True)
        _text(found, "horizon", content["horizon"], "why")

    ids = _bodies(found, content)
    _initial(found, content, ids)

    for index, constraint in enumerate(content.get("constraint", []) or []):
        where = f"constraint[{index}]"
        if _keys(found, where, constraint, ("kind", "holds")):
            _text(found, where, constraint, "kind")
            _text(found, where, constraint, "holds")

    if "contact" in content and _keys(found, "contact", content["contact"],
                                      ("model", "dissipation")):
        _text(found, "contact", content["contact"], "model")
        # Required even where the answer is none. The two cases in this suite
        # that only do the interesting thing because of dissipation are the two
        # where a default would be invisible.
        _text(found, "contact", content["contact"], "dissipation")

    _measured(found, content)

    if "reference" in content and _keys(found, "reference", content["reference"],
                                        ("kind", "statement", "bound")):
        _text(found, "reference", content["reference"], "kind", one_line=True)
        _text(found, "reference", content["reference"], "statement")
        # A reference answer carrying no bound is refused, which is #49. The
        # field is required here so that refusal has something to read.
        _text(found, "reference", content["reference"], "bound")

    if "tolerance" in content and _keys(found, "tolerance", content["tolerance"],
                                        ("value", "units", "why")):
        _number(found, "tolerance", content["tolerance"], "value", positive=True)
        _text(found, "tolerance", content["tolerance"], "units", one_line=True)
        # A tolerance with no derivation is a number somebody chose after seeing
        # a result, and this field is what makes that visible in a diff.
        _text(found, "tolerance", content["tolerance"], "why")

    _provenance(found, content)
    return sorted(set(found))


def canonical(value: Any) -> str:
    """The parsed content as one deterministic string.

    Table keys are ordered, so key order in the file is not content. A list
    whose entries are all tables is ordered by its own canonical form, so moving
    a `[[body]]` block does not change the case; a list of numbers keeps its
    order, because there position is the meaning. Comments and whitespace never
    reach here at all, having been dropped by the parser.

    A float is written by `repr`, which is the shortest string that reads back
    as the same binary64 value, so the canonical form of a number does not
    depend on how it was spelled.
    """
    if isinstance(value, dict):
        inner = ",".join(
            f"{key!r}:{canonical(value[key])}" for key in sorted(value)
        )
        return "{" + inner + "}"
    if isinstance(value, list):
        parts = [canonical(item) for item in value]
        if value and all(isinstance(item, dict) for item in value):
            parts = sorted(parts)
        return "[" + ",".join(parts) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return repr(value)


def content_hash(content: dict[str, Any]) -> str:
    """A stable hash over the parsed content of a case.

    Over the parsed content and not over the file bytes. A result record names
    the case it ran against, and hashing the bytes would make a reformatting
    look like a physics change, which is the one thing a record naming a hash
    must not do. The cost is the other direction and is real: two files whose
    parsed content is identical are one case here, however differently they read
    in a diff.

    `format` is inside the hashed content, so raising a case file's format
    changes its hash and every published number naming the old one is visibly
    about a different file rather than silently about this one.
    """
    return hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()


def problems_of(text: str) -> list[str]:
    """Every way the text of a case file is not a case, without raising.

    The same verdict `loads` acts on, available to a caller that wants to look
    at a file rather than to read it.
    """
    try:
        content = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return [f"the file is not TOML: {error}"]
    return problems(content)


def loads(text: str) -> Case:
    """A validated case from the text of a case file, or a refusal."""
    try:
        content = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise CaseRefused([f"the file is not TOML: {error}"]) from error
    found = problems(content)
    if found:
        raise CaseRefused(found)
    return Case(content)


def read(path: Path) -> Case:
    """A validated case from a file on disk, or a refusal naming the file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise CaseRefused([f"{path} could not be read: {error}"]) from error
    try:
        return loads(text)
    except CaseRefused as refusal:
        raise CaseRefused([f"{path}: {problem}" for problem in refusal.problems])
