# CHCl3 Benchmark Pulse Compiler TODO

This TODO list is derived from `plan.md` and is intended to be implementation-ready for future agents.

## Phase 1: Scaffold Capture

- [ ] Create the Python package skeleton under `/Users/atalnarayansahu/Desktop/F25/UCLA/ucla_course_docs/QNT_SCI_412/nmr_compiler`.
- [ ] Add `__init__.py` and expose the intended public API surface.
- [ ] Capture canonical 13C-detect scaffold content from the CHCl3 benchmark family.
- [ ] Capture canonical 1H-detect scaffold content from the CHCl3 benchmark family.
- [ ] Decide whether each output file will be:
  - [ ] rendered from a literal template file
  - [ ] or assembled from structured constants plus rendering logic
- [ ] Prefer template-backed rendering for `.mac` and `_interface.mac` unless there is a strong reason not to.

## Phase 2: Public Data Model

- [ ] Implement `RotationPulse`.
- [ ] Implement `WaitUs`.
- [ ] Implement `DelayUs`.
- [ ] Implement `ReadoutSpec`.
- [ ] Implement `ProgramSpec`.
- [ ] Implement `BundleResult`.
- [ ] Add strict validation of allowed nuclei, axes, and sample preset values.
- [ ] Add docstrings that explain the intended benchmark-family semantics.

## Phase 3: CHCl3 Preset and Scaffold Constants

- [ ] Encode CHCl3 calibration defaults:
  - [ ] `1H center = 7.26 ppm`
  - [ ] `1H a90 = 0 dB`
  - [ ] `1H d90 = 11.8 us`
  - [ ] `13C center = 77 ppm`
  - [ ] `13C a90 = -5.9 dB`
  - [ ] `13C d90 = 75 us`
- [ ] Encode `chcl3_benchmark_13c_detect` interface list exactly as documented in `plan.md`.
- [ ] Encode `chcl3_benchmark_13c_detect` relationship superset exactly as documented in `plan.md`.
- [ ] Encode `chcl3_benchmark_13c_detect` default parameter set exactly as documented in `plan.md`.
- [ ] Encode `chcl3_benchmark_1h_detect` interface list exactly as documented in `plan.md`.
- [ ] Encode `chcl3_benchmark_1h_detect` relationship superset exactly as documented in `plan.md`.
- [ ] Encode `chcl3_benchmark_1h_detect` default parameter set exactly as documented in `plan.md`.
- [ ] Encode the fixed benchmark `phaseList` once and reuse it in both scaffolds.

## Phase 4: Pulse Lowering

- [ ] Implement axis-sign to phase-token mapping:
  - [ ] `+x -> p1`
  - [ ] `+y -> p2`
  - [ ] `-x -> p3`
  - [ ] `-y -> p4`
- [ ] Implement target-to-channel lowering:
  - [ ] `1H -> channel 1`
  - [ ] `13C -> channel 2`
- [ ] Implement duration derivation:
  - [ ] common 90-degree pulse
  - [ ] common 180-degree pulse
  - [ ] arbitrary-angle numeric duration fallback
- [ ] Implement per-pulse amplitude override behavior.
- [ ] Implement per-pulse duration override behavior.
- [ ] Ensure negative angles affect only phase token selection, not duration sign.
- [ ] Make lowering scaffold-aware so frequency/amplitude/duration symbols match the selected detection scaffold.

## Phase 5: Timing Insertion

- [ ] Implement explicit rendering for `WaitUs(value)` as `wait(value)`.
- [ ] Implement explicit rendering for `DelayUs(value)` as `delay(value)`.
- [ ] Implement automatic insertion of `delay(0.5)` between adjacent RF pulses.
- [ ] Ensure automatic delay is skipped when:
  - [ ] a `WaitUs` already separates the pulses
  - [ ] a `DelayUs` already separates the pulses
- [ ] Ensure no spurious `delay(0.5)` is inserted before the scaffold readout pulse if the caller already ended the body with an explicit timing step.

