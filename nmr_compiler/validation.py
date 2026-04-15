from __future__ import annotations

import re

from .api import DelayUs, ProgramSpec, RotationPulse, WaitUs
from .scaffolds import Scaffold


SAFE_STEM_RE = re.compile(r"[^A-Za-z0-9_.-]+")
SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def normalize_experiment_name(name: str) -> str:
    normalized = SAFE_STEM_RE.sub("_", name.strip()).strip("._")
    if not normalized:
        raise ValueError("Experiment name must not be empty.")
    return normalized


def validate_spec(spec: ProgramSpec, scaffold: Scaffold) -> None:
    normalize_experiment_name(spec.name)
    if spec.sample_preset != "chcl3":
        raise ValueError("V1 only supports sample_preset='chcl3'.")
    if spec.detect_nucleus != scaffold.detect_nucleus:
        raise ValueError("Scaffold/detect_nucleus mismatch.")

    for step in spec.body_steps:
        if isinstance(step, RotationPulse):
            if step.axis not in {"x", "y"}:
                raise ValueError(f"Unsupported pulse axis: {step.axis}")
            if step.target not in {"1H", "13C"}:
                raise ValueError(f"Unsupported pulse target: {step.target}")
            if step.angle_deg == 0:
                raise ValueError("Pulse angle must be non-zero.")
            if step.duration_us is not None and step.duration_us <= 0:
                raise ValueError("Pulse duration override must be positive.")
        elif isinstance(step, (WaitUs, DelayUs)):
            if step.value_us < 0:
                raise ValueError("Delays and waits must be non-negative.")
        else:
            raise ValueError(f"Unsupported body step type: {type(step)!r}")

    if spec.readout_override is not None:
        readout = spec.readout_override
        if readout.pulse_target not in {"1H", "13C"}:
            raise ValueError(f"Unsupported readout target: {readout.pulse_target}")
        if readout.pulse_axis not in {"x", "y"}:
            raise ValueError(f"Unsupported readout axis: {readout.pulse_axis}")
        if readout.pulse_angle_deg == 0:
            raise ValueError("Readout pulse angle must be non-zero.")
        if not readout.acquire_mode:
            raise ValueError("Acquire mode must not be empty.")
        for symbol in (readout.preacq_symbol, readout.points_symbol):
            if not SYMBOL_RE.fullmatch(symbol):
                raise ValueError(f"Invalid readout symbol: {symbol}")
            if symbol not in scaffold.allowed_symbols:
                raise ValueError(
                    f"Readout symbol {symbol!r} is not defined by scaffold {scaffold.name}."
                )

    for key in spec.default_param_overrides:
        if not key:
            raise ValueError("Override keys must not be empty.")
