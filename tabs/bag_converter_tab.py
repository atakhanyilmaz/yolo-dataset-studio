import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QPushButton, QSpinBox,
    QProgressBar, QTextEdit, QFileDialog, QCheckBox
)
from PyQt5.QtGui import QColor, QTextCursor, QTextCharFormat, QFont
from PyQt5.QtCore import Qt

from workers.bag_converter_worker import BagConverterWorker

class BagConverterTab(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # --- Source group ---
        src_gb = QGroupBox("Girdi & Çıktı")
        src_f = QFormLayout(src_gb)
        src_f.setSpacing(6)

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText(".bag dosyası veya klasör seçin")
        
        self.cb_batch = QCheckBox("Klasördeki tüm .bag dosyalarını çevir (Batch Mode)")
        self.cb_batch.stateChanged.connect(self._on_batch_changed)
        src_f.addRow(self.cb_batch)

        src_f.addRow("Girdi Yolu:", self._browse_row(self.input_path, is_dir=False, flt="Bag Files (*.bag)"))

        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Çıktı dosyası (Opsiyonel, tek dosya modunda)")
        src_f.addRow("Çıktı Yolu:", self._browse_row(self.output_path, is_dir=False, flt="MP4 Files (*.mp4)", is_save=True))

        root.addWidget(src_gb)

        # --- Options group ---
        opt_gb = QGroupBox("Ayarlar")
        opt_f = QFormLayout(opt_gb)
        self.fps_val = QSpinBox()
        self.fps_val.setRange(1, 120)
        self.fps_val.setValue(30)
        opt_f.addRow("Fallback FPS:", self.fps_val)
        root.addWidget(opt_gb)
        
        root.addStretch()

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

        self.progress_lbl = QLineEdit()
        self.progress_lbl.setReadOnly(True)
        self.progress_lbl.setPlaceholderText("İşlenen kare sayısı burada görünür...")

        ctrl.addWidget(self.start_btn)
        ctrl.addWidget(self.stop_btn)
        ctrl.addWidget(self.progress_lbl, 1)
        root.addLayout(ctrl)

        # --- Log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 10))
        self.log.setMaximumHeight(200)
        root.addWidget(self.log)

    def _on_batch_changed(self, state):
        if state == Qt.Checked:
            self.output_path.setEnabled(False)
            self.output_path.setPlaceholderText("Batch modunda çıktı yolu otomatik belirlenir")
        else:
            self.output_path.setEnabled(True)
            self.output_path.setPlaceholderText("Çıktı dosyası (Opsiyonel, tek dosya modunda)")

    def _browse_row(self, le, is_dir=False, flt=None, is_save=False):
        c = QWidget()
        hl = QHBoxLayout(c); hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(le)
        btn = QPushButton("Gözat"); btn.setMaximumWidth(70)
        if is_dir:
            btn.clicked.connect(lambda: self._pick_dir(le))
        else:
            if is_save:
                btn.clicked.connect(lambda: self._pick_save_file(le, flt))
            else:
                btn.clicked.connect(lambda: self._pick_file(le, flt))
        hl.addWidget(btn)
        return c

    def _pick_dir(self, le):
        path = QFileDialog.getExistingDirectory(self, "Klasör seç", le.text())
        if path:
            le.setText(path)

    def _pick_file(self, le, flt):
        if self.cb_batch.isChecked():
            self._pick_dir(le)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Dosya seç", "", flt or "All (*)")
            if path:
                le.setText(path)

    def _pick_save_file(self, le, flt):
        path, _ = QFileDialog.getSaveFileName(self, "Kaydedilecek Dosya", "", flt or "All (*)")
        if path:
            le.setText(path)

    def _start(self):
        input_path = self.input_path.text().strip()
        output_path = self.output_path.text().strip()
        fps = self.fps_val.value()
        is_batch = self.cb_batch.isChecked()

        if not input_path:
            self._append_log("[Hata] Girdi dosyası veya klasörü seçilmedi.")
            return

        self.log.clear()
        self.progress_lbl.clear()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self._worker = BagConverterWorker(input_path, output_path, fps, is_batch)
        self._worker.log.connect(self._append_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.stop()
        self.stop_btn.setEnabled(False)

    def _on_progress(self, frame_count):
        self.progress_lbl.setText(f"İşlenen Kare: {frame_count}")

    def _on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._append_log(f"─── İşlem Tamamlandı ───", color='#6bcb77')

    def _append_log(self, text, color=None):
        if color is None:
            tl = text.lower()
            if '[hata]' in tl or 'error' in tl:
                color = '#ff6b6b'
            elif '[uyari]' in tl or 'warning' in tl or '[!]' in tl:
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
