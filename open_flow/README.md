# Open-source SHA-256 baseline

This directory contains a reproducible SiliconCompiler 0.38.10 / OpenROAD
implementation of the SHA-256 RTL in `../sources/`. It uses SiliconCompiler's
`asap7_demo` target and the **stock LambdaPDK ASAP7** tech/cell libraries. It
is separate from the modified technology LEF and Cadence Innovus flow in this
repository; the extra density/color rules are **not** enforced here.

## Setup and run

From the repository root (with Yosys, OpenROAD and KLayout on `PATH`):

```sh
uv venv .venv
uv pip install --python .venv/bin/python 'siliconcompiler==0.38.10'
.venv/bin/python open_flow/run_sha256.py --check-only
.venv/bin/python open_flow/run_sha256.py --to synthesis  # quick RTL smoke test
.venv/bin/python open_flow/run_sha256.py                 # full P&R/GDS
```

The per-task timeout is 3600 seconds. Run the full flow in a durable terminal
or managed background process; a caller's foreground timeout can still kill it.
Outputs, logs and the generated manifest live in ignored `build/open_flow/`.
The GDS output is normally:
`build/open_flow/sha256/sha256_official/write.gds/0/outputs/sha256.gds.gz`.

The explicit timing mode uses the reference 600 ps clock period, 1 ps
input delay and 300 ps output delay at the typical library corner. The clock
port is excluded from input-delay assignment in `sha256.sdc`. These are example
constraints, not a verified tapeout target. This flow does **not** claim
signoff DRC/LVS, density compliance or timing closure.

The earlier successful baseline GDS was generated using the same stock ASAP7
target, before this script was re-created. Re-running can differ with tool and
package versions; verify reports and GDS before drawing comparisons.

## M6/M7 ring

The original Innovus script in `../scripts/innovus.tcl` creates an M6/M7 power
ring. `pdn_ring.tcl` replaces the stock LambdaPDK OpenROAD grid definition with
one that retains its followpin and strap layers, extends the M6/M7 straps to an
M6/M7 core ring, and connects adjacent PDN layers. The flow uses a 2 um
core-to-die margin so the ring fits inside the die. A complete local P&R run
through GDS export finished with zero task errors; the GDS passed `gzip -t`.
The PDN configuration report lists the ring on M6/M7, but the exported geometry
and via connectivity have not been independently inspected, and signoff checks
have not been run.

Post-route STA from that run failed the 600 ps target: typical-corner setup WNS
was -661.10 ps, slow-corner setup WNS -1246.33 ps (reported Fmax 541.62 MHz),
and fast-corner hold WNS -4.06 ps. These results are not directly comparable
to the closed-source flow's modified PDK and Genus/Innovus implementation.
