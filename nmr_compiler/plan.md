# CHCl3 Benchmark Pulse Compiler Plan

## Purpose

This document is the canonical implementation plan for the `nmr_compiler` module under:

- `/Users/atalnarayansahu/Desktop/F25/UCLA/ucla_course_docs/QNT_SCI_412/nmr_compiler`

The intent is to preserve the design decisions already made in discussion so that future agents or engineers can implement the module without re-litigating the architecture.

This is a **CHCl3-only v1** for benchmark-style pulse programs. It is **general over benchmark circuits**, but it is **not** a general compiler for every NMR experiment family yet.

## Preserved Design Decisions

The following decisions are in scope and must be treated as fixed for v1:

1. Scope v1 to the **CHCl3 benchmarking family**, not water experiments and not the full Spinsolve template zoo.
2. The user-facing pulse abstraction is **axis-angle pulses**, not raw `pulse(...)` calls.
3. The primary authoring surface is:
   - `Rx(...)`
   - `Ry(...)`
   - `WaitUs(...)`
   - optional `DelayUs(...)`
4. Ship exactly **two default scaffolds** in v1:
   - `chcl3_benchmark_1h_detect`
   - `chcl3_benchmark_13c_detect`
5. Reuse these same scaffolds for simpler CHCl3 cases such as FID by allowing an empty or minimal pulse body before the standard acquisition block.
6. Use the **dominant five-row quantum phase cycle** as the default `phaseList` for both benchmark scaffolds:

   ```text
   [0,2,0,2;
    1,3,1,3;
    2,0,2,0;
    3,1,3,1;
    0,2,0,2]
   ```

7. Do **not** infer `phaseList` from the pulse body.
8. Use the **DJ/Grover relationship superset** for each detection mode. TT can compile under that superset safely even if it does not use every derived symbol.
9. Use `delay(0.5)` as the default inter-pulse spacing between adjacent RF pulses unless the user inserted an explicit `DelayUs` or `WaitUs`.
10. Generate a full SpinSolve-style source bundle:
    - `{name}_pp.mac`
    - `{name}.mac`
    - `{name}_interface.mac`
    - `{name}Default.par`
11. Do **not** generate proprietary compiled `.p` binaries in v1.
12. Keep the compiler general over arbitrary benchmark pulse lists; DJ, Grover, and TT are **verification targets**, not hard-coded algorithms.

## Verified Repo Facts

These were checked directly against the sample corpus in:

- `/Users/atalnarayansahu/Desktop/F25/UCLA/code/ucla_nmr_lab/pulse_programs`

### CHCl3 13C-detect benchmark family

The following programs share one interface block:

- `DJ_f1_13C_p0`
- `Grover_11_13C_p0`
- `CNOT_TT_13C_00_p0`

The DJ and Grover 13C-detect files share the same relationship block. The TT 13C-detect file uses a slightly smaller relationship set, but the DJ/Grover relationship block is a safe superset because unused derived variables do not break the pulse program.

### CHCl3 1H-detect benchmark family

The following programs share one interface block:

- `DJ_f1_1H_p0`
- `Grover_11_1H_p0`
- `CNOT_TT_1H_00_p0`

The DJ and Grover 1H-detect files share the same relationship block. The TT 1H-detect file uses a slightly smaller relationship set, but again the DJ/Grover relationship block is a safe superset.

### Phase cycle

The default benchmark `phaseList` is identical across the checked DJ/Grover/TT examples in both detection modes:

```text
[0,2,0,2;
 1,3,1,3;
 2,0,2,0;
 3,1,3,1;
 0,2,0,2]
```

### Inter-pulse spacing

The benchmark families use `delay(0.5)` between adjacent RF pulses. The `delay(20)` seen elsewhere is from a different 13C template context and must **not** be treated as the default benchmark pulse spacing.

## Non-Goals

The following are explicitly out of scope for v1:

