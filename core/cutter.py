"""Video cutting, trimming, and splitting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.ffmpeg_wrapper import (
    FFmpegError,
    format_timestamp,
    parse_timestamp,
    probe,
    run_ffmpeg,
)


class CutMode(str, Enum):
    FAST = "fast"
    PRECISE = "precise"


@dataclass
class CutRange:
    start: str
    end: str
    output_path: str


@dataclass
class CutOptions:
    start: str = "00:00:00.000"
    end: str | None = None
    mode: CutMode = CutMode.FAST


def _duration_for_cut(input_path: str, start: str, end: str | None) -> float:
    info = probe(input_path)
    start_s = parse_timestamp(start)
    end_s = parse_timestamp(end) if end else info.duration
    return max(end_s - start_s, 0.001)


def build_cut_args(
    input_path: str,
    output_path: str,
    start: str,
    end: str | None,
    mode: CutMode,
) -> list[str]:
    args: list[str] = []
    if mode == CutMode.FAST:
        args.extend(["-ss", start, "-i", input_path])
        if end:
            args.extend(["-to", end])
        args.extend(["-c", "copy"])
    else:
        args.extend(["-i", input_path, "-ss", start])
        if end:
            args.extend(["-to", end])
        args.extend(["-c:v", "libx264", "-crf", "18", "-c:a", "aac"])
    args.append(output_path)
    return args


def cut(
    input_path: str,
    output_path: str,
    opts: CutOptions | None = None,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    opts = opts or CutOptions()
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    duration = _duration_for_cut(input_path, opts.start, opts.end)
    args = build_cut_args(input_path, output_path, opts.start, opts.end, opts.mode)
    run_ffmpeg(
        args,
        duration=duration,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
    return output_path


def multi_cut(
    input_path: str,
    ranges: list[CutRange],
    mode: CutMode = CutMode.FAST,
    *,
    progress_callback=None,
    cancel_check=None,
) -> list[str]:
    outputs: list[str] = []
    total = len(ranges)
    for i, r in enumerate(ranges):
        def _progress(p: float) -> None:
            if progress_callback:
                progress_callback((i + p) / total)

        opts = CutOptions(start=r.start, end=r.end, mode=mode)
        outputs.append(
            cut(
                input_path,
                r.output_path,
                opts,
                progress_callback=_progress,
                cancel_check=cancel_check,
            )
        )
    return outputs


def split_equal(
    input_path: str,
    output_dir: str,
    segments: int,
    mode: CutMode = CutMode.FAST,
    *,
    progress_callback=None,
    cancel_check=None,
) -> list[str]:
    info = probe(input_path)
    if segments < 1:
        raise FFmpegError("segments must be >= 1")
    seg_len = info.duration / segments
    stem = Path(input_path).stem
    suffix = Path(input_path).suffix
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ranges: list[CutRange] = []
    for i in range(segments):
        start = i * seg_len
        end = (i + 1) * seg_len if i < segments - 1 else info.duration
        ranges.append(
            CutRange(
                start=format_timestamp(start),
                end=format_timestamp(end),
                output_path=str(out_dir / f"{stem}_part{i + 1:03d}{suffix}"),
            )
        )
    return multi_cut(
        input_path,
        ranges,
        mode,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )


def split_by_max_duration(
    input_path: str,
    output_dir: str,
    max_duration_seconds: float,
    mode: CutMode = CutMode.FAST,
    *,
    progress_callback=None,
    cancel_check=None,
) -> list[str]:
    info = probe(input_path)
    if max_duration_seconds <= 0:
        raise FFmpegError("max_duration must be positive")

    ranges: list[CutRange] = []
    stem = Path(input_path).stem
    suffix = Path(input_path).suffix
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    start = 0.0
    idx = 1
    while start < info.duration:
        end = min(start + max_duration_seconds, info.duration)
        ranges.append(
            CutRange(
                start=format_timestamp(start),
                end=format_timestamp(end),
                output_path=str(out_dir / f"{stem}_chunk{idx:03d}{suffix}"),
            )
        )
        start = end
        idx += 1

    return multi_cut(
        input_path,
        ranges,
        mode,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )


def split_by_max_size(
    input_path: str,
    output_dir: str,
    max_size_mb: float,
    mode: CutMode = CutMode.FAST,
    *,
    progress_callback=None,
    cancel_check=None,
) -> list[str]:
    info = probe(input_path)
    file_size = Path(input_path).stat().st_size
    if file_size <= 0 or info.duration <= 0:
        raise FFmpegError("Invalid input file size or duration")

    bytes_per_second = file_size / info.duration
    max_bytes = max_size_mb * 1024 * 1024
    max_duration = max_bytes / bytes_per_second
    return split_by_max_duration(
        input_path,
        output_dir,
        max_duration,
        mode,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
