"""Drag-and-drop file zone widget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".ts", ".m4v"}


class DropZone(QWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        self.label = QLabel("Drag & drop video files here\n(or click Browse)")
        self.label.setObjectName("dropZone")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: list[str] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                paths.append(str(path.resolve()))
            elif path.is_dir():
                for f in sorted(path.iterdir()):
                    if f.suffix.lower() in VIDEO_EXTENSIONS:
                        paths.append(str(f.resolve()))
        if paths:
            self.files_dropped.emit(paths)
            self.label.setText(f"{len(paths)} file(s) selected")
        event.acceptProposedAction()

    def set_files(self, paths: list[str]) -> None:
        if paths:
            self.label.setText(f"{len(paths)} file(s) selected")
        else:
            self.label.setText("Drag & drop video files here\n(or click Browse)")
