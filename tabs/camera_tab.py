import os
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QPushButton, QSpinBox,
    QLabel, QTextEdit, QFileDialog, QComboBox
)
from PyQt5.QtGui import QImage, QPixmap, QColor, QTextCursor, QTextCharFormat, QFont
from PyQt5.QtCore import Qt

from workers.camera_worker import CameraWorker

class CameraTab(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # --- Settings Group ---
        settings_gb = QGroupBox("Kamera ve Kayıt Ayarları")
        settings_f = QFormLayout(settings_gb)
        settings_f.setSpacing(6)

        self.cam_source = QComboBox()
        self.cam_source.addItems(["Intel RealSense", "Standart WebCam (USB)"])
        settings_f.addRow("Kamera Türü:", self.cam_source)

        self.cam_index = QSpinBox()
        self.cam_index.setRange(0, 10)
        self.cam_index.setValue(0)
        settings_f.addRow("Kamera Index (Sadece WebCam):", self.cam_index)

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Kayıtların kaydedileceği klasörü seçin...")
        # Default to a folder in the current directory
        default_out = os.path.join(os.getcwd(), "outputs", "camera_records")
        self.output_dir.setText(default_out)
        settings_f.addRow("Kayıt Klasörü:", self._browse_row(self.output_dir, is_dir=True))

        root.addWidget(settings_gb)

        # --- Camera View ---
        self.video_label = QLabel("Kamera Kapalı")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("QLabel { background-color: #1e1e1e; color: #888; border: 1px solid #333; border-radius: 4px; }")
        self.video_label.setMinimumHeight(360)
        root.addWidget(self.video_label, 1) # stretch=1 to take available space

        # --- Controls ---
        ctrl = QHBoxLayout()
        
        self.start_cam_btn = QPushButton("▶ Kamerayı Başlat")
        self.start_cam_btn.setStyleSheet("QPushButton{background:#2e7d32;color:#fff;font-weight:600;padding:6px 20px;border-radius:4px}")
        self.start_cam_btn.clicked.connect(self._start_camera)

        self.stop_cam_btn = QPushButton("■ Kamerayı Durdur")
        self.stop_cam_btn.setStyleSheet("QPushButton{background:#555;color:#fff;font-weight:600;padding:6px 20px;border-radius:4px}")
        self.stop_cam_btn.setEnabled(False)
        self.stop_cam_btn.clicked.connect(self._stop_camera)

        self.record_btn = QPushButton("⏺ Kaydı Başlat (MP4)")
        self.record_btn.setStyleSheet("QPushButton{background:#c62828;color:#fff;font-weight:600;padding:6px 20px;border-radius:4px}")
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self._toggle_record)

        ctrl.addWidget(self.start_cam_btn)
        ctrl.addWidget(self.stop_cam_btn)
        ctrl.addWidget(self.record_btn)
        ctrl.addStretch()
        
        root.addLayout(ctrl)

        # --- Log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 10))
        self.log.setMaximumHeight(120)
        root.addWidget(self.log)

    def _browse_row(self, le, is_dir=True):
        c = QWidget()
        hl = QHBoxLayout(c); hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(le)
        btn = QPushButton("Gözat"); btn.setMaximumWidth(70)
        if is_dir:
            btn.clicked.connect(lambda: self._pick_dir(le))
        hl.addWidget(btn)
        return c

    def _pick_dir(self, le):
        path = QFileDialog.getExistingDirectory(self, "Klasör seç", le.text())
        if path:
            le.setText(path)

    def _start_camera(self):
        index = self.cam_index.value()
        out_dir = self.output_dir.text().strip()

        if not out_dir:
            self._append_log("[Hata] Kayıt klasörü seçilmedi.")
            return

        self.start_cam_btn.setEnabled(False)
        self.cam_source.setEnabled(False)
        self.cam_index.setEnabled(False)
        self.output_dir.setEnabled(False)
        self.stop_cam_btn.setEnabled(True)
        self.record_btn.setEnabled(True)
        self.record_btn.setText("⏺ Kaydı Başlat (MP4)")
        self.record_btn.setStyleSheet("QPushButton{background:#c62828;color:#fff;font-weight:600;padding:6px 20px;border-radius:4px}")

        use_realsense = (self.cam_source.currentIndex() == 0)
        self._worker = CameraWorker(camera_index=index, output_dir=out_dir, use_realsense=use_realsense)
        self._worker.frame_ready.connect(self._update_frame)
        self._worker.log.connect(self._append_log)
        self._worker.error.connect(self._append_error)
        self._worker.record_status_changed.connect(self._on_record_status)
        self._worker.finished_capture.connect(self._on_camera_stopped)
        self._worker.start()

    def _stop_camera(self):
        if self._worker:
            self._worker.stop_camera()
        self.stop_cam_btn.setEnabled(False)
        self.record_btn.setEnabled(False)

    def _toggle_record(self):
        if not self._worker:
            return
            
        if not self._worker.is_recording:
            self._worker.start_recording()
        else:
            self._worker.stop_recording()

    def _on_record_status(self, is_recording):
        if is_recording:
            self.record_btn.setText("⏹ Kaydı Durdur")
            self.record_btn.setStyleSheet("QPushButton{background:#555;color:#fff;font-weight:600;padding:6px 20px;border-radius:4px; border: 2px solid #ff5252}")
        else:
            self.record_btn.setText("⏺ Kaydı Başlat (MP4)")
            self.record_btn.setStyleSheet("QPushButton{background:#c62828;color:#fff;font-weight:600;padding:6px 20px;border-radius:4px}")

    def _update_frame(self, frame_rgb):
        # Convert numpy array to QPixmap
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale to fit label maintaining aspect ratio
        pixmap = QPixmap.fromImage(qimg)
        scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)

    def _on_camera_stopped(self):
        self.start_cam_btn.setEnabled(True)
        self.cam_source.setEnabled(True)
        self.cam_index.setEnabled(True)
        self.output_dir.setEnabled(True)
        self.stop_cam_btn.setEnabled(False)
        self.record_btn.setEnabled(False)
        self.video_label.clear()
        self.video_label.setText("Kamera Kapalı")

    def _append_error(self, text):
        self._append_log(f"[Hata] {text}", color='#ff6b6b')

    def _append_log(self, text, color=None):
        if color is None:
            tl = text.lower()
            if '[hata]' in tl or 'error' in tl:
                color = '#ff6b6b'
            elif '[uyari]' in tl or 'warning' in tl or '[!]' in tl:
                color = '#ffd93d'
            else:
                color = '#d0d0d0'
        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text + '\n', fmt)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()
