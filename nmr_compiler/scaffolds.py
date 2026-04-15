from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from .api import Nucleus, ReadoutSpec


PHASE_LIST_COMPACT = "[0,2,0,2;1,3,1,3;2,0,2,0;3,1,3,1;0,2,0,2]"
PHASE_LIST_MULTILINE = """[0,2,0,2; # 90 phase
               1,3,1,3;
               2,0,2,0;
               3,1,3,1;
               0,2,0,2] # Acquire phase"""


@dataclass(frozen=True, slots=True)
class Scaffold:
    name: str
    detect_nucleus: Nucleus
    canonical_experiment_name: str
    wrapper_template_name: str
    pp_template_name: str
    interface_template_name: str
    default_template_name: str
    frequency_symbols: dict[Nucleus, str]
    amplitude_symbols: dict[Nucleus, str]
    d90_symbols: dict[Nucleus, str]
    d180_symbols: dict[Nucleus, str]
    pulse_length_param_keys: dict[Nucleus, str]
    default_readout: ReadoutSpec
    allowed_symbols: frozenset[str]


def _template_path(filename: str) -> Path:
    return Path(files("nmr_compiler") / "templates" / filename)


def load_template_text(filename: str) -> str:
    return _template_path(filename).read_text(encoding="utf-8")


def parse_default_parameters(filename: str) -> OrderedDict[str, str]:
    parsed: OrderedDict[str, str] = OrderedDict()
    for line in load_template_text(filename).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        key, value = stripped.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


CHCL3_BENCHMARK_13C = Scaffold(
    name="chcl3_benchmark_13c_detect",
    detect_nucleus="13C",
    canonical_experiment_name="DJ_f1_13C_p0",
    wrapper_template_name="chcl3_benchmark_13c_detect.mac.tpl",
    pp_template_name="chcl3_benchmark_13c_detect_pp.mac.tpl",
    interface_template_name="chcl3_benchmark_13c_detect_interface.mac.tpl",
    default_template_name="chcl3_benchmark_13c_detectDefault.par.tpl",
    frequency_symbols={"1H": "freqCh1", "13C": "freqCh2"},
    amplitude_symbols={"1H": "a90H", "13C": "a90C"},
    d90_symbols={"1H": "d90H", "13C": "d90C"},
    d180_symbols={"1H": "d180H", "13C": "d180C"},
    pulse_length_param_keys={"1H": "pulseLengthH90", "13C": "pulseLengthC90"},
    default_readout=ReadoutSpec(
        pulse_target="13C",
        pulse_axis="x",
        pulse_angle_deg=90.0,
        preacq_symbol="dPreAcq",
        acquire_mode="overwrite",
        points_symbol="n1",
    ),
    allowed_symbols=frozenset(
        {
            "a90C",
            "a90H",
            "aNOE",
            "d90C",
            "d180C",
            "d45C",
            "d90H",
            "d180H",
            "d90HWaltz",
            "d180HWaltz",
            "d270HWaltz",
            "d360HWaltz",
            "dPreAcq",
            "freqCh1",
            "freqCh2",
            "freqRx",
            "f1H",
            "n1",
            "n2",
            "n3",
            "offFreq1H",
            "offFreqX",
            "p1",
            "p2",
            "p3",
            "p4",
            "totPnts",
            "totTime",
            "waltzDuration",
        }
    ),
)


CHCL3_BENCHMARK_1H = Scaffold(
    name="chcl3_benchmark_1h_detect",
    detect_nucleus="1H",
    canonical_experiment_name="DJ_f1_1H_p0",
    wrapper_template_name="chcl3_benchmark_1h_detect.mac.tpl",
    pp_template_name="chcl3_benchmark_1h_detect_pp.mac.tpl",
    interface_template_name="chcl3_benchmark_1h_detect_interface.mac.tpl",
    default_template_name="chcl3_benchmark_1h_detectDefault.par.tpl",
    frequency_symbols={"1H": "fTx1H", "13C": "fTx13C"},
    amplitude_symbols={"1H": "a90H", "13C": "a90C"},
    d90_symbols={"1H": "d90H", "13C": "d90C"},
    d180_symbols={"1H": "d180H", "13C": "d180C"},
    pulse_length_param_keys={"1H": "pulseLength1H", "13C": "pulseLength13C"},
    default_readout=ReadoutSpec(
        pulse_target="1H",
        pulse_axis="x",
        pulse_angle_deg=90.0,
        preacq_symbol="dAcq",
        acquire_mode="overwrite",
        points_symbol="nPnts",
    ),
    allowed_symbols=frozenset(
        {
            "O1",
            "a90C",
            "a90H",
            "b1Freq",
            "d90C",
            "d180C",
            "d90H",
            "d180H",
            "dAcq",
            "fTx1H",
            "fTx13C",
            "nPnts",
            "offFreq1H",
            "offFreq13C",
            "p1",
            "p2",
            "p3",
            "p4",
            "totPnts",
            "totTime",
        }
    ),
)


SCAFFOLDS_BY_NUCLEUS: dict[Nucleus, Scaffold] = {
    "13C": CHCL3_BENCHMARK_13C,
    "1H": CHCL3_BENCHMARK_1H,
}


def get_scaffold(detect_nucleus: Nucleus) -> Scaffold:
    return SCAFFOLDS_BY_NUCLEUS[detect_nucleus]
