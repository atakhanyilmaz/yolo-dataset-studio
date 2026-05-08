import threading

from PyQt5.QtCore import QThread, pyqtSignal

from core.augmentor import run_augmentation


class AugmentWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.stop_flag = threading.Event()

    def stop(self):
        self.stop_flag.set()

    def run(self):
        self.stop_flag.clear()
        run_augmentation(
            self.cfg,
            log_cb=self.log.emit,
            progress_cb=lambda cur, tot: self.progress.emit(cur, tot),
            stop_flag=self.stop_flag,
        )
        self.finished.emit()
