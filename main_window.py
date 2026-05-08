from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from PyQt5.QtCore import Qt

from tabs.extract_tab import ExtractTab
from tabs.label_tab import LabelTab
from tabs.augment_tab import AugmentTab


def _gpu_status():
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            return f"● GPU: {name}", "#4caf50"
        return "● CUDA kullanılamıyor", "#f44336"
    except Exception:
        return "● torch yüklü değil", "#f44336"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO Dataset Studio")
        self.resize(920, 700)
        self.setMinimumSize(760, 560)

        tabs = QTabWidget()
        tabs.addTab(ExtractTab(), "⬡  Frame Extract")
        tabs.addTab(LabelTab(),   "⬡  Auto Label")
        tabs.addTab(AugmentTab(), "⬡  Augmentation")
        self.setCentralWidget(tabs)

        status = QStatusBar()
        self.setStatusBar(status)
        text, color = _gpu_status()
        gpu_lbl = QLabel(text)
        gpu_lbl.setStyleSheet(f"color:{color};font-size:12px;padding:0 8px")
        status.addPermanentWidget(gpu_lbl)
