"""Load and apply platform export presets."""

from __future__ import annotations

import json
from pathlib import Path

from core.advanced.compressor import CompressOptions, compress_to_size
from core.converter import ConvertOptions, QualityMode, VideoCodec, convert

PRESETS_FILE = Path(__file__).resolve().parent.parent / "presets" / "platform_presets.json"


def load_presets() -> dict:
    if not PRESETS_FILE.exists():
        return {}
    return json.loads(PRESETS_FILE.read_text(encoding="utf-8"))


def apply_preset(
    preset_key: str,
    input_path: str,
    output_path: str,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    presets = load_presets()
    if preset_key not in presets:
        raise KeyError(f"Unknown preset: {preset_key}")
    preset = presets[preset_key]

    if "target_size_mb" in preset:
        return compress_to_size(
            input_path,
            output_path,
            CompressOptions(target_size_mb=preset["target_size_mb"]),
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )

    opts = ConvertOptions(
        output_format=preset.get("format", "mp4"),
        video_codec=VideoCodec(preset.get("video_codec", "h264")),
        quality_mode=QualityMode.CRF,
        crf=preset.get("crf", 23),
        width=preset.get("width"),
        height=preset.get("height"),
    )
    return convert(
        input_path,
        output_path,
        opts,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
