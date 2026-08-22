"""Tests for ffmpeg_wrapper."""

import pytest

from core.ffmpeg_wrapper import (
    check_ffmpeg,
    format_timestamp,
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
