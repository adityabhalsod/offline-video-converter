# Offline Video Converter / Cutter / Audio Extractor — Build Prompt

🎯 **Target:** Cursor / GitHub Copilot (Agent / Composer mode), Python project
💡 Structured as a scoped multi-file build spec with explicit phases, file boundaries, and stop conditions — so the agent scaffolds the whole app correctly without drifting or hallucinating extra scope.

**How to use:** Open the project folder in Cursor (or a repo with Copilot Agent enabled), open Composer/Agent chat, and paste everything below the line into it.

---

## PROMPT START

### Role
You are a senior Python engineer specializing in desktop media tools and FFmpeg pipelines. You write production-quality, modular, well-typed Python. You prioritize correctness and working code over cleverness.

### Objective
Build a complete, working, cross-platform **desktop video toolkit** in Python called **Offline Video Converter** with three core capabilities — **video format conversion, video cutting/trimming, and video-to-audio extraction** — plus the advanced features listed below. The app must run both as a **GUI application** and as a **CLI tool** from the same codebase.

### Engineering Principles (apply throughout — non-negotiable)

**KISS (Keep It Simple, Stupid)**
- Prefer the simplest solution that works. No premature abstractions, no over-engineered patterns, no "future-proof" layers that aren't needed yet.
- One function should do one obvious thing. If a module is hard to explain in one sentence, split it.

**SOLID**
- **S — Single Responsibility:** Each module/class owns one concern (e.g. `ffmpeg_wrapper.py` runs FFmpeg; `converter.py` builds convert args; GUI only renders and dispatches).
- **O — Open/Closed:** Extend behavior via new modules or presets (e.g. `presets/platform_presets.json`), not by editing core logic for every new format.
- **L — Liskov Substitution:** Job handlers and worker interfaces must be interchangeable — any `core/` operation callable from CLI must work identically when invoked from the GUI.
- **I — Interface Segregation:** Keep function signatures small and focused. Don't force callers to pass unused parameters or depend on bloated config objects.
- **D — Dependency Inversion:** GUI and CLI depend on `core/` abstractions (pure functions / dataclass job models), not on FFmpeg subprocess details. `core/` must not import from `gui/`.

