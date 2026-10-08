"""Run SHA-256 with SiliconCompiler's open-source ASAP7 target.

This uses LambdaPDK's stock ASAP7 technology, NOT this repository's modified
tech LEF or the Cadence Innovus implementation. All outputs stay in build/.
"""

import argparse
from pathlib import Path

from siliconcompiler import ASIC, Design
from siliconcompiler.targets import asap7_demo

ROOT = Path(__file__).resolve().parents[1]
RTL = ("sha256.v", "sha256_core.v", "sha256_k_constants.v", "sha256_w_mem.v")


def make_chip(to: str = "write.gds", builddir: Path | None = None) -> ASIC:
    design = Design("sha256")
    design.add_file([str(ROOT / "sources" / name) for name in RTL],
                    fileset="rtl", filetype="verilog")
    design.add_file(str(ROOT / "open_flow" / "sha256.sdc"),
                    fileset="constraints", filetype="sdc")
    design.add_file(str(ROOT / "open_flow" / "pdn_ring.tcl"),
                    fileset="pdn_ring", filetype="tcl")
    design.set("fileset", "rtl", "topmodule", "sha256")
    design.set("fileset", "constraints", "topmodule", "sha256")

    chip = ASIC()
    chip.add_dep(design)
    chip.set("option", "design", "sha256")
    chip.set("option", "fileset", ["rtl", "constraints"])
    chip.set("option", "builddir", str(builddir or ROOT / "build" / "open_flow"))
    chip.set("option", "jobname", "sha256_official")
    chip.set("option", "timeout", 3600)

    asap7_demo(chip, language="verilog")
    # The M6/M7 ring extends beyond the core; the target's 1 um margin is
    # insufficient (PDN-0351 reports 0.246 um outside the die).
    chip.constraint.area.set_coremargin(2)
    # Replace the LambdaPDK default PDN definition with our complete grid:
    # the ring, straps, and vias must be generated together in one pdngen run.
    pdn_task = chip.get("tool", "openroad", "task", "power_grid", field="schema")
    pdn_task.add_openroad_powergridfileset(design.name, "pdn_ring", clobber=True)
    mode = chip.constraint.timing.make_mode("func")
    mode.add_sdcfileset(design, "constraints")
    scenario = chip.constraint.timing.make_scenario("sha256_tt")
    scenario.set_mode("func")
    scenario.add_libcorner(["typical", "generic"])
    scenario.set_pexcorner("typical")
    scenario.add_check(["setup", "hold"])
    chip.set("option", "to", to)
    return chip


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to", default="write.gds",
                        help="End flow at a node (default: write.gds; synthesis for smoke test)")
    parser.add_argument("--builddir", type=Path, help="Override the build directory")
    parser.add_argument("--check-only", action="store_true",
                        help="Validate and write manifest without running tools")
    args = parser.parse_args()
    chip = make_chip(args.to, args.builddir)
    out = ROOT / "build" / "open_flow" / "sha256_official.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    chip.write_manifest(str(out))
    print(f"manifest: {out}", flush=True)
    if not chip.check_manifest():
        raise SystemExit("SiliconCompiler manifest validation failed")
    if not args.check_only:
        chip.run()


if __name__ == "__main__":
    main()
