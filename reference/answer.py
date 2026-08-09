"""A reference value and how far it is trusted, which are one thing here.

Issue #49. Every comparison in this project is a number from an engine against a
number from the reference, so a reference number with no bound attached implies the
reference is exact, and nothing in this repository is exact.

The decision behind it is `docs/decisions/reference-answer-and-trust.md`, which
says a computed reference is admitted only with a bound attached, names this issue
as what refuses one without, and adds the clause that makes this more than a
required field: the refusal reaches a qualitative case through a stability
statement rather than through a numeric bound, so a case with no continuous error
cannot pass by having nothing to bound.

## Why it is a type and not a check

A check runs after something was built and can be skipped, forgotten or run on the
wrong object. This is structural instead: `ReferenceAnswer` takes its trust
statement as a required argument, so the comparison code cannot be written without
one. Omitting it is a `TypeError` from the interpreter before any of this module
runs, and passing something that is not a trust statement is refused here. Both
are shown by tests in `tests/test_reference_answer.py`.

The three trust statements are the three states the decision admits, and there is
no fourth and no adjective that softens one:

    Bound       a magnitude in the units of the case's metric, with the routes it
                was produced by, for a class whose error is continuous
    Stability   what replaces a bound for a qualitative case, being the same
                outcome across a resolution ladder and across the perturbations
                the case declares
    Unbounded   no bound could be produced, with the reason, which is a much
                better outcome than a bound invented to fill a field

Each is refused for the class it does not belong to. A qualitative answer carrying
a `Bound` is refused, because a discrete outcome has no continuous error to bound
and a number there would be a number about something else. A numeric answer
carrying a `Stability` is refused for the mirror reason: an outcome that did not
move across a ladder is not a bound on a trajectory error.

## What a comparison does with it

`compare` produces the cell state, and the two states it can produce are the
`measured` and `bounded` states of `docs/decisions/report-card-shape.md`, named
from there rather than invented here. A bound smaller than the case's tolerance
gives `measured`. A bound that is not smaller gives `bounded`, because what is then
known is that the engine's error is somewhere inside an interval, and that is not a
number. An unbounded reference gives `bounded` and carries the mark, and the mark
is what #49 asks to survive into the report card.

What this module does not decide. Whether two engines are distinguished by their
values is the rule in `docs/decisions/uncertainty-reporting.md` and belongs to #81,
and writing it here would put a second implementation of it in another issue's
territory. The bound's own computation is #47. The record the bound is stored in is
#10 and #79. The rendering of a `bounded` cell as an inequality rather than as a
number is #81.

## The means

Python and the standard library, in the numerical core, where nothing imports an
adapter or an engine. Frozen dataclasses with validation in `__post_init__`, so
the refusal happens at construction and there is no window in which a half-built
reference answer exists to be passed on. The three rules survive it: every property
is refused by code here rather than asserted in prose, each refusal is tripped by a
fixture in `tests/test_reference_answer.py` that is a valid answer with one thing
changed, and the numbers in the tests are the ones the code computes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import casefile

# The class whose reference answer is an outcome rather than a number, from
# `docs/decisions/metric-per-class.md` by way of the class vocabulary in
# `casefile.CLASSES`. It is the one class whose trust statement is a stability
# statement, and it is named here rather than listed with the others because
# every rule below is about the difference between it and the rest.
QUALITATIVE = "qualitative"

# The two cell states a comparison against a reference can produce, from
# `docs/decisions/report-card-shape.md`. The other two states that document names
# are about a run that did not happen and are not reachable from here.
MEASURED = "measured"
BOUNDED = "bounded"

# The fewest rungs a resolution ladder can have and still say anything. One rung
# is a single run, and an outcome that did not move across a set of one moved
# across nothing.
LADDER_FLOOR = 2

# The fewest declared perturbations of the initial condition a stability statement
# rests on. Zero is a statement about one initial condition, which is the thing
# whose stability was in question.
PERTURBATION_FLOOR = 1


class ReferenceRefused(ValueError):
    """Raised instead of returning a reference answer that is wrong in any way.

    It carries every problem found rather than the first, for the reason
    `casefile.CaseRefused` carries: a reader that stops at the first one turns one
    review into several.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(self.problems))


def _refuse(problems: list[str]) -> None:
    if problems:
        raise ReferenceRefused(sorted(set(problems)))


def _is_finite_float(value: Any) -> bool:
    """A float that is a number. A bool is not a float and an integer is not one.

    An integer where a float belongs is refused rather than widened, which is the
    rule `casefile` applies to every number in a case file, for the same reason:
    a conversion nobody sees is where this project's largest class of error lives.
    """
    return isinstance(value, float) and math.isfinite(value)


