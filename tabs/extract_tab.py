import cv2

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QPushButton, QDoubleSpinBox,
    QSpinBox, QRadioButton, QButtonGroup, QProgressBar,
    QTextEdit, QFileDialog, QLabel, QGridLayout,
)
from PyQt5.QtGui import QColor, QTextCursor, QTextCharFormat, QFont, QImage, QPixmap
from PyQt5.QtCore import Qt

from workers.extract_worker import ExtractWorker, PreviewWorker


class ExtractTab(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._preview_worker = None
        self._video_info = None
        self._setup_ui()

    # ------------------------------------------------------------------ UI --
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # --- Source group ---
        src_gb = QGroupBox("Video & Çıktı")
        src_f = QFormLayout(src_gb)
        src_f.setSpacing(6)

        self.video_path = QLineEdit()
        self.video_path.setPlaceholderText("Video dosyası seçin (.mp4 .avi .mov .mkv)")
        src_f.addRow("Video dosyası:", self._browse_row(
            self.video_path,
            flt="Video (*.mp4 *.avi *.mov *.mkv *.MP4 *.AVI)",
            on_select=self._on_video_selected,
        ))

        self.output_dir = QLineEdit(r"C:\Users\Atakan\datasets\to_label\images")
        src_f.addRow("Çıktı klasörü:", self._browse_row(self.output_dir, is_dir=True))
        root.addWidget(src_gb)

        # --- Mode + Info (side by side) ---
        mid = QHBoxLayout()

        # Mode group
        mode_gb = QGroupBox("Extraction Modu")
        mode_vl = QVBoxLayout(mode_gb)
        mode_vl.setSpacing(8)

        self._mode_group = QButtonGroup(self)

        # Every Nth frame
        nth_row = QHBoxLayout()
        self.rb_nth = QRadioButton("Her N. frame")
        self.rb_nth.setChecked(True)
        self._mode_group.addButton(self.rb_nth, 0)
        self.nth_val = QSpinBox()
        self.nth_val.setRange(1, 9999); self.nth_val.setValue(10); self.nth_val.setMaximumWidth(80)
        self.nth_val.setToolTip("Her kaçıncı frame kaydedilsin")
        nth_row.addWidget(self.rb_nth); nth_row.addWidget(self.nth_val)
        nth_row.addWidget(QLabel("frame")); nth_row.addStretch()
        mode_vl.addLayout(nth_row)

        # Frames per second
        fps_row = QHBoxLayout()
        self.rb_fps = QRadioButton("Saniyede X frame")
        self._mode_group.addButton(self.rb_fps, 1)
        self.fps_val = QDoubleSpinBox()
        self.fps_val.setRange(0.1, 120.0); self.fps_val.setValue(2.0)
        self.fps_val.setSingleStep(0.5); self.fps_val.setMaximumWidth(80)
        fps_row.addWidget(self.rb_fps); fps_row.addWidget(self.fps_val)
        fps_row.addWidget(QLabel("fps")); fps_row.addStretch()
        mode_vl.addLayout(fps_row)

        # Motion threshold
        motion_row = QHBoxLayout()
        self.rb_motion = QRadioButton("Hareket eşiği")
        self._mode_group.addButton(self.rb_motion, 2)
        self.motion_val = QDoubleSpinBox()
        self.motion_val.setRange(0.1, 255.0); self.motion_val.setValue(15.0)
        self.motion_val.setSingleStep(1.0); self.motion_val.setMaximumWidth(80)
        self.motion_val.setToolTip("Frame fark skoru bu değerin üzerindeyse kaydedilir")
        motion_row.addWidget(self.rb_motion); motion_row.addWidget(self.motion_val)
        motion_row.addWidget(QLabel("diff skoru")); motion_row.addStretch()
        mode_vl.addLayout(motion_row)
        mode_vl.addStretch()

        # Connect mode + params change → update estimate
        self._mode_group.buttonClicked.connect(self._update_estimate)
        self.nth_val.valueChanged.connect(self._update_estimate)
        self.fps_val.valueChanged.connect(self._update_estimate)

        mid.addWidget(mode_gb, 1)

        # Info group
        info_gb = QGroupBox("Video Bilgisi")
        info_f = QFormLayout(info_gb)
        info_f.setSpacing(5)

        self._lbl_duration    = QLabel("—")
        self._lbl_total       = QLabel("—")
        self._lbl_fps         = QLabel("—")
        self._lbl_res         = QLabel("—")
        self._lbl_estimate    = QLabel("—")
        for row in [
            ("Süre:", self._lbl_duration),
            ("Toplam frame:", self._lbl_total),
            ("FPS:", self._lbl_fps),
            ("Çözünürlük:", self._lbl_res),
            ("Tahmini çıktı:", self._lbl_estimate),
        ]:
            info_f.addRow(row[0], row[1])

        mid.addWidget(info_gb, 1)
        root.addLayout(mid)

        # --- Preview group ---
        prev_gb = QGroupBox("Önizleme")
        prev_vl = QVBoxLayout(prev_gb)

        self._preview_labels = []
        grid = QGridLayout()
        grid.setSpacing(6)
        for i in range(6):
            lbl = QLabel()
            lbl.setFixedSize(200, 113)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background:#1a1a1a;border:0.5px solid #444;border-radius:4px;color:#666")
            lbl.setText("—")
            self._preview_labels.append(lbl)
            grid.addWidget(lbl, i // 3, i % 3)

        prev_vl.addLayout(grid)

        self.preview_btn = QPushButton("⬡  Önizle (6 rastgele frame)")
        self.preview_btn.setMaximumWidth(220)
        self.preview_btn.clicked.connect(self._run_preview)
        prev_vl.addWidget(self.preview_btn, alignment=Qt.AlignLeft)

        root.addWidget(prev_gb)

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
        self.log.setMaximumHeight(140)
        root.addWidget(self.log)

    # -------------------------------------------------- helpers --
    def _browse_row(self, le, is_dir=False, flt=None, on_select=None):
        c = QWidget()
        hl = QHBoxLayout(c); hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(le)
        btn = QPushButton("Gözat"); btn.setMaximumWidth(70)
        if is_dir:
            btn.clicked.connect(lambda: self._pick_dir(le))
        else:
            btn.clicked.connect(lambda: self._pick_file(le, flt, on_select))
        hl.addWidget(btn)
        return c

    def _pick_dir(self, le):
        path = QFileDialog.getExistingDirectory(self, "Klasör seç", le.text())
        if path:
            le.setText(path)

    def _pick_file(self, le, flt, callback):
        path, _ = QFileDialog.getOpenFileName(self, "Video seç", "", flt or "All (*)")
        if path:
            le.setText(path)
            if callback:
                callback(path)

    # ------------------------------------------ video info & estimate --
    def _on_video_selected(self, path):
        from core.extractor import get_video_info
        info = get_video_info(path)
        if info is None:
            self._append_log(f"[Hata] Video okunamadı: {path}")
            return
        self._video_info = info
        m, s = divmod(int(info['duration']), 60)
        self._lbl_duration.setText(f"{m}:{s:02d}")
        self._lbl_total.setText(f"{info['total_frames']:,}")
        self._lbl_fps.setText(f"{info['fps']:.2f}")
        self._lbl_res.setText(f"{info['width']}×{info['height']}")
        self._update_estimate()

    def _update_estimate(self):
        if self._video_info is None:
            return
        info = self._video_info
        mode_id = self._mode_group.checkedId()
        if mode_id == 0:   # nth
            est = max(1, info['total_frames'] // max(1, self.nth_val.value()))
        elif mode_id == 1:  # fps
            est = int(info['duration'] * self.fps_val.value())
        else:               # motion
            est = "?"
        self._lbl_estimate.setText(f"~{est}" if isinstance(est, int) else est)

    # ------------------------------------------ preview --
    def _run_preview(self):
        path = self.video_path.text().strip()
        if not path:
            self._append_log("[Uyari] Önce bir video seçin.")
            return
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("Yükleniyor…")
        self._preview_worker = PreviewWorker(path)
        self._preview_worker.preview_ready.connect(self._show_preview)
        self._preview_worker.finished.connect(
            lambda: (self.preview_btn.setEnabled(True),
                     self.preview_btn.setText("⬡  Önizle (6 rastgele frame)"))
        )
        self._preview_worker.start()

    def _show_preview(self, frames):
        for i, lbl in enumerate(self._preview_labels):
            if i < len(frames):
                lbl.setPixmap(self._frame_to_pixmap(frames[i], 200, 113))
            else:
                lbl.clear()
                lbl.setText("—")

    @staticmethod
    def _frame_to_pixmap(bgr, w, h):
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        fh, fw = rgb.shape[:2]
        qi = QImage(bytes(rgb.data), fw, fh, fw * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(qi).scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    # ------------------------------------------ extraction --
    def _collect_cfg(self):
        mode_id = self._mode_group.checkedId()
        mode = ['nth', 'fps', 'motion'][mode_id]
        return {
            'video_path': self.video_path.text().strip(),
            'output_dir': self.output_dir.text().strip(),
            'mode': mode,
            'nth': self.nth_val.value(),
            'target_fps': self.fps_val.value(),
            'motion_thresh': self.motion_val.value(),
        }

    def _start(self):
        cfg = self._collect_cfg()
        if not cfg['video_path']:
            self._append_log("[Hata] Video dosyası seçilmedi.")
            return
        self.log.clear()
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self._worker = ExtractWorker(cfg)
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

    def _on_finished(self, saved):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._append_log(f"─── Tamamlandı — {saved} frame kaydedildi ───", color='#6bcb77')

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
