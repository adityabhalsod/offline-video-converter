"""Reusable settings panel helpers."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QFrame, QLabel, QVBoxLayout, QWidget


def make_form() -> QFormLayout:
    form = QFormLayout()
    form.setSpacing(8)
    form.setContentsMargins(0, 0, 0, 0)
    form.setHorizontalSpacing(10)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    return form


class SettingsGroup(QFrame):
    """Bordered settings block with an in-box title tile and compact form rows."""

    def __init__(self, title: str, form: QFormLayout, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsGroup")
        self.setFrameShape(QFrame.Shape.NoFrame)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title_label = QLabel(title)
        title_label.setObjectName("settingsGroupTitle")
        outer.addWidget(title_label)

        body = QWidget()
        body.setObjectName("settingsGroupBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 10)
        body_layout.setSpacing(0)
        body_layout.addLayout(form)
        outer.addWidget(body)


class SettingsPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.form = make_form()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.form)

    def add_row(self, label: str, widget) -> None:
        self.form.addRow(label, widget)