- Water-specific scaffolds
- T1IR, Hahn echo, CPMG, NOE-decoupled, or general relaxation experiments
- Direct `.p` binary generation
- Reverse-engineering the Magritek internal compiler
- Automatic inference of a benchmark algorithm from a circuit name like "Grover" or "DJ"
- Automatic inference of `phaseList` from the pulse body
- Full support for arbitrary macro vocabulary beyond the benchmark family needs

## Recommended Implementation Strategy

Implement the compiler as a **template-backed source generator**, not as a reimplementation of the proprietary Magritek compiler.

Use canonical scaffold source files from the lab repo as fixed structural references, and programmatically substitute:

- experiment name
- generated pulse body
- derived `pp_list`
- `pp_name`
- default parameter values

Recommended scaffold sources to copy structurally:

- 13C-detect scaffold basis:
  - `DJ_f1_13C_p0`
- 1H-detect scaffold basis:
  - `DJ_f1_1H_p0`

This gives the implementation stable reference points that already match the benchmark family conventions.

## Public Python API

### Data model

The public API should be centered around typed Python objects.

#### `RotationPulse`

Represents one axis-angle RF pulse.

Fields:

- `axis: Literal["x", "y"]`
- `angle_deg: float`
- `target: Literal["1H", "13C"]`
- `amplitude_db: float | None = None`
- `duration_us: float | None = None`

Rules:

- `angle_deg` may be positive or negative.
- `duration_us`, when omitted, is derived from the calibration preset:

  ```text
  abs(angle_deg) / 90 * d90_us
  ```

- `amplitude_db`, when omitted, uses the target-specific calibrated `a90` value.

#### `WaitUs`

Represents explicit coherent evolution delay. This is used for steps such as `wait(2325)`.

Fields:

- `value_us: float`

#### `DelayUs`

Represents explicit ordinary delay. This is used when the caller wants a specific `delay(...)` rather than the automatic `delay(0.5)`.

Fields:

- `value_us: float`

#### `ProgramSpec`

Primary compile input.

Fields:

- `name: str`
- `detect_nucleus: Literal["1H", "13C"]`
- `sample_preset: Literal["chcl3"]`
- `body_steps: list[RotationPulse | WaitUs | DelayUs]`
- `readout_override: ReadoutSpec | None = None`
- `default_param_overrides: dict[str, str | int | float] | None = None`

#### `ReadoutSpec`

Optional override of the default acquisition pulse/readout block.

Fields:

- `pulse_target: Literal["1H", "13C"]`
- `pulse_axis: Literal["x", "y"]`
- `pulse_angle_deg: float`
- `preacq_symbol: str`
- `acquire_mode: str`
- `points_symbol: str`

For v1, callers will usually omit this and use the scaffold default.

#### `BundleResult`

Compile output.

Fields:

- `output_dir: Path`
- `pp_mac_path: Path`
- `mac_path: Path`
- `interface_mac_path: Path`
- `default_par_path: Path`
- `pp_list: list[str]`
- `phase_list: str`

### Public compile function

```python
compile_program(spec, output_dir, *, overwrite=False) -> BundleResult
```

Behavior:

- validates `ProgramSpec`
- selects the correct scaffold based on `detect_nucleus`
- lowers axis-angle pulses into benchmark-family `pulse(...)` calls
- renders the full source bundle
- returns paths and derived metadata

## Calibration and Sample Preset

V1 uses one sample preset: `chcl3`.

This preset contains target-specific CHCl3 defaults inferred from the benchmark sample files.

### CHCl3 preset

#### 1H channel defaults

- `centerFreqPPM1H = 7.26`
- `90Amplitude1H = 0`
- `pulseLength1H = 11.8`

#### 13C channel defaults

- `centerFreqPPM13C = 77`
- `90Amplitude13C = -5.9`
- `pulseLength13C = 75`

These values are scaffold defaults. Per-program overrides are allowed through `default_param_overrides`, and per-pulse overrides are allowed through `RotationPulse.amplitude_db` and `RotationPulse.duration_us`.

## Lowering Rules

### Axis to phase-token mapping

This mapping is fixed for v1:

- `+x -> p1`
- `+y -> p2`
- `-x -> p3`
- `-y -> p4`

Where sign is determined from `angle_deg`.

Examples:

