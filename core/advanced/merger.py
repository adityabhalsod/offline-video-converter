"""Merge / concatenate clips."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.converter import ConvertOptions, convert
from core.ffmpeg_wrapper import FFmpegError, probe, run_ffmpeg


class MergeMode(str, Enum):
    FAST = "fast"
    REENCODE = "reencode"


@dataclass
class MergeOptions:
    mode: MergeMode = MergeMode.FAST
    output_format: str = "mp4"


def _same_codecs(paths: list[str]) -> bool:
    first = probe(paths[0])
    for p in paths[1:]:
        info = probe(p)
        if info.video_codec != first.video_codec or info.audio_codec != first.audio_codec:
            return False
    return True


def merge_videos(
    input_paths: list[str],
    output_path: str,
    opts: MergeOptions | None = None,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    if len(input_paths) < 2:
        raise FFmpegError("Need at least two files to merge")

    opts = opts or MergeOptions()
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    resolved = [str(Path(p).resolve()) for p in input_paths]
    total_duration = sum(probe(p).duration for p in resolved)

    use_fast = opts.mode == MergeMode.FAST and _same_codecs(resolved)

    if use_fast:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            for p in resolved:
                escaped = p.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
            list_path = f.name
        try:
            run_ffmpeg(
                ["-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", output_path],
                duration=total_duration,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )
        finally:
            Path(list_path).unlink(missing_ok=True)
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            for p in resolved:
                escaped = p.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
            list_path = f.name
        temp_out = str(Path(output_path).with_suffix(".tmp.mp4"))
        try:
            run_ffmpeg(
                [
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_path,
                    "-c:v",
                    "libx264",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    temp_out,
                ],
                duration=total_duration,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )
            convert_opts = ConvertOptions(output_format=opts.output_format)
            convert(temp_out, output_path, convert_opts)
        finally:
            Path(list_path).unlink(missing_ok=True)
            Path(temp_out).unlink(missing_ok=True)

    return output_path
