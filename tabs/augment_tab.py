from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QPushButton, QDoubleSpinBox,
    QSpinBox, QCheckBox, QProgressBar, QTextEdit,
    QFileDialog, QScrollArea, QLabel,
)
from PyQt5.QtGui import QColor, QTextCursor, QTextCharFormat, QFont
from PyQt5.QtCore import Qt

from workers.augment_worker import AugmentWorker


def _dbl(val, lo=0.0, hi=1.0, step=0.05, dec=2, w=80):
    s = QDoubleSpinBox()
    s.setRange(lo, hi); s.setSingleStep(step); s.setDecimals(dec); s.setValue(val)
    s.setMaximumWidth(w)
    return s


def _int(val, lo=1, hi=9999, w=80):
    s = QSpinBox()
    s.setRange(lo, hi); s.setValue(val); s.setMaximumWidth(w)
    return s


class AugmentTab(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    # ------------------------------------------------------------------ UI --
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # Scrollable area for all groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setSpacing(6)

        cl.addWidget(self._make_source_group())
        cl.addWidget(self._make_geo_group())
        cl.addWidget(self._make_pl_group())
        cl.addWidget(self._make_pg_group())
        cl.addWidget(self._make_pc_group())
        cl.addWidget(self._make_blur_group())
        cl.addWidget(self._make_noise_group())
        cl.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # Controls
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

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 10))
        self.log.setMaximumHeight(160)
        root.addWidget(self.log)

    # -------------------------------------------------------- Group builders --
    def _make_source_group(self):
        gb = QGroupBox("Kaynak & Çıktı")
        f = QFormLayout(gb)
        f.setSpacing(6)

        self.aug_input = QLineEdit(r"C:\Users\Atakan\datasets\to_label\images")
        f.addRow("Girdi (görsel + txt):", self._browse_row(self.aug_input, is_dir=True))

        self.aug_output = QLineEdit(r"C:\Users\Atakan\results\augmented")
        f.addRow("Çıktı klasörü:", self._browse_row(self.aug_output, is_dir=True))

        self.multiplier = _int(5, lo=1, hi=50)
        row = QHBoxLayout()
        row.addWidget(self.multiplier)
        row.addWidget(QLabel("kopya / görsel"))
        row.addStretch()
        f.addRow("Multiplier:", row)
        return gb

    def _make_geo_group(self):
        self.geo_gb = QGroupBox("Geometrik")
        self.geo_gb.setCheckable(True); self.geo_gb.setChecked(True)
        f = QFormLayout(self.geo_gb)
        f.setSpacing(4)

        self.hflip_en = QCheckBox("HorizontalFlip"); self.hflip_en.setChecked(True)
        self.hflip_p = _dbl(0.5)
        f.addRow(self.hflip_en, self._lbl_widget("p:", self.hflip_p))
        self._link_enable(self.hflip_en, [self.hflip_p])

        self.affine_en = QCheckBox("Affine"); self.affine_en.setChecked(True)
        self.aff_sc_min = _dbl(0.9, 0.5, 1.5)
        self.aff_sc_max = _dbl(1.1, 0.5, 1.5)
        self.aff_rot_min = _int(-15, -180, 0)
        self.aff_rot_max = _int(15, 0, 180)
        self.aff_sh_min = _int(-5, -45, 0)
        self.aff_sh_max = _int(5, 0, 45)
        self.aff_p = _dbl(0.5)
        row_w = QWidget()
        rl = QHBoxLayout(row_w); rl.setContentsMargins(0,0,0,0)
        for lbl, w in [("scale:", self.aff_sc_min), ("-", self.aff_sc_max),
                       ("rot:", self.aff_rot_min), ("-", self.aff_rot_max),
                       ("shear:", self.aff_sh_min), ("-", self.aff_sh_max),
                       ("p:", self.aff_p)]:
            rl.addWidget(QLabel(lbl)); rl.addWidget(w)
        rl.addStretch()
        f.addRow(self.affine_en, row_w)
        self._link_enable(self.affine_en,
                          [self.aff_sc_min, self.aff_sc_max, self.aff_rot_min,
                           self.aff_rot_max, self.aff_sh_min, self.aff_sh_max, self.aff_p])
        return self.geo_gb

    def _make_pl_group(self):
        self.pl_gb = QGroupBox("Fotometrik — Lineer")
        self.pl_gb.setCheckable(True); self.pl_gb.setChecked(True)
        f = QFormLayout(self.pl_gb); f.setSpacing(4)

        self.bc_en = QCheckBox("BrightnessContrast"); self.bc_en.setChecked(True)
        self.bc_br = _dbl(0.2, 0.0, 1.0)
        self.bc_co = _dbl(0.2, 0.0, 1.0)
        self.bc_p = _dbl(0.5)
        f.addRow(self.bc_en, self._lbl_row(
            [("brightness:", self.bc_br), ("contrast:", self.bc_co), ("p:", self.bc_p)]
        ))
        self._link_enable(self.bc_en, [self.bc_br, self.bc_co, self.bc_p])
        return self.pl_gb

    def _make_pg_group(self):
        self.pg_gb = QGroupBox("Fotometrik — Gamma")
        self.pg_gb.setCheckable(True); self.pg_gb.setChecked(True)
        f = QFormLayout(self.pg_gb); f.setSpacing(4)

        self.rg_en = QCheckBox("RandomGamma"); self.rg_en.setChecked(True)
        self.rg_min = _int(80, 1, 300)
        self.rg_max = _int(120, 1, 300)
        self.rg_p = _dbl(0.3)
        f.addRow(self.rg_en, self._lbl_row(
            [("min:", self.rg_min), ("max:", self.rg_max), ("p:", self.rg_p)]
        ))
        self._link_enable(self.rg_en, [self.rg_min, self.rg_max, self.rg_p])

        self.cl_en = QCheckBox("CLAHE"); self.cl_en.setChecked(False)
        self.cl_clip = _dbl(4.0, 0.5, 40.0, step=0.5)
        self.cl_tile = _int(8, 2, 32)
        self.cl_p = _dbl(0.3)
        f.addRow(self.cl_en, self._lbl_row(
            [("clip:", self.cl_clip), ("tile:", self.cl_tile), ("p:", self.cl_p)]
        ))
        self._link_enable(self.cl_en, [self.cl_clip, self.cl_tile, self.cl_p])
        return self.pg_gb

    def _make_pc_group(self):
        self.pc_gb = QGroupBox("Fotometrik — Renk")
        self.pc_gb.setCheckable(True); self.pc_gb.setChecked(False)
        f = QFormLayout(self.pc_gb); f.setSpacing(4)

        self.hsv_en = QCheckBox("HueSaturationValue"); self.hsv_en.setChecked(True)
        self.hsv_h = _int(20, 0, 180)
        self.hsv_s = _int(30, 0, 255)
        self.hsv_v = _int(20, 0, 255)
        self.hsv_p = _dbl(0.3)
        f.addRow(self.hsv_en, self._lbl_row(
            [("hue:", self.hsv_h), ("sat:", self.hsv_s), ("val:", self.hsv_v), ("p:", self.hsv_p)]
        ))
        self._link_enable(self.hsv_en, [self.hsv_h, self.hsv_s, self.hsv_v, self.hsv_p])

        self.cj_en = QCheckBox("ColorJitter"); self.cj_en.setChecked(False)
        self.cj_br = _dbl(0.2)
        self.cj_co = _dbl(0.2)
        self.cj_sa = _dbl(0.2)
        self.cj_hu = _dbl(0.1, 0.0, 0.5)
        self.cj_p = _dbl(0.3)
        f.addRow(self.cj_en, self._lbl_row(
            [("br:", self.cj_br), ("co:", self.cj_co),
             ("sat:", self.cj_sa), ("hue:", self.cj_hu), ("p:", self.cj_p)]
        ))
        self._link_enable(self.cj_en, [self.cj_br, self.cj_co, self.cj_sa, self.cj_hu, self.cj_p])
        return self.pc_gb

    def _make_blur_group(self):
        self.bl_gb = QGroupBox("Bulanıklık")
        self.bl_gb.setCheckable(True); self.bl_gb.setChecked(False)
        f = QFormLayout(self.bl_gb); f.setSpacing(4)

        self.mb_en = QCheckBox("MotionBlur"); self.mb_en.setChecked(True)
        self.mb_bl = _int(7, 3, 31)
        self.mb_p = _dbl(0.2)
        f.addRow(self.mb_en, self._lbl_row([("blur_limit:", self.mb_bl), ("p:", self.mb_p)]))
        self._link_enable(self.mb_en, [self.mb_bl, self.mb_p])

        self.gb_en = QCheckBox("GaussianBlur"); self.gb_en.setChecked(True)
        self.gb_bl = _int(7, 3, 31)
        self.gb_p = _dbl(0.2)
        f.addRow(self.gb_en, self._lbl_row([("blur_limit:", self.gb_bl), ("p:", self.gb_p)]))
        self._link_enable(self.gb_en, [self.gb_bl, self.gb_p])

        self.df_en = QCheckBox("Defocus"); self.df_en.setChecked(False)
        self.df_rmin = _int(3, 1, 20)
        self.df_rmax = _int(10, 1, 20)
        self.df_alias = _dbl(0.1, 0.0, 1.0)
        self.df_p = _dbl(0.2)
        f.addRow(self.df_en, self._lbl_row(
            [("r_min:", self.df_rmin), ("r_max:", self.df_rmax),
             ("alias:", self.df_alias), ("p:", self.df_p)]
        ))
        self._link_enable(self.df_en, [self.df_rmin, self.df_rmax, self.df_alias, self.df_p])
        return self.bl_gb

    def _make_noise_group(self):
        self.ns_gb = QGroupBox("Sensör Gürültüsü")
        self.ns_gb.setCheckable(True); self.ns_gb.setChecked(False)
        f = QFormLayout(self.ns_gb); f.setSpacing(4)

        self.gn_en = QCheckBox("GaussNoise"); self.gn_en.setChecked(True)
        self.gn_vmin = _dbl(10.0, 0.0, 500.0, step=5.0, dec=1)
        self.gn_vmax = _dbl(50.0, 0.0, 500.0, step=5.0, dec=1)
        self.gn_p = _dbl(0.2)
        f.addRow(self.gn_en, self._lbl_row(
            [("var_min:", self.gn_vmin), ("var_max:", self.gn_vmax), ("p:", self.gn_p)]
        ))
        self._link_enable(self.gn_en, [self.gn_vmin, self.gn_vmax, self.gn_p])

        self.ic_en = QCheckBox("ImageCompression"); self.ic_en.setChecked(False)
        self.ic_lo = _int(70, 1, 99)
        self.ic_hi = _int(100, 1, 100)
        self.ic_p = _dbl(0.2)
        f.addRow(self.ic_en, self._lbl_row(
            [("q_low:", self.ic_lo), ("q_high:", self.ic_hi), ("p:", self.ic_p)]
        ))
        self._link_enable(self.ic_en, [self.ic_lo, self.ic_hi, self.ic_p])
        return self.ns_gb

    # --------------------------------------------------- Layout helpers --
    def _browse_row(self, le, is_dir=False):
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

    def _lbl_widget(self, label, widget):
        c = QWidget()
        hl = QHBoxLayout(c); hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(QLabel(label)); hl.addWidget(widget); hl.addStretch()
        return c

    def _lbl_row(self, pairs):
        c = QWidget()
        hl = QHBoxLayout(c); hl.setContentsMargins(0, 0, 0, 0)
        for lbl, w in pairs:
            hl.addWidget(QLabel(lbl)); hl.addWidget(w)
        hl.addStretch()
        return c

    def _link_enable(self, cb, widgets):
        def toggle(checked):
            for w in widgets:
                w.setEnabled(checked)
        cb.toggled.connect(toggle)

    # --------------------------------------------------------------- Logic --
    def _collect_cfg(self):
        return {
            'input_dir': self.aug_input.text(),
            'output_dir': self.aug_output.text(),
            'multiplier': self.multiplier.value(),
            'geometric': {
                'enabled': self.geo_gb.isChecked(),
                'horizontal_flip': {'enabled': self.hflip_en.isChecked(), 'p': self.hflip_p.value()},
                'affine': {
                    'enabled': self.affine_en.isChecked(),
                    'scale_min': self.aff_sc_min.value(), 'scale_max': self.aff_sc_max.value(),
                    'rotate_min': self.aff_rot_min.value(), 'rotate_max': self.aff_rot_max.value(),
                    'shear_min': self.aff_sh_min.value(), 'shear_max': self.aff_sh_max.value(),
                    'p': self.aff_p.value(),
                },
            },
            'photometric_linear': {
                'enabled': self.pl_gb.isChecked(),
                'brightness_contrast': {
                    'enabled': self.bc_en.isChecked(),
                    'brightness_limit': self.bc_br.value(),
                    'contrast_limit': self.bc_co.value(),
                    'p': self.bc_p.value(),
                },
            },
            'photometric_gamma': {
                'enabled': self.pg_gb.isChecked(),
                'random_gamma': {
                    'enabled': self.rg_en.isChecked(),
                    'gamma_min': self.rg_min.value(), 'gamma_max': self.rg_max.value(),
                    'p': self.rg_p.value(),
                },
                'clahe': {
                    'enabled': self.cl_en.isChecked(),
                    'clip_limit': self.cl_clip.value(),
                    'tile_grid_size': self.cl_tile.value(),
                    'p': self.cl_p.value(),
                },
            },
            'photometric_color': {
                'enabled': self.pc_gb.isChecked(),
                'hue_saturation': {
                    'enabled': self.hsv_en.isChecked(),
                    'hue_shift': self.hsv_h.value(),
                    'sat_shift': self.hsv_s.value(),
                    'val_shift': self.hsv_v.value(),
                    'p': self.hsv_p.value(),
                },
                'color_jitter': {
                    'enabled': self.cj_en.isChecked(),
                    'brightness': self.cj_br.value(), 'contrast': self.cj_co.value(),
                    'saturation': self.cj_sa.value(), 'hue': self.cj_hu.value(),
                    'p': self.cj_p.value(),
                },
            },
            'blur': {
                'enabled': self.bl_gb.isChecked(),
                'motion_blur': {'enabled': self.mb_en.isChecked(), 'blur_limit': self.mb_bl.value(), 'p': self.mb_p.value()},
                'gaussian_blur': {'enabled': self.gb_en.isChecked(), 'blur_limit': self.gb_bl.value(), 'p': self.gb_p.value()},
                'defocus': {
                    'enabled': self.df_en.isChecked(),
                    'radius_min': self.df_rmin.value(), 'radius_max': self.df_rmax.value(),
                    'alias_blur': self.df_alias.value(), 'p': self.df_p.value(),
                },
            },
            'noise': {
                'enabled': self.ns_gb.isChecked(),
                'gauss_noise': {
                    'enabled': self.gn_en.isChecked(),
                    'var_min': self.gn_vmin.value(), 'var_max': self.gn_vmax.value(),
                    'p': self.gn_p.value(),
                },
                'image_compression': {
                    'enabled': self.ic_en.isChecked(),
                    'quality_lower': self.ic_lo.value(), 'quality_upper': self.ic_hi.value(),
                    'p': self.ic_p.value(),
                },
            },
        }

    def _start(self):
        self.log.clear()
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self._worker = AugmentWorker(self._collect_cfg())
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

    def _on_finished(self):
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
