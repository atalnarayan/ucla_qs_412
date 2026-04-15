from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypeAlias


Axis: TypeAlias = Literal["x", "y"]
Nucleus: TypeAlias = Literal["1H", "13C"]
SamplePreset: TypeAlias = Literal["chcl3"]


@dataclass(frozen=True, slots=True)
class RotationPulse:
    """One axis-angle RF pulse."""

    axis: Axis
    angle_deg: float
    target: Nucleus
    amplitude_db: float | None = None
    duration_us: float | None = None


@dataclass(frozen=True, slots=True)
class WaitUs:
    """Explicit coherent evolution time."""

    value_us: float


@dataclass(frozen=True, slots=True)
class DelayUs:
    """Explicit ordinary delay."""

    value_us: float


BodyStep: TypeAlias = RotationPulse | WaitUs | DelayUs


@dataclass(frozen=True, slots=True)
class ReadoutSpec:
    """Optional override for the default scaffold acquisition block."""

    pulse_target: Nucleus
    pulse_axis: Axis
    pulse_angle_deg: float
    preacq_symbol: str
    acquire_mode: str
    points_symbol: str


@dataclass(slots=True)
class ProgramSpec:
    """Compile input for one benchmark pulse-program bundle."""

    name: str
    detect_nucleus: Nucleus
    body_steps: list[BodyStep]
    sample_preset: SamplePreset = "chcl3"
    readout_override: ReadoutSpec | None = None
    default_param_overrides: dict[str, str | int | float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BundleResult:
    """Paths and derived metadata for a generated source bundle."""

    output_dir: Path
    pp_mac_path: Path
    mac_path: Path
    interface_mac_path: Path
    default_par_path: Path
    pp_list: list[str]
    phase_list: str


def Rx(
    angle_deg: float,
    target: Nucleus,
    *,
    amplitude_db: float | None = None,
    duration_us: float | None = None,
) -> RotationPulse:
    return RotationPulse(
        axis="x",
        angle_deg=angle_deg,
        target=target,
        amplitude_db=amplitude_db,
        duration_us=duration_us,
    )


def Ry(
    angle_deg: float,
    target: Nucleus,
    *,
    amplitude_db: float | None = None,
    duration_us: float | None = None,
) -> RotationPulse:
    return RotationPulse(
        axis="y",
        angle_deg=angle_deg,
        target=target,
        amplitude_db=amplitude_db,
        duration_us=duration_us,
    )
