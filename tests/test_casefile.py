"""The schema refuses a bad case, the reader returns one or an error, and the
content hash is over the parsed content.

Issue #31. Every fixture below is the clean case with one thing changed, so a
refusal that fired for the wrong reason shows up as the clean case failing
rather than as a green.

The clean case is a fixture and not a case file. It is the worked example from
`docs/decisions/case-file-format.md` with three departures, and each one is a
place where implementing the schema found the document disagreeing with itself
or with the convention it defers to:

- Its `convention` is the identifier
  `docs/decisions/units-frames-and-inertia.md` fixes. The example names
  `unset-pending-13`, which was correct when it was written and is now a value
  no reader implements.
- Its inertia carries all six components. The example carries three, and the
  convention refuses three rather than reading them as a diagonal tensor.
- Its provenance covers every number. The example covers three of seven, so the
  rule the format document states over that table refuses the file the same
  document offers as the worked case.

None of those is a defect in this schema and all three are recorded in #31.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import casefile

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = "cases"

CLEAN = """\
format = 1
id = "torque-free-asymmetric-top-generic"
title = "Torque-free asymmetric top, generic orbit"
class = "integrable"
convention = "pruefstand-units-frames-inertia-1"
summary = \"\"\"
A rigid body with three distinct principal moments, in free rotation with no
applied torque. The spatial angular momentum and the energy are constants of the
motion, so drift in either is drift the integrator introduced.
\"\"\"

[horizon]
seconds = 100.0
why = \"\"\"
Roughly fifty periods of the body-frame motion, which is where a drift small
enough to be plausible still separates from rounding.
\"\"\"

[[body]]
id = "top"
mass = 1.0
inertia = { xx = 1.0, yy = 2.0, zz = 3.0, xy = 0.0, xz = 0.0, yz = 0.0 }

[[body.geometry]]
kind = "none"
why = "Nothing touches the world in this case; the body is in free rotation."

[initial.top]
placement = [0.0, 0.0, 0.0]
orientation = "identity"
velocity = [0.0, 0.0, 0.0]
angular_velocity = [1.0, 0.3, 0.7]

[contact]
model = "none"
dissipation = "none"

[measured]
quantity = "relative drift in the spatial angular momentum vector"
units = "dimensionless"
why = \"\"\"
The spatial angular momentum is exactly conserved by the continuous system, so
any change in it over the horizon was introduced by the integrator.
\"\"\"

[reference]
kind = "closed-form"
statement = \"\"\"
The Jacobi solution for the free asymmetric top.
\"\"\"
bound = \"\"\"
A property of the evaluation rather than of this case.
\"\"\"

[tolerance]
value = 1e-9
units = "dimensionless"
why = \"\"\"
Placeholder, and this field is where saying so belongs.
\"\"\"

[[provenance]]
field = "horizon.seconds"
kind = "chosen"
why = "Fifty periods, for the reason the horizon's own field gives."

[[provenance]]
field = "body.top.mass"
kind = "chosen"
why = "A torque-free top's motion does not depend on its mass."

[[provenance]]
field = "body.top.inertia"
kind = "chosen"
why = "Three distinct principal moments, spread widely enough to be unambiguous."

[[provenance]]
field = "initial.top.placement"
kind = "chosen"
why = "The origin. Nothing in this case depends on where the body is."

[[provenance]]
field = "initial.top.velocity"
kind = "chosen"
why = "At rest in translation, so the motion is rotation alone."

[[provenance]]
field = "initial.top.angular_velocity"
kind = "chosen"
why = "Away from the separatrix, where the closed form is well conditioned."