@dataclass(frozen=True)
class Bound:
    """A magnitude the reference's own error is known not to exceed.

    In the units of the case's metric, which is why the units are a field rather
    than a convention: the metric of a case is that case's, and a bound compared
    against a tolerance in other units is a comparison of two different things.

    `routes` names how the bound was produced, and at least one is required. The
    decision asks for at least two independent routes per reference trajectory,
    which is #47's to satisfy and is not required here, because requiring two of
    them at construction would refuse the partial bound #47 builds up.
    """

    value: float
    units: str
    routes: tuple[str, ...]

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not _is_finite_float(self.value):
            problems.append(
                f"a bound is a finite float and this is {self.value!r}"
            )
        elif self.value <= 0.0:
            problems.append(
                f"a bound is {self.value!r}, and a bound of zero or less claims "
                f"the reference is exact, which nothing in this project is"
            )
        if not isinstance(self.units, str) or not self.units.strip():
            problems.append(
                "a bound carries the units of the case's metric, and a bound with "
                "no units cannot be compared against that case's tolerance"
            )
        if not isinstance(self.routes, tuple) or not self.routes:
            problems.append(
                "a bound names at least one route it was produced by, because a "
                "bound nobody can reproduce is a number somebody chose"
            )
        elif not all(
            isinstance(route, str) and route.strip() for route in self.routes
        ):
            problems.append("every route a bound names is a non-empty statement")
        _refuse(problems)


@dataclass(frozen=True)
class Stability:
    """What replaces a bound where the answer is an outcome rather than a number.

    A discrete outcome has no continuous error, so a bound on the reference's
    trajectory does not become a bound on its outcome. What stands in for it is
    that the outcome did not move: the same outcome across the reference's own
    resolution ladder, and across the perturbations of the initial condition the
    case declares.

    Replaced rather than dropped. An outcome with no continuous error is not an
    outcome that needs no evidence, which is why every field below is required and
    why two of them carry floors.
    """

    outcome: str
    ladder: tuple[float, ...]
    perturbations: int

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not isinstance(self.outcome, str) or not self.outcome.strip():
            problems.append(
                "a stability statement names the outcome that did not move"
            )
        if not isinstance(self.ladder, tuple) or not all(
            _is_finite_float(rung) and rung > 0.0 for rung in self.ladder
        ):
            problems.append(
                "a resolution ladder is finite positive floats, being the steps "
                "the outcome was the same at"
            )
        elif len(set(self.ladder)) < LADDER_FLOOR:
            problems.append(
                f"a stability statement rests on {len(set(self.ladder))} distinct "
                f"rung(s) and the floor is {LADDER_FLOOR}, because an outcome that "
                f"did not move across a set of one moved across nothing"
            )
        if isinstance(self.perturbations, bool) or not isinstance(
            self.perturbations, int
        ):
            problems.append("the perturbation count is a whole number")
        elif self.perturbations < PERTURBATION_FLOOR:
            problems.append(
                f"a stability statement rests on {self.perturbations} "
                f"perturbation(s) of the initial condition and the floor is "
                f"{PERTURBATION_FLOOR}, because the stability in question is "
                f"stability under a perturbation"
            )
        _refuse(problems)


@dataclass(frozen=True)
class Unbounded:
    """No bound could be produced, and the reason it could not.

    This is a legitimate state and it is the honest one where a bound would have to
    be invented to fill a field. What it costs is that every comparison against
    this reference is marked, which is the whole point of admitting it: a reference
    nobody could bound is a reference whose numbers are not measurements, and the
    mark is what says so where the number is read.
    """

    why: str

    def __post_init__(self) -> None:
        if not isinstance(self.why, str) or not self.why.strip():
            raise ReferenceRefused(
                [
                    "an unbounded reference carries the reason no bound could be "
                    "produced, and an unbounded reference with no reason is "
                    "indistinguishable from a bound somebody forgot"
                ]
            )


Trust = Bound | Stability | Unbounded


