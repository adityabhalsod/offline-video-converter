"""Reusable settings panel helpers."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QWidget


class SettingsPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.form = QFormLayout(self)

    def add_row(self, label: str, widget) -> None:
        self.form.addRow(label, widget)
