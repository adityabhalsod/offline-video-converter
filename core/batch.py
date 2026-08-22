"""Batch processing for folders of videos."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.converter import ConvertOptions, convert
from core.job import Job, JobQueue


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".ts", ".m4v"}


def list_videos(folder: str) -> list[str]:
    path = Path(folder)
    if not path.is_dir():
        raise FileNotFoundError(f"Not a directory: {folder}")
    return sorted(
        str(p.resolve())
        for p in path.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )


def batch_convert_folder(
    folder: str,
    output_dir: str,
    opts: ConvertOptions,
    *,
    max_workers: int = 2,
    progress_callback: Callable[[Job], None] | None = None,
) -> JobQueue:
    videos = list_videos(folder)
    queue = JobQueue(max_workers=max_workers)
    if progress_callback:
        queue.add_listener(progress_callback)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    def _worker(job: Job) -> None:
        inp = job.params["input"]
        dest = out / f"{Path(inp).stem}.{opts.output_format}"

        def _prog(p: float) -> None:
            job.progress = p
            if progress_callback:
                progress_callback(job)

        job.output_path = convert(
            inp,
            str(dest),
            opts,
            progress_callback=_prog,
            cancel_check=job.is_cancelled,
        )

    for video in videos:
        job = Job(name=Path(video).name, operation="convert", params={"input": video})
        queue.add_job(job, _worker)

    return queue
