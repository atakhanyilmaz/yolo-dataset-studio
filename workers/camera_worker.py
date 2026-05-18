import os
import cv2
import numpy as np
import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

try:
    import pyrealsense2 as rs
    HAS_REALSENSE = True
except ImportError:
    HAS_REALSENSE = False

class CameraWorker(QThread):
    # Signals
    frame_ready = pyqtSignal(np.ndarray)  # Emits RGB frames for UI
    log = pyqtSignal(str)                 # Emits log messages
    error = pyqtSignal(str)               # Emits error messages
    record_status_changed = pyqtSignal(bool) # Emits True when recording starts, False when stops
    finished_capture = pyqtSignal()       # Emits when camera is completely stopped

    def __init__(self, camera_index=0, output_dir="", use_realsense=False):
        super().__init__()
        self.camera_index = camera_index
        self.output_dir = output_dir
        self.use_realsense = use_realsense
        
        self.is_running = True
        self.is_recording = False
        self._record_request = False
        self._stop_record_request = False
        
        self.cap = None
        self.writer = None
        self.current_video_path = None
        
        # RealSense specific
        self.rs_pipeline = None

    def start_recording(self):
        self._record_request = True

    def stop_recording(self):
        self._stop_record_request = True

    def stop_camera(self):
        self.is_running = False

    def run(self):
        if self.use_realsense:
            self._run_realsense()
        else:
            self._run_opencv()

    def _run_opencv(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            self.error.emit(f"Kamera (Index: {self.camera_index}) açılamadı! Lütfen bağlantıyı kontrol edin.")
            self.finished_capture.emit()
            return

        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 120:
            fps = 30.0 # fallback

        self.log.emit(f"WebCam başlatıldı: {width}x{height} @ {fps}FPS")

        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                self.error.emit("Kameradan görüntü alınamadı.")
                break

            self._handle_recording(frame, width, height, fps)

            # Convert to RGB for UI
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(frame_rgb)

            time.sleep(0.001)

        self._stop_video_writer()
        self.cap.release()
        self.log.emit("WebCam durduruldu.")
        self.finished_capture.emit()

    def _run_realsense(self):
        if not HAS_REALSENSE:
            self.error.emit("pyrealsense2 kütüphanesi bulunamadı!")
            self.finished_capture.emit()
            return

        try:
            self.rs_pipeline = rs.pipeline()
            config = rs.config()
            # Enable Color stream
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            
            profile = self.rs_pipeline.start(config)
            
            # Get actual properties
            color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
            width = color_stream.width()
            height = color_stream.height()
            fps = color_stream.fps()
            
            self.log.emit(f"Intel RealSense başlatıldı: {width}x{height} @ {fps}FPS")

            while self.is_running:
                frames = self.rs_pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                
                if not color_frame:
                    continue

                # Get BGR frame
                frame = np.asanyarray(color_frame.get_data())

                self._handle_recording(frame, width, height, fps)

                # Convert to RGB for UI
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frame_ready.emit(frame_rgb)
                
                time.sleep(0.001)

        except Exception as e:
            self.error.emit(f"RealSense hatası: {str(e)}")
        finally:
            self._stop_video_writer()
            if self.rs_pipeline:
                self.rs_pipeline.stop()
            self.log.emit("Intel RealSense durduruldu.")
            self.finished_capture.emit()


    def _handle_recording(self, frame, width, height, fps):
        if self._record_request:
            self._record_request = False
            self._start_video_writer(width, height, fps)
        
        if self._stop_record_request:
            self._stop_record_request = False
            self._stop_video_writer()

        if self.is_recording and self.writer is not None:
            self.writer.write(frame)

    def _start_video_writer(self, width, height, fps):
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir, exist_ok=True)
            except Exception as e:
                self.error.emit(f"Klasör oluşturulamadı: {e}")
                return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.mp4"
        self.current_video_path = os.path.join(self.output_dir, filename)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(self.current_video_path, fourcc, fps, (width, height))
        
        if self.writer.isOpened():
            self.is_recording = True
            self.log.emit(f"Kayıt başladı: {filename}")
            self.record_status_changed.emit(True)
        else:
            self.error.emit("VideoWriter açılamadı. OpenCV codec desteğini kontrol edin.")
            self.writer = None

    def _stop_video_writer(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None
            self.is_recording = False
            self.log.emit(f"Kayıt kaydedildi: {self.current_video_path}")
            self.record_status_changed.emit(False)
