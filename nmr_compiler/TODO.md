# CHCl3 Benchmark Pulse Compiler TODO

This TODO list is derived from `plan.md` and is intended to be implementation-ready for future agents.

## Phase 1: Scaffold Capture

- [x] Create the Python package skeleton under `/Users/atalnarayansahu/Desktop/F25/UCLA/ucla_course_docs/QNT_SCI_412/nmr_compiler`.
- [x] Add `__init__.py` and expose the intended public API surface.
- [x] Capture canonical 13C-detect scaffold content from the CHCl3 benchmark family.
- [x] Capture canonical 1H-detect scaffold content from the CHCl3 benchmark family.
- [x] Decide whether each output file will be:
  - [x] rendered from a literal template file
  - [x] or assembled from structured constants plus rendering logic
- [x] Prefer template-backed rendering for `.mac` and `_interface.mac` unless there is a strong reason not to.

## Phase 2: Public Data Model

- [x] Implement `RotationPulse`.
- [x] Implement `WaitUs`.
- [x] Implement `DelayUs`.
- [x] Implement `ReadoutSpec`.
- [x] Implement `ProgramSpec`.
- [x] Implement `BundleResult`.
- [x] Add strict validation of allowed nuclei, axes, and sample preset values.
- [x] Add docstrings that explain the intended benchmark-family semantics.

## Phase 3: CHCl3 Preset and Scaffold Constants

- [x] Encode CHCl3 calibration defaults:
  - [x] `1H center = 7.26 ppm`
  - [x] `1H a90 = 0 dB`
  - [x] `1H d90 = 11.8 us`
  - [x] `13C center = 77 ppm`
  - [x] `13C a90 = -5.9 dB`
  - [x] `13C d90 = 75 us`
- [x] Encode `chcl3_benchmark_13c_detect` interface list exactly as documented in `plan.md`.
- [x] Encode `chcl3_benchmark_13c_detect` relationship superset exactly as documented in `plan.md`.
- [x] Encode `chcl3_benchmark_13c_detect` default parameter set exactly as documented in `plan.md`.
- [x] Encode `chcl3_benchmark_1h_detect` interface list exactly as documented in `plan.md`.
- [x] Encode `chcl3_benchmark_1h_detect` relationship superset exactly as documented in `plan.md`.
- [x] Encode `chcl3_benchmark_1h_detect` default parameter set exactly as documented in `plan.md`.
- [x] Encode the fixed benchmark `phaseList` once and reuse it in both scaffolds.

## Phase 4: Pulse Lowering

- [x] Implement axis-sign to phase-token mapping:
  - [x] `+x -> p1`
  - [x] `+y -> p2`
  - [x] `-x -> p3`
  - [x] `-y -> p4`
- [x] Implement target-to-channel lowering:
  - [x] `1H -> channel 1`
  - [x] `13C -> channel 2`
- [x] Implement duration derivation:
  - [x] common 90-degree pulse
  - [x] common 180-degree pulse
  - [x] arbitrary-angle numeric duration fallback
- [x] Implement per-pulse amplitude override behavior.
- [x] Implement per-pulse duration override behavior.
- [x] Ensure negative angles affect only phase token selection, not duration sign.
- [x] Make lowering scaffold-aware so frequency/amplitude/duration symbols match the selected detection scaffold.

## Phase 5: Timing Insertion

- [x] Implement explicit rendering for `WaitUs(value)` as `wait(value)`.
- [x] Implement explicit rendering for `DelayUs(value)` as `delay(value)`.
- [x] Implement automatic insertion of `delay(0.5)` between adjacent RF pulses.
- [x] Ensure automatic delay is skipped when:
  - [x] a `WaitUs` already separates the pulses
  - [x] a `DelayUs` already separates the pulses
- [x] Ensure no spurious `delay(0.5)` is inserted before the scaffold readout pulse if the caller already ended the body with an explicit timing step.

## Phase 6: Readout Generation

- [x] Implement the default 13C-detect readout block:
  - [x] final `13C` acquisition pulse on `p1`
  - [x] `delay(dPreAcq)`
  - [x] `acquire("overwrite", n1)`
- [x] Implement the default 1H-detect readout block:
  - [x] final `1H` acquisition pulse on `p1`
  - [x] `delay(dAcq)`
  - [x] `acquire("overwrite", nPnts)`
