"""Video filters: rotate, flip, crop, denoise, stabilization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.ffmpeg_wrapper import probe, run_ffmpeg


class FilterType(str, Enum):
    ROTATE_90 = "rotate_90"
    ROTATE_180 = "rotate_180"
    ROTATE_270 = "rotate_270"
    FLIP_H = "flip_h"
    FLIP_V = "flip_v"
    CROP = "crop"
    DENOISE = "denoise"
    STABILIZE = "stabilize"


@dataclass
class FilterOptions:
    filter_type: FilterType
    crop_w: int | None = None
    crop_h: int | None = None
    crop_x: int = 0
    crop_y: int = 0


FILTER_MAP = {
    FilterType.ROTATE_90: "transpose=1",
    FilterType.ROTATE_180: "transpose=1,transpose=1",
    FilterType.ROTATE_270: "transpose=2",
    FilterType.FLIP_H: "hflip",
    FilterType.FLIP_V: "vflip",
    FilterType.DENOISE: "hqdn3d=4:3:6:4",
    FilterType.STABILIZE: "deshake",
}


def apply_filter(
    input_path: str,
    output_path: str,
    opts: FilterOptions,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    info = probe(input_path)

    if opts.filter_type == FilterType.CROP:
        if not opts.crop_w or not opts.crop_h:
            raise ValueError("crop_w and crop_h required for crop filter")
        vf = f"crop={opts.crop_w}:{opts.crop_h}:{opts.crop_x}:{opts.crop_y}"
    else:
        vf = FILTER_MAP[opts.filter_type]

    args = ["-i", input_path, "-vf", vf, "-c:a", "copy", "-c:v", "libx264", "-crf", "23", output_path]
    run_ffmpeg(
        args,
        duration=info.duration,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
    return output_path
