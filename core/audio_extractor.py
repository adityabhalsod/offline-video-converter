"""Video to audio extraction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.ffmpeg_wrapper import FFmpegError, probe, run_ffmpeg


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    AAC = "aac"
    OGG = "ogg"
    M4A = "m4a"


class AudioBitrate(str, Enum):
    KBPS_128 = "128k"
    KBPS_192 = "192k"
    KBPS_256 = "256k"
    KBPS_320 = "320k"
    LOSSLESS = "lossless"


@dataclass
class ExtractOptions:
    format: AudioFormat = AudioFormat.MP3
    bitrate: AudioBitrate = AudioBitrate.KBPS_192
    channels: int = 2
    normalize_loudness: bool = False


CODEC_MAP = {
    AudioFormat.MP3: ("libmp3lame", "mp3"),
    AudioFormat.WAV: ("pcm_s16le", "wav"),
    AudioFormat.FLAC: ("flac", "flac"),
    AudioFormat.AAC: ("aac", "aac"),
    AudioFormat.OGG: ("libvorbis", "ogg"),
    AudioFormat.M4A: ("aac", "m4a"),
}


def build_extract_args(input_path: str, output_path: str, opts: ExtractOptions) -> list[str]:
    codec, _ = CODEC_MAP[opts.format]
    args = ["-i", input_path, "-vn"]

    if opts.normalize_loudness:
        args.extend(["-af", "loudnorm"])

    layout = "mono" if opts.channels == 1 else "stereo"
    args.extend(["-ac", str(opts.channels), "-channel_layout", layout])

    if opts.bitrate == AudioBitrate.LOSSLESS and opts.format in (
        AudioFormat.WAV,
        AudioFormat.FLAC,
    ):
        args.extend(["-c:a", codec])
    elif opts.format == AudioFormat.MP3:
        br = opts.bitrate.value if opts.bitrate != AudioBitrate.LOSSLESS else "320k"
        args.extend(["-c:a", codec, "-b:a", br])
    elif opts.format in (AudioFormat.AAC, AudioFormat.M4A):
        br = opts.bitrate.value if opts.bitrate != AudioBitrate.LOSSLESS else "256k"
        args.extend(["-c:a", codec, "-b:a", br])
    else:
        args.extend(["-c:a", codec])

    args.append(output_path)
    return args


def extract_audio(
    input_path: str,
    output_path: str,
    opts: ExtractOptions | None = None,
    *,
    progress_callback=None,
    cancel_check=None,
) -> str:
    opts = opts or ExtractOptions()
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    info = probe(input_path)
    if info.duration <= 0:
        raise FFmpegError("Could not determine input duration")

    args = build_extract_args(input_path, output_path, opts)
    run_ffmpeg(
        args,
        duration=info.duration,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
    )
    return output_path