- `Rx(+90, "13C") -> pulse(..., p1, d90C, ...)`
- `Ry(+90, "13C") -> pulse(..., p2, d90C, ...)`
- `Rx(-90, "13C") -> pulse(..., p3, d90C, ...)`
- `Ry(-90, "13C") -> pulse(..., p4, d90C, ...)`

### Angle to duration

When `duration_us` is not supplied:

```text
duration_us = abs(angle_deg) / 90 * d90_us(target)
```

Examples:

- `Rx(180, "1H") -> d180H`
- `Ry(90, "13C") -> d90C`
- `Rx(45, "13C") -> 0.5 * d90C`

For v1, generated code may either:

- emit exact symbolic durations for common angles already present in the scaffold, or
- emit numeric durations directly if the angle is non-standard.

Recommended v1 behavior:

- use symbolic durations when available:
  - 1H: `d90H`, `d180H`
  - 13C: `d90C`, `d180C`
- emit numeric duration literals for non-standard angles

### Target to channel mapping

- `target="1H"`:
  - channel index `1`
  - amplitude symbol `a90H`
  - duration symbol family `d90H`, `d180H`
  - frequency symbol `fTx1H` in 1H-detect scaffold and `freqCh1` in 13C-detect scaffold
- `target="13C"`:
  - channel index `2`
  - amplitude symbol `a90C`
  - duration symbol family `d90C`, `d180C`
  - frequency symbol `fTx13C` in 1H-detect scaffold and `freqCh2` in 13C-detect scaffold

### Automatic `delay(0.5)`

The compiler must insert `delay(0.5)` automatically between adjacent emitted RF pulses unless the caller explicitly placed:

- a `DelayUs(...)`, or
- a `WaitUs(...)`

between them.

This rule is part of preserving the benchmark-family convention and matching the sample pulse bodies.

### Explicit waits

`WaitUs(value)` must render to:

```text
wait(value)
```

This is necessary for benchmark sequences that use J-coupling evolution periods such as `wait(2325)`.

## Default Scaffolds

There are exactly two canonical scaffolds in v1.

### `chcl3_benchmark_13c_detect`

#### Canonical interface list for `{name}_pp.mac`

```text
["nucleus", "Nucleus", "tb", "readonly_string";
 "b1Freq13C", "13C frequency (MHz)", "tb", "freq";
 "centerFreqPPM1H", "Centre frequency 1H (ppm)", "tb", "float";
 "centerFreqPPM13C", "Centre frequency 13C (ppm)", "tb", "float";
 "b1Freq1H", "1H frequency (MHz)", "tb", "freq";
 "amplitudeC90", "13C 90 pulse amplitude (dB)", "tb", "pulseamp";
 "pulseLengthC90", "13C 90 pulse length (us)", "tb", "pulselength";
 "amplitudeH90", "1H 90 pulse amplitude (dB)", "tb", "pulseamp";
 "pulseLengthH180Waltz", "Waltz 1H 180 pulse length (us)", "tb", "pulselength";
 "pulseLengthH90", "1H 90 pulse length (us)", "tb", "pulselength";
 "noeDelay", "NOE delay time (ms)", "tb", "reptime";
 "noeAmp", "NOE power (dB)", "tb", "pulseamp";
 "repTime", "Repetition time (ms)", "tb", "reptime"]
```

#### Canonical relationship superset