**DRY (Don't Repeat Yourself)**
- GUI and CLI share the same `core/` functions — never duplicate conversion, cutting, or extraction logic.
- Reuse `ffmpeg_wrapper.py` for all subprocess execution, progress parsing, and ffprobe calls.

**YAGNI (You Aren't Gonna Need It)**
- Only implement what's in the Feature Spec. Do not add plugins, cloud sync, licensing, or other scope not listed here.
- If something seems useful but isn't specified, name it and ask — don't silently add it.

**Other habits**
- Explicit over implicit: typed parameters, clear return values, no hidden global state.
- Fail fast with readable errors — never raw tracebacks in the GUI.
- Test behavior that matters; skip trivial "does import work" tests.

### Tech Stack (hard constraints — do not substitute)
- Python 3.11+
- **FFmpeg / FFprobe** as the actual processing engine, invoked via `subprocess` (stream stderr for progress). Do **NOT** use `moviepy` — it's slower and adds unnecessary dependency weight for this use case.
- **PySide6** for the GUI (native look, `QMediaPlayer` for preview, drag-and-drop support, threading via `QThread`/`QThreadPool`).
- `argparse` with subcommands for the CLI.
- `dataclasses` (or `pydantic` if already idiomatic) for job/config models.
- `concurrent.futures.ProcessPoolExecutor` or `QThreadPool` for parallel batch jobs.
- Standard `logging` module with a rotating file handler.
- Only add a dependency if it's in the `requirements.txt` you generate — do not silently pull in extras.

### Non-negotiable engine constraint
At startup, verify `ffmpeg` and `ffprobe` are on PATH. If missing, show a clear error (GUI dialog and CLI stderr message) with install instructions per OS — do not crash with a raw traceback.

---

## Feature Spec

### Core Features (MUST — build and fully test these first)

**1. Format Conversion**
- Inputs: mp4, mkv, mov, avi, webm, flv, wmv, ts, m4v
- Outputs: mp4 (H.264/H.265), mkv, mov, avi, webm (VP9), animated GIF
- Codec selector (h264 / h265 / vp9 / copy)
- Quality control via CRF (0–51) *or* explicit target bitrate — user picks one mode
- Toggle: preserve original metadata vs strip it

**2. Cutting / Trimming**
- Cut by start/end timestamp (`HH:MM:SS.mmm`)
- Two cut modes: **fast** (stream copy, snaps to nearest keyframe, near-instant) and **precise** (re-encode, frame-accurate)
- Split one file into N equal-length segments
- Split by max output file size or max duration per chunk
- Support multiple cut ranges from one source in a single job → multiple output files

**3. Video → Audio Extraction**
- Output formats: mp3, wav, flac, aac, ogg, m4a
- Bitrate presets (128/192/256/320 kbps) or lossless passthrough
- Mono/stereo channel selection
- Optional loudness normalization (`loudnorm` filter)

### Advanced Features (SHOULD — build after core is working and tested)
- **Batch processing**: drop a folder, apply one settings profile to every video inside; configurable parallel worker count
- **Job queue**: pause / resume / cancel / retry per job, with a visible queue in the GUI
- **Real-time progress**: parse ffmpeg stderr `time=` output into a % progress bar, per-job and overall-batch
- **Hardware acceleration**: auto-detect and offer NVENC / QSV / VAAPI / VideoToolbox, with automatic CPU (`libx264`) fallback if unavailable
- **Smart compression**: "target file size" mode (back-calculates required bitrate) alongside CRF quality mode
- **Resolution/aspect tools**: resolution presets (4K/1080p/720p/480p), custom WxH, aspect-ratio-aware crop or letterbox pad
- **Speed change**: 0.25x–4x, with correct audio pitch preservation (chain `atempo` filters for factors beyond 2x)
- **Merge/concatenate**: reorderable list of clips; same-codec fast concat, mixed-codec re-encode concat
- **Watermark/overlay**: image (PNG with alpha) or text overlay, position presets, opacity, scale
- **Subtitles**: burn-in from `.srt`/`.ass`, or soft-embed as a selectable subtitle track
- **Silence auto-trim**: detect silence (`silencedetect`) and auto-cut dead air — useful for podcast/vlog cleanup
- **Thumbnails & preview GIFs**: extract a frame at any timestamp; generate a short animated GIF preview from a range
- **Metadata editor**: edit title/artist/album/comment via `-metadata`
- **Filters**: rotate, flip, crop, denoise, basic stabilization
- **Platform export presets**: YouTube 1080p, Instagram Reel (9:16), TikTok, WhatsApp (size-capped), Twitter/X — stored as editable JSON presets, not hardcoded
- **Settings persistence**: remember last-used settings per feature in a JSON config under the user's home directory
- **Operation history / undo last export**
- **GUI extras**: multi-file drag-and-drop zone, before/after preview player, dark/light theme toggle
- **CLI parity**: every GUI feature must also be reachable as a CLI subcommand (`convert`, `cut`, `extract-audio`, `compress`, `merge`, `watermark`, `batch`, etc.)
- **Logging**: rotating log file + readable on-screen error messages (never raw stack traces in the GUI)

---

## Project Structure

**Important:** The workspace root **is** the project root. Create all files directly in the current directory — **do NOT** nest everything inside a subfolder like `offline_video_converter/` or `ultimate_video_toolkit/`. `main.py`, `cli.py`, `core/`, `gui/`, etc. live at the top level of the repo.

Create exactly this layout (add files inside these paths as needed, don't restructure it):

```
./                              # project root — this IS the repo root, not a parent folder
  main.py                       # entry point — launches GUI, or CLI if args are passed
  cli.py                        # argparse subcommands, dispatches to core/
  gui/
    main_window.py              # PySide6 main window, tabs per feature
    widgets/
      drop_zone.py
      job_queue_view.py
      preview_player.py
      settings_panel.py
    theme.py
  core/
    ffmpeg_wrapper.py           # subprocess runner + progress parsing + ffprobe helpers
    converter.py                # format conversion
    cutter.py                   # trim/split/multi-cut
    audio_extractor.py          # video -> audio
    advanced/
      compressor.py
      merger.py
      watermark.py
      subtitles.py
      speed.py
      silence_trim.py
      thumbnails.py
      metadata.py
    job.py                      # Job / JobQueue models
    config.py                   # settings persistence (JSON)
  presets/
    platform_presets.json
  tests/
    test_converter.py
    test_cutter.py
    test_audio_extractor.py
    test_ffmpeg_wrapper.py
  requirements.txt
  README.md
  .gitignore
```

---

## Build Phases
Work through these **in order**. Do not start a phase until the previous one runs and is tested.

1. **Engine core** — `core/ffmpeg_wrapper.py` (subprocess execution, stderr progress parsing, ffprobe metadata/duration lookup, ffmpeg/ffprobe presence check). Add unit tests using a tiny sample video generated with `ffmpeg -f lavfi` (so tests don't need external assets).
2. **Core features + CLI** — implement `converter.py`, `cutter.py`, `audio_extractor.py`, wire them into `cli.py` with subcommands. Confirm all three work end-to-end from the command line on a sample file.
3. **GUI shell** — `main_window.py` with tabs for Convert / Cut / Extract Audio, wired to the same `core/` functions the CLI uses (no logic duplication between GUI and CLI).
4. **Advanced features** — implement each `advanced/` module one at a time, add a GUI tab or panel and a CLI subcommand for each, test each before moving to the next.
5. **Polish** — job queue UI, progress bars, settings persistence, theming, logging, README with setup/usage instructions.

After each phase, output: `✅ Phase N complete — [what was built, how to run/test it]`.

---

## Scope & Constraints
- Only implement what's in the Feature Spec above. If you think something else would be valuable, name it explicitly and ask before adding it — don't silently expand scope.
- **All files belong at the project root** — never create a wrapper subfolder that duplicates the repo layout.
- Do not touch files outside this project root (no edits to parent directories or unrelated sibling folders).
- GUI and CLI must call the **same** `core/` functions — never reimplement conversion/cutting logic separately for each.
- Every `core/` function must accept explicit parameters (no hidden global state) so it's independently testable.
- Handle FFmpeg failures gracefully everywhere: capture stderr, surface a readable message, never let the GUI freeze or crash silently.
- Keep GUI work off the main thread — all ffmpeg calls run in a worker thread/process so the UI stays responsive.
- Follow KISS, SOLID, DRY, and YAGNI on every change — prefer a small, clear diff over a clever refactor.

## Forbidden Actions
- Do NOT create a nested project folder (e.g. `offline_video_converter/main.py`) — put `main.py` at `./main.py`.
- Do NOT use `moviepy`, `imageio-ffmpeg` wrappers, or any GUI-blocking synchronous ffmpeg calls on the main thread.
- Do NOT hardcode absolute file paths.
- Do NOT commit or require any API keys/cloud services — this is a fully local/offline tool.
- Do NOT skip the tests in `tests/` — every core module needs at least one passing test before moving to the next phase.
- Do NOT violate dependency direction: `core/` must never import from `gui/`.

## Stop Conditions
Pause and ask before:
- Adding any dependency not already justified in the Tech Stack section
- Changing the project structure defined above
- Choosing between two materially different architectures for the job queue or threading model

## Definition of Done
- `python main.py` launches the GUI with working Convert / Cut / Extract Audio tabs plus at least three advanced feature tabs.
- `python main.py convert|cut|extract-audio ...` all work from the terminal with `--help` text for each subcommand.
- Batch processing can process a folder of videos in parallel with a visible progress bar.
- `pytest` passes with no failures.
- `README.md` explains: prerequisites (Python + FFmpeg install per OS), `pip install -r requirements.txt`, how to run the GUI, and the full CLI command reference.
- Codebase respects SOLID separation: `core/` is GUI-agnostic and fully reachable from CLI alone.

## PROMPT END

---

### Setup note (do this before pasting the prompt)
Make sure FFmpeg is installed and on PATH first — Cursor/Copilot will assume it's available: `winget install ffmpeg` (Windows), `brew install ffmpeg` (macOS), or `sudo apt install ffmpeg` (Debian/Ubuntu). Open the **Offline Video Converter** project folder in Cursor (the folder that will contain `main.py` at its root — not a parent directory with the app nested inside), and paste the block between **PROMPT START** and **PROMPT END** into Agent/Composer chat.