[[provenance]]
field = "tolerance.value"
kind = "chosen"
why = "Placeholder, for the reason the tolerance's own field gives."
"""


def changed(old: str, new: str) -> str:
    """The clean case with one thing changed. Refuses a replacement that missed.

    Without this the fixture for a refusal could silently be the clean case, and
    the test would then be asserting that the clean case is refused.
    """
    if old not in CLEAN:
        raise AssertionError(f"{old!r} is not in the clean case")
    return CLEAN.replace(old, new, 1)


def with_orientation(spelling: str) -> str:
    """The clean case with its orientation written out, and accounted for.

    A written-out orientation is four numbers, so it needs a provenance entry
    the shorthand does not. Every fixture that replaces the shorthand goes
    through here, so a refusal about the orientation is about the orientation.
    """
    text = changed('orientation = "identity"', f"orientation = {spelling}")
    return text.replace(
        '[[provenance]]\nfield = "tolerance.value"',
        '[[provenance]]\nfield = "initial.top.orientation"\n'
        'kind = "chosen"\n'
        'why = "Written out rather than taken from the shorthand."\n\n'
        '[[provenance]]\nfield = "tolerance.value"',
        1,
    )


def refusal(text: str) -> tuple[str, ...]:
    try:
        casefile.loads(text)
    except casefile.CaseRefused as refused:
        return refused.problems
    raise AssertionError("the case was accepted")


class TheCleanCaseIsAccepted(unittest.TestCase):
    """The near-miss under everything below. A schema that refused this would
    make every refusal in this file pass for the wrong reason."""

    def test_it_parses(self) -> None:
        self.assertEqual(casefile.problems_of(CLEAN), [])

    def test_it_carries_what_a_reader_asks_it_for(self) -> None:
        case = casefile.loads(CLEAN)
        self.assertEqual(case.id, "torque-free-asymmetric-top-generic")
        self.assertEqual(case.case_class, "integrable")
        self.assertEqual(case.body_ids, ("top",))


class TheFileIsRefusedByVersionFirst(unittest.TestCase):
    def test_an_unimplemented_format_is_refused_on_that_field_alone(self) -> None:
        # The difference between "this suite is too old for this case" and a
        # stack trace about a missing key. A reader that reported the whole file
        # would send somebody looking for the wrong thing.
        problems = refusal(changed("format = 1", "format = 2"))
        self.assertEqual(len(problems), 1)
        self.assertIn("this reader implements 1", problems[0])

    def test_a_missing_format_is_refused_on_that_field_alone(self) -> None:
        problems = refusal(CLEAN.replace("format = 1\n", "", 1))
        self.assertEqual(len(problems), 1)
        self.assertIn("format is missing", problems[0])

    def test_a_boolean_format_is_not_read_as_one(self) -> None:
        # The one-character mistake a hand-written file makes: in Python a
        # boolean is an integer, so `format = true` compares equal to 1 and a
        # reader without this line would accept it.
        problems = refusal(changed("format = 1", "format = true"))
        self.assertEqual(len(problems), 1)
        self.assertIn("format is True", problems[0])

    def test_an_unimplemented_convention_is_refused_rather_than_guessed(self) -> None:
        problems = refusal(
            changed('convention = "pruefstand-units-frames-inertia-1"',
                    'convention = "unset-pending-13"')
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("read under a guess", problems[0])


class AMissingFieldIsNamed(unittest.TestCase):
    def test_the_field_is_named_and_not_only_the_block(self) -> None:
        problems = refusal(changed('units = "dimensionless"\nwhy = """\nPlaceholder',
                                   'why = """\nPlaceholder'))
        self.assertIn("tolerance.units is missing", problems)

    def test_a_missing_dissipation_is_refused_even_where_it_is_none(self) -> None:
        # Required even when the answer is none. The two cases in this suite
        # that only do the interesting thing because of dissipation are the two
        # where a default would be invisible.
        problems = refusal(changed('dissipation = "none"\n', ""))
        self.assertIn("contact.dissipation is missing", problems)

    def test_a_missing_reference_bound_is_refused(self) -> None:
        problems = refusal(
            changed('bound = """\nA property of the evaluation rather than of '
                    'this case.\n"""\n', "")
        )
        self.assertIn("reference.bound is missing", problems)

    def test_a_missing_tolerance_derivation_is_refused(self) -> None:
        problems = refusal(
            changed('why = """\nPlaceholder, and this field is where saying so '
                    'belongs.\n"""\n', "")
        )
        self.assertIn("tolerance.why is missing", problems)

    def test_every_problem_is_reported_rather_than_the_first(self) -> None:
        # A reader that stopped at the first missing field would turn one review
        # into six.
        text = changed('dissipation = "none"\n', "")
        text = text.replace('units = "dimensionless"\nwhy = """\nPlaceholder',
                            'why = """\nPlaceholder', 1)
        problems = refusal(text)
        self.assertIn("contact.dissipation is missing", problems)
        self.assertIn("tolerance.units is missing", problems)


