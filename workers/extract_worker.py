import threading

from PyQt5.QtCore import QThread, pyqtSignal

from core.extractor import run_extraction, get_preview_frames


class ExtractWorker(QThread):
    log      = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int)   # saved frame count

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.stop_flag = threading.Event()

    def stop(self):
        self.stop_flag.set()

    def run(self):
        self.stop_flag.clear()
        try:
            saved = run_extraction(
                self.cfg,
                log_cb=self.log.emit,
                progress_cb=lambda cur, tot: self.progress.emit(cur, tot),
                stop_flag=self.stop_flag,
            )
            self.finished.emit(saved or 0)
        except Exception as e:
            import traceback
            self.log.emit(f"[Hata] {e}")
            self.log.emit(traceback.format_exc())
            self.finished.emit(0)


class PreviewWorker(QThread):
    preview_ready = pyqtSignal(list)   # list[np.ndarray] BGR frames

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        try:
            frames = get_preview_frames(self.video_path, n=6)
            self.preview_ready.emit(frames)
        except Exception:
            self.preview_ready.emit([])
