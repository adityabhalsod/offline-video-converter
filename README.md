# Offline Video Converter

A cross-platform desktop video toolkit in Python with **format conversion**, **cutting/trimming**, and **video-to-audio extraction**, plus batch processing, compression, merge, watermark, and speed change.

Runs as a **GUI** (PySide6) or **CLI** from the same codebase.

## Prerequisites

- Python 3.11+ (GUI requires 3.11-3.13 until PySide6 supports 3.14)
- FFmpeg and FFprobe on your PATH

### Install FFmpeg

| OS | Command |
|----|---------|
| Windows | `winget install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Debian/Ubuntu | `sudo apt install ffmpeg` |

## Setup

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Run GUI

```bash
python main.py
```

## CLI Usage

```bash
# Convert
python main.py convert input.mp4 output.webm --codec vp9 --crf 30

# Cut (fast stream copy or precise re-encode)
python main.py cut input.mp4 clip.mp4 --start 00:00:05.000 --end 00:00:15.000 --mode fast

# Extract audio
python main.py extract-audio input.mp4 output.mp3 --format mp3 --bitrate 192k

# Compress to target size
python main.py compress input.mp4 small.mp4 --target-mb 10

# Merge videos
python main.py merge part1.mp4 part2.mp4 merged.mp4 --mode fast

# Watermark
python main.py watermark input.mp4 out.mp4 --text "Demo"

# Batch convert folder
python main.py batch ./videos ./output --workers 2 --format mp4

# Speed change
python main.py speed input.mp4 fast.mp4 --factor 1.5

# Thumbnail
python main.py thumbnail input.mp4 thumb.jpg --time 00:00:02.000
```

Use `--help` on any subcommand for options.

## Releases

Releases are published by hand from GitHub Actions:

1. Open the **Actions** tab, pick the **Release** workflow, and click **Run workflow**.
2. Enter a version such as `1.0.0` (or `1.1.0-beta.1`), and optionally tick pre-release or draft.
3. The workflow runs the tests, builds the app for Windows, macOS and Linux with PyInstaller, tags the commit `v<version>`, and publishes a GitHub Release with the builds and a `SHA256SUMS.txt` attached.

Release files:

| File | What it is |
|------|------------|
| `...-windows-x64-setup.exe` | Windows installer (Start menu and optional desktop shortcut, uninstaller). FFmpeg included. |
| `...-windows-x64-portable.zip` | Windows, no install: extract the whole folder, then run `OfflineVideoConverter.exe`. FFmpeg included. |
| `...-macos-arm64.zip` | macOS app bundle. Needs FFmpeg (`brew install ffmpeg`). |
| `...-linux-x64.tar.gz` | Linux build. Needs FFmpeg (`sudo apt install ffmpeg`). |

The Windows builds ship a GPL build of FFmpeg from [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds); its license is in `ffmpeg/FFMPEG-LICENSE.txt`.
`python main.py --version` prints the version (`0.0.0-dev` when running from source).

## Tests

```bash
pytest
```

Tests generate a tiny sample video with FFmpeg lavfi - no external assets required.

## Project Layout

```
main.py              # GUI or CLI entry
cli.py               # argparse subcommands
core/                # GUI-agnostic processing
gui/                 # PySide6 UI
presets/             # Platform export presets (JSON)
tests/
```

## Settings

User settings and operation history are stored under `~/.offline-video-converter/`.

Logs rotate at `~/.offline-video-converter/app.log`.

## License

See LICENSE.
