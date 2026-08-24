"""FFmpeg subprocess runner, progress parsing, and ffprobe helpers."""

from __future__ import annotations

import json
import logging
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger(__name__)

TIME_RE = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d+)")
DURATION_RE = re.compile(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)")


def stderr_summary(stderr: str, max_lines: int = 16) -> str:
    """Extract the useful tail of ffmpeg stderr, skipping progress lines."""
    if not stderr:
        return ""
    keywords = (
        "error",
        "failed",
        "cannot",
        "invalid",
        "not permitted",
        "unknown encoder",
        "not found",
        "does not support",
        "unrecognized",
        "permission denied",
        "no such file",
    )
    lines = [ln.rstrip() for ln in stderr.splitlines() if ln.strip()]
    interesting = [
        ln
        for ln in lines
        if any(key in ln.lower() for key in keywords)
        and not (ln.lstrip().startswith("frame=") and "time=" in ln)
    ]
    chosen = interesting[-max_lines:] if interesting else lines[-max_lines:]
    return "\n".join(chosen)


def signed_exit_code(code: int | None) -> int:
    """Normalize Windows DWORD exit codes such as 4294967295 to -1."""
    if code is None:
        return -1
    if code > 0x7FFFFFFF:
        return code - 0x100000000
    return code


class FFmpegError(Exception):
    """Raised when ffmpeg/ffprobe fails."""

    def __init__(self, message: str, stderr: str = "") -> None:
        self.stderr = stderr
        super().__init__(message)

    def __str__(self) -> str:
        message = super().__str__()
        summary = stderr_summary(self.stderr)
        if summary and summary not in message:
            return f"{message}\n{summary}"
        return message


@dataclass
class ProbeResult:
    """Metadata returned by ffprobe."""

    duration: float
    width: Optional[int]
    height: Optional[int]
    video_codec: Optional[str]
    audio_codec: Optional[str]
    format_name: Optional[str]
    raw: dict


def get_install_instructions() -> str:
    system = platform.system()
    if system == "Windows":
        return "Install FFmpeg: winget install ffmpeg"
    if system == "Darwin":
        return "Install FFmpeg: brew install ffmpeg"
    return "Install FFmpeg: sudo apt install ffmpeg  (Debian/Ubuntu)"


def check_ffmpeg() -> tuple[bool, str]:
    """Return (ok, message). Message is empty when ok, else install hint or error."""
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        return False, (
            f"Missing on PATH: {', '.join(missing)}.\n{get_install_instructions()}"
        )
    return True, ""


def require_ffmpeg() -> None:
    ok, msg = check_ffmpeg()
    if not ok:
        raise FFmpegError(msg)


