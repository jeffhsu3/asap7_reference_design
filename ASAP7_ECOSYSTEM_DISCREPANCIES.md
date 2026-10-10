# ASAP7 ecosystem discrepancies

This is a running list of differences between the ASAP7 design-rule manual (DRM), technology collateral, routing flows, and independent DRC decks. A rule being present in a deck or a router reporting zero violations does **not** establish that the corresponding DRM requirement was checked on the final GDS. Treat findings here as specific to the cited collateral and experiments, not as signoff.

## 1. V1.M1.EN.1: M1 enclosure of V1 (open investigation)

**DRM requirement.** ASAP7 DRM `asap7_drm_201207a.pdf`, §3.13, Table 3.13.1 (printed p. 49), says: “Minimum enclosure of V1 by M1 on two opposite sides,” `≥ 5&2 nm`. Our working interpretation is **5 nm on one side and 2 nm on its opposite side, on the same axis**; either axis and orientation may satisfy the pair. A 2/2 nm pair does not satisfy 5/2. The manual is at `../asap7/asap7_pdk_r1p7/docs/asap7_drm_201207a.pdf` in this workspace.

| Component | Observed encoding or result | Status / limitation |
| --- | --- | --- |
| [ASAP7_for_KLayout deck](../ASAP7_for_KLayout/drc/drc_ASAP7.lydrc), lines 312–314 | Contains two active checks labelled `V1.M1.EN.1`, using `enclosing(..., 2.nm, ..., two_connected_sides_allowed)` and `enclosing(..., 5.nm, ...)` plus an `m1ovlp5v1` filter. | **Suspected implementation bug/false negatives, not an intentional omission.** A focused run using those exact two expressions emitted zero `V1.M1.EN.1` markers on the failing fixtures below. We have not proved the exact cause inside KLayout's edge/region operations or that all violations are missed. |
| [gdscheck V1 deck](../gdscheck/pdks/asap7/decks/v1.yml), lines 50–56 | `min_enclosure` with `value: 0.005`, `sides: opposite`, `opposite_value: 0.002`. | Matches the working DRM interpretation on the fixtures below. Its [ASAP7 tests](../gdscheck/tests/asap7.rs) include a 5/2 vs. short/split-pair case. This does not certify every marker in a full design. |
| [Closed-source flow's modified 4× tech LEF](techlef/asap7_tech_4x_201209.lef), lines 837–844 | Default `VIA12` has M1 `RECT -0.036 -0.044 0.036 0.044`, V1 `RECT -0.036 -0.036 0.036 0.036`. At 4×, its M1 enclosure is 0/0 nm along x and 8/8 nm along y; scaled back to DRM coordinates this is **0/0 and 2/2 nm**, not 5/2. | The **visible default via geometry** does not independently meet this DRM rule. Additional same-net M1 metal could change the final merged geometry of a particular occurrence. |
| [Closed-source flow's generated via rule](techlef/asap7_tech_4x_201209.lef), lines 969–977 | `VIARULE M2_M1 GENERATE DEFAULT` specifies `ENCLOSURE 0 0.0` for M1. The V1 layer definition at lines 146–150 has width and spacing but no V1-specific LEF58 enclosure rule. | No explicit 5/2 requirement was located in this tech LEF. **Do not infer that Innovus internally ignores it**: proprietary node-specific rules, effective-rule settings, and the actual Innovus DRC results were not inspected. |
| [Innovus script](scripts/innovus.tcl), lines 21–25, 193, 204–224, 274 | Loads that modified tech LEF; calls `verify_drc` **before** placement optimization and signal routing, with no final signoff DRC command provided. | The [README](README.md) reports DRC-clean Innovus databases, but those claims do not establish this particular rule was checked on final GDS. No Innovus run was performed in this investigation. |
| Open-source SiliconCompiler/OpenROAD flow (separate collateral) | LambdaPDK `asap7_tech.lef` `VIA12` likewise has 2/2 nm M1 end enclosure, and its `M2_M1` generated via rule specifies zero M1 enclosure. | This is **not** the modified Innovus LEF above. A zero OpenROAD router-violation count only covers the constraints that flow was given; it is not a DRM signoff result. |

**Controlled geometric reproduction.** An isolated GDS fixture with 18 nm square V1 cuts and three M1 cases was checked with gdscheck's `asap7/v1` deck and a focused KLayout deck containing the two expressions from the cited ASAP7_for_KLayout runset. For the M1 margins below, the unaffected opposite axis has zero margin. Auxiliary gdscheck `V1.M2.AUX.2` markers were present because the deliberately simple fixture's M2 shape does not meet that separate rule; they are excluded from this enclosure comparison.

| Opposite M1 margins | Expected for V1.M1.EN.1 | gdscheck markers | KLayout markers |
| --- | --- | ---: | ---: |
| 5/2 nm | Pass | 0 | 0 |
| 2/2 nm | Fail | 1 | 0 |
| 4/2 nm | Fail | 1 | 0 |

The local test artifacts were `/tmp/v1_enclosure_fixture.py`, `/tmp/v1_enclosure_fixture.gds`, `/tmp/v1_enclosure_klayout.lydrc`, `/tmp/v1_enclosure_klayout.lyrdb`, and `/tmp/v1_enclosure_gdscheck.lyrdb` (temporary, **not checked into this repository**). To reproduce after those files disappear, construct three isolated 18 nm V1 squares on GDS layer 21/0 with rectangular M1 on 19/0 at the tabulated margins, add M2 on 20/0, run the two KLayout expressions at lines 313–314 on M1/V1, and run `gdscheck run --process asap7 --deck v1` on the same GDS. Inspect only `V1.M1.EN.1` markers in both reports.

**Design-level evidence, not a one-for-one comparison.** On the open-source SHA-256 baseline GDS, gdscheck's ASAP7 main deck reported **4,145** `V1.M1.EN.1` markers; the full ASAP7_for_KLayout deck reported **zero** in that category. At one gdscheck marker near `(2.304, 16.515) µm`, a local merged-GDS probe found the V1 rectangle `(2.304, 16.506)–(2.322, 16.524) µm` and M1 extending just 2 nm above/below the V1 cut, with no qualifying 5/2 opposing pair at that site. The two decks have different coverage; neither total proves that all reported markers are independent electrical defects, and the open-source GDS is **not** the archived Innovus layout.

**Next checks before changing a PDK or declaring a tool bug:** isolate the first KLayout expression's failure mode with single-rectangle and merged-cell fixtures and establish a regression test; examine the effective Innovus rule database and `verify_drc` output on a controlled 5/2-versus-2/2 fixture, if licensed tools are available; run a final independent DRC on any exported Innovus GDS (with layer mapping and 4× scaling verified). Do not silently alter the official DRM or either flow's LEF based only on these observations.

## 2. Other gdscheck / ASAP7_for_KLayout differences (triage, not signoff)

For the same **open-source** SHA-256 baseline GDS (`build/pdn_m5_minwidth/sha256/sha256_official/write.gds/0/outputs/sha256.gds.gz`), the full [ASAP7_for_KLayout deck](../ASAP7_for_KLayout/drc/drc_ASAP7.lydrc) returned **493 report items in 12 categories** (`/tmp/sha256_m5_default_full_drc.lyrdb`); the gdscheck ASAP7 **main** suite returned **17,729 in 13 categories** (`/tmp/sha256_seed0_gdscheck_main.lyrdb`). After gdscheck added `M4`–`M7` `.S.4`/`.S.5` (commits `763954c`, `3ccb754`), the same suite returns **17,955 in 15 categories**: the earlier 17,729 unchanged plus 164 `M4.S.5` and 62 `M4.S.4`. These are different rule sets and reporting granularities, **not** two estimates of the same number of physical defects. The following are additional, individually traceable discrepancies. Counts below are for this GDS and these deck versions only; zero means no category appeared in that report, not that the underlying geometry is DRM-clean.

| Rule(s) | KLayout | gdscheck | What differs / next validation |
| --- | ---: | ---: | --- |
| `M4.AUX.1`, `M4.AUX.2` | 0, 0 | **7,612**, **2,211** | DRM §3.14 Table 3.14.2 (printed p. 54) requires M4 horizontal edges on a 24 nm grid and minimum-width M4 on specified tracks. KLayout's grid section at lines 515–523 is **disabled by `OFFGRID = false` (line 42)**; its main M4 section explicitly says `M4.AUX.2` is not coded (line 368). gdscheck's [`m4.yml`](../gdscheck/pdks/asap7/decks/m4.yml), lines 100–113, enables both checks with a *default* zero grid offset and 12 nm track offset. The DRM permits design-specific offsets (p. 54 note 1): verify the intended offsets and test individual shapes before calling every marker a real violation. Even if KLayout's optional grid section were enabled, its M6/M7 rules at lines 521–522 are **mislabelled as `M4.AUX.1`/`M5.AUX.1`**, which would confound category counts. |
| `M4.S.5` | **258** | **164** | DRM §3.14 Table 3.14.1 (printed p. 53) requires ≥44 nm parallel run length for M4 polygons on adjacent tracks. KLayout line 366 checks `m4.space(25.nm, projection)` edges shorter than 44 nm. gdscheck now implements it as `min_track_run` ([`m4.yml`](../gdscheck/pdks/asap7/decks/m4.yml), lines 93–99): two rectangular M4 wires whose long walls face across y with a gap under **72 nm** (three widths, so no wire could be routed between them), and which share a positive run under 44 nm. KLayout's 258 report items form **129 facing-edge pairs**, predominantly 1 nm overlap. **Every one of the 129 matches a gdscheck marker** (same x-range and gap). With gdscheck's adjacency limit narrowed to <25 nm, its count is exactly 129. The extra 35 come from the wider adjacency definition. Six inspected extras (e.g. M4 `(14.226,24.558)–(14.310,24.582)` and `(13.201,24.624)–(14.249,24.648)` µm) have a 42 nm gap because one wire is **off-track** (centre 24.570 µm, not 12 + 48k nm), so they are also `M4.AUX.2` markers. Gaps of 48 nm beside a three-width wire are also included by design. None of these counts is 164 or 129 unique defects; review the 1 nm overlaps against the router's intended geometry before changing routes. |
| `M4.S.4` | 0 | **62** | DRM §3.14 Table 3.14.1 requires ≥40 nm tip-to-tip spacing for M4 polygons on adjacent tracks that share a parallel run. DRM Fig. 3.14.2(d) draws it between the **same-side** tips of two overlapping wires. gdscheck implements it as `min_tip_stagger` (lines 86–92), with the same pairs as `.S.5`. It flags a same-side tip offset that is positive and under 40 nm, and treats **aligned tips as clean**, because the manual draws flush ends in its `.S.1` example. That clean-when-aligned reading is an interpretation, not stated in the table. KLayout line 365 checks something different: a projected notch under 40 nm in M4 grown 48 nm across the track, minus the same-track `.S.2` gaps. That finds facing walls, not same-side tips, and reported nothing here. With the <25 nm adjacency limit, gdscheck reports 26. The predicates differ, so 0 vs 62 is not a like-for-like comparison. No M5–M7 `.S.4`/`.S.5` items appeared in either report. |
| `M1.S.2` and `M1.S.4/.S.5` | **46** (`M1.S.2`); 0 (`M1.S.4-5`) | **2,133** (`M1.S.2`); **490/93** (`M1.S.4/.S.5`) | DRM §3.12 Table 3.12.1 (printed p. 47) defines tip-to-side and edge-length-dependent tip-to-tip spacings. KLayout lines 269–274 filter generic `m1.space` results with edge-length interactions; gdscheck's [`m1.yml`](../gdscheck/pdks/asap7/decks/m1.yml), lines 18–43, explicitly selects short/long/tiny/mid edges. **Not yet established which differing markers are valid.** In particular, the first gdscheck `M1.S.2` marker is an M1 24 nm gap near `(2.304, 16.515) µm`, coincident with the previously inspected `V1.M1.EN.1` site; check the actual opposing edge lengths and nearby same-net merged geometry before attributing the count gap to a checker bug. |
| `M1.S.6` | **78** | **78** | This same-code, same-count corner-spacing check (DRM p. 47, ≥20 nm) is a useful control, **not proof of marker identity**. Compare marker geometry one-to-one before claiming checker equivalence. |
| `V6.S.1/.S.2/.S.3` | **3** under combined `V6.S.1-2-3` | **624** under `V6.S.2` | DRM §3.17 Table 3.17.1 (printed p. 65) sets ≥45 nm for same-net, different-net, and corner spacing; it also warns these rules will be revised. KLayout line 448 applies one 45 nm check, and its **three report items are in the reusable `VIA_via6_7_288_288_4_1_322_66` cell**. gdscheck's [`v6.yml`](../gdscheck/pdks/asap7/decks/v6.yml), lines 5–7 and 17–20, combines the three checks under `.S.2` and reports top-cell occurrences: the first markers have 34 nm gap at `(0.784, 0.953–0.987) µm`. Thus raw 3-vs-624 mixes category naming and hierarchy/multiplicity. Whether 624 maps precisely to repeats of those three master-cell defects needs an explicit transformed-cell/coordinate match. |

**M4 AUX attribution and controlled PDN test.** On the min-width baseline GDS, every `M4.AUX.1` (7,612) and `M4.AUX.2` (2,211) marker coordinate falls inside a `VDD` or `VSS` M4 `DRCFILL` rectangle in the *floorplan.power_grid* DEF; the same M4 special-net rectangles persist after detailed routing. This is coordinate-to-PDN attribution, not a claim that 9,823 unique pads exist: the baseline DEF contains 2,530 M4 pad rectangles and the two checks emit different numbers of markers per pad. The installed LambdaPDK RVT `apr/openroad/tracks.tcl` has `make_tracks M4 ... -y_offset 0.012 -y_pitch 0.048`; its stock `apr/openroad/pdngen.tcl` connects `{M2 M5}` without `-ongrid`. Our [custom PDN](open_flow/pdn_ring.tcl) retains the LambdaPDK track definition but replaces the stock PDN grid. The actual OpenROAD `add_pdn_connect` supports `-ongrid` for intermediate layers. In an isolated run with only `-ongrid {M4}` added to the existing minimum-width M2→M5 connection, the 2,530 M4 PDN pads all had centre y ≡ 12 nm (mod 48 nm), versus eight residues in the baseline. The full run exported `build/pdn_m4_ongrid/sha256/sha256_official/write.gds/0/outputs/sha256.gds.gz`, passed OpenROAD VDD/VSS connectivity and `gzip -t`, and the **stock** gdscheck M4 deck returned `M4.AUX.1 = 0` and `M4.AUX.2 = 0` (`/tmp/sha256_pdn_m4_ongrid_gdscheck.lyrdb`), versus 7,612/2,211 on the baseline. Other M4 checks still fail (`M4.S.4 = 61`, `M4.S.5 = 153`); this is not a full-deck, LVS, or power-integrity pass. The earlier +12 nm **tech-LEF** variant was a different experiment and did not align the PDN pads.

**Scope to investigate next.** Other gdscheck-only categories on this GDS include `M4.S.4` (above), `M6.AUX.1`, `M6.W.4`, `M7.AUX.1`, `M7.W.4`, and `V0.M1.AUX.3`; KLayout-only reported categories include `V1.S.4`, `V0.S.1`, `V5.M6.AUX.2`, and `GATE.S.1`. Do not label these as bugs based on report absence alone: check each DRM rule, deck switches, layer/SRAM filtering, GDS hierarchy, and a known-pass/known-fail fixture. The open-source GDS and the modified 4× Innovus collateral are separate experiments.

## 3. Follow-up on the remaining report-only categories

Same baseline GDS and reports as §2. The DRM citations below refer to `../asap7/asap7_pdk_r1p7/docs/asap7_drm_201207a.pdf`; **report items are not necessarily unique placed defects**. This investigation inspected the applicable deck code and selected merged-GDS sites, but did not run new full-deck checks, tune offsets, or establish signoff correctness.

| Rule(s) | Baseline report items (KLayout / gdscheck) | Evidence and assessment |
| --- | ---: | --- |
| `M6.AUX.1`, `M7.AUX.1` | 0 / **16**, 0 / **16** | DRM §3.16, Table 3.16.2 (printed p. 61) specifies a 32 nm grid, perpendicular directions for M6/M7, and configurable offsets (note 1). gdscheck [`m6.yml`](../gdscheck/pdks/asap7/decks/m6.yml) and [`m7.yml`](../gdscheck/pdks/asap7/decks/m7.yml), lines 100–106, use **zero** offset. One shared marker at `(0.784, 0.892) µm` is the corner of top-level M6/M7 **power-grid** rectangles; `0.892 µm` is not on the zero-origin 32 nm y grid and `0.784 µm` is not on the zero-origin 32 nm x grid. KLayout's checks remain disabled by `OFFGRID = false` ([deck](../ASAP7_for_KLayout/drc/drc_ASAP7.lydrc), lines 42, 515–522). If enabled, its M6/M7 checks also have the **wrong output category labels** noted above. Missing KLayout items follow from the disabled section; gdscheck's marker validity still depends on the design's actual configured grid origin. |
| `M6.W.4`, `M7.W.4` | 0 / **4**, 0 / **4** | DRM §3.16, Table 3.16.1 (printed p. 60) forbids wide metal spanning an even number of minimum-width tracks. KLayout explicitly says these two checks are **not coded** (lines 413, 431). gdscheck's [`m6.yml`](../gdscheck/pdks/asap7/decks/m6.yml) / [`m7.yml`](../gdscheck/pdks/asap7/decks/m7.yml), lines 42–48, use wide-metal centreline off-track checks with a fixed 16 nm offset and 64 nm pitch. The reports give example M6 centre `y=1.036 µm` and M7 centre `x=0.928 µm`. They are **not independently validated as violations of the DRM's even-track condition**: distinguish power strap widths/track origin from a generic off-track centre before changing PDN geometry. |
| `V0.M1.AUX.3` | 0 / **303** | DRM §3.11, Table 3.11.2 (printed p. 43): V0 must match M1 width perpendicular to M1 length. Both decks contain checks: KLayout line 264 uses `v0.not_interacting(m1.enclosing(...).edges)`; gdscheck [`v0.yml`](../gdscheck/pdks/asap7/decks/v0.yml), lines 101–106, uses zero max enclosure on opposite sides. The first gdscheck marker reports **4 nm** M1 overhang. At `(3.636,29.230)–(3.654,29.248) µm`, the merged V0 is 18 nm square and merged M1 extends to `y=29.252 µm` above it. This verifies an overhang exists, **not** that the perpendicular-to-M1-length direction or 303 independent sites all violate the DRM. KLayout's missing category is a candidate false negative requiring a controlled orientation fixture; no intentional omission is documented. |
| `V1.S.4` | **49** / 0 | DRM §3.13, Table 3.13.1 (printed p. 49): ≥27 nm **corner-to-corner** only for vias with differing 5 nm M2 end-cap status. Both decks implement a check (KLayout line 310; gdscheck [`v1.yml`](../gdscheck/pdks/asap7/decks/v1.yml), lines 41–49), but use different corner/end-cap classification. In one top-level KLayout marker near `(13.599,60.417) µm`, the two V1 boxes are `(13.574,60.392)–(13.590,60.408)` and `(13.608,60.426)–(13.624,60.442)` µm; their nearest corners are offset **18 nm in both x and y**, while local merged M2 touches the lower via and extends 5 nm to its right. This establishes a corner candidate but **does not prove both vias' full end-cap classes** or which checker is right. KLayout's 49 include hierarchical standard-cell items, so direct total comparisons need cell-occurrence expansion. |
| `V0.S.1` | **7** / 0 | DRM §3.11, Table 3.11.1 (printed p. 42) distinguishes same-track and aligned/not-aligned adjacent-track spacing. KLayout lines 249–251 use projection and Euclidean checks; gdscheck [`v0.yml`](../gdscheck/pdks/asap7/decks/v0.yml), lines 14–27, applies the 18 nm facing check and separately classifies corner spacing under `.S.2`–`.S.4`. All seven KLayout report items are in reusable **standard-cell** masters, not the top cell; these are not seven distinct placed sites. A transformed-instance geometry and SRAM-applicability comparison is needed before interpreting gdscheck's zero as a false negative. |
| `V5.M6.AUX.2` | **2** / 0 | DRM §3.15, Table 3.15.1 (printed p. 58; V4 rule inherited by V5) requires the via to match M6 width perpendicular to M6 length. Both decks check it (KLayout line 405; gdscheck [`v5.yml`](../gdscheck/pdks/asap7/decks/v5.yml), lines 44–49). KLayout's two items occur in **via master cells**: `VIA_via5_6_24_288_1_1_58_322` has a 24 nm-wide V5 and M6 rectangle flush in x; `VIA_VIA56` has a 24 nm-wide V5 with M6 from `x=-23` to `+23` nm, an 11 nm overhang per side. This flags a hierarchy/merged-geometry question, not two verified DRM defects: check placed M6 and the axis of the mismatch before identifying a false positive/negative. |
| `GATE.S.1` | **22** / 0 | DRM §3.4, Table 3.4.1 (printed p. 19) requires exact 54 nm horizontal gate pitch. KLayout line 147 uses a derived `gate.space(100.nm, projection)`-based check; gdscheck [`gate.yml`](../gdscheck/pdks/asap7/decks/gate.yml), lines 7–10 and 28–34, checks gate centres on a 54 nm grid with a fixed 27 nm offset. A KLayout marker near `(25.893,63.725) µm` overlaps a merged GATE rectangle `x=25.883–25.903 µm` and GCUT `x=25.868–25.918 µm`. **These checks do not express identical predicates** (pairwise pitch versus absolute-grid placement). Check transformed gate centres, the design's gate grid origin, GCUT treatment, and a two-gate fixture before deciding if either report is incorrect. |

**Priority:** first establish actual M6/M7 power-grid origins and track definitions, then compare the orientation-specific `V0.M1.AUX.3` and `V5.M6.AUX.2` checks with small pass/fail fixtures; follow with end-cap and gate-pitch fixtures. Keep master-cell report items distinct from their placed occurrences. None of these report-only categories is established as a checker bug by count alone.

## 4. M4.S.4 / M4.S.5 after the on-grid PDN rerun

**Layout.** Open-source SHA-256 rerun with the M2→M5 PDN via stacks snapped onto LambdaPDK's M4 tracks (`open_flow/pdn_ring.tcl`, `add_pdn_connect ... -min_width_layers {M3 M4} -ongrid {M4}`): `build/pdn_m4_ongrid/sha256/sha256_official/write.gds/0/outputs/sha256.gds.gz` (sha256 `fa0a56b1…e67b`). With that change, gdscheck reports no `M4.AUX.1`/`.AUX.2` markers. Earlier, the 2,211 off-track M4 wires were minimum-width PDN pads on the 270 nm cell-row pitch, which does not fit the 48 nm track pitch.

**Report.** `gdscheck run --process asap7 --deck m4` at gdscheck commit `3ccb754` returns **153 `M4.S.5`** and **61 `M4.S.4`**. The full per-marker list is [`drc_findings/sha256_pdn_m4_ongrid_m4_s4_s5.csv`](drc_findings/sha256_pdn_m4_ongrid_m4_s4_s5.csv). Each row gives the marker, the overlap (`.S.5`) or tip offset (`.S.4`), the gap, both M4 wire rectangles, and whether each wire is a signal wire or a PDN pad. A PDN pad is an M4 shape that overlaps a PDN M5 strap and a V4. The CSV was produced by matching each lyrdb marker to the merged top-cell M4, V3, V4 and M5 geometry. It does not include net names.

| | `M4.S.5` | `M4.S.4` |
| --- | ---: | ---: |
| Total | 153 | 61 |
| Signal wire / signal wire | 136 | 58 |
| One side a PDN M2→M5 pad | 17 | 3 |
| Gap between the wires | 24 nm (all) | 24 nm (all) |
| Most common value | 1 nm overlap (119) | 18 / 24 / 30 nm offset (11 / 10 / 9) |

Every marker is a pair of minimum-width wires on neighbouring tracks. None depends on gdscheck's wider adjacency limit (gap < 72 nm), and none involves an off-track wire.

**How the 1 nm overlaps arise.** The M4 wires end on V3/V4 vias, which sit on the 36 nm M3 track pitch (via centre x ≡ 9 nm mod 36). In 87 of the 119 1 nm `.S.5` overlaps, one wire extends 11 nm past its last via and the neighbour extends 44 nm past its first via, with the two vias two M3 tracks (72 nm) apart. The overlap is 11 + 44 + 18 (via width) − 72 = **1 nm**. Most remaining 1 nm cases are the same arithmetic with other extensions (e.g. 38/11 nm at 69 nm). `.S.4` is the same mechanism for tips on the same side: they land 6–39 nm apart (33 high-tip, 28 low-tip). The cause of the 44 nm extension has not been traced; a min-area extension for the M4 `AREA 0.002` rule is plausible but unverified.

**LambdaPDK encodes these rules only approximately, and the approximation is disabled by rounding.** *(Corrected; an earlier version of this paragraph said the LEF has no such rule.)* The `LAYER M4` section of LambdaPDK's `asap7_tech.lef` (identical to ASAP7's `asap7_tech_1x_201209.lef`) has `LEF58_EOLKEEPOUT 0.025 EXTENSION 0.048 0.02425 0.048 CORNERONLY`: no corner of another shape within 48 nm either way of a line end, reaching 24.25 nm to the side. Since adjacent-track wires are 24 nm apart, this forbids a neighbouring tip near a line end, which covers both `M4.S.4` and `M4.S.5`. It is stricter than the DRM, because it also forbids aligned tips and a 40–48 nm stagger. However, the LEF declares `DATABASE MICRONS 1000`, and OpenROAD rounds 24.25 nm to 24, exactly the neighbour's edge. Its checker requires the corner to lie strictly inside the keep-out, so the rule never reaches the adjacent track. On the routed V6 cut-pitch trial database, `drt::check_drc` reports 0 M4/M5 keep-out violations as loaded. With the side extension set to 25 nm it reports 249 on M4 and 2 on M5, and every gdscheck `M4.S.4` (61), `M4.S.5` (153) and `M5.S.5` (1) marker matches one within 50 nm. The other 20 are presumably the stricter-than-DRM cases (not verified). M6/M7 have the same problem (`0.03225` → 32 nm against a 32 nm gap) but report no new violations on this design. gdscheck now marks M4–M7 `S.4`/`S.5` as `tech_lef: partial`. See §6 for the LEF fix.

**Agreement with KLayout.** On the earlier baseline (§2), all 129 KLayout `M4.S.5` pairs matched gdscheck markers, so the 1 nm overlaps are flagged by both decks. KLayout's `M4.S.4` expression checks facing walls rather than same-side tips (§2), so it is not an independent check of the 61 `.S.4` markers. Their validity rests on gdscheck's reading of DRM Fig. 3.14.2(d), which treats aligned tips as clean.

## 5. M1 spacing markers against the tech LEF's end-of-line keep-out

**Layout and report.** The V6 cut-pitch trial (`build/v6_cut_pitch_xy_trial/sha256/sha256_official/write.gds/0/outputs/sha256.gds.gz`, sha256 `868c437b…a7c9`; `add_pdn_connect -layers {M6 M7} -cut_pitch {0.333 0.077}`). The gdscheck main suite at commit `42ce435` reports **7,620** markers, including `M1.S.2` 2,210, `M1.S.4` 508, `M1.S.5` 77 and `M1.S.6` 73. The standard cells on their own are DRC clean, and every one of these M1 markers sits at or next to a router `VIA12` M1 pad.

**What the LEF states for M1.** LambdaPDK's `asap7_tech.lef` (the ASAP7 1x tech LEF, unchanged) has three M1 spacing statements:
- `SPACING 0.018`, which is DRM `M1.S.1`;
- `LEF58_EOLKEEPOUT 0.01825 EXTENSION 0.0 0.0 0.031`, a 31 nm keep-out in front of a line end at most 18.25 nm wide;
- `LEF58_CORNERSPACING ... SPACING 0.018`.

It has nothing for the DRM's edge-length rules as such. gdscheck therefore marks `M1.S.2`/`.S.4`/`.S.5` as `tech_lef: partial`, `M1.S.3` as `absent` and `M1.S.6` as `weaker`.

**Method.** Each marker is the closest-approach segment between two facing M1 edges. Both edges were recovered from the merged top-cell M1. A marker counts as **covered** by the keep-out if either facing edge is an end-of-line edge and the other edge overlaps the 31 nm strip in front of it by more than a point. An end-of-line edge here is one shorter than 18.25 nm with both corners convex. The extension values are read as backward 0, side 0, forward 31 nm, so the strip is exactly as wide as the line end. `M1.S.6` is corner-to-corner, which that strip cannot cover, so it was compared with the LEF's 18 nm corner spacing instead. Per-marker results are in [`drc_findings/sha256_v6_cut_pitch_m1_eol_keepout.csv`](drc_findings/sha256_v6_cut_pitch_m1_eol_keepout.csv): the edge lengths, whether the gap lies inside one polygon, and whether a `VIA12` pad is at the marker. Nets were not resolved.

| Rule | Markers | Covered by the keep-out | Not covered |
| --- | ---: | ---: | ---: |
| `M1.S.2` (≥25 nm) | 2,210 | 1 | 2,209 |
| `M1.S.4` (≥31 nm) | 508 | **417** | 91 |
| `M1.S.5` (≥31 nm) | 77 | **25** | 52 |
| `M1.S.6` (≥20 nm corner) | 73 | n/a: all 19.3 nm, above the LEF's 18 nm | 73 |
| **Total** | **2,868** | **443** | **2,425** |

**Not covered (2,425): a gap in the LEF.**
- `M1.S.2`: neither facing edge is a line end by the LEF's definition. Typical pairs are a 22 nm `VIA12` pad side facing a 99 or 180 nm pin edge, or an 11 nm or 4 nm jog edge with a concave corner.
- `M1.S.4` (91) and `M1.S.5` (52): these are gaps inside a single polygon. The short edge has a concave corner, so the LEF does not treat it as a line end.
- `M1.S.6`: every marker clears the LEF's 18 nm corner spacing and fails only the DRM's 20 nm.

None of these is a rule the router was given, so the zero OpenROAD violation count says nothing about them.

**Covered (443): the LEF keep-out applies, yet OpenROAD reported zero violations.** All 443 are between two separate polygons, not inside one, and all sit next to a `VIA12` pad.
- `M1.S.4` (417): typically an 18 nm tip of cell obstruction (LEF `OBS`) metal with the router's pad 22 nm in front of it, e.g. `(3.042–3.064, 43.5095) µm`; 392 also have router M1 nearby (mostly DFFASRHQNx1 sites).
- `M1.S.5` (25): an 18 nm obstruction tip 30 nm from a cell pin whose edge a pad has lengthened to 27 nm, e.g. `(16.990, 35.415–35.445) µm`.
- `M1.S.2` (1): a 24 nm gap in front of an 18 nm tip at `(22.383, 49.222–49.246) µm`.

**Resolved with OpenROAD's checker.** On the routed database (`route.detailed_antenna_repair` output, OpenROAD 26Q3), `drt::check_drc` reports **no** M1 violations. Nets and owners were resolved from the database: every one of the 443 has cell obstruction metal on one side, and the router's `VIA12` pad (418) or a cell pin (25) on the other. Checked against OpenROAD's source and by experiment:
- **The order of the extension values is as assumed** (backward, side, forward; `lefTechLayerEolKeepOutRuleParser.cpp`).
- **Different nets are not exempt.** `check_drc` itself reports 41 single-net keep-out violations on M3.
- **The cell LEF abstracts match the GDS.** For DFFASRHQNx1, OAI21x1, BUFx2 and TIEHIx1, the LEF M1 (pins + `OBS`) equals the GDS M1.
- **The cause: the stored line-end width is 18, not 18.25.** OpenROAD stores LEF distances as `lround(value × 1000)` for `DATABASE MICRONS 1000`. Its line-end test is `length < eolWidth`, so no 18 nm tip is ever a line end. Raising the stored width to 19 on the same database makes `check_drc` report 1,164 M1 keep-out violations, including all 417 `M1.S.4` and the 1 `M1.S.2`. The rest (746) are where the 31 nm keep-out is stricter than the DRM.
- **The 25 `M1.S.5` markers are not affected:** both shapes are fixed cell metal, a pair OpenROAD's checker deliberately skips. The router's pad does not move either shape; it only lengthens the pin's facing edge into the DRM's mid-length class.

**Summary of the 7,620 markers on this layout.**
- **633** are rules the LEF does encode, but in values that a 1 nm database rounds into ineffectiveness: the 418 M1 keep-out cases above, and the 215 `M4`/`M5` `S.4`/`S.5` markers (§4). See §6.
- **6,987** are rules the tech LEF lacks, only partly covers, or states weaker: `V1.M1.EN.1` (4,228), `V0.M1.AUX.3` (309), the 2,425 uncovered M1 markers above, and the 25 `M1.S.5` markers between fixed cell shapes.

None of the 7,620 is a router failing to enforce a rule as it was stored.

Two of gdscheck's DRM readings also affect the counts. 2,238 of the `V1.M1.EN.1` markers fail only because the 5 nm and 2 nm margins must be on opposite sides. 909 M1 spacing markers are gaps inside one polygon, which would drop if the DRM's "two M1 polygons' edges" excludes them.

## 6. Quarter-nanometre values in the tech LEF

The ASAP7 1x tech LEF (and LambdaPDK's copy) declares `UNITS DATABASE MICRONS 1000` and `MANUFACTURINGGRID 0.001`, but writes several values on a 0.25 nm grid. OpenROAD stores LEF distances as `lround(value × 1000)` (`odb/lefin.h`). Every value that is not a whole nanometre was read back from an OpenROAD database loaded from the LEF and checked against the comparison OpenROAD's router makes with it (OpenROAD source as of `aea554fa3f`):

| Layer: rule | LEF → stored | Router comparison | Effect |
| --- | --- | --- | --- |
| M1 `EOLKEEPOUT` line-end width | 0.01825 → 18 nm | `length < eolWidth` | **Disabled for 18 nm tips** (§5). Needs 0.019. |
| M4/M5 `EOLKEEPOUT` side extension | 0.02425 → 24 nm | corner strictly inside | **Misses the adjacent track** (§4). Needs 0.025. |
| M6/M7 `EOLKEEPOUT` side extension | 0.03225 → 32 nm | corner strictly inside | **Same.** Needs 0.033. |
| M8/M9 `SPACINGTABLE` widths and run lengths (0.05975 … 0.99975; 0.39975, 1.19975, 1.79975) | rounded up to 60 … 1,000 and 400, 1,200, 1,800 nm | row/column applies when the value is greater than its threshold | **A width or run exactly on the DRM threshold falls into the row below.** The table differs only in the 500/1,000 nm rows beyond a 1,800 nm run, so the effect is limited there. Needs rounding down (0.059 … 0.999; 0.399, 1.199, 1.799). Source analysis only; this design has no M8/M9. |
| M2/M3 `EOLKEEPOUT` side extension | 0.0125 → 13 nm | strictly inside | Equivalent for whole-nm geometry. |
| M3 `LEF58_SPACING ... WITHIN` | 0.0125 → 13 nm | query box | Equivalent for strict tests; on-grid M3 neighbours are 18 nm away. |
| M6/M7 `LEF58_SPACING ENDOFLINE` width | 0.0375 → 38 nm | `length < eolWidth` | Equivalent. |
| V3/V5 `LEF58_ENCLOSURE ... EOL` width | 0.02425 → 24 nm | `width ≤ value`, used only to generate secondary vias | Equivalent. Separately, OpenROAD's checker never applies these EOL enclosure rules. |
| M6/M7 `AREA` | 2,187.5 → 2,188 nm² | area ≥ minimum | Equivalent. |
| `VIARULE M4_M3widePWR0p864` widths | [233.5, 234.5] → [234, 235]; [215.5, 216.5] → [216, 217] nm | width range | Still includes the intended 234 / 216 nm. |

**LEF fix.** On branch `asap7-m1-eolkeepout` of LambdaPDK ([jeffhsu3/lambdapdk](https://github.com/jeffhsu3/lambdapdk/tree/asap7-m1-eolkeepout)), based on `upstream/main` `15c783c`, the three effective cases are changed to whole-nanometre values that preserve the intended behaviour. Each change has a comment in the LEF explaining it:
- M1 `0.01825` → `0.019`;
- M4/M5 `0.02425` → `0.025`; M6/M7 `0.03225` → `0.033`;
- the M8/M9 table thresholds rounded down.

OpenROAD reads the patched LEF without warnings and stores 19, 25, 33 and the rounded-down thresholds. The fix is committed as LambdaPDK `be6ee59`, and the flow rerun with it is in §7.

**Where the LEF comes from, and the upstream PRs.** LambdaPDK's tech LEF is not its own:
- It is byte-identical to `techlef_misc/asap7_tech_1x_201209.lef` in [The-OpenROAD-Project/asap7sc7p5t_28](https://github.com/The-OpenROAD-Project/asap7sc7p5t_28), the repository that [The-OpenROAD-Project/asap7](https://github.com/The-OpenROAD-Project/asap7) includes as a git submodule. LambdaPDK synced it in 2024.
- That file was added there in November 2023. It matches OpenROAD-flow-scripts' `flow/platforms/asap7/lef/asap7_tech_1x_201209.lef` without the six VT implant layers ORFS added in 2025; the rule values are the same. The match is observed; no commit message says one was copied from the other. ORFS's file is the platform's `TECH_LEF`.
- Both upstreams also carry `asap7_tech_1x_260907.lef`, a newer LEF that brings M1–M3 in line with the DRM (OpenROAD-flow-scripts#4532, asap7sc7p5t_28#9, merged September 2026). It has the same four rounded values.

The same fix is proposed at every copy:

| Repository | Files | PR |
| --- | --- | --- |
| siliconcompiler/lambdapdk | `asap7/base/apr/asap7_tech.lef` | [#246](https://github.com/siliconcompiler/lambdapdk/pull/246) |
| The-OpenROAD-Project/OpenROAD-flow-scripts | `asap7_tech_1x_201209.lef`, `asap7_tech_1x_260907.lef` | [#4663](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/pull/4663) |
| The-OpenROAD-Project/asap7sc7p5t_28 | `asap7_tech_1x_201209.lef`, `asap7_tech_1x_260907.lef` | [#10](https://github.com/The-OpenROAD-Project/asap7sc7p5t_28/pull/10) |

Each upstream file was verified in OpenROAD after patching: no warnings, and the same stored values as above. The 4× LEF (`asap7_tech_4x_201209.lef`) holds these values as whole nanometres and is unaffected. In ORFS, the `201209` change affects every ASAP7 design, so the ORFS PR offers to restrict it to `260907`, as #4532 did. All three PRs were open at the time of writing.

## 7. SHA-256 rerun with the patched tech LEF

**Setup.** This is the V6 cut-pitch trial (§5) with one change: the ASAP7 tech LEF comes from LambdaPDK `be6ee59`. Upstream LambdaPDK's tech LEF (`15c783c`) is byte-identical to the v0.2.22 copy the earlier runs loaded, so the four whole-nanometre fixes of §6 are the only difference. The runner `build/lambdapdk_lef_fix_trial/run_trial.py` calls `open_flow/run_sha256.py`'s `make_chip` unchanged, then swaps in two files:
- the trial's `pdn_v6_cut_pitch.tcl`;
- the tech LEF (`library/asap7/fileset/views.lef`), through a separate `lambdapdk_patched` data root.

No repository file or installed package was changed. Output: `build/lambdapdk_lef_fix_trial/sha256/sha256_official/write.gds/0/outputs/sha256.gds.gz` (sha256 `f668a1a1…ce1e`). Reports are from gdscheck `3475644`, main suite.

**Routing.** Detailed routing converged to **0** violations, antenna repair found none, and GDS export completed. Compared with the V6 trial:

| | V6 trial | Patched LEF |
| --- | ---: | ---: |
| Final detailed-route violations | 0 | 0 |
| Wirelength | 53,798 µm | 53,790 µm |
| Vias | 130,756 | 130,984 (+0.17%) |
| `route.detailed` task time | 156 s | 191 s (+22%) |
| Setup WNS / hold WNS | −1,411 / −4.06 | identical |
| Setup violation count | 1,558 | 1,559 |

On this design, re-enabling the stricter-than-DRM M4–M7 keep-out cost no routability.

**gdscheck main suite: 7,620 → 6,455.**

| Rule | V6 trial | Patched LEF | Change |
| --- | ---: | ---: | ---: |
| `M4.S.4` / `M4.S.5` / `M5.S.5` | 61 / 153 / 1 | 0 / 0 / 0 | −215 |
| `M1.S.4` | 508 | 91 | −417 |
| `M1.S.2` | 2,210 | 2,147 | −63 |
| `M1.S.5` | 77 | 55 | −22 |
| `M1.S.6` | 73 | 72 | −1 |
| `V1.M1.EN.1` | 4,228 | 3,801 | −427 |
| `V0.M1.AUX.3` | 309 | 289 | −20 |
| **Total** | **7,620** | **6,455** | **−1,165** |

**Against the predictions of §4–§5.** The 215 M4/M5 markers and the 417 keep-out-covered `M1.S.4` markers are gone, as predicted. The §5 method was rerun on the new layout ([`drc_findings/sha256_lambdapdk_lef_fix_m1_eol_keepout.csv`](drc_findings/sha256_lambdapdk_lef_fix_m1_eol_keepout.csv)): **none** of the 2,365 remaining M1 spacing markers is covered by the LEF keep-out.
- The 91 `M1.S.4` markers are exactly the gaps inside one polygon.
- `M1.S.2` and `M1.S.5` have no qualifying line end.
- `M1.S.6` clears the LEF's 18 nm corner spacing.

What remains on M1 is therefore rules the LEF lacks or only partly covers. The drops in `V1.M1.EN.1` (−427), `M1.S.2` (−63) and `V0.M1.AUX.3` (−20) were **not** predicted. They are consistent with the router choosing different pin-access points once the M1 keep-out applies, but the mechanism has not been traced.

**OpenROAD's own checker.** `drt::check_drc` on the routed database confirms the patched values are in force (stored M1 line-end width 19, M4/M5 side extension 25). It reports 117 violations, against 70 on the V6 trial. Both counts are the same before and after antenna repair, so this is a standing gap between the router's final count (0) and a fresh `check_drc` of the saved database, not something antenna repair introduces. The extra 47 include 50 keep-out violations (42 on M1, 5 on M4, 3 on M5). None lies within 5 nm of a gdscheck marker, so they are presumably places where the LEF keep-out is stricter than the DRM. Why the router's count and `check_drc` disagree is an open OpenROAD question.

**Remaining 6,455 markers**, all on rules the tech LEF lacks, only partly covers, or states weaker (with the §5 checker-reading caveats):
- `V1.M1.EN.1` 3,801 and `V0.M1.AUX.3` 289 (absent);
- `M1.S.2` 2,147, `M1.S.4` 91 and `M1.S.5` 55 (partial);
- `M1.S.6` 72 (weaker).

Two of gdscheck's DRM readings still apply. First, the opposite-sides reading of `V1.M1.EN.1`, which was not re-measured on this layout. Second, whether gaps inside one polygon count for M1 spacing: **887** of the M1 spacing markers are such gaps (741 `M1.S.2`, all 91 `M1.S.4`, all 55 `M1.S.5`), and they would drop if the DRM's "two M1 polygons' edges" excludes them.

**Not checked:** LVS, power integrity and via current capacity for this run.
