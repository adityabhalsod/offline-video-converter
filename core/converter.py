"""Format conversion via FFmpeg."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path

from core.ffmpeg_wrapper import FFmpegError, detect_hw_encoder, probe, run_ffmpeg

logger = logging.getLogger(__name__)


class QualityMode(str, Enum):
    CRF = "crf"
    BITRATE = "bitrate"


class VideoCodec(str, Enum):
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    COPY = "copy"


@dataclass
class ConvertOptions:
    output_format: str = "mp4"
    video_codec: VideoCodec = VideoCodec.H264
    quality_mode: QualityMode = QualityMode.CRF
    crf: int = 23
    target_bitrate: str = "5M"
    preserve_metadata: bool = True
    use_hw_accel: bool = False
    width: int | None = None
    height: int | None = None
    hw_encoder: str | None = None


CODEC_MAP = {
    VideoCodec.H264: "libx264",
    VideoCodec.H265: "libx265",
    VideoCodec.VP9: "libvpx-vp9",
}

_HW_ENCODER_SUFFIXES = ("_nvenc", "_qsv", "_amf", "_vaapi", "_videotoolbox")


def _is_hardware_encoder(name: str) -> bool:
    return name.endswith(_HW_ENCODER_SUFFIXES)


def _video_encoder(opts: ConvertOptions) -> str:
    if opts.video_codec == VideoCodec.COPY:
        return "copy"
    software = CODEC_MAP[opts.video_codec]
    if not opts.use_hw_accel:
        return software
    if opts.hw_encoder:
        return opts.hw_encoder
    return detect_hw_encoder(opts.video_codec.value) or software


def _quality_args(encoder: str, opts: ConvertOptions) -> list[str]:
    if opts.quality_mode == QualityMode.BITRATE:
        return ["-b:v", opts.target_bitrate]
    if encoder.endswith("_nvenc"):
        return ["-rc", "vbr", "-cq", str(opts.crf)]
    if encoder.endswith("_qsv"):
        return ["-global_quality", str(opts.crf)]
    if encoder.endswith("_amf"):
        return ["-rc", "cqp", "-qp_i", str(opts.crf), "-qp_p", str(opts.crf)]
    if encoder.endswith("_videotoolbox"):
        quality = max(1, min(100, round((51 - opts.crf) * 100 / 51)))
        return ["-q:v", str(int(quality))]
    return ["-crf", str(opts.crf)]


def build_convert_args(input_path: str, output_path: str, opts: ConvertOptions) -> list[str]:
    args = ["-i", input_path]
    ext = Path(output_path).suffix.lower().lstrip(".")

    if ext == "gif":
        args.extend(["-vf", "fps=10,scale=480:-1:flags=lanczos", "-c:v", "gif"])
        return args + [output_path]

    vcodec = _video_encoder(opts)
    if vcodec == "copy":
        args.extend(["-c:v", "copy", "-c:a", "copy"])
    else:
        args.extend(["-c:v", vcodec])
        args.extend(_quality_args(vcodec, opts))
        args.extend(["-c:a", "aac", "-b:a", "192k"])
        if _is_hardware_encoder(vcodec):
            args.extend(["-pix_fmt", "yuv420p"])

    if opts.width and opts.height:
        args.extend(["-vf", f"scale={opts.width}:{opts.height}"])

    if not opts.preserve_metadata:
        args.append("-map_metadata")
        args.append("-1")

    args.append(output_path)
    return args


def convert(
    input_path: str,
    output_path: str,
    opts: ConvertOptions | None = None,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    opts = opts or ConvertOptions()
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    info = probe(input_path)
    if info.duration <= 0:
        raise FFmpegError("Could not determine input duration")

    encoder = _video_encoder(opts)
    args = build_convert_args(input_path, output_path, opts)
    try:
        run_ffmpeg(
            args,
            duration=info.duration,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )
    except FFmpegError:
        if not _is_hardware_encoder(encoder):
            raise
        logger.warning("Hardware encoder %s failed; retrying with software", encoder)
        fallback = replace(opts, use_hw_accel=False, hw_encoder=None)
        run_ffmpeg(
            build_convert_args(input_path, output_path, fallback),
            duration=info.duration,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )
    return output_path
