"""PySide6 main window."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.advanced.compressor import CompressOptions, compress_to_size
from core.advanced.merger import MergeOptions, merge_videos
from core.advanced.speed import SpeedOptions, change_speed
from core.advanced.watermark import Position, WatermarkOptions, apply_watermark
from core.audio_extractor import AudioBitrate, AudioFormat, ExtractOptions, extract_audio
from core.batch import batch_convert_folder
from core.config import append_history, get_feature_settings, save_feature_settings
from core.converter import ConvertOptions, QualityMode, VideoCodec, convert
from core.cutter import CutMode, CutOptions, cut, split_equal
from core.ffmpeg_wrapper import FFmpegError, check_ffmpeg, get_install_instructions
from core.job import Job, JobQueue
from gui.theme import DARK_THEME, LIGHT_THEME
from gui.widgets.drop_zone import DropZone
from gui.widgets.job_queue_view import JobQueueView
from gui.widgets.preview_player import PreviewPlayer
from gui.widgets.settings_panel import SettingsGroup, make_form

LOG_DIR = Path.home() / ".offline-video-converter"
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[handler, logging.StreamHandler(sys.stderr)],
    )


class WorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(float)


class FFmpegWorker(QThread):
    def __init__(self, func, *args, **kwargs) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            def progress_cb(p: float) -> None:
                self.signals.progress.emit(p)

            self.kwargs["progress_callback"] = progress_cb
            self.kwargs["cancel_check"] = lambda: self._cancelled
            result = self.func(*self.args, **self.kwargs)
            self.signals.finished.emit(str(result))
        except Exception as exc:
            logging.exception("Worker failed")
            self.signals.error.emit(str(exc))


def _insert_settings_group(tab: FeatureTab, title: str, form: QFormLayout) -> SettingsGroup:
    group = SettingsGroup(title, form)
    tab.layout.insertWidget(2, group)
    return group


class FeatureTab(QWidget):
    """Base tab with input/output paths and run button."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.feature_name = title.lower().replace(" ", "_")
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.drop = DropZone()
        self.layout.addWidget(self.drop)
        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()
        form = make_form()
        form.addRow("Input", self.input_edit)
        form.addRow("Output", self.output_edit)
        self.layout.addLayout(form)
        browse_in = QPushButton("Browse Input")
        browse_out = QPushButton("Browse Output")
        browse_in.clicked.connect(self._browse_input)
        browse_out.clicked.connect(self._browse_output)
        row = QHBoxLayout()
        row.addWidget(browse_in)
        row.addWidget(browse_out)
        self.layout.addLayout(row)
        self.progress = QProgressBar()
        self.layout.addWidget(self.progress)
        self.run_btn = QPushButton(f"Run {title}")
        self.layout.addWidget(self.run_btn)
        self.drop.files_dropped.connect(self._on_drop)

    def _on_drop(self, paths: list[str]) -> None:
        if paths:
            self.input_edit.setText(paths[0])

    def _browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select input video")
        if path:
            self.input_edit.setText(path)

    def _browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Select output path")
        if path:
            self.output_edit.setText(path)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Offline Video Converter")
        self.resize(960, 720)
        self._dark = False
        self._workers: list[FFmpegWorker] = []
        self._job_queue = JobQueue(max_workers=2)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        header = QHBoxLayout()
        self.theme_btn = QPushButton("Toggle Theme")
        self.theme_btn.clicked.connect(self._toggle_theme)
        header.addStretch()
        header.addWidget(self.theme_btn)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._build_convert_tab()
        self._build_cut_tab()
        self._build_extract_tab()
        self._build_compress_tab()
        self._build_merge_tab()
        self._build_watermark_tab()
        self._build_batch_tab()
        self._build_speed_tab()

        self.preview = PreviewPlayer()
        layout.addWidget(QLabel("Preview"))
        layout.addWidget(self.preview)

        self.queue_view = JobQueueView()
        self.queue_view.bind_queue(self._job_queue)
        self.queue_view.cancel_requested.connect(self._job_queue.cancel_job)
        self.queue_view.pause_requested.connect(self._job_queue.pause_job)
        self.queue_view.resume_requested.connect(self._job_queue.resume_job)
        layout.addWidget(QLabel("Job Queue"))
        layout.addWidget(self.queue_view)

        self._apply_theme()

    def _apply_theme(self) -> None:
        stylesheet = DARK_THEME if self._dark else LIGHT_THEME
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet)
        else:
            self.setStyleSheet(stylesheet)

    def _toggle_theme(self) -> None:
        self._dark = not self._dark
        self._apply_theme()

    def _run_worker(self, func, inp: str, out: str, **kwargs) -> None:
        if not inp or not out:
            QMessageBox.warning(self, "Missing paths", "Provide input and output paths.")
            return
        self.preview.load(inp)
        worker = FFmpegWorker(func, inp, out, **kwargs)
        worker.signals.progress.connect(lambda p: self.sender().progress.setValue(int(p * 100)) if hasattr(self.sender(), "progress") else None)
        tab = self.tabs.currentWidget()
        if isinstance(tab, FeatureTab):
            worker.signals.progress.connect(lambda p, t=tab: t.progress.setValue(int(p * 100)))
            tab.run_btn.setEnabled(False)

            def on_done(result: str, t=tab) -> None:
                t.progress.setValue(100)
                t.run_btn.setEnabled(True)
                append_history({"operation": func.__name__, "input": inp, "output": result})
                QMessageBox.information(self, "Done", f"Saved to:\n{result}")
                self.preview.load(result)

            def on_err(msg: str, t=tab) -> None:
                t.run_btn.setEnabled(True)
                QMessageBox.critical(self, "Error", msg)

            worker.signals.finished.connect(on_done)
            worker.signals.error.connect(on_err)

        self._workers.append(worker)
        worker.start()

    def _build_convert_tab(self) -> None:
        tab = FeatureTab("Convert")
        settings = get_feature_settings("convert")
        self.codec_combo = QComboBox()
        self.codec_combo.addItems([c.value for c in VideoCodec])
        self.codec_combo.setCurrentText(settings.get("codec", "h264"))
        self.crf_spin = QSpinBox()
        self.crf_spin.setRange(0, 51)
        self.crf_spin.setValue(settings.get("crf", 23))
        self.strip_meta = QCheckBox("Strip metadata")
        self.strip_meta.setChecked(settings.get("strip_metadata", False))
        self.hw_accel = QCheckBox("Hardware acceleration")
        self.hw_accel.setChecked(settings.get("hw_accel", False))
        form = make_form()
        form.addRow("Codec", self.codec_combo)
        form.addRow("CRF", self.crf_spin)
        form.addRow(self.strip_meta)
        form.addRow(self.hw_accel)
        _insert_settings_group(tab, "Convert Settings", form)
        tab.run_btn.clicked.connect(self._run_convert)
        self.tabs.addTab(tab, "Convert")

    def _run_convert(self) -> None:
        tab: FeatureTab = self.tabs.widget(0)
        opts = ConvertOptions(
            output_format=Path(tab.output_edit.text()).suffix.lstrip(".") or "mp4",
            video_codec=VideoCodec(self.codec_combo.currentText()),
            crf=self.crf_spin.value(),
            preserve_metadata=not self.strip_meta.isChecked(),
            use_hw_accel=self.hw_accel.isChecked(),
        )
        save_feature_settings(
            "convert",
            {
                "codec": self.codec_combo.currentText(),
                "crf": self.crf_spin.value(),
                "strip_metadata": self.strip_meta.isChecked(),
                "hw_accel": self.hw_accel.isChecked(),
            },
        )
        self._run_worker(convert, tab.input_edit.text(), tab.output_edit.text(), opts=opts)

    def _build_cut_tab(self) -> None:
        tab = FeatureTab("Cut")
        self.cut_start = QLineEdit("00:00:00.000")
        self.cut_end = QLineEdit("00:00:02.000")
        self.cut_mode = QComboBox()
        self.cut_mode.addItems(["fast", "precise"])
        form = make_form()
        form.addRow("Start", self.cut_start)
        form.addRow("End", self.cut_end)
        form.addRow("Mode", self.cut_mode)
        _insert_settings_group(tab, "Cut Settings", form)
        tab.run_btn.clicked.connect(self._run_cut)
        self.tabs.addTab(tab, "Cut")

    def _run_cut(self) -> None:
        tab: FeatureTab = self.tabs.widget(1)
        opts = CutOptions(
            start=self.cut_start.text(),
            end=self.cut_end.text() or None,
            mode=CutMode(self.cut_mode.currentText()),
        )
        self._run_worker(cut, tab.input_edit.text(), tab.output_edit.text(), opts=opts)

    def _build_extract_tab(self) -> None:
        tab = FeatureTab("Extract Audio")
        self.audio_fmt = QComboBox()
        self.audio_fmt.addItems([f.value for f in AudioFormat])
        self.audio_br = QComboBox()
        self.audio_br.addItems([b.value for b in AudioBitrate])
        self.audio_norm = QCheckBox("Loudness normalization")
        form = make_form()
        form.addRow("Format", self.audio_fmt)
        form.addRow("Bitrate", self.audio_br)
        form.addRow(self.audio_norm)
        _insert_settings_group(tab, "Audio Settings", form)
        tab.run_btn.clicked.connect(self._run_extract)
        self.tabs.addTab(tab, "Extract Audio")

    def _run_extract(self) -> None:
        tab: FeatureTab = self.tabs.widget(2)
        opts = ExtractOptions(
            format=AudioFormat(self.audio_fmt.currentText()),
            bitrate=AudioBitrate(self.audio_br.currentText()),
            normalize_loudness=self.audio_norm.isChecked(),
        )
        self._run_worker(extract_audio, tab.input_edit.text(), tab.output_edit.text(), opts=opts)

    def _build_compress_tab(self) -> None:
        tab = FeatureTab("Compress")
        self.target_mb = QDoubleSpinBox()
        self.target_mb.setRange(0.5, 5000)
        self.target_mb.setValue(10)
        form = make_form()
        form.addRow("Target size (MB)", self.target_mb)
        _insert_settings_group(tab, "Compress Settings", form)
        tab.run_btn.clicked.connect(self._run_compress)
        self.tabs.addTab(tab, "Compress")

    def _run_compress(self) -> None:
        tab: FeatureTab = self.tabs.widget(3)
        opts = CompressOptions(target_size_mb=self.target_mb.value())
        self._run_worker(compress_to_size, tab.input_edit.text(), tab.output_edit.text(), opts=opts)

    def _build_merge_tab(self) -> None:
        tab = FeatureTab("Merge")
        self.merge_list = QLineEdit()
        self.merge_list.setPlaceholderText("Comma-separated input paths")
        form = make_form()
        form.addRow("Inputs", self.merge_list)
        _insert_settings_group(tab, "Merge Settings", form)
        tab.run_btn.clicked.connect(self._run_merge)
        self.tabs.addTab(tab, "Merge")

    def _run_merge(self) -> None:
        tab: FeatureTab = self.tabs.widget(4)
        inputs = [p.strip() for p in self.merge_list.text().split(",") if p.strip()]
        if len(inputs) < 2:
            QMessageBox.warning(self, "Merge", "Provide at least two input paths.")
            return

        def merge_wrapper(_inp: str, out: str, inputs=inputs, **kwargs):
            return merge_videos(inputs, out, MergeOptions(), **kwargs)

        self._run_worker(merge_wrapper, inputs[0], tab.output_edit.text())

    def _build_watermark_tab(self) -> None:
        tab = FeatureTab("Watermark")
        self.wm_image = QLineEdit()
        self.wm_text = QLineEdit()
        self.wm_pos = QComboBox()
        self.wm_pos.addItems([p.value for p in Position])
        form = make_form()
        form.addRow("Image path", self.wm_image)
        form.addRow("Text", self.wm_text)
        form.addRow("Position", self.wm_pos)
        _insert_settings_group(tab, "Watermark Settings", form)
        tab.run_btn.clicked.connect(self._run_watermark)
        self.tabs.addTab(tab, "Watermark")

    def _run_watermark(self) -> None:
        tab: FeatureTab = self.tabs.widget(5)
        opts = WatermarkOptions(
            image_path=self.wm_image.text() or None,
            text=self.wm_text.text() or None,
            position=Position(self.wm_pos.currentText()),
        )
        self._run_worker(apply_watermark, tab.input_edit.text(), tab.output_edit.text(), opts=opts)

    def _build_batch_tab(self) -> None:
        tab = FeatureTab("Batch")
        self.batch_folder = QLineEdit()
        self.batch_workers = QSpinBox()
        self.batch_workers.setRange(1, 8)
        self.batch_workers.setValue(2)
        form = make_form()
        form.addRow("Input folder", self.batch_folder)
        form.addRow("Workers", self.batch_workers)
        _insert_settings_group(tab, "Batch Settings", form)
        tab.run_btn.clicked.connect(self._run_batch)
        self.tabs.addTab(tab, "Batch")

    def _run_batch(self) -> None:
        tab: FeatureTab = self.tabs.widget(6)
        folder = self.batch_folder.text() or tab.input_edit.text()
        out_dir = tab.output_edit.text()
        if not folder or not out_dir:
            QMessageBox.warning(self, "Batch", "Provide folder and output directory.")
            return

        def on_update(job: Job) -> None:
            self.queue_view.set_overall_progress(self._job_queue.overall_progress())

        queue = batch_convert_folder(
            folder,
            out_dir,
            ConvertOptions(),
            max_workers=self.batch_workers.value(),
            progress_callback=on_update,
        )
        self._job_queue = queue
        self.queue_view.bind_queue(queue)
        QMessageBox.information(self, "Batch", "Batch jobs queued.")

    def _build_speed_tab(self) -> None:
        tab = FeatureTab("Speed")
        self.speed_factor = QDoubleSpinBox()
        self.speed_factor.setRange(0.25, 4.0)
        self.speed_factor.setSingleStep(0.25)
        self.speed_factor.setValue(1.0)
        form = make_form()
        form.addRow("Factor", self.speed_factor)
        _insert_settings_group(tab, "Speed Settings", form)
        tab.run_btn.clicked.connect(self._run_speed)
        self.tabs.addTab(tab, "Speed")

    def _run_speed(self) -> None:
        tab: FeatureTab = self.tabs.widget(7)
        opts = SpeedOptions(factor=self.speed_factor.value())
        self._run_worker(change_speed, tab.input_edit.text(), tab.output_edit.text(), opts=opts)


def run_gui() -> int:
    setup_logging()
    ok, msg = check_ffmpeg()
    app = QApplication(sys.argv)
    if not ok:
        QMessageBox.critical(None, "FFmpeg Required", f"{msg}\n\n{get_install_instructions()}")
        return 1
    window = MainWindow()
    window.show()
    return app.exec()
