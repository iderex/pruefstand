# pruefstand

Existing benchmarks are robotics-centred by design and deliberately avoid conservation laws, so nobody checks whether MuJoCo, Bullet and their siblings can do mechanics at all. This suite tests against the classical canon where the answer is known: Euler, Lagrange and Kovalevskaya tops, Euler's disk, the tippe top, the Chaplygin sleigh and sphere, and the double pendulum measured by Lyapunov exponent rather than trajectory. The deciding case is the celtic rattleback, which reverses its spin with no external torque and which most engines fail.

Planning happens on the issue tracker first. Every decision that shapes
the architecture is written down there with its reasons before the code
that depends on it exists.

## The gate

One command, the same one locally and in CI:

    python -m gate

It runs its parts in order, stops at the first failure, and prints every part
with its outcome. A part that did not run says why and what asking for it would
cost, so a run that covered less than everything cannot be read as one that
covered everything and found nothing. A part that could not start is a failure
rather than a skip, and a part that collected fewer items than its declared
floor is a failure with the count in the message.

It needs no engine installed and no display. Which parts run is derived from the
tree, so the formatting part starts running on the day a formatter configuration
lands and the engine part on the day an adapter does.

The interpreter floor is CPython 3.12, and the reason it is there is in
[docs/decisions/language-and-toolchain.md](docs/decisions/language-and-toolchain.md).
Nothing is pinned yet, which is issue #19, so today the command runs on whatever
interpreter is on the path.

See [NOTICE.md](NOTICE.md) for the intended-use notice, and
[docs/what-this-is-not-for.md](docs/what-this-is-not-for.md) for what a number
from this suite does and does not support. It is worth reading before quoting
one: there is no ranking here and no overall winner, by design.
