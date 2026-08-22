"""Thumbnail and preview GIF generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.ffmpeg_wrapper import format_timestamp, probe, run_ffmpeg


@dataclass
class ThumbnailOptions:
    timestamp: str = "00:00:01.000"


@dataclass
class PreviewGifOptions:
    start: str = "00:00:00.000"
    duration: float = 3.0
    fps: int = 10
    width: int = 480


def extract_thumbnail(
    input_path: str,
    output_path: str,
    opts: ThumbnailOptions | None = None,
) -> str:
    opts = opts or ThumbnailOptions()
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    run_ffmpeg(
        [
            "-ss",
            opts.timestamp,
            "-i",
            input_path,
            "-frames:v",
            "1",
            "-q:v",
            "2",
            output_path,
        ]
    )
    return output_path


def generate_preview_gif(
    input_path: str,
    output_path: str,
    opts: PreviewGifOptions | None = None,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    opts = opts or PreviewGifOptions()
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    run_ffmpeg(
        [
            "-ss",
            opts.start,
            "-t",
            str(opts.duration),
            "-i",
            input_path,
            "-vf",
            f"fps={opts.fps},scale={opts.width}:-1:flags=lanczos",
            "-c:v",
            "gif",
            output_path,
        ],
        duration=opts.duration,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
    return output_path
