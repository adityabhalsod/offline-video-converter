"""Job queue list view."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.job import Job, JobQueue, JobStatus


class JobQueueView(QWidget):
    cancel_requested = Signal(str)
    pause_requested = Signal(str)
    resume_requested = Signal(str)
    retry_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.overall_bar = QProgressBar()
        self.overall_bar.setFormat("Overall: %p%")
        layout.addWidget(self.overall_bar)
        self._job_widgets: dict[str, tuple[QListWidgetItem, QProgressBar]] = {}

    def bind_queue(self, queue: JobQueue) -> None:
        queue.add_listener(self._on_job_update)

    def _on_job_update(self, job: Job) -> None:
        if job.id not in self._job_widgets:
            item = QListWidgetItem()
            self.list.addItem(item)
            widget = QWidget()
            vlay = QVBoxLayout(widget)
            title = QLabel(f"{job.name} [{job.operation}]")
            bar = QProgressBar()
            bar.setFormat(f"%p% - {job.status.value}")
            btn_row = QHBoxLayout()
            cancel_btn = QPushButton("Cancel")
            pause_btn = QPushButton("Pause")
            resume_btn = QPushButton("Resume")
            retry_btn = QPushButton("Retry")
            cancel_btn.clicked.connect(lambda: self.cancel_requested.emit(job.id))
            pause_btn.clicked.connect(lambda: self.pause_requested.emit(job.id))
            resume_btn.clicked.connect(lambda: self.resume_requested.emit(job.id))
            retry_btn.clicked.connect(lambda: self.retry_requested.emit(job.id))
            btn_row.addWidget(cancel_btn)
            btn_row.addWidget(pause_btn)
            btn_row.addWidget(resume_btn)
            btn_row.addWidget(retry_btn)
            vlay.addWidget(title)
            vlay.addWidget(bar)
            vlay.addLayout(btn_row)
            item.setSizeHint(widget.sizeHint())
            self.list.setItemWidget(item, widget)
            self._job_widgets[job.id] = (item, bar)

        _, bar = self._job_widgets[job.id]
        bar.setValue(int(job.progress * 100))
        bar.setFormat(f"{int(job.progress * 100)}% - {job.status.value}")
        if job.error:
            bar.setFormat(f"Failed: {job.error[:60]}")

    def set_overall_progress(self, value: float) -> None:
        self.overall_bar.setValue(int(value * 100))
