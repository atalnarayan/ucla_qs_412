from __future__ import annotations

from pathlib import Path

from .api import BundleResult, ProgramSpec
from .lowering import (
    build_readout_ops,
    compose_program_ops,
    derive_pp_list,
    lower_body_steps,
)
from .render import (
    merge_default_parameters,
    render_default_par,
    render_interface_mac,
    render_pp_mac,
    render_wrapper_mac,
)
from .scaffolds import PHASE_LIST_COMPACT, get_scaffold
from .validation import normalize_experiment_name, validate_spec


def _write_text(path: Path, content: str, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content, encoding="utf-8")


def compile_program(
    spec: ProgramSpec,
    output_dir: str | Path,
    *,
    overwrite: bool = False,
) -> BundleResult:
    scaffold = get_scaffold(spec.detect_nucleus)
    validate_spec(spec, scaffold)

    experiment_name = normalize_experiment_name(spec.name)
    merged_defaults = merge_default_parameters(scaffold, spec.default_param_overrides)

    body_ops = lower_body_steps(spec.body_steps, scaffold, merged_defaults)
    readout_ops = build_readout_ops(
        scaffold,
        merged_defaults,
        spec.readout_override,
    )
    program_ops = compose_program_ops(body_ops, readout_ops)
    pp_list = derive_pp_list(program_ops)

    pp_mac_text = render_pp_mac(scaffold, body_ops, program_ops, spec.readout_override)
    mac_text = render_wrapper_mac(scaffold, experiment_name, pp_list, PHASE_LIST_COMPACT)
    interface_text = render_interface_mac(scaffold)
    default_text = render_default_par(
        scaffold,
        merged_defaults,
        spec.default_param_overrides,
    )

    bundle_dir = Path(output_dir) / experiment_name
    if bundle_dir.exists() and not bundle_dir.is_dir():
        raise FileExistsError(f"Output path exists and is not a directory: {bundle_dir}")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    pp_mac_path = bundle_dir / f"{experiment_name}_pp.mac"
    mac_path = bundle_dir / f"{experiment_name}.mac"
    interface_mac_path = bundle_dir / f"{experiment_name}_interface.mac"
    default_par_path = bundle_dir / f"{experiment_name}Default.par"

    for path in (pp_mac_path, mac_path, interface_mac_path, default_par_path):
        if path.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file: {path}")

    _write_text(pp_mac_path, pp_mac_text, overwrite=overwrite)
    _write_text(mac_path, mac_text, overwrite=overwrite)
    _write_text(interface_mac_path, interface_text, overwrite=overwrite)
    _write_text(default_par_path, default_text, overwrite=overwrite)

    return BundleResult(
        output_dir=bundle_dir,
        pp_mac_path=pp_mac_path,
        mac_path=mac_path,
        interface_mac_path=interface_mac_path,
        default_par_path=default_par_path,
        pp_list=pp_list,
        phase_list=PHASE_LIST_COMPACT,
    )
