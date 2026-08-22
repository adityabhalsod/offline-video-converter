"""Shared test fixtures."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.ffmpeg_wrapper import check_ffmpeg


@pytest.fixture(scope="session")
def sample_video(tmp_path_factory) -> Path:
    ok, _ = check_ffmpeg()
    if not ok:
        pytest.skip("ffmpeg not available")
    out = tmp_path_factory.mktemp("media") / "sample.mp4"
    if not out.exists():
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc=duration=2:size=320x240:rate=30",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=2",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-shortest",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
    return out
