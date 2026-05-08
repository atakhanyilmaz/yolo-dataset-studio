import threading

from PyQt5.QtCore import QThread, pyqtSignal

from core.labeler import run_pipeline


class LabelWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(dict)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.stop_flag = threading.Event()

    def stop(self):
        self.stop_flag.set()

    def run(self):
        self.stop_flag.clear()
        result = run_pipeline(
            self.cfg,
            log_cb=self.log.emit,
            progress_cb=lambda cur, tot: self.progress.emit(cur, tot),
            stop_flag=self.stop_flag,
        )
        self.finished.emit(result or {})
