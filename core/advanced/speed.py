"""Speed change with audio pitch preservation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.ffmpeg_wrapper import probe, run_ffmpeg


@dataclass
class SpeedOptions:
    factor: float = 1.0


def _atempo_chain(factor: float) -> str:
    """Build atempo filter chain for factors beyond 0.5-2.0 range."""
    filters: list[str] = []
    remaining = factor
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.4f}")
    return ",".join(filters)


def change_speed(
    input_path: str,
    output_path: str,
    opts: SpeedOptions | None = None,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    opts = opts or SpeedOptions()
    if not 0.25 <= opts.factor <= 4.0:
        raise ValueError("Speed factor must be between 0.25 and 4.0")

    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    info = probe(input_path)

    video_filter = f"setpts=PTS/{opts.factor}"
    audio_filter = _atempo_chain(opts.factor)
    args = [
        "-i",
        input_path,
        "-filter_complex",
        f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-crf",
        "23",
        output_path,
    ]
    effective_duration = info.duration / opts.factor
    run_ffmpeg(
        args,
        duration=effective_duration,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
    return output_path
