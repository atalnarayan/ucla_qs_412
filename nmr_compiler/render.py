from __future__ import annotations

from collections import OrderedDict
import re

from .api import ReadoutSpec
from .lowering import AcquireOp, DelayOp, PulseOp, RenderedOp, render_operation
from .scaffolds import PHASE_LIST_COMPACT, Scaffold, load_template_text, parse_default_parameters


PP_LIST_LINE_RE = re.compile(r'^\s*pp_list = \[.*\]$', re.MULTILINE)
PP_NAME_LINE_RE = re.compile(r'^\s*pp_name = ".*"$', re.MULTILINE)
PHASE_LIST_LINE_RE = re.compile(r'^\s*phase_list = \[.*\]$', re.MULTILINE)


def _format_default_override(value: str | int | float) -> str:
    if isinstance(value, bool):
        return '"true"' if value else '"false"'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        text = f"{value:g}"
        return text
    stripped = value.strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        return stripped
    return f'"{stripped}"'


def merge_default_parameters(
    scaffold: Scaffold,
    overrides: dict[str, str | int | float],
) -> OrderedDict[str, str]:
    merged = parse_default_parameters(scaffold.default_template_name)
    for key, value in overrides.items():
        merged[key] = _format_default_override(value)
    return merged


def render_default_par(
    scaffold: Scaffold,
    merged_defaults: OrderedDict[str, str],
    overrides: dict[str, str | int | float],
) -> str:
    template_text = load_template_text(scaffold.default_template_name)
    if not overrides:
        return template_text

    lines = template_text.splitlines()
    seen: set[str] = set()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        key, _ = stripped.split("=", 1)
        key = key.strip()
        if key in overrides:
            lines[index] = f"{key} = {merged_defaults[key]}"
            seen.add(key)

    for key in overrides:
        if key not in seen:
            lines.append(f"{key} = {merged_defaults[key]}")

    return "\n".join(lines) + "\n"


def render_wrapper_mac(
    scaffold: Scaffold,
    experiment_name: str,
    pp_list: list[str],
    phase_list: str = PHASE_LIST_COMPACT,
) -> str:
    template_text = load_template_text(scaffold.wrapper_template_name)
    rendered = template_text.replace(scaffold.canonical_experiment_name, experiment_name)
    rendered_pp_list = "[" + ",".join(f'"{item}"' for item in pp_list) + "]"
    rendered = PP_LIST_LINE_RE.sub(f"   pp_list = {rendered_pp_list}", rendered)
    rendered = PP_NAME_LINE_RE.sub(f'   pp_name = "{experiment_name}.p"', rendered)
    rendered = PHASE_LIST_LINE_RE.sub(f"   phase_list = {phase_list}", rendered)
    return rendered


def render_interface_mac(scaffold: Scaffold) -> str:
    return load_template_text(scaffold.interface_template_name)


def _extract_pp_template_parts(scaffold: Scaffold) -> tuple[str, str]:
    text = load_template_text(scaffold.pp_template_name)
    lines = text.splitlines(keepends=True)
    body_index = None
    end_index = None
    for index, line in enumerate(lines):
        if "# Your pulse program goes here" in line:
            body_index = index
        if "lst = endpp(0) # Return parameter list" in line:
            end_index = index
            break
    if body_index is None or end_index is None:
        raise ValueError(f"Unable to locate pulse-program template markers in {scaffold.pp_template_name}")
    prefix = "".join(lines[: body_index + 1]).rstrip("\n")
    suffix = "".join(lines[end_index:])
    return prefix, suffix


def _render_section_header(title: str) -> list[str]:
    return ["", f"    # {title}"]


def _render_readout_lines(
    readout_ops: list[RenderedOp],
    readout_override: ReadoutSpec | None,
) -> list[str]:
    lines: list[str] = []
    if readout_override is not None:
        lines.append("    # Readout override active")
    if readout_ops and isinstance(readout_ops[0], DelayOp):
        lines.append(f"    {render_operation(readout_ops[0])}")
        readout_ops = readout_ops[1:]
    if not readout_ops or not isinstance(readout_ops[0], PulseOp):
        raise ValueError("Readout block must start with an acquisition pulse.")
    lines.extend(_render_section_header("Acquisition pulse"))
    lines.append(f"    {render_operation(readout_ops[0])}")
    lines.extend(["", "    # Acquire"])
    if len(readout_ops) != 3 or not isinstance(readout_ops[1], DelayOp) or not isinstance(readout_ops[2], AcquireOp):
        raise ValueError("Readout block must end with delay/acquire.")
    lines.append(f"    {render_operation(readout_ops[1])}")
    lines.append(f"    {render_operation(readout_ops[2])}")
    return lines


def render_pp_mac(
    scaffold: Scaffold,
    body_ops: list[RenderedOp],
    program_ops: list[RenderedOp],
    readout_override: ReadoutSpec | None,
) -> str:
    prefix, suffix = _extract_pp_template_parts(scaffold)
    readout_ops = program_ops[len(body_ops) :]

    lines: list[str] = []
    if body_ops:
        lines.extend(f"    {render_operation(op)}" for op in body_ops)
    else:
        lines.append("    # Empty pulse body")
    lines.extend(_render_readout_lines(readout_ops, readout_override))
    return prefix + "\n" + "\n".join(lines) + "\n" + suffix
