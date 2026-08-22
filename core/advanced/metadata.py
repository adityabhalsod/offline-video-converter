"""Metadata editing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.ffmpeg_wrapper import probe, run_ffmpeg


@dataclass
class MetadataOptions:
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    comment: str | None = None


def edit_metadata(
    input_path: str,
    output_path: str,
    opts: MetadataOptions,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    info = probe(input_path)

    args = ["-i", input_path, "-c", "copy", "-map", "0"]
    for key, value in (
        ("title", opts.title),
        ("artist", opts.artist),
        ("album", opts.album),
        ("comment", opts.comment),
    ):
        if value:
            args.extend(["-metadata", f"{key}={value}"])

    args.append(output_path)
    run_ffmpeg(
        args,
        duration=info.duration,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
    return output_path