class AnUndeclaredFieldIsRefused(unittest.TestCase):
    def test_a_field_this_format_does_not_have_is_refused(self) -> None:
        # A field nobody reads is a value somebody meant to set. This is also
        # where the units rule lands: a case that writes a unit beside a number
        # has either put a string where a float belongs or added a key nobody
        # declared, and both are refused.
        problems = refusal(changed("seconds = 100.0", "seconds = 100.0\nunits = \"s\""))
        self.assertTrue(any("horizon.units is not a field" in p for p in problems))

    def test_a_body_frame_spelling_under_the_bare_name_is_refused(self) -> None:
        # Every vector in a case file is in the world frame, and the body-frame
        # quantity carries `_body` in its name. Nothing may carry a body-frame
        # angular velocity, so the key is refused rather than read.
        problems = refusal(
            changed("angular_velocity = [1.0, 0.3, 0.7]",
                    "angular_velocity = [1.0, 0.3, 0.7]\n"
                    "angular_velocity_body = [1.0, 0.3, 0.7]")
        )
        self.assertTrue(
            any("initial.top.angular_velocity_body is not a field" in p
                for p in problems)
        )


class TheTypeOfANumber(unittest.TestCase):
    def test_an_integer_where_a_float_belongs_is_refused(self) -> None:
        # The numbers in a case file are binary64. A reader that widened an
        # integer would be performing a conversion, and a conversion nobody sees
        # is where this project's largest class of error lives.
        problems = refusal(changed("mass = 1.0", "mass = 1"))
        self.assertTrue(any("body.top.mass is int" in p for p in problems))

    def test_a_number_written_as_a_string_is_refused(self) -> None:
        problems = refusal(changed("seconds = 100.0", 'seconds = "100.0 s"'))
        self.assertTrue(any("horizon.seconds is str" in p for p in problems))

    def test_a_horizon_of_zero_is_refused(self) -> None:
        problems = refusal(changed("seconds = 100.0", "seconds = 0.0"))
        self.assertTrue(any("greater than zero" in p for p in problems))


class TheClassVocabulary(unittest.TestCase):
    def test_a_class_outside_the_vocabulary_is_refused(self) -> None:
        problems = refusal(changed('class = "integrable"', 'class = "conservative"'))
        self.assertTrue(any("case.class is 'conservative'" in p for p in problems))

    def test_every_declared_class_is_accepted(self) -> None:
        # Without this the check could be refusing four of the five and passing
        # every other test in this file.
        for name in casefile.CLASSES:
            with self.subTest(declared=name):
                text = changed('class = "integrable"', f'class = "{name}"')
                self.assertEqual(casefile.problems_of(text), [])


class TheInertiaTensor(unittest.TestCase):
    def test_three_components_are_refused_rather_than_read_as_diagonal(self) -> None:
        # The refusal the rattleback needs. A reader filling the missing
        # components with zero would accept a body whose skew somebody forgot to
        # write and would run it as a body with no chirality.
        problems = refusal(
            changed("inertia = { xx = 1.0, yy = 2.0, zz = 3.0, xy = 0.0, "
                    "xz = 0.0, yz = 0.0 }",
                    "inertia = { xx = 1.0, yy = 2.0, zz = 3.0 }")
        )
        for component in ("xy", "xz", "yz"):
            self.assertIn(f"body.top.inertia.{component} is missing", problems)

    def test_a_skewed_tensor_is_accepted(self) -> None:
        # The case this whole format exists for. A rattleback's body frame is
        # not a principal frame, and the schema has to be able to say so.
        text = changed(
            "inertia = { xx = 1.0, yy = 2.0, zz = 3.0, xy = 0.0, xz = 0.0, "
            "yz = 0.0 }",
            "inertia = { xx = 1.0669952663115909e-05, yy = 3.933004733688409e-05, "
            "zz = 4.5e-05, xy = -4.432803099920094e-06, xz = 0.0, yz = 0.0 }",
        )
        self.assertEqual(casefile.problems_of(text), [])


