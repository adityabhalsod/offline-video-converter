"""Watermark and overlay."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.ffmpeg_wrapper import probe, run_ffmpeg


class Position(str, Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"


@dataclass
class WatermarkOptions:
    image_path: str | None = None
    text: str | None = None
    position: Position = Position.BOTTOM_RIGHT
    opacity: float = 0.8
    scale: float = 0.15


POSITION_MAP = {
    Position.TOP_LEFT: "10:10",
    Position.TOP_RIGHT: "W-w-10:10",
    Position.BOTTOM_LEFT: "10:H-h-10",
    Position.BOTTOM_RIGHT: "W-w-10:H-h-10",
    Position.CENTER: "(W-w)/2:(H-h)/2",
}


def apply_watermark(
    input_path: str,
    output_path: str,
    opts: WatermarkOptions,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    info = probe(input_path)
    pos = POSITION_MAP[opts.position]

    if opts.image_path:
        img = str(Path(opts.image_path).resolve())
        filter_complex = (
            f"[1:v]scale=iw*{opts.scale}:-1,format=rgba,colorchannelmixer=aa={opts.opacity}[wm];"
            f"[0:v][wm]overlay={pos}"
        )
        args = ["-i", input_path, "-i", img, "-filter_complex", filter_complex, "-c:a", "copy"]
    elif opts.text:
        escaped = opts.text.replace(":", "\\:").replace("'", "\\'")
        filter_complex = (
            f"drawtext=text='{escaped}':x={pos.split(':')[0]}:y={pos.split(':')[1]}"
            f":fontsize=24:fontcolor=white@{opts.opacity}"
        )
        args = ["-i", input_path, "-vf", filter_complex, "-c:a", "copy"]
    else:
        raise ValueError("Provide image_path or text for watermark")

    args.extend(["-c:v", "libx264", "-crf", "23", output_path])
    run_ffmpeg(
        args,
        duration=info.duration,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
    return output_path
