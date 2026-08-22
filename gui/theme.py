"""Light and dark theme styles for PySide6."""

_SHARED_GROUPBOX = """
QGroupBox {
    font-weight: bold;
    border-radius: 6px;
    margin-top: 16px;
    padding: 20px 12px 12px 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
}
"""

LIGHT_THEME = f"""
QMainWindow {{
    background: #f3f4f6;
    color: #111827;
}}
QWidget {{
    color: #111827;
}}
QLabel {{
    background: transparent;
    color: #374151;
}}
QTabWidget::pane {{
    border: 1px solid #d1d5db;
    background: #ffffff;
    top: -1px;
    border-radius: 0 0 6px 6px;
    padding: 4px;
}}
QTabBar::tab {{
    background: #e5e7eb;
    color: #4b5563;
    padding: 8px 16px;
    border: 1px solid #d1d5db;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: #ffffff;
    color: #111827;
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background: #d1d5db;
}}
QPushButton {{
    background: #2563eb;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    min-height: 20px;
}}
QPushButton:hover {{ background: #1d4ed8; }}
QPushButton:disabled {{ background: #94a3b8; color: #f8fafc; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    padding: 6px 8px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: #ffffff;
    color: #111827;
    min-height: 20px;
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: #ffffff;
    color: #111827;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    border: 1px solid #d1d5db;
    outline: none;
}}
QProgressBar {{
    border: 1px solid #d1d5db;
    border-radius: 6px;
    text-align: center;
    background: #ffffff;
    color: #111827;
    min-height: 22px;
}}
QProgressBar::chunk {{ background: #2563eb; border-radius: 5px; }}
{_SHARED_GROUPBOX}
QGroupBox {{
    border: 1px solid #d1d5db;
    background: #ffffff;
}}
QGroupBox::title {{
    color: #111827;
    background: #ffffff;
}}
QLabel#dropZone {{
    border: 2px dashed #94a3b8;
    border-radius: 8px;
    padding: 28px;
    background: #f9fafb;
    color: #4b5563;
}}
QListWidget {{
    background: #ffffff;
    color: #111827;
    border: 1px solid #d1d5db;
    border-radius: 6px;
}}
QCheckBox {{
    color: #374151;
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    background: #ffffff;
}}
QCheckBox::indicator:checked {{
    background: #2563eb;
    border-color: #2563eb;
}}
QVideoWidget {{ background: #000000; }}
"""

DARK_THEME = f"""
QMainWindow {{
    background: #181825;
    color: #cdd6f4;
}}
QWidget {{
    color: #cdd6f4;
}}
QLabel {{
    background: transparent;
    color: #bac2de;
}}
QTabWidget::pane {{
    border: 1px solid #45475a;
    background: #1e1e2e;
    top: -1px;
    border-radius: 0 0 6px 6px;
    padding: 4px;
}}
QTabBar::tab {{
    background: #313244;
    color: #a6adc8;
    padding: 8px 16px;
    border: 1px solid #45475a;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: #1e1e2e;
    color: #cdd6f4;
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{ background: #45475a; }}
QPushButton {{
    background: #89b4fa;
    color: #1e1e2e;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    min-height: 20px;
}}
QPushButton:hover {{ background: #b4befe; }}
QPushButton:disabled {{ background: #585b70; color: #a6adc8; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    padding: 6px 8px;
    border: 1px solid #45475a;
    border-radius: 6px;
    background: #313244;
    color: #cdd6f4;
    min-height: 20px;
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: #313244;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
    border: 1px solid #45475a;
    outline: none;
}}
QProgressBar {{
    border: 1px solid #45475a;
    border-radius: 6px;
    text-align: center;
    background: #313244;
    color: #cdd6f4;
    min-height: 22px;
}}
QProgressBar::chunk {{ background: #89b4fa; border-radius: 5px; }}
{_SHARED_GROUPBOX}
QGroupBox {{
    border: 1px solid #45475a;
    background: #1e1e2e;
}}
QGroupBox::title {{
    color: #cdd6f4;
    background: #1e1e2e;
}}
QLabel#dropZone {{
    border: 2px dashed #585b70;
    border-radius: 8px;
    padding: 28px;
    background: #313244;
    color: #a6adc8;
}}
QListWidget {{
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
}}
QCheckBox {{
    color: #bac2de;
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #45475a;
    border-radius: 4px;
    background: #313244;
}}
QCheckBox::indicator:checked {{
    background: #89b4fa;
    border-color: #89b4fa;
}}
QVideoWidget {{ background: #000000; }}
"""
