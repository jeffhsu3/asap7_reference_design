# ASAP7 ecosystem discrepancies

Differences between the ASAP7 design rule manual (DRM, `asap7_drm_201207a.pdf`), its technology collateral, the routing flows and two independent DRC decks: gdscheck and [ASAP7_for_KLayout](../ASAP7_for_KLayout/drc/drc_ASAP7.lydrc). Counts are for the cited layout and deck versions only. A rule present in a deck, or a router reporting zero violations, does not show that the DRM rule was checked on the final GDS; nothing here is signoff.

| § | Topic | Finding | Status |
| --- | --- | --- | --- |
| [1](#1-v1m1en1-m1-enclosure-of-v1) | `V1.M1.EN.1` | Every tech LEF's `VIA12` gives M1 2/2 nm, not the DRM's 5/2 nm. The KLayout deck misses 5/2 failures. | KLayout cause open |
| [2](#2-gdscheck-vs-asap7_for_klayout-on-sha-256) | gdscheck vs KLayout on SHA-256 | 17,729 vs 493 items; mostly different predicates or disabled checks. All `M4.AUX` markers were PDN pads, cleared by `-ongrid`. | Triaged |
| [3](#3-report-only-categories) | Categories one deck reports | Per-rule triage of the rest. | Open, fixtures needed |
| [4](#4-m4s4--m4s5-after-the-on-grid-pdn) | `M4.S.4` / `M4.S.5` | 1 nm overlaps from via positions; the LEF keep-out that covers them is disabled by rounding. | Explained (§6) |
| [5](#5-m1-spacing-against-the-lef-end-of-line-keep-out) | M1 spacing | 443 markers the LEF covers but rounding disables; 2,425 the LEF does not state. | Explained |
| [6](#6-quarter-nanometre-values-in-the-tech-lef) | LEF rounding | Three quarter-nm values disable rules under `DATABASE MICRONS 1000`. | #4663, #246 open; #10 withdrawn |
| [7](#7-sha-256-rerun-with-the-patched-lef) | Rerun with the patched LEF | 7,620 → 6,455 markers; no routability cost. | Done |
| [8](#8-the-hand-built-asap7-sram-banks) | SRAM banks | Periphery violations are real; the bitcells are clean. | Done |
| [9](#9-openroad-flow-scripts-designs) | ORFS `gcd`, `aes`, `aes-block` | `syn` writes a 10 nm GDS; the PDN scripts, macro placement and two LEF vias break DRM rules the router is not given. Fixes clear `gcd`/`aes` and leave `aes-block` with 2,912, mostly LEF gaps. | OpenROAD PR open; ORFS branches local |

## 1. `V1.M1.EN.1`: M1 enclosure of V1

**DRM** §3.13, Table 3.13.1 (p. 49): "Minimum enclosure of V1 by M1 on two opposite sides, ≥ 5&2 nm". Read as 5 nm on one side and 2 nm on its opposite, on either axis; 2/2 does not pass.

| Component | Encoding | Assessment |
| --- | --- | --- |
| ASAP7_for_KLayout, lines 312–314 | Two `V1.M1.EN.1` checks: `enclosing(..., 2.nm, ..., two_connected_sides_allowed)` and `enclosing(..., 5.nm, ...)` with an `m1ovlp5v1` filter. | **Suspected false negatives**: zero markers on the failing fixtures below. Cause inside KLayout not isolated. |
| [gdscheck `v1.yml`](../gdscheck/pdks/asap7/decks/v1.yml), lines 50–56 | `min_enclosure`, `value: 0.005`, `sides: opposite`, `opposite_value: 0.002`. | Matches the reading on the fixtures; covered by [its tests](../gdscheck/tests/asap7.rs). |
| [Innovus 4× tech LEF](techlef/asap7_tech_4x_201209.lef), lines 837–844 | `VIA12`: M1 `RECT -0.036 -0.044 0.036 0.044` over V1 `RECT -0.036 -0.036 0.036 0.036`, i.e. **0/0 and 2/2 nm** at 1×. | The default via cannot meet the rule by itself; other same-net M1 could. |
| Same LEF, lines 969–977 and 146–150 | `VIARULE M2_M1` sets M1 `ENCLOSURE 0 0.0`; `LAYER V1` has no enclosure rule. | No 5/2 rule found. Innovus's effective rules were not inspected. |
| [Innovus script](scripts/innovus.tcl), lines 21–25, 193, 204–224, 274 | Loads that LEF; runs `verify_drc` before optimisation and routing; no final DRC. | The README's DRC-clean claim does not cover this rule on the final GDS. Innovus was not run. |
| LambdaPDK `asap7_tech.lef` (open flow) | `VIA12` also 2/2 nm; `M2_M1` gives M1 zero enclosure. | A zero router count covers only the rules the router was given. |

**Fixture** (isolated 18 nm V1 squares on 21/0, rectangular M1 on 19/0, M2 on 20/0; zero margin on the other axis):

| M1 margins | Expected | gdscheck | KLayout |
| --- | --- | ---: | ---: |
| 5/2 nm | pass | 0 | 0 |
| 2/2 nm | fail | 1 | 0 |
| 4/2 nm | fail | 1 | 0 |

The fixture files were temporary; rebuild them as described and run the KLayout expressions at lines 313–314 and `gdscheck run --process asap7 --deck v1`.

**On the SHA-256 layout**, gdscheck reports 4,145 `V1.M1.EN.1` markers and KLayout none. At `(2.304, 16.515) µm` the V1 is `(2.304, 16.506)–(2.322, 16.524)` with M1 just 2 nm above and below.

**Open:** isolate the KLayout expression's failure on single- and merged-cell fixtures; check Innovus's effective rules and `verify_drc` on a 5/2 vs 2/2 fixture if licensed; run an independent DRC on exported Innovus GDS (4× scaling verified).

## 2. gdscheck vs ASAP7_for_KLayout on SHA-256

**Layout:** open-flow SHA-256 baseline, `build/pdn_m5_minwidth/.../sha256.gds.gz`. KLayout: **493 items, 12 categories**. gdscheck main: **17,729 items, 13 categories**, then 17,955 in 15 after `M4`–`M7` `.S.4`/`.S.5` were added (`763954c`, `3ccb754`: +164 `M4.S.5`, +62 `M4.S.4`). The decks differ in rules and granularity, so the totals are not two counts of one set of defects.

| Rule | KLayout | gdscheck | Why they differ |
| --- | ---: | ---: | --- |
| `M4.AUX.1` / `.AUX.2` | 0 / 0 | 7,612 / 2,211 | DRM §3.14 Table 3.14.2 (p. 54): M4 edges on a 24 nm grid, minimum-width M4 on tracks. KLayout's grid checks are off (`OFFGRID = false`, line 42; lines 515–523) and `M4.AUX.2` is not coded (line 368). Its M6/M7 grid checks are also mislabelled `M4.AUX.1`/`M5.AUX.1` (lines 521–522). gdscheck ([`m4.yml`](../gdscheck/pdks/asap7/decks/m4.yml) lines 100–113) uses grid offset 0, track offset 12 nm; the DRM lets a design choose offsets (p. 54 note 1). All markers were PDN pads; see below. |
| `M4.S.5` | 258 | 164 | DRM §3.14 Table 3.14.1 (p. 53): ≥ 44 nm run for M4 on adjacent tracks. KLayout (line 366) flags projected `space(25.nm)` edges under 44 nm: 258 items = **129 pairs**, mostly 1 nm overlaps, all matched by gdscheck markers. gdscheck's `min_track_run` takes adjacency as a gap < 72 nm; at < 25 nm it gives exactly 129; the other 35 come from the wider limit. Six inspected extras involve an off-track wire (also `M4.AUX.2`). |
| `M4.S.4` | 0 | 62 | DRM: ≥ 40 nm between same-side tips of overlapping adjacent-track wires (Fig. 3.14.2(d)). gdscheck's `min_tip_stagger` treats aligned tips as clean, an interpretation. KLayout (line 365) checks facing walls instead, a different predicate. 26 with the < 25 nm limit. |
| `M1.S.2` / `.S.4` / `.S.5` | 46 / 0 / 0 | 2,133 / 490 / 93 | DRM §3.12 (p. 47) edge-length-dependent spacings. KLayout (lines 269–274) filters generic `space` results; gdscheck ([`m1.yml`](../gdscheck/pdks/asap7/decks/m1.yml) lines 18–43) sorts edges by length. Not established which markers are valid; see §5. |
| `M1.S.6` | 78 | 78 | Same check and count (≥ 20 nm corner). A control, not proof the markers coincide. |
| `V6.S.1`–`.S.3` | 3 | 624 | DRM §3.17 (p. 65): ≥ 45 nm. KLayout (line 448) applies one 45 nm check; its 3 items are in the via master `VIA_via6_7_288_288_4_1_322_66`; gdscheck reports placed occurrences under `.S.2` (first: 34 nm gap at `(0.784, 0.953–0.987) µm`). Hierarchy, not disagreement, until matched per occurrence. |

**`M4.AUX` markers are all PDN pads.** Every marker lies in a VDD/VSS M4 rectangle of the floorplan DEF (2,530 pads; the two checks mark them differently). LambdaPDK's `tracks.tcl` puts M4 tracks at `-y_offset 0.012 -y_pitch 0.048`, but its `pdngen.tcl` connects `{M2 M5}` without `-ongrid`. Adding `-ongrid {M4}` to [`pdn_ring.tcl`](open_flow/pdn_ring.tcl) put all 2,530 pads at y ≡ 12 nm (mod 48), and the stock M4 deck reported `M4.AUX.1 = 0`, `M4.AUX.2 = 0` (`build/pdn_m4_ongrid/...`; connectivity passed). `M4.S.4 = 61` and `M4.S.5 = 153` remained (§4).

**Also one-sided on this layout:** gdscheck only: `M6.AUX.1`, `M6.W.4`, `M7.AUX.1`, `M7.W.4`, `V0.M1.AUX.3`. KLayout only: `V1.S.4`, `V0.S.1`, `V5.M6.AUX.2`, `GATE.S.1`. See §3.

## 3. Report-only categories

Same layout and reports as §2. Report items are not necessarily distinct placed defects.

| Rule | KLayout / gdscheck | Assessment |
| --- | ---: | --- |
| `M6.AUX.1`, `M7.AUX.1` | 0 / 16, 0 / 16 | DRM §3.16 Table 3.16.2 (p. 61): 32 nm grid, design-chosen offset. gdscheck ([`m6.yml`](../gdscheck/pdks/asap7/decks/m6.yml), [`m7.yml`](../gdscheck/pdks/asap7/decks/m7.yml) lines 100–106) uses offset 0. A shared marker at `(0.784, 0.892) µm` is a power-grid corner off that grid. KLayout's checks are disabled (and mislabelled). Validity depends on the design's grid origin. |
| `M6.W.4`, `M7.W.4` | 0 / 4, 0 / 4 | DRM §3.16 Table 3.16.1 (p. 60): wide metal must not span an even number of tracks. KLayout: not coded (lines 413, 431). gdscheck checks wide-wire centres on 64 nm tracks offset 16 nm (e.g. M6 centre y = 1.036, M7 centre x = 0.928 µm). Not yet separated from a track-origin choice. |
| `V0.M1.AUX.3` | 0 / 303 | DRM §3.11 Table 3.11.2 (p. 43): V0 as wide as M1 across M1. gdscheck ([`v0.yml`](../gdscheck/pdks/asap7/decks/v0.yml) lines 101–106): flush on two opposite sides. First marker: 4 nm M1 overhang at `(3.636, 29.230)–(3.654, 29.248) µm`. KLayout (line 264) is a candidate false negative. **Reading settled by §8**: DRM Fig. 3.11.2(d) marks a via with M1 continuing past one side as a violation. |
| `V1.S.4` | 49 / 0 | DRM §3.13 (p. 49): ≥ 27 nm corner to corner where the two vias' 5 nm M2 end-caps differ. Both decks check it (KLayout line 310; [`v1.yml`](../gdscheck/pdks/asap7/decks/v1.yml) lines 41–49) with different end-cap classification. One KLayout site: V1s at `(13.574, 60.392)–(13.590, 60.408)` and `(13.608, 60.426)–(13.624, 60.442)` µm, corners 18 × 18 nm apart. Includes standard-cell master items. Undecided. |
| `V0.S.1` | 7 / 0 | DRM §3.11 (p. 42). KLayout (lines 249–251) uses projection and Euclidean checks; gdscheck applies 18 nm facing and classifies corners under `.S.2`–`.S.4`. All 7 KLayout items are in standard-cell masters. Needs a per-instance comparison. |
| `V5.M6.AUX.2` | 2 / 0 | DRM §3.15 (p. 58, from V4). Both decks check it (KLayout line 405; [`v5.yml`](../gdscheck/pdks/asap7/decks/v5.yml) lines 44–49). Both KLayout items are in via masters: `VIA_via5_6_24_288_1_1_58_322` (V5 and M6 flush) and `VIA_VIA56` (24 nm V5, M6 ±23 nm). A hierarchy question; check the placed M6 and the axis. |
| `GATE.S.1` | 22 / 0 | DRM §3.4 (p. 19): exact 54 nm gate pitch. KLayout (line 147): pairwise `gate.space(100.nm, projection)`; gdscheck ([`gate.yml`](../gdscheck/pdks/asap7/decks/gate.yml)): centres on a 54 nm grid offset 27 nm. Different predicates; e.g. GATE `x = 25.883–25.903 µm` under GCUT `25.868–25.918 µm`. |

**Priority:** fix the M6/M7 grid origins, then orientation fixtures for `V0.M1.AUX.3` and `V5.M6.AUX.2`, then end-cap and gate-pitch fixtures. Keep master-cell items separate from placed occurrences.

## 4. `M4.S.4` / `M4.S.5` after the on-grid PDN

**Layout:** SHA-256 with `add_pdn_connect ... -min_width_layers {M3 M4} -ongrid {M4}`, `build/pdn_m4_ongrid/.../sha256.gds.gz` (`fa0a56b1…e67b`); no `M4.AUX` markers. gdscheck `3ccb754`, `m4` deck. Per-marker list: [`drc_findings/sha256_pdn_m4_ongrid_m4_s4_s5.csv`](drc_findings/sha256_pdn_m4_ongrid_m4_s4_s5.csv) (marker, overlap or tip offset, gap, both wires, signal or PDN pad; no net names).

| | `M4.S.5` | `M4.S.4` |
| --- | ---: | ---: |
| Total | 153 | 61 |
| Signal / signal | 136 | 58 |
| One side a PDN pad | 17 | 3 |
| Gap | 24 nm (all) | 24 nm (all) |
| Most common | 1 nm overlap (119) | 18 / 24 / 30 nm offset (11 / 10 / 9) |

All are minimum-width wires on neighbouring tracks; none depends on the < 72 nm adjacency limit or an off-track wire.

- **Where the 1 nm comes from.** M4 wires end on V3/V4 vias on the 36 nm M3 pitch. In 87 of the 119, one wire runs 11 nm past its last via and the neighbour 44 nm past its first, with the vias 72 nm apart: 11 + 44 + 18 − 72 = 1 nm. `.S.4` is the same for same-side tips (6–39 nm apart). The 44 nm extension (perhaps M4 `AREA 0.002`) is not traced.
- **The LEF covers these, but rounding disables it.** M4's `LEF58_EOLKEEPOUT 0.025 EXTENSION 0.048 0.02425 0.048 CORNERONLY` forbids a neighbour's corner within 48 nm of a line end and 24.25 nm to the side, which covers both rules and is stricter (it also forbids aligned tips and a 40–48 nm stagger). OpenROAD stores 24.25 as 24, exactly the neighbour's edge, and needs the corner strictly inside. As loaded, `drt::check_drc` finds 0 keep-out violations; with 25 nm it finds 249 on M4 and 2 on M5, matching every gdscheck `M4.S.4` (61), `M4.S.5` (153) and `M5.S.5` (1) within 50 nm. M6/M7 have the same problem (`0.03225` → 32). gdscheck marks M4–M7 `S.4`/`S.5` as `tech_lef: partial`. Fix: §6.
- **KLayout** flags the same 129 `M4.S.5` pairs (§2). Its `M4.S.4` checks a different predicate, so the 61 rest on gdscheck's reading of Fig. 3.14.2(d).

## 5. M1 spacing against the LEF end-of-line keep-out

**Layout:** V6 cut-pitch trial, `build/v6_cut_pitch_xy_trial/.../sha256.gds.gz` (`868c437b…a7c9`; `add_pdn_connect -layers {M6 M7} -cut_pitch {0.333 0.077}`). gdscheck `42ce435` main: **7,620** markers, including `M1.S.2` 2,210, `M1.S.4` 508, `M1.S.5` 77, `M1.S.6` 73. The standard cells alone are clean; every M1 marker is at or next to a router `VIA12` pad.

**LEF M1 statements** (LambdaPDK `asap7_tech.lef` = ASAP7 1x tech LEF): `SPACING 0.018` (`M1.S.1`); `LEF58_EOLKEEPOUT 0.01825 EXTENSION 0.0 0.0 0.031` (31 nm ahead of a line end ≤ 18.25 nm wide); `LEF58_CORNERSPACING ... SPACING 0.018`. gdscheck therefore tags `M1.S.2`/`.S.4`/`.S.5` partial, `M1.S.3` absent, `M1.S.6` weaker.

**Method.** Each marker's two facing edges were recovered from merged M1. A marker is **covered** if one edge is a line end (shorter than 18.25 nm, both corners convex) and the other overlaps the 31 nm strip ahead of it. `M1.S.6` was compared with the LEF's 18 nm corner spacing instead. Per marker: [`drc_findings/sha256_v6_cut_pitch_m1_eol_keepout.csv`](drc_findings/sha256_v6_cut_pitch_m1_eol_keepout.csv).

| Rule | Markers | Covered | Not covered | Why not covered |
| --- | ---: | ---: | ---: | --- |
| `M1.S.2` (≥ 25 nm) | 2,210 | 1 | 2,209 | Neither edge is a line end: e.g. a 22 nm pad side facing a 99 or 180 nm pin edge, or a jog with a concave corner. |
| `M1.S.4` (≥ 31 nm) | 508 | **417** | 91 | Gaps inside one polygon; the short edge has a concave corner. |
| `M1.S.5` (≥ 31 nm) | 77 | **25** | 52 | Same. |
| `M1.S.6` (≥ 20 nm corner) | 73 | n/a | 73 | All 19.3 nm: clear the LEF's 18 nm, fail the DRM's 20. |
| **Total** | **2,868** | **443** | **2,425** | |

**The 443 covered markers, resolved in OpenROAD** (routed database, OpenROAD 26Q3; `drt::check_drc` reports no M1 violations). Each has cell `OBS` metal on one side and the router's `VIA12` pad (418) or a cell pin (25) on the other.
- Extension order is backward, side, forward (`lefTechLayerEolKeepOutRuleParser.cpp`).
- Different nets are not exempt: `check_drc` reports 41 single-net keep-out violations on M3.
- The cell LEF abstracts match the GDS (DFFASRHQNx1, OAI21x1, BUFx2, TIEHIx1).
- **Cause:** OpenROAD stores `lround(0.01825 × 1000)` = 18 and tests `length < eolWidth`, so no 18 nm tip is a line end. Stored as 19, `check_drc` reports 1,164 M1 keep-out violations, including all 417 `M1.S.4` and the 1 `M1.S.2`; the other 746 are where the keep-out is stricter than the DRM.
- The 25 `M1.S.5` are between two fixed cell shapes, which the checker skips by design.

**All 7,620 markers:**
- **633** are rules the LEF encodes but rounding disables: 418 M1 keep-out cases and 215 `M4`/`M5` `S.4`/`S.5` (§4). Fix: §6.
- **6,987** are rules the LEF lacks, covers partly or states weaker: `V1.M1.EN.1` 4,228, `V0.M1.AUX.3` 309, the 2,425 uncovered M1 markers, and the 25 `M1.S.5` between fixed shapes.

None is the router failing a rule as stored. Two gdscheck readings affect the counts: 2,238 `V1.M1.EN.1` markers fail only on the opposite-sides requirement, and 909 M1 spacing markers are gaps inside one polygon, which would drop if the DRM's "two M1 polygons' edges" excludes them.

## 6. Quarter-nanometre values in the tech LEF

The 1x tech LEF declares `DATABASE MICRONS 1000` and `MANUFACTURINGGRID 0.001` but writes some values on a 0.25 nm grid. OpenROAD stores `lround(value × 1000)` (`odb/lefin.h`). Each such value was read back from OpenROAD and checked against the router's comparison (source `aea554fa3f`):

| Rule | LEF → stored | Comparison | Effect / fix |
| --- | --- | --- | --- |
| M1 `EOLKEEPOUT` line-end width | 0.01825 → 18 | `length < eolWidth` | **Disabled for 18 nm tips** (§5). → 0.019 |
| M4/M5 `EOLKEEPOUT` side extension | 0.02425 → 24 | corner strictly inside | **Misses the adjacent track** (§4). → 0.025 |
| M6/M7 `EOLKEEPOUT` side extension | 0.03225 → 32 | corner strictly inside | **Same.** → 0.033 |
| M8/M9 `SPACINGTABLE` thresholds (0.05975 … 0.99975; 0.39975, 1.19975, 1.79975) | rounded up | value > threshold | **A value exactly on a DRM threshold falls in the row below**; matters only in the 500/1,000 nm rows past 1,800 nm. → round down (0.059 …; 0.399, 1.199, 1.799). Source analysis only. |
| M2/M3 `EOLKEEPOUT` side extension | 0.0125 → 13 | strictly inside | Equivalent for whole-nm geometry |
| M3 `LEF58_SPACING ... WITHIN` | 0.0125 → 13 | query box | Equivalent |
| M6/M7 `ENDOFLINE` width | 0.0375 → 38 | `length < eolWidth` | Equivalent |
| V3/V5 `LEF58_ENCLOSURE ... EOL` width | 0.02425 → 24 | `≤`, via generation only | Equivalent (the checker never applies these rules) |
| M6/M7 `AREA` | 2,187.5 → 2,188 nm² | ≥ | Equivalent |
| `VIARULE M4_M3widePWR0p864` widths | [233.5, 234.5] → [234, 235]; [215.5, 216.5] → [216, 217] | range | Still includes 234 / 216 |

With the fixes, OpenROAD reads the LEF without warnings and stores 19, 25, 33 and the rounded-down thresholds. The 4× LEF holds these values as whole nanometres and is unaffected.

**Where the LEF comes from.** LambdaPDK's `asap7_tech.lef` is byte-identical to `techlef_misc/asap7_tech_1x_201209.lef` in [asap7sc7p5t_28](https://github.com/The-OpenROAD-Project/asap7sc7p5t_28) (added November 2023; LambdaPDK synced it in 2024). That file matches ORFS's `flow/platforms/asap7/lef/asap7_tech_1x_201209.lef` (the platform `TECH_LEF`) less six VT implant layers ORFS added in 2025. Both upstreams also carry `asap7_tech_1x_260907.lef` (M1–M3 aligned with the DRM; ORFS#4532, asap7sc7p5t_28#9), with the same four values.

| Repository | Files | PR | Branch / commit |
| --- | --- | --- | --- |
| siliconcompiler/lambdapdk | `asap7/base/apr/asap7_tech.lef` | [#246](https://github.com/siliconcompiler/lambdapdk/pull/246) | [`asap7-m1-eolkeepout`](https://github.com/jeffhsu3/lambdapdk/tree/asap7-m1-eolkeepout), `be6ee59` |
| The-OpenROAD-Project/OpenROAD-flow-scripts | `asap7_tech_1x_201209.lef`, `_260907.lef` | [#4663](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/pull/4663) | |
| The-OpenROAD-Project/asap7sc7p5t_28 | `asap7_tech_1x_201209.lef`, `_260907.lef` | [#10](https://github.com/The-OpenROAD-Project/asap7sc7p5t_28/pull/10), closed unmerged | |

In ORFS the `201209` change affects every ASAP7 design, so #4663 offers to restrict it to `260907`, as #4532 did. On #246 a reviewer asked whether `DATABASE MICRONS 4000` would be better: it holds the quarter-nanometre values exactly instead of rounding them to whole ones. #10 was withdrawn while that is open, since the 4× LEF might serve OpenROAD flows instead of a patched 1×.

## 7. SHA-256 rerun with the patched LEF

**Setup:** the §5 V6 trial with only the tech LEF swapped for LambdaPDK `be6ee59` (upstream `15c783c` is byte-identical to the v0.2.22 copy used before). `build/lambdapdk_lef_fix_trial/run_trial.py` reuses `open_flow/run_sha256.py`'s `make_chip` and swaps the PDN script and the LEF through a separate data root; no repository file or package changed. Output `build/lambdapdk_lef_fix_trial/.../sha256.gds.gz` (`f668a1a1…ce1e`); gdscheck `3475644` main.

| | V6 trial | Patched LEF |
| --- | ---: | ---: |
| Detailed-route violations | 0 | 0 |
| Wirelength | 53,798 µm | 53,790 µm |
| Vias | 130,756 | 130,984 (+0.17%) |
| `route.detailed` time | 156 s | 191 s (+22%) |
| Setup WNS / hold WNS | −1,411 / −4.06 | identical |
| Setup violations | 1,558 | 1,559 |

| gdscheck rule | V6 trial | Patched LEF | Change |
| --- | ---: | ---: | ---: |
| `M4.S.4` / `M4.S.5` / `M5.S.5` | 61 / 153 / 1 | 0 / 0 / 0 | −215 |
| `M1.S.4` | 508 | 91 | −417 |
| `M1.S.2` | 2,210 | 2,147 | −63 |
| `M1.S.5` | 77 | 55 | −22 |
| `M1.S.6` | 73 | 72 | −1 |
| `V1.M1.EN.1` | 4,228 | 3,801 | −427 |
| `V0.M1.AUX.3` | 309 | 289 | −20 |
| **Total** | **7,620** | **6,455** | **−1,165** |

- **As predicted:** the 215 M4/M5 markers and the 417 keep-out-covered `M1.S.4` are gone. Rerunning the §5 method ([`drc_findings/sha256_lambdapdk_lef_fix_m1_eol_keepout.csv`](drc_findings/sha256_lambdapdk_lef_fix_m1_eol_keepout.csv)) finds none of the 2,365 remaining M1 markers covered: the 91 `M1.S.4` are exactly the in-polygon gaps, `M1.S.2`/`.S.5` have no line end, and `M1.S.6` clears 18 nm.
- **Not predicted:** the drops in `V1.M1.EN.1` (−427), `M1.S.2` (−63) and `V0.M1.AUX.3` (−20), consistent with different pin-access points but not traced.
- **OpenROAD's checker** confirms the stored values (19; 25). A fresh `check_drc` reports 117 violations against 70 on the V6 trial (the router's own final count is 0 on both, before and after antenna repair, an open OpenROAD question). The extra 47 include 50 keep-out violations (42 M1, 5 M4, 3 M5), none within 5 nm of a gdscheck marker, so presumably where the keep-out is stricter than the DRM.
- **Remaining 6,455**, all on rules the LEF lacks or states partly or weaker: `V1.M1.EN.1` 3,801 and `V0.M1.AUX.3` 289 (absent); `M1.S.2` 2,147, `M1.S.4` 91, `M1.S.5` 55 (partial); `M1.S.6` 72 (weaker). §5's two reading caveats still apply; **887** M1 markers are in-polygon gaps (741 `M1.S.2`, 91 `M1.S.4`, 55 `M1.S.5`).

**Not checked:** LVS, power integrity, via current capacity.

## 8. The hand-built ASAP7 SRAM banks

**Setup:** `../asap7/asap7_sram_0p0/gds/srambank_{32b,64b,128b}.gds` (`522eecc`), gdscheck `3475644` main. The banks draw `SRAMDRC` (99/0) over the arrays, and gdscheck exempts shapes overlapping it (DRM §1.2.2, convention 7). KLayout was rerun **flat** (`deep` → `flat`) so its counts are placed occurrences; the repository's `gds/ref_sram.lyrdb` is an earlier hierarchical run and not comparable. Every gdscheck marker, with bank, leaf cell and `SRAMDRC` status: [`drc_findings/asap7_sram_0p0_gdscheck_markers.csv`](drc_findings/asap7_sram_0p0_gdscheck_markers.csv).

**Where:** all but 26 / 26 / 8 markers are in the periphery: row decoders (`dec_nand_*`, `dec_inv_*`), the I/O column (`write_draslatch_02`, `io_inv_18f`, `sram_prech_ymux_*`, `senseamp_sram_6t122`), the control standard cells and the Virtuoso via cells (`M2_M1_CDNS_*`, `M3_M2_CDNS_*`). The few on `SRAMDRC` are `SRAM.LISD.S.4` and `SRAM.NSELECT.ACTIVE.EN.4` in dummy and tap cells and `M5.AUX.1` in the dummy rows. The bitcells raise nothing.

| Group (rules) | 32b | 64b | 128b | Reading |
| --- | ---: | ---: | ---: | --- |
| M4/M5 grid and tracks (`M4.AUX.1/.2`, `M4.W.4`, `M5.AUX.1/.2`) | 1,391 | 1,412 | 710 | **Real.** I/O-column M4 sits at residues 3, 11, 13, 19 nm mod 24, so no single offset clears it. KLayout skips these. |
| 27 nm increments (`SDT.W.3`, `ACTIVE.W.2`) | 472 | 888 | 1,720 | **Real.** Decoder SDT edges are 190 and 55 nm, not multiples of 27. |
| LIG on gate (`LIG.GATE.A.3`, `.AUX.1`, `.EX.1`) | 172 | 284 | 540 | **Real**, one defect per site: in `dec_nand_2f_4f` the 22 nm LIG starts 5 nm inside the gate (15 × 18 = 270 nm² < 320). |
| Front-end spacing (`LISD.S.2`, `LIG.S.4`) | 250 | 442 | 826 | **Real**, e.g. an 18 nm LISD gap between a 27 nm tip and an 81 nm side (≥ 25). |
| M1 spacing (`M1.S.2`, `M1.S.6`) | 204 | 379 | 710 | **Real**: `M1.S.6` in `dec_inv_62f_halved_AND` is 12 nm corner to corner. On 64b, 18 of 123 `M1.S.2` are in-polygon gaps. |
| Via rules (`V0.M1.AUX.3`, `V1.M1.EN.1`, `V1.S.*`, `V2.M2.EN.1`, …) | 125 | 220 | 490 | **Real.** CDNS vias give V2 4 nm of M2 (needs 5) and V1 0 nm of M1 (needs 5/2); decoder V1s are 9 nm apart (needs 18). |
| Other (19 rules on 64b, ≤ 44 each) | 150 | 170 | 499 | Not each inspected; e.g. `GATE.ACTIVE.EX.2` 24.5 nm (≥ 25), `M2.S.6` 19.4–19.7 nm (≥ 20), `M5.S.4` 1 nm stagger. Many are sub-nm misses on the 0.25 nm grid. |
| **Total** | **2,764** | **3,795** | **5,495** | |

**`V0.M1.AUX.3` is settled.** Most SRAM markers are an 18 nm V0 at a T-junction: flush with each 18 nm wire, but M1 continues past it on one side. DRM Fig. 3.11.2(d) (p. 46) marks exactly this ✗, as it does a via at a cross. gdscheck's reading is the DRM's; these 58 / 82 / 130 markers are violations. KLayout finds 4 / 2 on 32b / 64b.

**Against flat KLayout** (32b / 64b):

| | Rules |
| --- | --- |
| Agree | `GATE.ACTIVE.EX.2` (28/28, 44/44), `LIG.GATE.EX.1`, `V1.S.1`, `V1.S.2`, `M2.S.6`, `M1.A.1`; `V2.M2.EN.1` on 32b (32/32; 72 vs 64 on 64b) |
| KLayout about half | `LISD.S.2` (256 vs 124), `M1.S.6` (256 vs 128): 256 distinct gdscheck gaps, so the predicates differ; not traced. On SHA-256 the decks agreed on `M1.S.6` (§2). |
| KLayout totals 107,544 / 209,554, almost all in the array | 202,436 of 204,308 `SDT.W.3` on 64b, all 1,040 `V0.LIG.A.1` and `V0.LISD.EN.3`, 1,028 of 1,160 `LIG.LISD.S.7`, 65 of 67 `GATE.S.1`. Those checks run on whole layers without the SRAM exemption; deck choices, not bitcell defects. |
| KLayout only, outside the array | `V1.S.4` 512, `V1.M2.EN.2` 256, `LIG.LISD.S.7` 132, `LIG.S.4-5` 314 (gdscheck `LIG.S.4` 186), `M2.W.1` 16, `NSELECT.*`, `WELL.S.1` 8. End-cap and same-net classification differ (§3); not compared site by site. |

The 128b flat KLayout run (414,163 items) follows the same pattern: 405,364 are in-array `SDT.W.3`; `LISD.S.2` 512 vs 252, `M1.S.6` 512 vs 386, `V2.M2.EN.1` 157 vs 128, `V0.M1.AUX.3` 130 vs 0, `GATE.ACTIVE.EX.2` 76 vs 76 (gdscheck vs KLayout).

**Not checked:** LVS, the banks' LEF abstracts, and whether the 0.25 nm database grid is acceptable.

## 9. OpenROAD-flow-scripts designs

**Setup:** ORFS master `5a76f84e` with its stock ASAP7 platform (`asap7_tech_1x_201209.lef`, unpatched), OpenROAD 26Q3 (local build of `chipforge-sc-755f577`; ORFS pins `91e5f5f`), checked with gdscheck `cf95b01`. Besides `main`, gdscheck now has an `openroad` suite: `main` without the rules the tech LEF does not give the router (§5–§7's `tech_lef: absent` and `partial` rules), and with `M1.S.6` and `V6.S.2` at the LEF's 18 and 34 nm. A marker under `openroad` is a rule the router was given and broke, or one not yet compared with the LEF. The ORFS build outputs were not archived.

### `syn` writes DEF on a 10 nm grid

`gcd`, `aes`, `aes_lvt`, `jpeg`, `jpeg_lvt` and `swerv_wrapper` (and IHP `gcd`/`aes`, nangate45 `dynamic_node`) set `SYNTH_USE_SYN = 1`, so OpenROAD's built-in `syn` creates the block. Its ODB export (`src/syn/src/flow/export.cc:52`) never sets the block's DEF units, which keep `dbBlock`'s default of 100; `read_verilog` sets them from the tech (`dbReadVerilog.cc:266`). `write_def` scales by `def_units / dbu_per_micron`, and ORFS streams the GDS from that DEF.

| ASAP7 `gcd` | `syn` (stock) | `syn` with fix | Yosys |
| --- | --- | --- | --- |
| `6_final.def` units | 100 | 1000 | 1000 |
| PDN V1 cut (`M2_M1`, 18 nm) | 10 × 10 nm | 18 × 18 nm | 18 × 18 nm |
| gdscheck `main` / `openroad` | 45,778 / 44,206 | 776 / 581 | 874 / 602 |

Fix and regression test: [OpenROAD#11700](https://github.com/The-OpenROAD-Project/OpenROAD/pull/11700). Until it lands, the rest of this section builds `gcd` and `aes` with `SYNTH_USE_SYN=0`.

### Stock ORFS against the two suites

| Design | `main` | `openroad` |
| --- | ---: | ---: |
| SHA-256 (§7, hand-built PDN, for comparison) | 6,455 | **0** |
| `gcd` | 874 | 602 |
| `aes` | 23,745 | 14,449 |
| `aes-block` (hierarchical: 21 `aes_sbox`/`aes_rcon` macros, routed to M9) | 121,152 | 114,821 |

The `openroad` markers trace to four sources, none of them a router failing a rule it was given:

| Source | Rules (`aes-block` count) | Cause |
| --- | --- | --- |
| ORFS PDN scripts | `M4.AUX.1/.2`, `V2.M3.AUX.2`, `V4.M5.AUX.2`, `V5.M6.AUX.2`, `M5`/`M6` `AUX.1`/`W.4`, `M3.S.2` (99,460) | All three ASAP7 PDN scripts (`grid_strategy-M1-M2-M5-M6.tcl`; `BLOCKS_`/`BLOCK_grid_strategy.tcl` for hierarchical designs) connect M2 to M5 on the 270 nm M2 rails, which are off M4's 24 nm grid, with pads wider than their cuts; 0.12 µm M5 straps take narrower V4 cuts; stripe and ring offsets are off-track. |
| Macro placement | `FIN.S.1`, `GATE.S.1` (11,940) | `mpl`'s `Snapper` aligns a macro's pins to the routing tracks only; the cells inside land off the 27 nm fin and 54 nm gate grids. No site/fin option exists in OpenROAD master. |
| LEF via definitions | `V7.M8.AUX.2`, `V8.M8.EN.1`, `V8.M9.EN.2` (989) | `VIA89` has no M8/M9 enclosure; `VIA78`'s 32 nm cut sits in a 40 nm M8 pad, since ORFS#142 (2021) widened the pad to M8's minimum width but not the cut. Not rounding: whole nanometres; asap7sc7p5t_28's 4× LEF has the same `VIA89` and a flush, under-width `VIA78` pad. |
| LEF rules absent | `M8.W.2`–`.W.4`, `M9.W.2`–`.W.4` (2,254) | The DRM widens M8/M9 with run length; the LEF states only 40 nm. The M8 spacing table is also 40 nm almost throughout, where the DRM's `M8.S.2`–`.S.8` grow (untagged; not counted here). |

### Fixes and their effect

Branches on upstream `5a76f84e`: `asap7-pdn-ongrid` (`1ea8e6d4`, pushed to [jeffhsu3/OpenROAD-flow-scripts](https://github.com/jeffhsu3/OpenROAD-flow-scripts/tree/asap7-pdn-ongrid)), with the macro snap `cf485eca` on top locally, and `asap7-tech-lef-vias` (`e501578a`, local). All builds below route with 0 detailed-route DRC errors and keep VDD/VSS connected.

**On-grid PDN** (`1ea8e6d4`), the §2 technique generalised to all three scripts:
- `add_pdn_connect -layers {M2 M5} -min_width_layers {M3 M4} -ongrid {M4}`;
- M5 straps at minimum width (0.024 µm) with `-snap_to_grid`, at a fifth of the pitch (1.08 µm; 0.432 µm at the `BLOCKS` top level) so the metal is unchanged; M6 straps `-snap_to_grid`;
- a new `ring_offsets.tcl` that computes per-side ring `-core_offsets` from the core area and the tracks; ring widths an odd number of track widths (M5 0.408 µm, under its 0.48 maximum; M6 0.288 µm, the only width with a flush V5 rule).

| Design | `openroad`, stock → on-grid PDN | Worst IR drop (VDD), stock → new | Setup WNS |
| --- | --- | --- | --- |
| `gcd` | 602 → **0** | 0.61% → 0.40% | |
| `aes` | 14,449 → **0** | 4.56% → 2.80% | −2.57 → −2.95 ps |
| `aes-block` | 114,821 → 15,756 | 0.44% → 0.17% | |

Minimum-width straps at the stock 5.4 µm pitch raised `aes` to 11.6%; 2.16 µm gave 5.2%, 1.08 µm 2.8%.

**Macro snap** (`cf485eca`): `snap_macros_to_fin_grid.tcl` as `POST_MACRO_PLACE_TCL` moves each macro to the nearest origin that puts its cells on the fin and gate grids and keeps its pins on the tracks of every layer they use, mirrored placements included. On `aes-block` the 21 macros move ≤ 0.192 µm, each a whole number of 48 nm tracks: `FIN.S.1`/`GATE.S.1` 11,940 → **0**, total 15,756 → 3,795, IR 0.22%, WNS −9.2 ps.

**LEF vias** (`e501578a`, kept separate because it changes routing for every design that uses M8/M9): `VIA89`'s M8 and M9 pads run 20 nm past the cut along their own direction; `VIA78`'s V7 is 32 × 40 nm, flush with the 40 nm M8, with the M7 pad lengthened to keep 11 nm. On `aes-block`: 874 → **0**, total 3,795 → **2,912**, WNS −8.9 ps.

**Tried and not adopted:**
- `MAX_ROUTING_LAYER = M7` at the `aes-block` top level removes every M8/M9 marker (3,795 → 975) but costs setup WNS −9.2 → −33.4 ps and TNS −9.2 → −378.6 ps. Overriding it on the command line also raises the sub-blocks to M7, whose abstracts then block the top PDN (`PDN-0006`).
- Setting `M6_M5widePWR1p152`'s M5 enclosure to `0.0 0.011` changes nothing: pdngen still writes `ENCLOSURE 0 0 0 0` for the V5 bar where a macro halo cuts an M5 strap flush with an M6 wire.

**What remains on `aes-block` (2,912):**

| Rules | Count | Cause | Possible fix |
| --- | ---: | --- | --- |
| `M8.W.2`–`.W.4`, `M9.W.2`–`.W.4` | 1,938 | LEF has no width-by-length rule | A LEF58 rule the router honours, if one exists; else M7 at a timing cost |
| `V5.M5.EN.1`, `V5.M6.EN.2` | 897 | pdngen places V5 at a cut strap's flush end | pdngen, or trim straps short of an M6 wire |
| `M4.S.2`, `M5.S.2` | 75 | Signal wires near PDN pads inside the macros | Untagged LEF gap; not traced |
| `ACTIVE.S.2A` | 2 | Adjacent `DFFHQx4` cells | Library or placement |

**Not checked:** LVS, EM, timing on designs other than `aes` and `aes-block`, and other ASAP7 designs (`ibex`, `jpeg`, `riscv32i-mock-sram`, …).
