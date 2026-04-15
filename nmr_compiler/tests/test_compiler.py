from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from nmr_compiler import DelayUs, ProgramSpec, Rx, Ry, WaitUs, compile_program
from nmr_compiler.lowering import DelayOp, PulseOp, WaitOp, derive_pp_list, lower_body_steps
from nmr_compiler.render import merge_default_parameters
from nmr_compiler.scaffolds import PHASE_LIST_COMPACT, get_scaffold


WORKSPACE_ROOT = Path("/Users/atalnarayansahu/Desktop/F25/UCLA")
SAMPLE_ROOT = WORKSPACE_ROOT / "code/ucla_nmr_lab/pulse_programs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _op_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(("pulse(", "delay(", "wait(", 'acquire("')):
            lines.append(stripped)
    return lines


def _compile(spec: ProgramSpec):
    tempdir = tempfile.TemporaryDirectory()
    bundle = compile_program(spec, tempdir.name)
    return tempdir, bundle


def dj_steps() -> list:
    return [
        Ry(-90, "13C"),
        Ry(90, "1H"),
        Ry(90, "13C"),
        Ry(-90, "1H"),
    ]


def grover_steps() -> list:
    return [
        Ry(90, "13C"),
        Ry(90, "1H"),
        WaitUs(2325),
        Ry(-90, "13C"),
        Rx(90, "13C"),
        Ry(90, "13C"),
        Ry(-90, "1H"),
        Rx(90, "1H"),
        Ry(90, "1H"),
        Ry(90, "13C"),
        Rx(180, "13C"),
        Ry(90, "1H"),
        Rx(180, "1H"),
        WaitUs(2325),
        Ry(90, "13C"),
        Rx(90, "13C"),
        Ry(-90, "13C"),
        Ry(90, "1H"),
        Rx(90, "1H"),
        Ry(-90, "1H"),
        Ry(90, "13C"),
        Rx(180, "13C"),
        Ry(90, "1H"),
        Rx(180, "1H"),
    ]


def tt_steps() -> list:
    return [
        Rx(-90, "13C"),
        Ry(-90, "13C"),
        Ry(90, "1H"),
        Rx(-90, "1H"),
        Ry(-90, "1H"),
        WaitUs(2325),
        Ry(90, "13C"),
    ]


class CompilerFixtureTests(unittest.TestCase):
    maxDiff = None

    def test_dj_13c_matches_sample_outputs(self) -> None:
        spec = ProgramSpec(name="DJ_f1_13C_p0", detect_nucleus="13C", body_steps=dj_steps())
        tempdir, bundle = _compile(spec)
        self.addCleanup(tempdir.cleanup)

        sample_dir = SAMPLE_ROOT / "DJ_f1_13C_p0"
        self.assertEqual(_read(bundle.mac_path), _read(sample_dir / "DJ_f1_13C_p0.mac"))
        self.assertEqual(
            _read(bundle.interface_mac_path),
            _read(sample_dir / "DJ_f1_13C_p0_interface.mac"),
        )
        self.assertEqual(
            _read(bundle.default_par_path),
            _read(sample_dir / "DJ_f1_13C_p0Default.par"),
        )
        self.assertEqual(
            _op_lines(_read(bundle.pp_mac_path)),
            _op_lines(_read(sample_dir / "DJ_f1_13C_p0_pp.mac")),
        )
        self.assertEqual(bundle.pp_list, ["a90C", "freqCh2", "p4", "d90C", "a90H", "freqCh1", "p2", "d90H", "p1", "dPreAcq", "n1"])
        self.assertEqual(bundle.phase_list, PHASE_LIST_COMPACT)

    def test_dj_1h_matches_sample_outputs(self) -> None:
        spec = ProgramSpec(name="DJ_f1_1H_p0", detect_nucleus="1H", body_steps=dj_steps())
        tempdir, bundle = _compile(spec)
        self.addCleanup(tempdir.cleanup)

        sample_dir = SAMPLE_ROOT / "DJ_f1_1H_p0"
        self.assertEqual(_read(bundle.mac_path), _read(sample_dir / "DJ_f1_1H_p0.mac"))
        self.assertEqual(
            _read(bundle.interface_mac_path),
            _read(sample_dir / "DJ_f1_1H_p0_interface.mac"),
        )
        self.assertEqual(
            _read(bundle.default_par_path),
            _read(sample_dir / "DJ_f1_1H_p0Default.par"),
        )
        self.assertEqual(
            _op_lines(_read(bundle.pp_mac_path)),
            _op_lines(_read(sample_dir / "DJ_f1_1H_p0_pp.mac")),
        )
        self.assertEqual(bundle.pp_list, ["a90C", "fTx13C", "p4", "d90C", "a90H", "fTx1H", "p2", "d90H", "p1", "dAcq", "nPnts"])

    def test_grover_13c_matches_sample_wrapper_and_body(self) -> None:
        spec = ProgramSpec(name="Grover_11_13C_p0", detect_nucleus="13C", body_steps=grover_steps())
        tempdir, bundle = _compile(spec)
        self.addCleanup(tempdir.cleanup)

        sample_dir = SAMPLE_ROOT / "Grover_11_13C_p0"
        self.assertEqual(_read(bundle.mac_path), _read(sample_dir / "Grover_11_13C_p0.mac"))
        self.assertEqual(
            _op_lines(_read(bundle.pp_mac_path)),
            _op_lines(_read(sample_dir / "Grover_11_13C_p0_pp.mac")),
        )

    def test_grover_1h_matches_sample_wrapper_and_body(self) -> None:
        spec = ProgramSpec(name="Grover_11_1H_p0", detect_nucleus="1H", body_steps=grover_steps())
        tempdir, bundle = _compile(spec)
        self.addCleanup(tempdir.cleanup)

        sample_dir = SAMPLE_ROOT / "Grover_11_1H_p0"
        self.assertEqual(_read(bundle.mac_path), _read(sample_dir / "Grover_11_1H_p0.mac"))
        self.assertEqual(
            _op_lines(_read(bundle.pp_mac_path)),
            _op_lines(_read(sample_dir / "Grover_11_1H_p0_pp.mac")),
        )

    def test_tt_13c_compiles_with_superset_relationships(self) -> None:
        spec = ProgramSpec(name="CNOT_TT_13C_00_p0", detect_nucleus="13C", body_steps=tt_steps())
        tempdir, bundle = _compile(spec)
        self.addCleanup(tempdir.cleanup)

        sample_dir = SAMPLE_ROOT / "CNOT_TT_13C_00_p0"
        self.assertEqual(
            _op_lines(_read(bundle.pp_mac_path)),
            _op_lines(_read(sample_dir / "CNOT_TT_13C_00_p0_pp.mac")),
        )
        wrapper = _read(bundle.mac_path)
        self.assertIn('"d180C = pulseLengthC90*2"', wrapper)
        self.assertIn('"d180H = pulseLengthH90*2"', wrapper)
        self.assertEqual(bundle.pp_list, ["a90C", "freqCh2", "p3", "d90C", "p4", "a90H", "freqCh1", "p2", "d90H", "p1", "dPreAcq", "n1"])

    def test_tt_1h_compiles_with_superset_relationships(self) -> None:
        spec = ProgramSpec(name="CNOT_TT_1H_00_p0", detect_nucleus="1H", body_steps=tt_steps())
        tempdir, bundle = _compile(spec)
        self.addCleanup(tempdir.cleanup)

        sample_dir = SAMPLE_ROOT / "CNOT_TT_1H_00_p0"
        self.assertEqual(
            _op_lines(_read(bundle.pp_mac_path)),
            _op_lines(_read(sample_dir / "CNOT_TT_1H_00_p0_pp.mac")),
        )
        wrapper = _read(bundle.mac_path)
        self.assertIn('"d180H = pulseLength1H*2"', wrapper)
        self.assertIn('"d180C = pulseLength13C*2"', wrapper)
        self.assertEqual(bundle.pp_list, ["a90C", "fTx13C", "p3", "d90C", "p4", "a90H", "fTx1H", "p2", "d90H", "p1", "dAcq", "nPnts"])

    def test_empty_body_produces_fid_like_readout_for_both_scaffolds(self) -> None:
        for detect_nucleus, expected in (
            ("13C", ["delay(0.5)", "pulse(2, a90C, p1, d90C)", "delay(dPreAcq)", 'acquire("overwrite", n1)']),
            ("1H", ["delay(0.5)", "pulse(1, a90H, p1, d90H)", "delay(dAcq)", 'acquire("overwrite", nPnts)']),
        ):
            with self.subTest(detect_nucleus=detect_nucleus):
                spec = ProgramSpec(name=f"fid_like_{detect_nucleus}", detect_nucleus=detect_nucleus, body_steps=[])
                tempdir, bundle = _compile(spec)
                self.addCleanup(tempdir.cleanup)
                self.assertEqual(_op_lines(_read(bundle.pp_mac_path)), expected)

    def test_overwrite_false_rejects_existing_files(self) -> None:
        spec = ProgramSpec(name="DJ_f1_13C_p0", detect_nucleus="13C", body_steps=dj_steps())
        with tempfile.TemporaryDirectory() as tempdir:
            compile_program(spec, tempdir)
            with self.assertRaises(FileExistsError):
                compile_program(spec, tempdir)


class LoweringTests(unittest.TestCase):
    def test_lowering_derives_symbols_and_auto_delay(self) -> None:
        scaffold = get_scaffold("1H")
        defaults = merge_default_parameters(scaffold, {})
        body = lower_body_steps(
            [
                Rx(180, "1H"),
                Ry(-90, "13C", amplitude_db=-3.5),
                DelayUs(1.25),
                WaitUs(2325),
            ],
            scaffold,
            defaults,
        )
        self.assertEqual(body[0], PulseOp(channel=1, amplitude="a90H", phase="p1", duration="d180H", frequency="fTx1H"))
        self.assertEqual(body[1], DelayOp("0.5"))
        self.assertEqual(body[2], PulseOp(channel=2, amplitude="-3.5", phase="p4", duration="d90C", frequency="fTx13C"))
        self.assertEqual(body[3], DelayOp("1.25"))
        self.assertEqual(body[4], WaitOp("2325"))

    def test_nonstandard_angle_uses_numeric_duration_and_pp_list_filters_literals(self) -> None:
        scaffold = get_scaffold("13C")
        defaults = merge_default_parameters(scaffold, {})
        body = lower_body_steps([Rx(45, "13C"), Ry(-90, "1H")], scaffold, defaults)
        self.assertEqual(body[0], PulseOp(channel=2, amplitude="a90C", phase="p1", duration="37.5", frequency="freqCh2"))
        self.assertEqual(body[1], DelayOp("0.5"))
        self.assertEqual(body[2], PulseOp(channel=1, amplitude="a90H", phase="p4", duration="d90H", frequency="freqCh1"))
        self.assertEqual(derive_pp_list(body), ["a90C", "freqCh2", "p1", "a90H", "freqCh1", "p4", "d90H"])


if __name__ == "__main__":
    unittest.main()
