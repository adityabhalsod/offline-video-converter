"""Smart compression - target file size mode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.converter import ConvertOptions, QualityMode, VideoCodec, convert
from core.ffmpeg_wrapper import FFmpegError, probe


@dataclass
class CompressOptions:
    target_size_mb: float = 10.0
    video_codec: VideoCodec = VideoCodec.H264
    preserve_metadata: bool = False


def calculate_bitrate(input_path: str, target_size_mb: float, audio_bitrate_kbps: int = 128) -> str:
    info = probe(input_path)
    if info.duration <= 0:
        raise FFmpegError("Could not determine duration for bitrate calculation")
    target_bits = target_size_mb * 1024 * 1024 * 8
    audio_bits = audio_bitrate_kbps * 1000 * info.duration
    video_bps = max((target_bits - audio_bits) / info.duration, 100_000)
    return f"{int(video_bps)}"



def compress_to_size(
    input_path: str,
    output_path: str,
    opts: CompressOptions | None = None,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    opts = opts or CompressOptions()
    bitrate = calculate_bitrate(input_path, opts.target_size_mb)
    convert_opts = ConvertOptions(
        output_format=Path(output_path).suffix.lstrip(".") or "mp4",
        video_codec=opts.video_codec,
        quality_mode=QualityMode.BITRATE,
        target_bitrate=bitrate,
        preserve_metadata=opts.preserve_metadata,
    )
    return convert(
        input_path,
        output_path,
        convert_opts,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
