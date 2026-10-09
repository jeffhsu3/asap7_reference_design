# Reference Design for a modified version of ASAP7nm 
Known differences between the DRM, verification decks, and routing collateral are tracked in [ASAP7 ecosystem discrepancies](ASAP7_ECOSYSTEM_DISCREPANCIES.md).

This repository contains a reference block design for a modified version of the ASAP7nm library. The ASAP7nm library/PDK was developed by ASU and all credits go to them. 

Here we provide a modified version of their 7nm technology. The differences are many:
* layers M4/M5/M6/M7 are colored in the tech lef.
* density rules are introduced, for max and min cases.


A reference design is provided as well (SHA256). The design is synthesized in Genus at 1.66GHz and it is possible to close timing on Innovus also at 1.66GHz.
A reference implementation script is also provided for Cadence Innovus. The script is *complete*, in the sense that it provides:
* power ring in M6-M7
* follow pin routing in stapled style (M2-VIA-M1)
* vertical stripes in M3
* horizontal stripes in M4
* signal routing in M2-M7
* placement of tap cells
* traditional Place->CTS->Route flow

The reference script has been evaluated on several versions of Innovus and the results are as follows:


| Innovus version | Floorplan     | DRCs          | Setup         | Hold          | Density |
|-----------------|---------------|---------------|---------------|---------------|---------|
| 17.11 |         {194.04 194.04} | FAIL (7)     | PASS (+0.020) | PASS (+0.022) | 70.38%  |
| 18.10 | 	  {194.04 194.04} | FAIL (4)      | PASS (+0.023) | PASS (+0.023) | 70.27%  |
| 19.11 |	  {194.04 194.04} | PASS (0) | PASS (+0.029) | PASS (+0.021) | 70.09%  | 
| 20.11 |	  {194.04 194.04} | FAIL (6)      | PASS (+0.025) | PASS (+0.020) | 70.26%  | 
| 21.11 | 	  {194.04 194.04} | FAIL (6)      | PASS (+0.019) | PASS (+0.019) | 70.32%  | 
|-|-|-|-|-|-|
| 21.11 | 	  {183.24 183.24} | FAIL (8)     | PASS (+0.020) | PASS (+0.019) | 78.91%  |
| 21.11 | 	  {172.44 172.44} | FAIL (31)     | PASS (+0.019) | PASS (+0.019) | 89.07%  |


The designs above often fail to route due to pin access issues. All DRCs have the same "pattern" and can be fixed with *some* manual effort. 
This repository also includes two Innovus databases of the same SHA design implemented in version 19.11 and 20.11. Both databases are DRC clean. Check the folder /db/

## Open-source SHA-256 place and route

The separate [SiliconCompiler/OpenROAD flow](open_flow/README.md) uses stock
LambdaPDK ASAP7, **not** the modified colored/density-rule technology above.
The table records one completed SHA-256 run with the default on-grid M4 via
stacks and M6/M7 ring. Unlike the Innovus table, setup and hold are shown as
diagnostic worst slacks rather than PASS/FAIL targets; this experiment is not
trying to close the reference clock frequency.

| Open-flow configuration | Core area / target density | Post-route utilization | gdscheck ASAP7 `main` DRC | gdscheck checkout | Setup WNS (ps) | Hold WNS (ps) |
| --- | --- | ---: | --- | --- | ---: | ---: |
| [On-grid M4 and M6/M7 PDN](open_flow/pdn_ring.tcl), SiliconCompiler 0.38.10 / OpenROAD 26Q3 | 3832.97 µm² / 40% | 51.01% | **FAIL (8,244)** | [`42ce435`](https://github.com/aesc-silicon/gdscheck/commit/42ce435dd4ebd46c5ef072d416f988bc5a5c8e54) | −1,411.05 (worst corner) | −4.06 (worst corner) |

The 40% figure is the *floorplan target*, whereas 51.01% is the post-route
standard-cell utilization reported by OpenROAD (1955.37 µm² instance area /
3832.97 µm² core area); neither is verified layout metal density. Worst-corner
STA combines the slow-corner setup and fast-corner hold results. For the explicit
`sha256_tt` scenario the measured setup/hold WNS were −755.11/+56.43 ps.
The illustrative [`600 ps clock constraint`](open_flow/sha256.sdc) remains in
the flow for timing-driven implementation; the negative setup result is not
frequency closure. See the run's
`build/ring_ongrid_bottom_trial/sha256/sha256_official/route.detailed_antenna_repair/0/reports/`
for its local STA/area reports.

The DRC count is from the stock gdscheck `--suite main` on the exported GDS
(`build/ring_ongrid_bottom_trial/sha256/sha256_official/write.gds/0/outputs/sha256.gds.gz`,
SHA-256 `e8b3e50e735020751fba88825e41bc39acd9683aac5ba3ed8f7365a82d8f4b98`).
It includes 4,228 `V1.M1.EN.1`, 2,210 `M1.S.2`, 624 `V6.S.2`,
153 `M4.S.5`, and other categories; the focused M4 and M6/M7 AUX grid/track
checks report zero. The local report is `/tmp/sha256_ring_ongrid_bottom_main.lyrdb`.
`42ce435` identifies the gdscheck *source checkout* at the check; the binary's
build provenance was not independently established. These report items are not
necessarily distinct physical defects. Zero final OpenROAD router violations
and connected VDD/VSS do not constitute full DRM, LVS, or power-integrity signoff.

For reference, floorplan box sizes are:
> - FP box of {0.0 0.0 172.44 172.44} means 150 std cell rows.
> - FP box of {0.0 0.0 183.24 183.24} means 160 std cell rows.
> - FP box of {0.0 0.0 194.04 194.04} means 170 std cell rows.