@dataclass(frozen=True)
class ReferenceAnswer:
    """The answer an engine is compared against, and how far it is trusted.

    `trust` has no default. A caller that omits it gets a `TypeError` from the
    interpreter, which is the structural half of this issue: there is no way to
    obtain a reference value without obtaining its bound, because there is no
    constructor that takes one without the other.
    """

    case_id: str
    case_class: str
    value: Any
    trust: Trust

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            problems.append("a reference answer names the case it is the answer to")
        if self.case_class not in casefile.CLASSES:
            problems.append(
                f"the class is {self.case_class!r}, and the vocabulary is "
                f"{', '.join(casefile.CLASSES)}"
            )

        qualitative = self.case_class == QUALITATIVE
        if qualitative:
            if not isinstance(self.value, str) or not self.value.strip():
                problems.append(
                    "a qualitative reference answer is an outcome, written out, "
                    "rather than a number"
                )
        elif not _is_finite_float(self.value):
            problems.append(
                f"a reference value for the {self.case_class!r} class is a finite "
                f"float and this is {self.value!r}"
            )

        if not isinstance(self.trust, (Bound, Stability, Unbounded)):
            problems.append(
                f"the trust statement is {type(self.trust).__name__}, and a "
                f"reference answer carries a Bound, a Stability or an Unbounded, "
                f"so a value cannot be published with nothing said about it"
            )
        elif qualitative and isinstance(self.trust, Bound):
            problems.append(
                "a qualitative reference answer may not carry a numeric bound, "
                "because a discrete outcome has no continuous error, and a number "
                "here would be a bound on something other than the answer"
            )
        elif not qualitative and isinstance(self.trust, Stability):
            problems.append(
                f"a reference answer for the {self.case_class!r} class may not "
                f"carry a stability statement in place of a bound, because an "
                f"outcome that did not move across a ladder is not a bound on a "
                f"trajectory error"
            )
        _refuse(problems)

    @property
    def is_bounded(self) -> bool:
        """Whether anything is known about how far this answer is trusted.

        True for a numeric bound and for a stability statement, which are the two
        shapes evidence takes here, and False for an unbounded answer.
        """
        return not isinstance(self.trust, Unbounded)


@dataclass(frozen=True)
class Comparison:
    """What a comparison against a reference answer may be reported as.

    `state` is `measured` or `bounded`. `reference_unbounded` is the mark, and it
    is a field rather than something derivable from the state, because a `bounded`
    cell arising from a bound that was too large and one arising from a reference
    nobody could bound are different statements and a reader has to be able to tell
    them apart.
    """

    case_id: str
    state: str
    reference_unbounded: bool
    why: str


def compare(answer: ReferenceAnswer, tolerance: float | None) -> Comparison:
    """The cell state a comparison against this answer may produce.

    The tolerance is the case's own, in the units of its metric. It is required for
    every class whose answer is a number and refused for a qualitative one, in both
    directions, because a tolerance supplied where the answer is an outcome is a
    number about nothing and an absent tolerance elsewhere is the comparison this
    function exists to make being skipped.

    What it does not do is order two engines against each other. That rule is
    `docs/decisions/uncertainty-reporting.md`'s and lands in #81.
    """
    problems: list[str] = []
    if not isinstance(answer, ReferenceAnswer):
        problems.append(
            f"a comparison is made against a ReferenceAnswer and this is "
            f"{type(answer).__name__}"
        )
        _refuse(problems)

    qualitative = answer.case_class == QUALITATIVE
    if qualitative:
        if tolerance is not None:
            problems.append(
                "a qualitative case is judged by its outcome and carries no "
                "tolerance for this comparison, so a tolerance here is a number "
                "about something else"
            )
    elif tolerance is None:
        problems.append(
            f"the {answer.case_class!r} class is judged against a tolerance and "
            f"none was supplied, and a comparison with no tolerance is a "
            f"comparison nobody made"
        )
    elif not _is_finite_float(tolerance) or tolerance <= 0.0:
        problems.append(
            f"a case tolerance is a finite float greater than zero and this is "
            f"{tolerance!r}"
        )
    _refuse(problems)

    if isinstance(answer.trust, Unbounded):
        return Comparison(
            case_id=answer.case_id,
            state=BOUNDED,
            reference_unbounded=True,
            why=(
                f"the reference for {answer.case_id!r} carries no bound: "
                f"{answer.trust.why}"
            ),
        )

    if isinstance(answer.trust, Stability):
        return Comparison(
            case_id=answer.case_id,
            state=MEASURED,
            reference_unbounded=False,
            why=(
                f"the reference outcome held across {len(set(answer.trust.ladder))} "
                f"rungs and {answer.trust.perturbations} perturbation(s)"
            ),
        )

    if answer.trust.value >= tolerance:
        return Comparison(
            case_id=answer.case_id,
            state=BOUNDED,
            reference_unbounded=False,
            why=(
                f"the reference's own bound is {answer.trust.value!r} "
                f"{answer.trust.units} and the case's tolerance is {tolerance!r}, "
                f"so what is known is an interval rather than a value"
            ),
        )

    return Comparison(
        case_id=answer.case_id,
        state=MEASURED,
        reference_unbounded=False,
        why=(
            f"the reference's own bound is {answer.trust.value!r} "
            f"{answer.trust.units}, below the case's tolerance of {tolerance!r}"
        ),
    )
