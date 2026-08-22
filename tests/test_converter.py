"""Tests for converter."""

from pathlib import Path

from core.converter import ConvertOptions, QualityMode, VideoCodec, build_convert_args, convert


def test_build_convert_args(sample_video, tmp_path):
    out = tmp_path / "out.mp4"
    opts = ConvertOptions(crf=28, quality_mode=QualityMode.CRF)
    args = build_convert_args(str(sample_video), str(out), opts)
    assert "-i" in args
    assert str(out) in args
    assert "28" in args


def test_convert_to_mp4(sample_video, tmp_path):
    out = tmp_path / "out.mp4"
    opts = ConvertOptions(
        output_format="mp4",
        video_codec=VideoCodec.H264,
        crf=28,
    )
    result = convert(str(sample_video), str(out), opts)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0
