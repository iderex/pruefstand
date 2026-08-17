"""The numbers in a case are a rigid body, and every refusal is tripped.

Issue #32. Every fixture below is a case that passes the schema with one number
changed, so a refusal firing for the wrong reason shows up as the clean case
failing rather than as a green.

The clean case is a rattleback rather than the torque-free top the schema's own
tests use, on purpose. The issue says the triangle inequality is the condition
that matters most and that the rattleback is the file somebody will write by hand
and get subtly wrong, because its principal axes are skewed relative to its
geometry. A fixture with a diagonal tensor would test the branch of the eigenvalue
routine that reads the diagonal off and would never reach the trigonometry the
rest of it is.

The tolerance is not written into this file. It is measured here, against tensors
built out of eigenvalues chosen before the tensor existed, and what the module
carries has to sit above what the measurement finds.

    python -m unittest discover -s tests -k casephysics
"""

from __future__ import annotations

import math
import random
import tempfile
import unittest
from pathlib import Path

import casefile
import casephysics
from casephysics import (
    INERTIA_TOLERANCE,
    deviatoric_moments,
    principal_moments,
    problems,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = "cases"

# The working precision, which is what the measured error below is quoted in.
EPSILON = 2.220446049250313e-16

# A rattleback, in the shape the format fixes: a body whose principal axes are
# skewed relative to its geometry, so its tensor is not diagonal and the numbers
# in it cannot be checked by looking at them. The values are a fixture and not a
# case of this suite; the rattleback's sourced parameters are #68.
CLEAN = """\
format = 1
id = "rattleback-fixture"
title = "Rattleback, as a fixture for the physics validator"
class = "qualitative"
convention = "pruefstand-units-frames-inertia-1"
summary = \"\"\"
A body whose principal axes are rotated relative to the axes of its own surface,
which is what makes a rattleback prefer one direction of spin. Here it exists to
carry a tensor that is not diagonal.
\"\"\"

[horizon]
seconds = 30.0
why = \"\"\"
Long enough for several reversals at these parameters, which is what a case about
reversal has to carry.
\"\"\"

[[body]]
id = "stone"
mass = 0.02
inertia = { xx = 1.2e-5, yy = 4.0e-5, zz = 4.6e-5, xy = 6.0e-6, xz = 0.0, yz = 0.0 }

[[body.geometry]]
kind = "ellipsoid"
why = "The surface that touches the table, and the axes the inertia is skewed against."

[initial.stone]
placement = [0.0, 0.0, 0.0]
orientation = "identity"
velocity = [0.0, 0.0, 0.0]
angular_velocity = [0.0, 0.0, 3.0]

[contact]
model = "rolling without slipping at a single point"
dissipation = "none"

[measured]
quantity = "the number of spin reversals and the direction of each"
units = "count"
why = \"\"\"
A reversal is the effect this body exists to show, and its direction is the half
an engine gets backwards.
\"\"\"

[reference]
kind = "computed"
statement = \"\"\"
The constrained equations, solved directly. The non-holonomic reference is #48.
\"\"\"
bound = \"\"\"
A property of that computation rather than of this fixture.
\"\"\"

[tolerance]
value = 1e-9
units = "dimensionless"
why = \"\"\"
Placeholder. This fixture exists to carry an inertia tensor and is not a case.
\"\"\"

[[provenance]]
field = "horizon.seconds"
kind = "chosen"
why = "Several reversals, for the reason the horizon's own field gives."

[[provenance]]
field = "body.stone.mass"
kind = "chosen"
why = "A fixture rather than a sourced body; the sourced one is #68."

[[provenance]]
field = "body.stone.inertia"
kind = "chosen"
why = "Skewed off the geometry's axes, which is the whole point of the shape."

[[provenance]]
field = "initial.stone.placement"
kind = "chosen"
why = "The origin. Nothing in this fixture depends on where the body is."

[[provenance]]
field = "initial.stone.velocity"
kind = "chosen"
why = "At rest in translation, so the motion is rotation alone."

[[provenance]]
field = "initial.stone.angular_velocity"
kind = "chosen"
why = "Spinning about the vertical, which is the condition a reversal starts from."

[[provenance]]
field = "tolerance.value"
kind = "chosen"
why = "Placeholder, for the reason the tolerance's own field gives."
"""


def content_with(**inertia: float) -> dict:
    """The clean case with the named inertia components replaced."""
    content = casefile.loads(CLEAN).content
    content["body"][0]["inertia"] = dict(content["body"][0]["inertia"], **inertia)
    return content


def rotated(moments: tuple[float, float, float], axis, angle: float):
    """A symmetric tensor with the given eigenvalues, built by rotating a diagonal.

    Written out here rather than imported, because the point of the measurement it
    feeds is that the eigenvalues are known before the tensor exists.
    """
    length = math.sqrt(sum(component * component for component in axis))
    x, y, z = (component / length for component in axis)
    cosine, sine = math.cos(angle), math.sin(angle)
    rotation = (
        (cosine + x * x * (1 - cosine), x * y * (1 - cosine) - z * sine,
         x * z * (1 - cosine) + y * sine),
        (y * x * (1 - cosine) + z * sine, cosine + y * y * (1 - cosine),
         y * z * (1 - cosine) - x * sine),
        (z * x * (1 - cosine) - y * sine, z * y * (1 - cosine) + x * sine,
         cosine + z * z * (1 - cosine)),
    )
    built = [
        [sum(rotation[row][k] * moments[k] * rotation[column][k] for k in range(3))
         for column in range(3)]
        for row in range(3)
    ]
    # Symmetrised, so the input is exactly symmetric and the measurement below is
    # of the eigenvalue routine rather than of this fixture's own rounding.
    return tuple(
        tuple(0.5 * (built[row][column] + built[column][row]) for column in range(3))
        for row in range(3)
    )


class TheCleanCaseIsABody(unittest.TestCase):
    """Without this every refusal below could be firing on the fixture itself."""

    def test_the_schema_accepts_it(self) -> None:
        self.assertEqual(casefile.problems_of(CLEAN), [])

    def test_the_physics_accepts_it(self) -> None:
        self.assertEqual(problems(casefile.loads(CLEAN).content), [])

    def test_its_tensor_is_not_diagonal(self) -> None:
        # The fixture reaches the trigonometric branch rather than the branch that
        # reads a diagonal off, and a fixture that stopped doing so would leave
        # every refusal below proved on the easy half of the routine.
        inertia = casefile.loads(CLEAN).content["body"][0]["inertia"]
        self.assertNotEqual((inertia["xy"], inertia["xz"], inertia["yz"]),
                            (0.0, 0.0, 0.0))

    def test_loads_returns_a_case(self) -> None:
        self.assertEqual(casephysics.loads(CLEAN).id, "rattleback-fixture")


class ATensorThatIsNotABody(unittest.TestCase):
    """One condition per fixture, each the clean case with one number changed."""

    def refusal(self, **inertia: float) -> str:
        found = problems(content_with(**inertia))
        self.assertEqual(len(found), 1, found)
        return found[0]

    def test_six_zeros_are_refused(self) -> None:
        # The case `casefile.py` names in its own docstring as the one it accepts
        # and should not.
        message = self.refusal(xx=0.0, yy=0.0, zz=0.0, xy=0.0, xz=0.0, yz=0.0)
        self.assertIn("trace", message)
        self.assertIn("not a body", message)

    def test_a_negative_principal_moment_is_refused(self) -> None:
        message = self.refusal(xx=-1.2e-5)
        self.assertIn("not positive definite", message)

    def test_a_zero_principal_moment_is_refused(self) -> None:
        # A body with a moment of zero is a line, and the reference cannot invert
        # its tensor into an angular velocity.
        message = self.refusal(xx=0.0, xy=0.0)
        self.assertIn("not positive definite", message)

    def test_an_off_diagonal_large_enough_to_break_definiteness_is_refused(self) -> None:
        message = self.refusal(xy=1.0e-4)
        self.assertIn("not positive definite", message)

    def test_a_moment_exceeding_the_sum_of_the_other_two_is_refused(self) -> None:
        message = self.refusal(zz=6.0e-5)
        self.assertIn("exceeds the sum of the other two", message)

    def test_the_refusal_prints_the_value_and_the_bound(self) -> None:
        message = self.refusal(zz=6.0e-5)
        # The done-when asks for both, so both are asserted rather than assumed
        # from the sentence reading well.
        self.assertIn("against a bound of", message)
        moments = principal_moments(
            casephysics._tensor(content_with(zz=6.0e-5)["body"][0]["inertia"])
        )
        self.assertIn(repr(moments[0]), message)

    def test_a_body_on_the_triangle_inequality_is_accepted(self) -> None:
        # A flat body satisfies one inequality exactly. Refusing it would refuse
        # Euler's disk, which is #58, before it is written.
        content = content_with(xx=2.0e-5, yy=2.0e-5, zz=4.0e-5, xy=0.0)
        self.assertEqual(problems(content), [])

    def test_every_body_in_a_case_is_reached(self) -> None:
        content = casefile.loads(CLEAN).content
        second = dict(content["body"][0])
        second["id"] = "second"
        second["inertia"] = dict(second["inertia"], zz=6.0e-5)
        content["body"] = [content["body"][0], second]
        found = problems(content)
        self.assertEqual(len(found), 1, found)
        self.assertIn("body.second.inertia", found[0])

    def test_refuse_raises_what_the_schema_raises(self) -> None:
        with self.assertRaises(casefile.CaseRefused):
            casephysics.refuse(content_with(zz=6.0e-5))

    def test_loads_refuses_a_document_that_is_not_a_body(self) -> None:
        text = CLEAN.replace("zz = 4.6e-5", "zz = 6.0e-5")
        with self.assertRaises(casefile.CaseRefused) as refused:
            casephysics.loads(text)
        self.assertIn("exceeds the sum of the other two", str(refused.exception))

    def test_read_puts_the_path_in_front_of_the_problem(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.toml"
            path.write_text(CLEAN.replace("zz = 4.6e-5", "zz = 6.0e-5"),
                            encoding="utf-8")
            with self.assertRaises(casefile.CaseRefused) as refused:
                casephysics.read(path)
            self.assertIn(str(path), str(refused.exception))

    def test_read_returns_a_case_for_a_file_that_is_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clean.toml"
            path.write_text(CLEAN, encoding="utf-8")
            self.assertEqual(casephysics.read(path).id, "rattleback-fixture")

    def test_the_schema_still_runs_first(self) -> None:
        # A file that is not a document at all gets the schema's message and not a
        # physics message about a field that is absent.
        with self.assertRaises(casefile.CaseRefused) as refused:
            casephysics.loads(CLEAN.replace('id = "stone"', 'id = ""'))
        self.assertNotIn("principal moments", str(refused.exception))


class TheEigenvalueRoutine(unittest.TestCase):
    """What the tolerance is sized against, measured rather than assumed."""

    def test_a_diagonal_tensor_is_read_off_exactly(self) -> None:
        self.assertEqual(
            principal_moments(((1.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 2.0))),
            (3.0, 2.0, 1.0),
        )

    def test_a_repeated_eigenvalue_does_not_raise(self) -> None:
        # The branch the clamp exists for. Rounding puts the scaled determinant a
        # few units in the last place outside the range the arc cosine takes.
        tensor = rotated((2.0, 2.0, 5.0), (1.0, 1.0, 1.0), 0.7)
        moments = principal_moments(tensor)
        self.assertAlmostEqual(moments[0], 5.0, places=12)
        self.assertAlmostEqual(moments[2], 2.0, places=12)

    def test_three_equal_eigenvalues_are_returned(self) -> None:
        tensor = rotated((4.0, 4.0, 4.0), (0.3, -0.5, 0.8), 1.1)
        for moment in principal_moments(tensor):
            self.assertAlmostEqual(moment, 4.0, places=12)

    def test_the_moments_sum_to_the_trace(self) -> None:
        tensor = rotated((1.0, 2.5, 3.25), (0.2, 0.9, -0.4), 0.9)
        trace = tensor[0][0] + tensor[1][1] + tensor[2][2]
        self.assertAlmostEqual(sum(principal_moments(tensor)) / trace, 1.0, places=15)

    def test_the_worst_error_over_many_tensors_is_below_the_tolerance(self) -> None:
        # The measurement the tolerance is derived from. The eigenvalues are chosen
        # first and the tensor is built from them, so the comparison is against a
        # number this module never computed.
        source = random.Random(32)
        worst = 0.0
        for _ in range(10000):
            moments = tuple(sorted(
                (source.uniform(0.1, 10.0) for _ in range(3)), reverse=True))
            axis = tuple(source.uniform(-1.0, 1.0) for _ in range(3))
            if axis == (0.0, 0.0, 0.0):
                continue
            tensor = rotated(moments, axis, source.uniform(0.0, math.pi))
            trace = tensor[0][0] + tensor[1][1] + tensor[2][2]
            got = principal_moments(tensor)
            worst = max(worst, max(abs(a - b) for a, b in zip(got, moments)) / trace)
        # Recorded rather than only bounded, so a change that costs the routine
        # accuracy is visible as a number moving and not only as a pass.
        self.assertGreater(worst, 0.0)
        self.assertLess(worst, 1e-11)
        self.assertLess(worst * 100.0, INERTIA_TOLERANCE)
        self.assertGreater(worst / EPSILON, 1.0)

    def test_the_deviatoric_moments_are_the_slack_in_each_inequality(self) -> None:
        tensor = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
        # A = 3, B = 2, C = 1. The slacks are (2 + 1 - 3)/2, (3 + 1 - 2)/2 and
        # (3 + 2 - 1)/2, largest first.
        self.assertEqual(deviatoric_moments(tensor), (2.0, 1.0, 0.0))

    def test_a_flat_body_sits_exactly_on_the_inequality(self) -> None:
        tensor = ((1.5, 0.0, 0.0), (0.0, 1.5, 0.0), (0.0, 0.0, 3.0))
        self.assertEqual(deviatoric_moments(tensor)[2], 0.0)


class EveryCaseFileInTheTree(unittest.TestCase):
    """The last done-when item, and what it covers today.

    A walk that found nothing passes, and a pass over nothing is the shape #30
    exists to refuse, so the count is asserted rather than left implied.
    """

    def case_files(self) -> list[Path]:
        directory = REPO_ROOT / CASES_DIR
        return sorted(directory.glob("*.toml")) if directory.is_dir() else []

    def test_every_case_file_is_a_document_and_a_body(self) -> None:
        for path in self.case_files():
            with self.subTest(case=path.name):
                casephysics.read(path)

    def test_the_walk_covers_what_the_directory_holds(self) -> None:
        # The trigger, derived from the tree rather than from anyone remembering.
        # On the day the first case file lands this reds, and what it asks for is
        # that somebody reads the test above and gives it a floor rather than
        # letting a walk over one file stand for a walk over the set.
        self.assertEqual(
            len(self.case_files()),
            0,
            "cases/ now holds case files. The walk above validates them and has no "
            "floor, so it passes over any number of them including none. Give it a "
            "floor and update this count.",
        )


if __name__ == "__main__":
    unittest.main()
