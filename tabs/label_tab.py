from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QPushButton, QDoubleSpinBox,
    QSpinBox, QComboBox, QCheckBox, QProgressBar,
    QTextEdit, QFileDialog, QLabel,
)
from PyQt5.QtGui import QColor, QTextCursor, QTextCharFormat, QFont
from PyQt5.QtCore import Qt

import yaml
from pathlib import Path

from workers.label_worker import LabelWorker

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def _load_config():
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)

_CFG = _load_config()


class LabelTab(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    # ------------------------------------------------------------------ UI --
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # --- Paths group ---
        paths_gb = QGroupBox("Model & Klasörler")
        paths_form = QFormLayout(paths_gb)
        paths_form.setSpacing(6)

        self.input_dir = QLineEdit(_CFG['input']['images_dir'])
        paths_form.addRow("Girdi klasörü:", self._browse_row(self.input_dir, is_dir=True))

        self.model_path = QLineEdit(_CFG['model']['path'])
        paths_form.addRow("Model yolu (.pt):", self._browse_row(self.model_path, flt="Model (*.pt)"))

        _out_root = str(Path(_CFG['output']['labels_txt_dir']).parent)
        self.output_dir = QLineEdit(_out_root)
        paths_form.addRow("Çıktı kök klasörü:", self._browse_row(self.output_dir, is_dir=True))

        root.addWidget(paths_gb)

        # --- Parameters group ---
        params_gb = QGroupBox("Parametreler")
        params_outer = QHBoxLayout(params_gb)
        params_outer.setSpacing(24)

        left = QFormLayout()
        left.setSpacing(6)
        self.conf = QDoubleSpinBox()
        self.conf.setRange(0.1, 1.0); self.conf.setSingleStep(0.05); self.conf.setValue(0.5)
        left.addRow("Conf eşiği:", self.conf)

        self.iou = QDoubleSpinBox()
        self.iou.setRange(0.1, 1.0); self.iou.setSingleStep(0.05); self.iou.setValue(0.45)
        left.addRow("IOU eşiği:", self.iou)

        self.img_size = QSpinBox()
        self.img_size.setRange(320, 1280); self.img_size.setSingleStep(32); self.img_size.setValue(640)
        left.addRow("Görsel boyutu:", self.img_size)

        right = QFormLayout()
        right.setSpacing(6)
        self.device = QComboBox()
        self.device.addItems(["cuda", "cpu"])
        right.addRow("Device:", self.device)

        self.save_txt = QCheckBox("Save TXT"); self.save_txt.setChecked(True)
        self.save_json = QCheckBox("Save JSON"); self.save_json.setChecked(True)
        self.save_ann = QCheckBox("Save Annotated"); self.save_ann.setChecked(True)
        self.skip_empty = QCheckBox("Skip Empty")
        right.addRow(self.save_txt, self.save_json)
        right.addRow(self.save_ann, self.skip_empty)

        params_outer.addLayout(left)
        params_outer.addLayout(right)
        params_outer.addStretch()
        root.addWidget(params_gb)

        # --- Controls ---
        ctrl = QHBoxLayout()
        self.start_btn = QPushButton("▶  Başlat")
        self.start_btn.setStyleSheet(
            "QPushButton{background:#2e7d32;color:#fff;font-weight:600;padding:6px 20px;border-radius:4px}"
            "QPushButton:disabled{background:#555}"
        )
        self.start_btn.clicked.connect(self._start)

        self.stop_btn = QPushButton("■  Durdur")
        self.stop_btn.setStyleSheet(
            "QPushButton{background:#c62828;color:#fff;font-weight:600;padding:6px 20px;border-radius:4px}"
            "QPushButton:disabled{background:#555}"
        )
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        ctrl.addWidget(self.start_btn)
        ctrl.addWidget(self.stop_btn)
        ctrl.addWidget(self.progress_bar, 1)
        root.addLayout(ctrl)

        # --- Log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 10))
        self.log.setMinimumHeight(180)
        root.addWidget(self.log, 1)

    def _browse_row(self, lineedit, is_dir=False, flt=None):
        container = QWidget()
        hl = QHBoxLayout(container)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(lineedit)
        btn = QPushButton("Gözat")
        btn.setMaximumWidth(70)
        if is_dir:
            btn.clicked.connect(lambda: self._pick_dir(lineedit))
        else:
            btn.clicked.connect(lambda: self._pick_file(lineedit, flt))
        hl.addWidget(btn)
        return container

    def _pick_dir(self, le):
        path = QFileDialog.getExistingDirectory(self, "Klasör seç", le.text())
        if path:
            le.setText(path)

    def _pick_file(self, le, flt):
        path, _ = QFileDialog.getOpenFileName(self, "Dosya seç", le.text(), flt or "All (*)")
        if path:
            le.setText(path)

    # --------------------------------------------------------------- logic --
    def _collect_cfg(self):
        od = self.output_dir.text()
        return {
            'device': self.device.currentText(),
            'model': {
                'path': self.model_path.text(),
                'img_size': self.img_size.value(),
                'conf_threshold': self.conf.value(),
                'iou_threshold': self.iou.value(),
            },
            'classes': _CFG['classes'],
            'class_colors': _CFG['class_colors'],
            'input': {
                'images_dir': self.input_dir.text(),
                'extensions': ['.jpg', '.jpeg', '.png'],
            },
            'output': {
                'labels_txt_dir': od + '\\labels_txt',
                'labels_json_dir': od + '\\labels_json',
                'annotated_dir': od + '\\annotated',
                'report_dir': od + '\\report',
            },
            'options': {
                'save_txt': self.save_txt.isChecked(),
                'save_json': self.save_json.isChecked(),
                'save_annotated': self.save_ann.isChecked(),
                'skip_empty': self.skip_empty.isChecked(),
                'warmup_images': 5,
            },
        }

    def _start(self):
        self.log.clear()
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self._worker = LabelWorker(self._collect_cfg())
        self._worker.log.connect(self._append_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.stop()
        self.stop_btn.setEnabled(False)

    def _on_progress(self, cur, tot):
        self.progress_bar.setMaximum(tot)
        self.progress_bar.setValue(cur)

    def _on_finished(self, _stats):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._append_log("─── Tamamlandı ───", color='#6bcb77')

    def _append_log(self, text, color=None):
        if color is None:
            tl = text.lower()
            if '[hata]' in tl or 'error' in tl:
                color = '#ff6b6b'
            elif '[uyari]' in tl or 'warning' in tl:
                color = '#ffd93d'
            elif 'tamamlandi' in tl or 'tamamland' in tl:
                color = '#6bcb77'
            else:
                color = '#d0d0d0'
        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text + '\n', fmt)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()
