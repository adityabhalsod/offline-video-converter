"""Job and job queue models."""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    operation: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    error: str = ""
    output_path: str = ""
    _cancel_requested: bool = field(default=False, repr=False)
    _pause_event: threading.Event = field(default_factory=threading.Event, repr=False)

    def __post_init__(self) -> None:
        self._pause_event.set()

    def request_cancel(self) -> None:
        self._cancel_requested = True
        self._pause_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_requested

    def pause(self) -> None:
        if self.status == JobStatus.RUNNING:
            self.status = JobStatus.PAUSED
            self._pause_event.clear()

    def resume(self) -> None:
        if self.status == JobStatus.PAUSED:
            self.status = JobStatus.RUNNING
            self._pause_event.set()

    def wait_if_paused(self) -> None:
        self._pause_event.wait()


class JobQueue:
    """Thread-safe job queue with parallel execution."""

    def __init__(self, max_workers: int = 2, use_processes: bool = False) -> None:
        self._jobs: list[Job] = []
        self._lock = threading.Lock()
        self._max_workers = max(1, max_workers)
        self._executor: ThreadPoolExecutor | ProcessPoolExecutor
        if use_processes:
            self._executor = ProcessPoolExecutor(max_workers=self._max_workers)
        else:
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._futures: dict[str, Future] = {}
        self._listeners: list[Callable[[Job], None]] = []

    def add_listener(self, callback: Callable[[Job], None]) -> None:
        self._listeners.append(callback)

    def _notify(self, job: Job) -> None:
        for cb in self._listeners:
            try:
                cb(job)
            except Exception:
                pass

    @property
    def jobs(self) -> list[Job]:
        with self._lock:
            return list(self._jobs)

    def add_job(self, job: Job, worker: Callable[[Job], None]) -> None:
        with self._lock:
            self._jobs.append(job)

        def _run() -> None:
            job.status = JobStatus.RUNNING
            self._notify(job)
            try:
                worker(job)
                if job.is_cancelled():
                    job.status = JobStatus.CANCELLED
                elif job.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
                    job.status = JobStatus.COMPLETED
                    job.progress = 1.0
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.error = str(exc)
            finally:
                self._notify(job)

        future = self._executor.submit(_run)
        self._futures[job.id] = future

    def cancel_job(self, job_id: str) -> None:
        with self._lock:
            for job in self._jobs:
                if job.id == job_id:
                    job.request_cancel()
                    break

    def pause_job(self, job_id: str) -> None:
        with self._lock:
            for job in self._jobs:
                if job.id == job_id:
                    job.pause()
                    break

    def resume_job(self, job_id: str) -> None:
        with self._lock:
            for job in self._jobs:
                if job.id == job_id:
                    job.resume()
                    break

    def retry_job(self, job_id: str, worker: Callable[[Job], None]) -> None:
        with self._lock:
            for job in self._jobs:
                if job.id == job_id and job.status in (
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                ):
                    job.status = JobStatus.PENDING
                    job.progress = 0.0
                    job.error = ""
                    job._cancel_requested = False
                    job._pause_event.set()
                    self.add_job(job, worker)
                    break

    def overall_progress(self) -> float:
        with self._lock:
            if not self._jobs:
                return 0.0
            return sum(j.progress for j in self._jobs) / len(self._jobs)

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=not wait)