## Phase 6: Readout Generation

- [ ] Implement the default 13C-detect readout block:
  - [ ] final `13C` acquisition pulse on `p1`
  - [ ] `delay(dPreAcq)`
  - [ ] `acquire("overwrite", n1)`
- [ ] Implement the default 1H-detect readout block:
  - [ ] final `1H` acquisition pulse on `p1`
  - [ ] `delay(dAcq)`
  - [ ] `acquire("overwrite", nPnts)`
- [ ] Implement `readout_override` support if needed for v1.
- [ ] Validate that overridden readout remains compatible with the scaffold parameter vocabulary.
- [ ] Confirm that an empty `body_steps` list still renders a valid FID-like program under each scaffold.

## Phase 7: `pp_list` Derivation

- [ ] Implement `pp_list` extraction from the rendered program.
- [ ] Use canonical parameter ordering for `pulse(...)`:
  - [ ] amplitude
  - [ ] frequency if present
  - [ ] phase
  - [ ] duration
- [ ] Include symbolic delay/wait/acquire arguments when applicable.
- [ ] Exclude:
  - [ ] numeric literals
  - [ ] channel numbers
  - [ ] string literals like `"overwrite"`
  - [ ] duplicates
- [ ] Preserve first-occurrence order.
- [ ] Verify derived `pp_list` against representative sample files.

## Phase 8: Bundle Rendering

- [ ] Implement rendering of `{name}_pp.mac`.
- [ ] Implement rendering of `{name}.mac`.
- [ ] Implement rendering of `{name}_interface.mac`.
- [ ] Implement rendering of `{name}Default.par`.
- [ ] Ensure experiment name substitution is consistent across all four generated files.
- [ ] Ensure `pp_name` in `{name}.mac` matches the generated `{name}.p` reference convention.
- [ ] Ensure derived `pp_list` in `{name}.mac` matches the generated body and readout.
- [ ] Ensure the fixed benchmark `phase_list` is inserted exactly.
- [ ] Ensure file naming matches the surrounding sample-program conventions.

## Phase 9: Compile Entry Point

- [ ] Implement `compile_program(spec, output_dir, *, overwrite=False)`.
- [ ] Create the output directory if missing.
- [ ] Refuse to overwrite generated files when `overwrite=False`.
- [ ] Overwrite cleanly when `overwrite=True`.
- [ ] Return `BundleResult` with all generated paths and derived metadata.

## Phase 10: Tests

- [ ] Add lowering unit tests:
  - [ ] `Rx(+90, "13C")`
  - [ ] `Ry(-90, "13C")`
  - [ ] `Rx(+180, "1H")`
  - [ ] duration override
  - [ ] amplitude override
- [ ] Add automatic-delay insertion tests.
- [ ] Add `WaitUs(2325)` rendering tests.
- [ ] Add `pp_list` derivation tests for both detection modes.
- [ ] Add `phaseList` exact-match tests for both scaffolds.
- [ ] Add synthetic empty-body CHCl3 FID tests for both scaffolds.
- [ ] Add snapshot tests against:
  - [ ] `DJ_f1_13C_p0`
  - [ ] `Grover_11_13C_p0`
  - [ ] `CNOT_TT_13C_00_p0`
  - [ ] `DJ_f1_1H_p0`
  - [ ] `Grover_11_1H_p0`
  - [ ] `CNOT_TT_1H_00_p0`
- [ ] Add a test that TT programs compile correctly under the DJ/Grover relationship superset.
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

- [ ] The implementation still matches every fixed decision in `plan.md`.
- [ ] There are still exactly two v1 scaffolds.
- [ ] DJ/Grover/TT remain verification targets only, not hard-coded APIs.
- [ ] The benchmark `phaseList` is scaffold-owned and fixed by default.
- [ ] `delay(0.5)` remains the automatic inter-pulse spacing rule.
- [ ] The generated bundle is complete enough to match the source-bundle structure used by the sample corpus.
