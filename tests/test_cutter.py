"""Tests for cutter."""

from pathlib import Path

from core.cutter import CutMode, CutOptions, CutRange, build_cut_args, cut, split_equal


def test_build_cut_args_fast(sample_video, tmp_path):
    out = tmp_path / "cut.mp4"
    args = build_cut_args(str(sample_video), str(out), "00:00:00.500", "00:00:01.500", CutMode.FAST)
    assert "-c" in args
    assert "copy" in args


def test_cut_precise(sample_video, tmp_path):
    out = tmp_path / "cut.mp4"
    opts = CutOptions(start="00:00:00.250", end="00:00:01.750", mode=CutMode.PRECISE)
    result = cut(str(sample_video), str(out), opts)
    assert Path(result).exists()


def test_split_equal(sample_video, tmp_path):
    outputs = split_equal(str(sample_video), str(tmp_path), segments=2, mode=CutMode.FAST)
    assert len(outputs) == 2
    for p in outputs:
        assert Path(p).exists()