- [x] Implement `readout_override` support if needed for v1.
- [x] Validate that overridden readout remains compatible with the scaffold parameter vocabulary.
- [x] Confirm that an empty `body_steps` list still renders a valid FID-like program under each scaffold.

## Phase 7: `pp_list` Derivation

- [x] Implement `pp_list` extraction from the rendered program.
- [x] Use canonical parameter ordering for `pulse(...)`:
  - [x] amplitude
  - [x] frequency if present
  - [x] phase
  - [x] duration
- [x] Include symbolic delay/wait/acquire arguments when applicable.
- [x] Exclude:
  - [x] numeric literals
  - [x] channel numbers
  - [x] string literals like `"overwrite"`
  - [x] duplicates
- [x] Preserve first-occurrence order.
- [x] Verify derived `pp_list` against representative sample files.

## Phase 8: Bundle Rendering

- [x] Implement rendering of `{name}_pp.mac`.
- [x] Implement rendering of `{name}.mac`.
- [x] Implement rendering of `{name}_interface.mac`.
- [x] Implement rendering of `{name}Default.par`.
- [x] Ensure experiment name substitution is consistent across all four generated files.
- [x] Ensure `pp_name` in `{name}.mac` matches the generated `{name}.p` reference convention.
- [x] Ensure derived `pp_list` in `{name}.mac` matches the generated body and readout.
- [x] Ensure the fixed benchmark `phase_list` is inserted exactly.
- [x] Ensure file naming matches the surrounding sample-program conventions.

## Phase 9: Compile Entry Point

- [x] Implement `compile_program(spec, output_dir, *, overwrite=False)`.
- [x] Create the output directory if missing.
- [x] Refuse to overwrite generated files when `overwrite=False`.
- [x] Overwrite cleanly when `overwrite=True`.
- [x] Return `BundleResult` with all generated paths and derived metadata.

## Phase 10: Tests

- [x] Add lowering unit tests:
  - [ ] `Rx(+90, "13C")`
  - [x] `Ry(-90, "13C")`
  - [x] `Rx(+180, "1H")`
  - [ ] duration override
  - [x] amplitude override
- [x] Add automatic-delay insertion tests.
- [x] Add `WaitUs(2325)` rendering tests.
- [ ] Add `pp_list` derivation tests for both detection modes.
- [ ] Add `phaseList` exact-match tests for both scaffolds.
- [x] Add synthetic empty-body CHCl3 FID tests for both scaffolds.
- [x] Add snapshot tests against:
  - [x] `DJ_f1_13C_p0`
  - [x] `Grover_11_13C_p0`
  - [x] `CNOT_TT_13C_00_p0`
  - [x] `DJ_f1_1H_p0`
  - [x] `Grover_11_1H_p0`
  - [x] `CNOT_TT_1H_00_p0`
- [x] Add a test that TT programs compile correctly under the DJ/Grover relationship superset.
- [ ] Add validation tests for unsupported nuclei, bad axes, unknown presets, and overwrite behavior.

## Phase 11: Optional CLI

- [ ] Decide whether to include a minimal CLI in v1.
- [ ] If included, implement:
  - [ ] JSON spec input
  - [ ] output directory argument
  - [ ] overwrite flag
- [ ] Keep the CLI thin and built on top of `compile_program`.

## Phase 12: Documentation and Examples

- [ ] Add a short package README or module docstring explaining scope.
- [ ] Add at least one 13C-detect usage example.
- [ ] Add at least one 1H-detect usage example.
- [ ] Add one example showing an empty-body CHCl3 FID-like compile.
- [ ] Document explicitly that water experiments are out of scope for v1.
- [ ] Document explicitly that `.p` binaries are not generated in v1.

## Final Verification Checklist

- [x] The implementation still matches every fixed decision in `plan.md`.
- [x] There are still exactly two v1 scaffolds.
- [x] DJ/Grover/TT remain verification targets only, not hard-coded APIs.
- [x] The benchmark `phaseList` is scaffold-owned and fixed by default.
- [x] `delay(0.5)` remains the automatic inter-pulse spacing rule.
- [x] The generated bundle is complete enough to match the source-bundle structure used by the sample corpus.