```text
["waltzDuration = WALTZ16:duration(pulseLengthH180Waltz/2,pgo)",
 "n1            = nrPnts",
 "n2            = trunc(1000*acqTime/waltzDuration)+1",
 "n3            = trunc(1000*noeDelay/waltzDuration)+1",
 "a90C          = amplitudeC90",
 "aNOE          = noeAmp",
 "a90H          = amplitudeH90",
 "d90C          = pulseLengthC90",
 "d180C         = pulseLengthC90*2",
 "d45C          = pulseLengthC90/2",
 "d90HWaltz     = pulseLengthH180Waltz/2",
 "d180HWaltz    = pulseLengthH180Waltz",
 "d270HWaltz    = 3*pulseLengthH180Waltz/2",
 "d360HWaltz    = 2*pulseLengthH180Waltz",
 "d90H          = pulseLengthH90",
 "d180H         = pulseLengthH90*2",
 "dPreAcq       = ucsUtilities:getacqDelay(d90C,4,dwellTime)",
 "offFreq1H     = (centerFreqPPM1H-wvPPMOffset1H)*b1Freq1H",
 "offFreqX      = (centerFreqPPM13C-wvPPMOffset13C)*b1Freq13C",
 "freqCh2       = double(b1Freq13C)+double(offFreqX/1e6d)",
 "freqCh1       = double(b1Freq1H)+double(offFreq1H/1e6d)",
 "f1H           = freqCh1",
 "freqRx        = freqCh2",
 "totPnts       = nrPnts",
 "totTime       = acqTime"]
```

#### Other scaffold constants

- `groups = ["Pulse_sequence","Acquisition","Processing_Std","Display_Std","File_Settings"]`
- `variables = [""]`
- default `phaseList` = the benchmark five-row phase cycle

#### Standard acquisition block

```text
delay(0.5)
pulse(2, a90C, p1, d90C)
delay(dPreAcq)
acquire("overwrite", n1)
```

#### Default parameters

Use the following defaults unless overridden:

```text
accumulate = "yes"
acqDelay = 20
amplitudeH90 = 0
pulseLengthH90 = 11.8
pulseLengthH180Waltz = 306.8
amplitudeC90 = -5.9
pulseLengthC90 = 75
b1Freq1H = "common"
b1Freq13C = "common"
centerFreqPPM1H = 7.26
centerFreqPPM13C = 77
decoupleAmp = "factory"
dispRange = 0
dispRangeMaxPPM = 220
dispRangeMinPPM = -20
dwellTime = "factory"
fdPhaseCorr = "none"
filter = "yes"
filterType = "exp:0.5"
flatFilter = "yes"
incExpNr = "yes"
noeAmp = "factory"
noeDelay = 1000
nrPnts = 8192
nrScans = 8
nucleus = "13C"
preacqDelay = "factory"
pulseLength1 = "factory"
repTime = 3500
rxChannel = "13C"
rxGain = "factory"
rxPhase = 0
saveData = "true"
usePhaseCycle = "yes"
usePPMScale = "yes"
zf = 2
```

### `chcl3_benchmark_1h_detect`

#### Canonical interface list for `{name}_pp.mac`

```text
["nucleus", "Nucleus", "tb", "readonly_string";
 "b1Freq1H", "1H frequency (MHz)", "tb", "freq";
 "centerFreqPPM1H", "Centre frequency 1H (ppm)", "tb", "float";
 "centerFreqPPM13C", "Centre frequency 13C (ppm)", "tb", "float";
 "90Amplitude1H", "Pulse amplitude 1H (dB)", "tb", "pulseamp";
 "90Amplitude13C", "Pulse amplitude 13C (dB)", "tb", "pulseamp";
 "pulseLength1H", "Pulse length 1H (us)", "tb", "pulselength";
 "pulseLength13C", "Pulse length 13C (us)", "tb", "pulselength";
 "b1Freq13C", "13C frequency (MHz)", "tb", "freq";
 "shiftPoints", "Number of points to shift", "tb", "float,[-100,100]";
 "repTime", "Repetition time (ms)", "tb", "reptime"]
```

#### Canonical relationship superset

```text
["b1Freq        = b1Freq1H",
 "nPnts         = nrPnts",
 "a90H          = 90Amplitude1H",
 "a90C          = 90Amplitude13C",
 "d90H          = pulseLength1H",
 "d180H         = pulseLength1H*2",
 "d90C          = pulseLength13C",
 "d180C         = pulseLength13C*2",
 "dAcq          = ucsUtilities:getacqDelay(pulseLength1H,shiftPoints,dwellTime)",
 "offFreq1H     = (centerFreqPPM1H-wvPPMOffset1H)*b1Freq1H",
 "offFreq13C    = (centerFreqPPM13C-wvPPMOffset13C)*b1Freq13C",
 "O1            = offFreq1H",
 "fTx1H         = double(b1Freq)+double(offFreq1H/1e6d)",
 "fTx13C        = double(b1Freq13C)+double(offFreq13C/1e6d)",
 "totPnts       = nrPnts",
 "totTime       = acqTime"]
```

