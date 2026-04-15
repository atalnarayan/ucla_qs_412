from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Iterable

from .api import BodyStep, DelayUs, ReadoutSpec, RotationPulse, WaitUs
from .scaffolds import Scaffold


CHANNEL_BY_TARGET = {"1H": 1, "13C": 2}
PHASE_BY_AXIS_AND_SIGN = {
    ("x", 1): "p1",
    ("y", 1): "p2",
    ("x", -1): "p3",
    ("y", -1): "p4",
}
SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class PulseOp:
    channel: int
    amplitude: str
    phase: str
    duration: str
    frequency: str | None = None


@dataclass(frozen=True, slots=True)
class DelayOp:
    value: str


@dataclass(frozen=True, slots=True)
class WaitOp:
    value: str


@dataclass(frozen=True, slots=True)
class AcquireOp:
    mode: str
    points: str


RenderedOp = PulseOp | DelayOp | WaitOp | AcquireOp


def _format_number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    decimal_value = Decimal(str(value)).normalize()
    text = format(decimal_value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _numeric_default(merged_defaults: dict[str, str], key: str) -> float:
    return float(merged_defaults[key].strip('"'))


def _duration_symbol_or_numeric(
    pulse: RotationPulse,
    scaffold: Scaffold,
    merged_defaults: dict[str, str],
) -> str:
    if pulse.duration_us is not None:
        return _format_number(pulse.duration_us)

    magnitude = abs(float(pulse.angle_deg))
    if magnitude == 90:
        return scaffold.d90_symbols[pulse.target]
    if magnitude == 180:
        return scaffold.d180_symbols[pulse.target]

    d90_value = _numeric_default(
        merged_defaults,
        scaffold.pulse_length_param_keys[pulse.target],
    )
    return _format_number((magnitude / 90.0) * d90_value)


def _lower_pulse(
    pulse: RotationPulse,
    scaffold: Scaffold,
    merged_defaults: dict[str, str],
    *,
    include_frequency: bool,
) -> PulseOp:
    sign = 1 if pulse.angle_deg > 0 else -1
    return PulseOp(
        channel=CHANNEL_BY_TARGET[pulse.target],
        amplitude=(
            scaffold.amplitude_symbols[pulse.target]
            if pulse.amplitude_db is None
            else _format_number(pulse.amplitude_db)
        ),
        phase=PHASE_BY_AXIS_AND_SIGN[(pulse.axis, sign)],
        duration=_duration_symbol_or_numeric(pulse, scaffold, merged_defaults),
        frequency=(
            scaffold.frequency_symbols[pulse.target] if include_frequency else None
        ),
    )


def lower_body_steps(
    body_steps: Iterable[BodyStep],
    scaffold: Scaffold,
    merged_defaults: dict[str, str],
) -> list[RenderedOp]:
    steps = list(body_steps)
    rendered: list[RenderedOp] = []
    for index, step in enumerate(steps):
        if isinstance(step, RotationPulse):
            rendered.append(
                _lower_pulse(
                    step,
                    scaffold,
                    merged_defaults,
                    include_frequency=True,
                )
            )
            next_step = steps[index + 1] if index + 1 < len(steps) else None
            if isinstance(next_step, RotationPulse):
                rendered.append(DelayOp("0.5"))
        elif isinstance(step, DelayUs):
            rendered.append(DelayOp(_format_number(step.value_us)))
        elif isinstance(step, WaitUs):
            rendered.append(WaitOp(_format_number(step.value_us)))
        else:
            raise TypeError(f"Unsupported body step: {step!r}")
    return rendered


def build_readout_ops(
    scaffold: Scaffold,
    merged_defaults: dict[str, str],
    readout_override: ReadoutSpec | None,
) -> list[RenderedOp]:
    spec = readout_override or scaffold.default_readout
    pulse = RotationPulse(
        axis=spec.pulse_axis,
        angle_deg=spec.pulse_angle_deg,
        target=spec.pulse_target,
    )
    return [
        _lower_pulse(
            pulse,
            scaffold,
            merged_defaults,
            include_frequency=False,
        ),
        DelayOp(spec.preacq_symbol),
        AcquireOp(spec.acquire_mode, spec.points_symbol),
    ]


def compose_program_ops(
    body_ops: list[RenderedOp],
    readout_ops: list[RenderedOp],
) -> list[RenderedOp]:
    ops = list(body_ops)
    if not body_ops or isinstance(body_ops[-1], PulseOp):
        ops.append(DelayOp("0.5"))
    ops.extend(readout_ops)
    return ops


def render_operation(op: RenderedOp) -> str:
    if isinstance(op, PulseOp):
        if op.frequency is None:
            return (
                f"pulse({op.channel}, {op.amplitude}, {op.phase}, {op.duration})"
            )
        return (
            f"pulse({op.channel}, {op.amplitude}, {op.phase}, {op.duration}, {op.frequency})"
        )
    if isinstance(op, DelayOp):
        return f"delay({op.value})"
    if isinstance(op, WaitOp):
        return f"wait({op.value})"
    return f'acquire("{op.mode}", {op.points})'


def render_body_lines(ops: Iterable[RenderedOp]) -> list[str]:
    return [f"    {render_operation(op)}" for op in ops]


def derive_pp_list(ops: Iterable[RenderedOp]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    def collect(candidate: str | None) -> None:
        if not candidate or not SYMBOL_RE.fullmatch(candidate):
            return
        if candidate in seen:
            return
        seen.add(candidate)
        ordered.append(candidate)

    for op in ops:
        if isinstance(op, PulseOp):
            collect(op.amplitude)
            collect(op.frequency)
            collect(op.phase)
            collect(op.duration)
        elif isinstance(op, (DelayOp, WaitOp)):
            collect(op.value)
        elif isinstance(op, AcquireOp):
            collect(op.points)

    return ordered
