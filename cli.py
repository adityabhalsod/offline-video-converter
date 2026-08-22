"""CLI entry point with argparse subcommands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.advanced.compressor import CompressOptions, compress_to_size
from core.advanced.filters import FilterOptions, FilterType, apply_filter
from core.advanced.merger import MergeOptions, merge_videos
from core.advanced.metadata import MetadataOptions, edit_metadata
from core.advanced.silence_trim import SilenceTrimOptions, trim_silence
from core.advanced.speed import SpeedOptions, change_speed
from core.advanced.subtitles import SubtitleMode, SubtitleOptions, apply_subtitles
from core.advanced.thumbnails import PreviewGifOptions, ThumbnailOptions, extract_thumbnail, generate_preview_gif
from core.advanced.watermark import Position, WatermarkOptions, apply_watermark
from core.audio_extractor import AudioBitrate, AudioFormat, ExtractOptions, extract_audio
from core.batch import batch_convert_folder
from core.converter import ConvertOptions, QualityMode, VideoCodec, convert
from core.cutter import CutMode, CutOptions, CutRange, cut, multi_cut, split_by_max_duration, split_equal
from core.ffmpeg_wrapper import cli_exit_if_missing_ffmpeg


def _add_convert(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("convert", help="Convert video format")
    p.add_argument("input", help="Input video path")
    p.add_argument("output", help="Output video path")
    p.add_argument("--codec", choices=[c.value for c in VideoCodec], default="h264")
    p.add_argument("--crf", type=int, default=23)
    p.add_argument("--bitrate", default="5M")
    p.add_argument("--quality-mode", choices=["crf", "bitrate"], default="crf")
    p.add_argument("--strip-metadata", action="store_true")
    p.add_argument("--hw-accel", action="store_true")


def _add_cut(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("cut", help="Cut/trim video")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--start", default="00:00:00.000")
    p.add_argument("--end", default=None)
    p.add_argument("--mode", choices=["fast", "precise"], default="fast")


def _add_extract(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("extract-audio", help="Extract audio from video")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--format", choices=[f.value for f in AudioFormat], default="mp3")
    p.add_argument("--bitrate", choices=[b.value for b in AudioBitrate], default="192k")
    p.add_argument("--channels", type=int, choices=[1, 2], default=2)
    p.add_argument("--normalize", action="store_true")


def _add_compress(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("compress", help="Compress to target file size")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--target-mb", type=float, default=10.0)


def _add_merge(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("merge", help="Merge multiple videos")
    p.add_argument("inputs", nargs="+")
    p.add_argument("output")
    p.add_argument("--mode", choices=["fast", "reencode"], default="fast")


def _add_watermark(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("watermark", help="Apply watermark")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--image", default=None)
    p.add_argument("--text", default=None)
    p.add_argument("--position", choices=[p.value for p in Position], default="bottom_right")


def _add_batch(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("batch", help="Batch convert folder")
    p.add_argument("folder")
    p.add_argument("output_dir")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--format", default="mp4")


def _add_speed(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("speed", help="Change playback speed")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--factor", type=float, default=1.0)


def _add_thumbnail(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("thumbnail", help="Extract thumbnail frame")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--time", default="00:00:01.000")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="offline-video-converter", description="Offline Video Converter CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_convert(sub)
    _add_cut(sub)
    _add_extract(sub)
    _add_compress(sub)
    _add_merge(sub)
    _add_watermark(sub)
    _add_batch(sub)
    _add_speed(sub)
    _add_thumbnail(sub)
    return parser


def dispatch(args: argparse.Namespace) -> int:
    cmd = args.command

    if cmd == "convert":
        opts = ConvertOptions(
            output_format=Path(args.output).suffix.lstrip(".") or "mp4",
            video_codec=VideoCodec(args.codec),
            quality_mode=QualityMode(args.quality_mode),
            crf=args.crf,
            target_bitrate=args.bitrate,
            preserve_metadata=not args.strip_metadata,
            use_hw_accel=args.hw_accel,
        )
        convert(args.input, args.output, opts)
        print(f"Saved: {args.output}")

    elif cmd == "cut":
        opts = CutOptions(start=args.start, end=args.end, mode=CutMode(args.mode))
        cut(args.input, args.output, opts)
        print(f"Saved: {args.output}")

    elif cmd == "extract-audio":
        opts = ExtractOptions(
            format=AudioFormat(args.format),
            bitrate=AudioBitrate(args.bitrate),
            channels=args.channels,
            normalize_loudness=args.normalize,
        )
        extract_audio(args.input, args.output, opts)
        print(f"Saved: {args.output}")

    elif cmd == "compress":
        compress_to_size(args.input, args.output, CompressOptions(target_size_mb=args.target_mb))
        print(f"Saved: {args.output}")

    elif cmd == "merge":
        merge_videos(args.inputs, args.output, MergeOptions(mode=args.mode))
        print(f"Saved: {args.output}")

    elif cmd == "watermark":
        apply_watermark(
            args.input,
            args.output,
            WatermarkOptions(image_path=args.image, text=args.text, position=Position(args.position)),
        )
        print(f"Saved: {args.output}")

    elif cmd == "batch":
        opts = ConvertOptions(output_format=args.format)
        queue = batch_convert_folder(args.folder, args.output_dir, opts, max_workers=args.workers)
        queue.shutdown()
        print(f"Batch complete: {args.output_dir}")

    elif cmd == "speed":
        change_speed(args.input, args.output, SpeedOptions(factor=args.factor))
        print(f"Saved: {args.output}")

    elif cmd == "thumbnail":
        extract_thumbnail(args.input, args.output, ThumbnailOptions(timestamp=args.time))
        print(f"Saved: {args.output}")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    cli_exit_if_missing_ffmpeg()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return dispatch(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
