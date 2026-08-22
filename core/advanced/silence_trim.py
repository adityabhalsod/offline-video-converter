"""Silence detection and auto-trim."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core.cutter import CutMode, CutOptions, CutRange, multi_cut
from core.ffmpeg_wrapper import FFmpegError, format_timestamp, probe, run_ffmpeg


@dataclass
class SilenceTrimOptions:
    noise_db: float = -30.0
    min_silence_duration: float = 0.5


def detect_silence_segments(
    input_path: str,
    opts: SilenceTrimOptions | None = None,
) -> list[tuple[float, float]]:
    opts = opts or SilenceTrimOptions()
    input_path = str(Path(input_path).resolve())
    info = probe(input_path)

    result = run_ffmpeg(
        [
            "-i",
            input_path,
            "-af",
            f"silencedetect=noise={opts.noise_db}dB:d={opts.min_silence_duration}",
            "-f",
            "null",
            "-",
        ],
        duration=info.duration,
    )
    silence_starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", result.stderr)]
    silence_ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", result.stderr)]

    silent: list[tuple[float, float]] = []
    for i, start in enumerate(silence_starts):
        end = silence_ends[i] if i < len(silence_ends) else info.duration
        silent.append((start, end))
    return silent


def trim_silence(
    input_path: str,
    output_dir: str,
    opts: SilenceTrimOptions | None = None,
    *,
    progress_callback=None,
    cancel_check=None,
) -> list[str]:
    opts = opts or SilenceTrimOptions()
    info = probe(input_path)
    silent = detect_silence_segments(input_path, opts)

    if not silent:
        raise FFmpegError("No silence segments detected")

    ranges: list[CutRange] = []
    stem = Path(input_path).stem
    suffix = Path(input_path).suffix
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cursor = 0.0
    idx = 1
    for s_start, s_end in silent:
        if s_start > cursor + 0.1:
            ranges.append(
                CutRange(
                    start=format_timestamp(cursor),
                    end=format_timestamp(s_start),
                    output_path=str(out_dir / f"{stem}_clip{idx:03d}{suffix}"),
                )
            )
            idx += 1
        cursor = s_end

    if cursor < info.duration - 0.1:
        ranges.append(
            CutRange(
                start=format_timestamp(cursor),
                end=format_timestamp(info.duration),
                output_path=str(out_dir / f"{stem}_clip{idx:03d}{suffix}"),
            )
        )

    if not ranges:
        raise FFmpegError("All content was silence")

    return multi_cut(
        input_path,
        ranges,
        CutMode.PRECISE,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