#### Other scaffold constants

- `groups = ["Pulse_sequence","Acquisition","Processing_Std","Display_Std","File_Settings"]`
- `variables = [""]`
- default `phaseList` = the benchmark five-row phase cycle

#### Standard acquisition block

```text
delay(0.5)
pulse(1, a90H, p1, d90H)
delay(dAcq)
acquire("overwrite", nPnts)
```

#### Default parameters

Use the following defaults unless overridden:

```text
90Amplitude1H = 0
90Amplitude13C = -5.9
accumulate = "yes"
acqDelay = 20
b1Freq1H = "common"
b1Freq13C = "common"
centerFreqPPM1H = 7.26
centerFreqPPM13C = 77
decoupleAmp = "factory"
dispRange = 0
dispRangeMaxPPM = 15
dispRangeMinPPM = -5
dwellTime = 200
errorProcDef = "yes"
fdPhaseCorr = "none"
filter = "no"
filterType = "exp:0.5"
flatFilter = "yes"
incExpNr = "yes"
nrPnts = 16384
nrScans = 1
nucleus = "1H"
pulseLength1H = 11.8
pulseLength13C = 75
pulseLengthC180 = "factory"
repTime = 10000
rxChannel = "1H"
rxGain = 25
rxPhase = 180
saveData = "true"
shiftPoints = 1
usePhaseCycle = "yes"
usePPMScale = "yes"
zf = 2
```

## Rendering Responsibilities by Output File

### `{name}_pp.mac`

This is the main generated pulse-program source.

It must include:

- scaffold header
- `procedure(pulse_program,dir,mode,pars)`
- scaffold interface list
- scaffold relationship list
- `groups`
- `variables`
- `initpp(dir)`
- generated benchmark pulse body
- scaffold acquisition/readout block
- `lst = endpp(0)`
- fixed benchmark `phaseList`
- `getFactoryBasedParameters`

### `{name}.mac`

This is the experiment wrapper and execution logic.

Recommended implementation:

- treat it as a scaffold template copied from the canonical sample and substitute:
  - experiment name
  - `pp_name`
  - derived `pp_list`
  - fixed `phase_list`

All execution logic outside those substitutions should remain scaffold-owned and unchanged in v1.

### `{name}_interface.mac`

This should also be scaffold-owned and rendered from a canonical template, not heuristically regenerated from first principles.

If the compiler chooses to derive it from the `interface` list, the result must match the scaffold conventions exactly. Otherwise, prefer template substitution over inference.

### `{name}Default.par`

Render from the scaffold default parameter set plus `default_param_overrides`.

Override precedence:

1. hard-coded scaffold defaults
2. CHCl3 sample preset values
3. user-provided `default_param_overrides`

## `pp_list` Derivation

`pp_list` must be derived from the rendered pulse body plus scaffold acquisition block so the wrapper `.mac` stays aligned with the generated program.

### Parameter collection rules

For each rendered operation, collect symbolic parameters in the following canonical order:

- `pulse(channel, amplitude, phase, duration, frequency?)`
  - collect `amplitude`
  - then `frequency` if present
  - then `phase`
  - then `duration`
- `delay(symbolic_value)`
  - collect the symbolic value if it is not numeric
- `wait(symbolic_value)`
  - collect the symbolic value if it is not numeric
- `acquire(mode, points, ...)`
  - collect symbolic arguments after the string mode

### Filtering rules

Do not include:

- numeric literals
- channel indices
- string literals like `"overwrite"`
- duplicate symbols already seen

### Ordering rule

Use **first occurrence order** under the canonical argument ordering above.

This matches the sample family behavior.

### Example

For:

```text
pulse(2, a90C, p4, d90C, freqCh2)
```

collect in this order:

```text
a90C, freqCh2, p4, d90C
```

not in raw textual order.

