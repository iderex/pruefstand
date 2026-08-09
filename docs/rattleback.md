# The rattleback, and why it decides this

This answers issue #67. It is written before the case file (#68), before the
reversal metric (#69), before the direction metric (#71) and before any engine
has been run, so that what counts as a right answer is fixed while nobody knows
which engines will produce one.

## The body and the mechanism

A rattleback is a convex body resting on a horizontal plane whose principal axes
of inertia are rotated, about the vertical, relative to the principal axes of
curvature of its contact surface. Spun about the vertical in one sense it spins
smoothly. Spun in the other, a pitching instability grows, takes energy out of
the spin, and the spin reverses. Nothing external applies a torque about the
vertical.

The misalignment is the whole mechanism, and it is between inertia and curvature
rather than between inertia and the visible outline of the body. Walker's 1896
paper is where that is first identified, and Moffatt and Tokieda restate it in
those terms: the chiral behaviour "results from misalignment of the celt's
principal axes of inertia and its axes of curvature at the point of contact with
the table". A body whose outline looks skewed and whose curvature axes are not
is not a rattleback, and the case file has to be able to say which is which.
[The case file format](decisions/case-file-format.md) carries the full inertia
tensor for this reason.

The coupling that carries energy from spin into pitching needs the contact
constraint. In the ideal model the contact point does not slip, so the constraint
is non-holonomic, it does no work, and the energy that leaves the spin goes into
the pitching and rolling modes rather than out of the system.
[The non-holonomic reference](../reference/nonholonomic-reference.md) fixes which
model this project's reference solves, which is that one, and this note does not
restate the fields it fixes.

## Why this case decides the question

The argument is in #67 and it is not repeated here in full. What it comes to is
that the effect is invisible to the measurements a robotics benchmark makes: it
costs almost no energy, the forces are small, the body barely moves, and speed
and penetration error say nothing about it. It needs the rolling constraint
handled rather than approximated. It has a discrete outcome nobody argues about.
It has a direction, so an engine can produce the effect and have it backwards. And
nobody tests it systematically, so the answer is not already known.

[The metric per class](decisions/metric-per-class.md) already places the reversal
among the outcomes that have no common scale with a drift, and
[what this project is not for](what-this-is-not-for.md) is where the conclusion a
poor result does not support is written.

## The competing models, and why the disagreement matters here

The literature does not disagree about whether a rattleback reverses. It
disagrees about what has to be in the model for the reversal to come out right,
and the disagreement changes the timescale and the count rather than the
existence.

The ideal rolling family treats the contact as rolling without slipping, with no
dissipation:

- G. T. Walker. On a dynamical top. Q. J. Pure Appl. Math. 28 (1896), 175-184.
- H. Bondi. The rigid body dynamics of unidirectional spin. Proc. R. Soc. Lond. A
  405 (1986), 265-274.
- H. K. Moffatt and T. Tokieda. Celt reversals: a prototype of chiral dynamics.
  Proc. R. Soc. Edinb. A 138 (2008), 361-368.

The family that carries slip, friction or other dissipation:

- T. R. Kane and D. A. Levinson. Realistic mathematical modeling of the
  rattleback. Int. J. Non-Linear Mech. 17 (1982), 175-186.
- R. E. Lindberg, Jr and R. W. Longman. On the dynamical behavior of the
  wobblestone. Acta Mech. 49 (1983), 81-94.
- A. Garcia and M. Hubbard. Spin reversal of the rattleback: theory and
  experiment. Proc. R. Soc. Lond. A 418 (1988), 165-197.

Two more that matter for what a long run is expected to look like:

- A. V. Borisov and I. S. Mamaev. Strange attractors in rattleback dynamics.
  Phys. Usp. 46 (2003), 393-403.
- Y. Kondo and H. Nakanishi. Rattleback dynamics and its reversal time of
  rotation. Phys. Rev. E 95 (2017), 062207.

The placement of each paper into a family above is taken from the survey in
Moffatt and Tokieda's introduction and from the titles, and not from having read
each paper here. Garcia and Hubbard is the one that paper names as including
dissipation from slip.

The reason this matters before a run rather than after one is in Moffatt and
Tokieda's own abstract. Their reduced third-order system, derived under no slip
and no dissipation, "is integrable, and its solutions are periodic, showing an
infinite succession of spin reversals", and it is the inclusion of linear
dissipation that "allows any given number of reversals". A real object reverses a
few times and stops: the same paper records Walker as having built one that
reversed four times and Pippard as having made one from a slice of a Rhine wine
bottle that "may reverse sense four or, rarely, five times".

So the number of reversals is a property of the dissipation and not of the
rattleback. This project's reference solves the ideal rolling model, which is
fixed in the non-holonomic reference note and is not this note's to change. An
engine realising the contact with friction will dissipate whether or not the case
asked it to, so the count it produces and the count the reference produces are
answers to different questions, and #69 has to define the count so that the
difference is visible rather than averaged into a disagreement.

Those statements are about a reduced system derived under stated approximations,
small chirality, small spin and an elongated body, rather than about the full
rolling rattleback. They are quoted because they fix what a count means, not
because the reduced system is the reference.

## What counts as getting it right, before any run

Stated now, and any later change to it is a change to this document with its
reason, because a criterion written after the numbers are in is a criterion
fitted to them.

An engine gets this right when, from the spin sense in which the reference
reverses, its run reverses; when the first reversal time agrees with the
reference within the uncertainty the resolution study gives it; when the body
stays in contact throughout; and when the measured slip at the contact stays
inside the threshold the case declares for rolling. All four, not the first
alone. A reversal produced by a body that bounced, or by a contact that was
sliding, is not the effect this case is about.

An engine gets it wrong when it does not reverse at all from that spin sense
while the reference does, or when it reverses from the sense in which the
reference does not, or when its reversal time is outside the uncertainty in a way
the resolution study does not close as the step is refined.

The direction half needs one qualification, and it is the reason this section
exists before the metric rather than inside it. The clean statement, that a
rattleback reverses one way and not the other, is not what the dissipative
reduced model shows at every parameter choice. Moffatt and Tokieda's figure 5 has
the initial spin in the other sense and reports "a single weak reversal induced
very late by rolling instability", with the pitching instability not excited at
all. So a run that reverses in both senses is not automatically a spurious
instability. What separates the two is the strength and the time: the reversal
this case is about is driven by pitching and arrives early, and a late weak one
driven by rolling is a different event. #69 owes a threshold and #71 owes the
paired outcome, and both have to be able to tell those apart or the direction
finding cannot be defended.

## What would say the case was configured badly rather than the engine being wrong

Four results, each of which points at this repository before it points anywhere
else.

The reference itself failing to reverse, or reversing in the sense the physics
does not. The reference is this project's own code and its answer is checked
first. [How the reference answer is produced and how far it is
trusted](decisions/reference-answer-and-trust.md) is where that check lives.

Every engine reversing in the same unexpected sense. A chirality inverted by a
frame convention is a mistake this project can make once and have it appear in
every adapter, because every adapter converts through this project's conventions.
Agreement between independent engines against the reference is evidence about the
reference, not about the engines.

Every engine failing to reverse at all, including one from a solver family with a
good reason to get it right. The likeliest explanation is a case whose spin, whose
horizon or whose inertia skew is too small for the instability to grow inside the
run, which is a property of the numbers in the case file and not of the software.

An engine reversing only at a step so fine that no other case needed it. That is
a case whose timescale was not derived, and the resolution study is what makes it
visible.

In each of those the finding is written about this repository, and nothing is
published about an engine until it is settled.

## The limits of what a result here can support

A result about this case supports a statement about the reversal happening and
about its direction. It supports a much weaker statement about the timing,
because the timing depends on the model of the contact and the models disagree,
which is the whole of the section above.

It supports nothing about an engine's suitability for work that is not this. That
is [what this project is not for](what-this-is-not-for.md) and the boundary is
argued there.

It is a statement about one engine version at one configuration on one case at
one hash, against a reference with a bound. Every one of those qualifiers has to
survive into anything quoted from it.

## The mark

PROSE, NOT ENFORCEMENT, whole document. Nothing in this tree reads it. The case
it describes does not exist, #68 is where it lands, and until then the criteria
above are held by a reader. The one half a machine could reach is whether the
case file's model matches the reference's, which is the schema's job and is #31.
