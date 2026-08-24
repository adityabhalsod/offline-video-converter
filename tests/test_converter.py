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


def test_convert_h265_hw_accel_succeeds(sample_video, tmp_path):
    """HW accel must use a working encoder (or CPU fallback), not a listed-but-unusable one."""
    out = tmp_path / "out.mp4"
    opts = ConvertOptions(
        output_format="mp4",
        video_codec=VideoCodec.H265,
        crf=28,
        use_hw_accel=True,
    )
    result = convert(str(sample_video), str(out), opts)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_build_convert_args_hw_encoder_matches_codec_and_quality(sample_video, tmp_path):
    out = tmp_path / "out.mkv"
    opts = ConvertOptions(
        video_codec=VideoCodec.H265,
        use_hw_accel=True,
        hw_encoder="hevc_qsv",
        crf=23,
    )
    args = build_convert_args(str(sample_video), str(out), opts)
    assert "hevc_qsv" in args
    assert "h264_nvenc" not in args
    assert "-crf" not in args
    assert "-global_quality" in args
    assert "23" in args


def test_build_convert_args_nvenc_uses_cq(sample_video, tmp_path):
    out = tmp_path / "out.mp4"
    opts = ConvertOptions(
        video_codec=VideoCodec.H264,
        use_hw_accel=True,
        hw_encoder="h264_nvenc",
        crf=23,
    )
    args = build_convert_args(str(sample_video), str(out), opts)
    assert "h264_nvenc" in args
    assert "-crf" not in args
    assert "-cq" in args