## Phase List Policy

### Default

The fixed benchmark `phaseList` for v1 is:

```text
[0,2,0,2;
 1,3,1,3;
 2,0,2,0;
 3,1,3,1;
 0,2,0,2]
```

### Why it is fixed

This pattern is consistent across the benchmark-family examples checked in both detection modes.

### Why it must not be inferred

The broader corpus contains many different phase-cycle patterns for other experiment families. Therefore, inference from the pulse body is not reliable and should not be attempted in v1.

### Extension point

Later versions may expose phase-cycle override support, but the default behavior in v1 must remain scaffold-owned and fixed.

## FID Support Under Benchmark Scaffolds

A CHCl3 FID-like program should be supported without a separate scaffold by allowing:

- `body_steps = []`

and then relying on the scaffold readout block to produce the final excitation pulse and acquisition.

This preserves the design decision to keep v1 at two scaffolds while still allowing simpler CHCl3 acquisitions.

## Validation Rules

The compiler must reject:

- unsupported `detect_nucleus`
- unsupported `sample_preset`
- unsupported pulse axis
- zero-angle or nonsensical pulse angle if the implementation chooses to forbid it
- missing experiment name
- overwrite conflicts when `overwrite=False`
- unknown `body_steps` element types
- `readout_override` that contradicts the selected scaffold in an unsupported way

The compiler should normalize:

- experiment names into safe file stems
- numeric formatting for durations and waits

## Verification Targets

The following programs must be reproducible as source-generation benchmarks:

### 13C-detect

- `DJ_f1_13C_p0`
- `Grover_11_13C_p0`
- `CNOT_TT_13C_00_p0`

### 1H-detect

- `DJ_f1_1H_p0`
- `Grover_11_1H_p0`
- `CNOT_TT_1H_00_p0`

### Synthetic simple cases

- CHCl3 13C-detect FID-like program under `chcl3_benchmark_13c_detect`
- CHCl3 1H-detect FID-like program under `chcl3_benchmark_1h_detect`

## Acceptance Criteria

The implementation is acceptable when all of the following are true:

1. Axis-angle pulses lower correctly into scaffold-specific `pulse(...)` calls.
2. The compiler inserts `delay(0.5)` automatically between adjacent RF pulses unless explicit timing steps are present.
3. The two scaffolds generate complete source bundles.
4. The default benchmark `phaseList` is emitted exactly for both scaffolds.
5. DJ, Grover, and TT example pulse bodies can be reproduced from generic benchmark pulse lists.
6. TT examples compile correctly under the DJ/Grover relationship superset.
7. Empty pulse bodies compile successfully as CHCl3 FID-like source bundles.
8. `pp_list` matches scaffold conventions and remains synchronized with generated pulse/readout content.

## Recommended Repository Layout

Recommended v1 file layout inside `nmr_compiler`:

```text
nmr_compiler/
  plan.md
  TODO.md
  __init__.py
  api.py
  compiler.py
  lowering.py
  scaffolds.py
  render.py
  validation.py
  templates/
    chcl3_benchmark_1h_detect.mac.tpl
    chcl3_benchmark_1h_detect_pp.mac.tpl
    chcl3_benchmark_1h_detect_interface.mac.tpl
    chcl3_benchmark_1h_detect_default.par.tpl
    chcl3_benchmark_13c_detect.mac.tpl
    chcl3_benchmark_13c_detect_pp.mac.tpl
    chcl3_benchmark_13c_detect_interface.mac.tpl
    chcl3_benchmark_13c_detect_default.par.tpl
  tests/
    test_lowering.py
    test_phase_list.py
    test_pp_list.py
    test_snapshots.py
```

The exact module names may vary, but the separation of concerns should stay similar.

## Final Note to Future Implementers

Do not widen the scope casually. The value of this v1 is that it preserves the exact CHCl3 benchmark-family conventions already present in the lab corpus while exposing a higher-level axis-angle authoring surface. If a future task needs water, CPMG, Hahn, T1IR, or broader SpinSolve support, add new scaffolds explicitly rather than silently over-generalizing this compiler.