def parse_timestamp(value: str) -> float:
    """Parse HH:MM:SS.mmm or SS.mmm into seconds."""
    value = value.strip()
    if not value:
        raise ValueError("Empty timestamp")
    parts = value.split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    raise ValueError(f"Invalid timestamp: {value}")


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm."""
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _hms_to_seconds(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_time_from_stderr(line: str) -> Optional[float]:
    match = TIME_RE.search(line)
    if match:
        return _hms_to_seconds(*match.groups())
    match = DURATION_RE.search(line)
    if match:
        return _hms_to_seconds(*match.groups())
    return None


def probe(path: str) -> ProbeResult:
    require_ffmpeg()
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise FFmpegError("ffprobe failed", exc.stderr or "") from exc

    data = json.loads(result.stdout or "{}")
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    width = height = video_codec = audio_codec = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_codec is None:
            video_codec = stream.get("codec_name")
            width = stream.get("width")
            height = stream.get("height")
        elif stream.get("codec_type") == "audio" and audio_codec is None:
            audio_codec = stream.get("codec_name")
    return ProbeResult(
        duration=duration,
        width=width,
        height=height,
        video_codec=video_codec,
        audio_codec=audio_codec,
        format_name=data.get("format", {}).get("format_name"),
        raw=data,
    )


def build_ffmpeg_cmd(args: list[str]) -> list[str]:
    return ["ffmpeg", "-hide_banner", "-nostdin", "-y", *args]


def run_ffmpeg(
    args: list[str],
    *,
    duration: Optional[float] = None,
    progress_callback: Optional[Callable[[float], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> subprocess.CompletedProcess:
    """Run ffmpeg with optional progress reporting via stderr parsing."""
    require_ffmpeg()
    cmd = build_ffmpeg_cmd(args)
    logger.debug("Running: %s", " ".join(cmd))

    popen_kwargs: dict = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "stdin": subprocess.DEVNULL,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "bufsize": 1,
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    process = subprocess.Popen(cmd, **popen_kwargs)
    stderr_lines: list[str] = []
    assert process.stderr is not None

    for line in process.stderr:
        stderr_lines.append(line)
        if cancel_check and cancel_check():
            process.kill()
            process.wait()
            raise FFmpegError("Operation cancelled", "".join(stderr_lines))

        if progress_callback and duration and duration > 0:
            current = parse_time_from_stderr(line)
            if current is not None:
                progress_callback(min(current / duration, 1.0))

    stdout, _ = process.communicate()
    if stdout:
        stderr_lines.append(stdout)
    stderr = "".join(stderr_lines)

    if process.returncode != 0:
        raise FFmpegError(
            f"ffmpeg failed (exit {signed_exit_code(process.returncode)})",
            stderr,
        )

    if progress_callback:
        progress_callback(1.0)

    return subprocess.CompletedProcess(cmd, process.returncode, "", stderr)


HW_ENCODER_CANDIDATES = {
    "h264": ("h264_nvenc", "h264_amf", "h264_qsv", "h264_vaapi", "h264_videotoolbox"),
    "h265": ("hevc_nvenc", "hevc_amf", "hevc_qsv", "hevc_vaapi", "hevc_videotoolbox"),
    "vp9": ("vp9_qsv", "vp9_vaapi"),
}

_listed_encoders_cache: Optional[set[str]] = None
_usable_encoders_cache: dict[str, bool] = {}


def hw_encoder_candidates(codec: str) -> tuple[str, ...]:
    if codec in ("h265", "hevc"):
        return HW_ENCODER_CANDIDATES["h265"]
    return HW_ENCODER_CANDIDATES.get(codec, HW_ENCODER_CANDIDATES["h264"])


def listed_encoders() -> set[str]:
    global _listed_encoders_cache
    if _listed_encoders_cache is not None:
        return _listed_encoders_cache
    require_ffmpeg()
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    names: set[str] = set()
    for line in (result.stdout or "").splitlines():
        if len(line) < 8 or line[1] not in "VAS" or "." not in line[:8]:
            continue
        parts = line.split()
        if len(parts) >= 2:
            names.add(parts[1])
    _listed_encoders_cache = names
    return names


def is_encoder_usable(name: str) -> bool:
    """Return True if ffmpeg can actually initialize this video encoder."""
    if name in _usable_encoders_cache:
        return _usable_encoders_cache[name]
    require_ffmpeg()
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostdin",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x240:d=0.1",
                "-c:v",
                name,
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            stdin=subprocess.DEVNULL,
        )
        ok = result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        ok = False
    _usable_encoders_cache[name] = ok
    logger.debug("Encoder %s usable=%s", name, ok)
    return ok


def detect_hw_encoder(codec: str = "h264") -> Optional[str]:
    """Return first hardware encoder that is listed AND actually works, or None."""
    available = listed_encoders()
    for name in hw_encoder_candidates(codec):
        if name in available and is_encoder_usable(name):
            return name
    return None


def cli_exit_if_missing_ffmpeg() -> None:
    ok, msg = check_ffmpeg()
    if not ok:
        print(msg, file=sys.stderr)
        sys.exit(1)
