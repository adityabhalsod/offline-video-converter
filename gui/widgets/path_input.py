"""Inline path field with an integrated browse button."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QStyle,
    QToolButton,
    QWidget,
)

class PathInput(QFrame):
    """Single-line path editor with a browse icon on the right."""

    def __init__(
        self,
        mode: str = "open",
        dialog_title: str = "Select file",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self._dialog_title = dialog_title
        self._default_path_provider: Callable[[], str] | None = None
        self.setObjectName("pathInput")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.line_edit = QLineEdit()
        self.line_edit.setObjectName("pathInputField")
        self.line_edit.setPlaceholderText("Choose a file…")

        self.browse_btn = QToolButton()
        self.browse_btn.setObjectName("pathInputBrowse")
        self.browse_btn.setAutoRaise(False)
        self.browse_btn.setToolTip("Browse")
        self._set_browse_icon()
        self.browse_btn.clicked.connect(self._browse)

        layout.addWidget(self.line_edit, 1)
        layout.addWidget(self.browse_btn)

    def _set_browse_icon(self) -> None:
        style = QApplication.style()
        if self._mode == "save":
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        elif self._mode == "dir":
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        else:
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        self.browse_btn.setIcon(icon)

    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, text: str) -> None:
        self.line_edit.setText(text)

    def setPlaceholderText(self, text: str) -> None:
        self.line_edit.setPlaceholderText(text)

    def set_default_path_provider(self, provider: Callable[[], str] | None) -> None:
        """Optional callback used when the field is empty to seed the browse dialog."""
        self._default_path_provider = provider

    def _browse_start_path(self) -> str:
        current = self.line_edit.text().strip()
        if current:
            return current
        if self._default_path_provider is not None:
            return self._default_path_provider().strip()
        return ""

    def _browse(self) -> None:
        start_path = self._browse_start_path()
        if self._mode == "save":
            path, _ = QFileDialog.getSaveFileName(self, self._dialog_title, start_path)
        elif self._mode == "dir":
            path = QFileDialog.getExistingDirectory(self, self._dialog_title, start_path)
        else:
            path, _ = QFileDialog.getOpenFileName(self, self._dialog_title, start_path)
        if path:
            self.line_edit.setText(path)
