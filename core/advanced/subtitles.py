"""Subtitle burn-in and soft embed."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.ffmpeg_wrapper import probe, run_ffmpeg


class SubtitleMode(str, Enum):
    BURN_IN = "burn_in"
    SOFT_EMBED = "soft_embed"


@dataclass
class SubtitleOptions:
    subtitle_path: str
    mode: SubtitleMode = SubtitleMode.BURN_IN
    language: str = "eng"


def apply_subtitles(
    input_path: str,
    output_path: str,
    opts: SubtitleOptions,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    sub_path = str(Path(opts.subtitle_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    info = probe(input_path)

    if opts.mode == SubtitleMode.BURN_IN:
        escaped = sub_path.replace("\\", "/").replace(":", "\\:")
        args = [
            "-i",
            input_path,
            "-vf",
            f"subtitles='{escaped}'",
            "-c:a",
            "copy",
            "-c:v",
            "libx264",
            "-crf",
            "23",
            output_path,
        ]
    else:
        args = [
            "-i",
            input_path,
            "-i",
            sub_path,
            "-c",
            "copy",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            f"language={opts.language}",
            output_path,
        ]

    run_ffmpeg(
        args,
        duration=info.duration,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
    return output_path
