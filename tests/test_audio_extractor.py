"""Tests for audio_extractor."""

from pathlib import Path

from core.audio_extractor import AudioFormat, ExtractOptions, build_extract_args, extract_audio


def test_build_extract_args(sample_video, tmp_path):
    out = tmp_path / "out.mp3"
    opts = ExtractOptions(format=AudioFormat.MP3)
    args = build_extract_args(str(sample_video), str(out), opts)
    assert "-vn" in args
    assert str(out) in args


def test_extract_mp3(sample_video, tmp_path):
    out = tmp_path / "out.mp3"
    opts = ExtractOptions(format=AudioFormat.MP3)
    result = extract_audio(str(sample_video), str(out), opts)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0