class TheOrientation(unittest.TestCase):
    def test_the_shorthand_is_permitted(self) -> None:
        # It is in the worked example of the format document, so a schema
        # refusing it would refuse the document that introduced it.
        self.assertEqual(casefile.problems_of(CLEAN), [])

    def test_named_components_are_accepted(self) -> None:
        text = with_orientation("{ w = 1.0, x = 0.0, y = 0.0, z = 0.0 }")
        self.assertEqual(casefile.problems_of(text), [])

    def test_an_ordered_list_is_refused(self) -> None:
        # Naming the components is what removes the scalar-first against
        # scalar-last question from the file, so the ordered spelling is refused
        # rather than read under one of the two orderings.
        problems = refusal(with_orientation("[1.0, 0.0, 0.0, 0.0]"))
        self.assertTrue(any("has to be a table" in p for p in problems))

    def test_a_quaternion_that_is_not_a_unit_is_refused(self) -> None:
        problems = refusal(with_orientation("{ w = 0.9, x = 0.0, y = 0.0, z = 0.0 }"))
        self.assertTrue(any("refused rather than normalised" in p for p in problems))

    def test_a_quaternion_just_inside_the_tolerance_is_accepted(self) -> None:
        # The near-miss on the tolerance itself. A check comparing against zero
        # rather than against 1e-12 would refuse every quaternion written to
        # seventeen digits.
        text = with_orientation(
            "{ w = 1.0000000000005, x = 0.0, y = 0.0, z = 0.0 }"
        )
        self.assertEqual(casefile.problems_of(text), [])

    def test_the_negated_quaternion_is_refused(self) -> None:
        # A quaternion and its negation are the same rotation. Without the sign
        # rule two files describing one physical state differ in their content
        # hash and read as a physical change in a diff.
        problems = refusal(with_orientation("{ w = -1.0, x = 0.0, y = 0.0, z = 0.0 }"))
        self.assertTrue(any("initial.top.orientation.w is negative" in p
                            for p in problems))

    def test_a_half_turn_takes_the_positive_spelling(self) -> None:
        negative = with_orientation("{ w = 0.0, x = -1.0, y = 0.0, z = 0.0 }")
        positive = with_orientation("{ w = 0.0, x = 1.0, y = 0.0, z = 0.0 }")
        self.assertTrue(any("first non-zero" in p for p in refusal(negative)))
        self.assertEqual(casefile.problems_of(positive), [])


class TheBodiesAndTheirInitialState(unittest.TestCase):
    def test_two_bodies_with_one_id_are_refused(self) -> None:
        # The initial state names bodies by id, so two bodies under one id is a
        # file in which one of them has no state and nothing says which.
        text = changed('[initial.top]', '[[body]]\nid = "top"\nmass = 2.0\n'
                       'inertia = { xx = 1.0, yy = 1.0, zz = 1.0, xy = 0.0, '
                       'xz = 0.0, yz = 0.0 }\n\n[[body.geometry]]\n'
                       'kind = "none"\n\n[initial.top]')
        self.assertTrue(any("already uses" in p for p in refusal(text)))

    def test_a_body_with_no_initial_state_is_refused(self) -> None:
        text = changed("[initial.top]", "[initial.other]")
        problems = refusal(text)
        self.assertIn("initial.top is missing, and body 'top' has no state at "
                      "time zero", problems)

    def test_an_initial_state_naming_no_body_is_refused(self) -> None:
        text = changed("[initial.top]", "[initial.top]\n\n[initial.ghost]")
        self.assertIn("initial.ghost names no body in this file", refusal(text))

    def test_a_body_with_no_geometry_block_is_refused(self) -> None:
        # A body with no geometry touches nothing, which is legitimate for a
        # torque-free top and a defect for a rolling disk. The difference is
        # visible only because the block is required and says `kind = "none"`.
        text = changed('[[body.geometry]]\nkind = "none"\nwhy = "Nothing touches '
                       'the world in this case; the body is in free rotation."\n',
                       "")
        self.assertTrue(any("body[0].geometry is missing" in p
                            for p in refusal(text)))


