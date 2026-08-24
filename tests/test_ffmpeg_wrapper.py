"""Tests for ffmpeg_wrapper."""

import pytest

from core.ffmpeg_wrapper import (
    FFmpegError,
    build_ffmpeg_cmd,
    check_ffmpeg,
    detect_hw_encoder,
    format_timestamp,
    hw_encoder_candidates,
    parse_time_from_stderr,
    parse_timestamp,
    probe,
)


def test_check_ffmpeg():
    ok, msg = check_ffmpeg()
    assert ok, msg


def test_parse_timestamp():
    assert parse_timestamp("00:00:01.500") == pytest.approx(1.5)
    assert parse_timestamp("01:30") == pytest.approx(90.0)


def test_format_timestamp():
    assert format_timestamp(3661.25) == "01:01:01.250"


def test_parse_time_from_stderr():
    line = "frame=  100 fps= 30 q=28.0 size=    1024kB time=00:00:01.50 bitrate= 5000kbits/s"
    assert parse_time_from_stderr(line) == pytest.approx(1.5)


def test_probe(sample_video):
    info = probe(str(sample_video))
    assert info.duration > 0
    assert info.width == 320
    assert info.height == 240


def test_ffmpeg_error_includes_stderr():
    err = FFmpegError("ffmpeg failed (exit 4294967295)", "Cannot load nvcuda.dll\nConversion failed!\n")
    text = str(err)
    assert "Cannot load nvcuda.dll" in text
    assert "ffmpeg failed" in text


def test_build_ffmpeg_cmd_disables_stdin():
    cmd = build_ffmpeg_cmd(["-i", "in.mkv", "out.mp4"])
    assert cmd[:4] == ["ffmpeg", "-hide_banner", "-nostdin", "-y"]


def test_hw_encoder_candidates_match_codec():
    h264 = hw_encoder_candidates("h264")
    h265 = hw_encoder_candidates("h265")
    assert "h264_nvenc" in h264
    assert "h264_amf" in h264
    assert "h264_qsv" in h264
    assert "hevc_nvenc" in h265
    assert "hevc_qsv" in h265
    assert "h264_nvenc" not in h265


def test_detect_hw_encoder_returns_only_listed_candidate():
    encoder = detect_hw_encoder("h264")
    if encoder is None:
        return
    assert encoder in hw_encoder_candidates("h264")


def test_detect_hw_encoder_h265_is_hevc_family_or_none():
    encoder = detect_hw_encoder("h265")
    if encoder is None:
        return
    assert encoder in hw_encoder_candidates("h265")
