# pruefstand

Existing benchmarks are robotics-centred by design and deliberately avoid conservation laws, so nobody checks whether MuJoCo, Bullet and their siblings can do mechanics at all. This suite tests against the classical canon where the answer is known: Euler, Lagrange and Kovalevskaya tops, Euler's disk, the tippe top, the Chaplygin sleigh and sphere, and the double pendulum measured by Lyapunov exponent rather than trajectory. The deciding case is the celtic rattleback, which reverses its spin with no external torque and which most engines fail.

Planning happens on the issue tracker first. Every decision that shapes
the architecture is written down there with its reasons before the code
that depends on it exists.

See [NOTICE.md](NOTICE.md) for the intended-use notice.