class TheTrajectoryBlock(unittest.TestCase):
    def test_a_shorter_horizon_is_accepted(self) -> None:
        text = changed('[reference]',
                       '[measured.trajectory]\nhorizon_seconds = 5.0\n'
                       'why = "Agreement is expected over the first few periods."\n'
                       '\n[reference]')
        text = text.replace('field = "tolerance.value"',
                            'field = "measured.trajectory.horizon_seconds"\n'
                            'kind = "chosen"\n'
                            'why = "Five periods."\n\n[[provenance]]\n'
                            'field = "tolerance.value"', 1)
        self.assertEqual(casefile.problems_of(text), [])

    def test_a_horizon_reaching_the_whole_run_is_refused(self) -> None:
        # There is no way to ask for trajectory comparison over the case's own
        # horizon by omission, and this closes the other route to the same ask.
        text = changed('[reference]',
                       '[measured.trajectory]\nhorizon_seconds = 100.0\n'
                       'why = "Over the whole run."\n\n[reference]')
        text = text.replace('field = "tolerance.value"',
                            'field = "measured.trajectory.horizon_seconds"\n'
                            'kind = "chosen"\n'
                            'why = "The whole run."\n\n[[provenance]]\n'
                            'field = "tolerance.value"', 1)
        self.assertTrue(any("trajectory agreement over the whole run" in p
                            for p in refusal(text)))


class TheProvenanceCovering(unittest.TestCase):
    def test_an_uncovered_number_is_refused(self) -> None:
        # What makes an invented parameter visible instead of absent.
        text = changed('[[provenance]]\nfield = "body.top.mass"\n'
                       'kind = "chosen"\n'
                       'why = "A torque-free top\'s motion does not depend on '
                       'its mass."\n\n', "")
        self.assertIn("body.top.mass is a value of this case and no provenance "
                      "entry covers it", refusal(text))

    def test_a_number_covered_twice_is_refused(self) -> None:
        text = changed('field = "body.top.mass"', 'field = "horizon.seconds"')
        self.assertTrue(any("covered by 2 provenance entries" in p
                            for p in refusal(text)))

    def test_an_entry_naming_no_value_is_refused(self) -> None:
        # A citation that has come loose from the thing it was citing.
        text = changed('field = "body.top.mass"', 'field = "body.top.density"')
        self.assertIn("provenance names body.top.density, and there is no such "
                      "value in this file", refusal(text))

    def test_a_sourced_value_with_no_citation_is_refused(self) -> None:
        text = changed('field = "body.top.inertia"\nkind = "chosen"\n'
                       'why = "Three distinct principal moments, spread widely '
                       'enough to be unambiguous."',
                       'field = "body.top.inertia"\nkind = "sourced"')
        self.assertTrue(any("provenance[2].citation is missing" in p
                            for p in refusal(text)))

    def test_a_chosen_value_with_no_reason_is_refused(self) -> None:
        text = changed('kind = "chosen"\nwhy = "Fifty periods, for the reason '
                       'the horizon\'s own field gives."',
                       'kind = "chosen"')
        self.assertTrue(any("provenance[0].why is missing" in p
                            for p in refusal(text)))

    def test_a_kind_outside_the_two_is_refused(self) -> None:
        text = changed('kind = "chosen"\nwhy = "Fifty periods, for the reason '
                       'the horizon\'s own field gives."',
                       'kind = "assumed"\nwhy = "Fifty periods."')
        self.assertTrue(any("provenance[0].kind is 'assumed'" in p
                            for p in refusal(text)))

    def test_the_orientation_shorthand_needs_no_entry(self) -> None:
        # It carries no number, so requiring an entry for it would be the
        # covering rule reaching past what it is about.
        self.assertNotIn("initial.top.orientation", casefile.numeric_paths(
            casefile.loads(CLEAN).content))

    def test_a_written_out_orientation_needs_one(self) -> None:
        text = with_orientation("{ w = 1.0, x = 0.0, y = 0.0, z = 0.0 }")
        self.assertIn("initial.top.orientation",
                      casefile.numeric_paths(casefile.loads(text).content))


