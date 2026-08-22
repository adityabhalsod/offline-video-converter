"""Light and dark theme styles for PySide6."""

LIGHT_THEME = """
QMainWindow, QWidget { background: #f5f5f5; color: #1a1a1a; }
QTabWidget::pane { border: 1px solid #ccc; background: #fff; }
QPushButton { background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 4px; }
QPushButton:hover { background: #1d4ed8; }
QPushButton:disabled { background: #94a3b8; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px; border: 1px solid #ccc; border-radius: 4px; background: white; }
QProgressBar { border: 1px solid #ccc; border-radius: 4px; text-align: center; }
QProgressBar::chunk { background: #2563eb; }
QGroupBox { font-weight: bold; margin-top: 8px; }
"""

DARK_THEME = """
QMainWindow, QWidget { background: #1e1e2e; color: #cdd6f4; }
QTabWidget::pane { border: 1px solid #45475a; background: #313244; }
QPushButton { background: #89b4fa; color: #1e1e2e; border: none; padding: 8px 16px; border-radius: 4px; }
QPushButton:hover { background: #b4befe; }
QPushButton:disabled { background: #585b70; color: #a6adc8; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px; border: 1px solid #45475a; border-radius: 4px; background: #313244; color: #cdd6f4; }
QProgressBar { border: 1px solid #45475a; border-radius: 4px; text-align: center; }
QProgressBar::chunk { background: #89b4fa; }
QGroupBox { font-weight: bold; margin-top: 8px; }
QLabel#dropZone { border: 2px dashed #585b70; border-radius: 8px; padding: 24px; }
"""