class TheContentHash(unittest.TestCase):
    def test_it_is_stable_across_reformatting(self) -> None:
        # Over the parsed content and not over the file bytes. Hashing the bytes
        # would make a reformatting look like a physics change, which is the one
        # thing a hash a result record names must not do.
        reformatted = CLEAN.replace("mass = 1.0", "# a comment nobody parses\nmass  =  1.0")
        reformatted = reformatted.replace(
            'id = "torque-free-asymmetric-top-generic"\n'
            'title = "Torque-free asymmetric top, generic orbit"',
            'title = "Torque-free asymmetric top, generic orbit"\n'
            'id = "torque-free-asymmetric-top-generic"',
        )
        self.assertEqual(
            casefile.loads(CLEAN).content_hash,
            casefile.loads(reformatted).content_hash,
        )

    def test_a_number_spelled_differently_is_the_same_case(self) -> None:
        self.assertEqual(
            casefile.loads(CLEAN).content_hash,
            casefile.loads(changed("mass = 1.0", "mass = 1.00")).content_hash,
        )

    def test_moving_a_provenance_block_is_not_a_change(self) -> None:
        moved = changed('[[provenance]]\nfield = "horizon.seconds"\n'
                        'kind = "chosen"\n'
                        'why = "Fifty periods, for the reason the horizon\'s own '
                        'field gives."\n\n', "")
        moved += (
            '\n[[provenance]]\nfield = "horizon.seconds"\nkind = "chosen"\n'
            'why = "Fifty periods, for the reason the horizon\'s own field '
            'gives."\n'
        )
        self.assertEqual(
            casefile.loads(CLEAN).content_hash,
            casefile.loads(moved).content_hash,
        )

    def test_a_physical_change_changes_it(self) -> None:
        self.assertNotEqual(
            casefile.loads(CLEAN).content_hash,
            casefile.loads(changed("mass = 1.0", "mass = 1.5")).content_hash,
        )

    def test_the_two_chiralities_are_different_cases(self) -> None:
        # The change this hash exists to make visible. The rattleback and its
        # mirror differ in the sign of one inertia component and in nothing
        # else, and they reverse from opposite spin senses.
        skewed = changed(
            "inertia = { xx = 1.0, yy = 2.0, zz = 3.0, xy = 0.0, xz = 0.0, "
            "yz = 0.0 }",
            "inertia = { xx = 1.0669952663115909e-05, yy = 3.933004733688409e-05, "
            "zz = 4.5e-05, xy = -4.432803099920094e-06, xz = 0.0, yz = 0.0 }",
        )
        mirror = skewed.replace("xy = -4.432803099920094e-06",
                                "xy = 4.432803099920094e-06")
        self.assertNotEqual(
            casefile.loads(skewed).content_hash,
            casefile.loads(mirror).content_hash,
        )

    def test_raising_the_format_changes_it(self) -> None:
        # A published number naming the old hash is then visibly about a
        # different file rather than silently about this one.
        content = dict(casefile.loads(CLEAN).content)
        raised = dict(content, format=2)
        self.assertNotEqual(
            casefile.content_hash(content), casefile.content_hash(raised)
        )

    def test_it_is_a_sha256_digest(self) -> None:
        digest = casefile.loads(CLEAN).content_hash
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))


class TheReader(unittest.TestCase):
    def test_a_file_that_is_not_toml_is_refused_rather_than_raising(self) -> None:
        problems = refusal("this is not a case file at all\n")
        self.assertEqual(len(problems), 1)
        self.assertIn("not TOML", problems[0])

    def test_a_file_on_disk_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "case.toml"
            path.write_text(CLEAN, encoding="utf-8")
            self.assertEqual(casefile.read(path).id,
                             "torque-free-asymmetric-top-generic")

    def test_a_refusal_from_disk_names_the_file(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "case.toml"
            path.write_text(changed("format = 1", "format = 2"), encoding="utf-8")
            with self.assertRaises(casefile.CaseRefused) as caught:
                casefile.read(path)
        self.assertIn("case.toml", caught.exception.problems[0])

    def test_a_missing_file_is_refused_rather_than_raising_an_os_error(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaises(casefile.CaseRefused):
                casefile.read(Path(name) / "absent.toml")


def case_files(root: Path) -> list[Path]:
    directory = root / CASES_DIR
    if not directory.is_dir():
        return []
    return sorted(directory.rglob("*.toml"))


class TheCasesInThisTree(unittest.TestCase):
    def test_every_case_file_parses(self) -> None:
        for path in case_files(REPO_ROOT):
            with self.subTest(case=path.name):
                casefile.read(path)

    def test_there_is_still_no_case_file(self) -> None:
        # A green over an empty directory is the shape #30 is about, so the
        # emptiness is asserted rather than passed over, and this test reds the
        # day the first case lands. That is the intended trigger: #31 stays open
        # on its fourth done-when, at least one case file per class, and
        # whoever adds the first one is the person who should read it.
        found = case_files(REPO_ROOT)
        self.assertEqual(
            [path.name for path in found],
            [],
            "a case file has landed; #31's fourth done-when is what this test "
            "is holding open, and this assertion is what needs replacing with a "
            "floor",
        )


if __name__ == "__main__":
    unittest.main()
