import os
import threading
import traceback
from pathlib import Path

import numpy as np
import cv2
import pyrealsense2 as rs
from PyQt5.QtCore import QThread, pyqtSignal


def convert_bag_to_mp4_logic(bag_path, out_path=None, fps=30, log_cb=None, progress_cb=None, stop_flag=None):
    bag_path = str(bag_path)
    if not os.path.isfile(bag_path):
        raise FileNotFoundError(f"Dosya bulunamadı: {bag_path}")

    if out_path:
        out_path_obj = Path(out_path)
        if out_path_obj.is_dir() or not out_path_obj.suffix:
            out_path_obj.mkdir(parents=True, exist_ok=True)
            out_path = str(out_path_obj / Path(bag_path).with_suffix(".mp4").name)
        else:
            out_path_obj.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_path = str(Path(bag_path).with_suffix(".mp4"))

    # Pipeline ve config kur
    pipeline = rs.pipeline()
    config = rs.config()

    # Dosyadan oku - realtime=False sayesinde tüm kareler işlenir (kare atlamaz)
    rs.config.enable_device_from_file(config, bag_path, repeat_playback=False)
    config.enable_stream(rs.stream.color)

    profile = pipeline.start(config)

    # Playback'i non-realtime moda al ki hiçbir kareyi kaçırmasın
    playback = profile.get_device().as_playback()
    playback.set_real_time(False)

    # Color stream'in çözünürlüğünü al
    color_profile = profile.get_stream(rs.stream.color).as_video_stream_profile()
    width = color_profile.width()
    height = color_profile.height()
    src_fps = color_profile.fps() or fps

    if log_cb:
        log_cb(f"[+] {os.path.basename(bag_path)}  ->  {os.path.basename(out_path)}")
        log_cb(f"    Çözünürlük: {width}x{height}  |  FPS: {src_fps}")

    # MP4 writer (H.264 yoksa mp4v fallback)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, src_fps, (width, height))
    if not writer.isOpened():
        pipeline.stop()
        raise RuntimeError("VideoWriter açılamadı. OpenCV codec desteğini kontrol et.")

    frame_count = 0
    seen_timestamps = set()

    try:
        while True:
            if stop_flag and stop_flag.is_set():
                if log_cb:
                    log_cb("    [!] İşlem kullanıcı tarafından durduruldu.")
                break

            # try_wait_for_frames bag bitince False döner
            ok, frames = pipeline.try_wait_for_frames(timeout_ms=5000)
            if not ok:
                break

            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            # Aynı kareyi iki kez yazmamak için frame number kontrolü
            fnum = color_frame.get_frame_number()
            if fnum in seen_timestamps:
                continue
            seen_timestamps.add(fnum)

            img = np.asanyarray(color_frame.get_data())
            # RealSense RGB döner, OpenCV BGR bekler
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            writer.write(img_bgr)
            frame_count += 1

            if frame_count % 30 == 0:
                if progress_cb:
                    progress_cb(frame_count)

    except RuntimeError as e:
        # Bag bitince bazı sürümlerde exception fırlatır, normal
        if "frame didn't arrive" not in str(e).lower():
            if log_cb:
                log_cb(f"    Uyarı: {e}")
    finally:
        writer.release()
        pipeline.stop()

    if log_cb:
        log_cb(f"    ✓ {frame_count} kare yazıldı: {out_path}")
    return out_path


class BagConverterWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, input_path, output_path, fps, is_batch):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.fps = fps
        self.is_batch = is_batch
        self.stop_flag = threading.Event()

    def stop(self):
        self.stop_flag.set()

    def run(self):
        self.stop_flag.clear()
        try:
            if self.is_batch or os.path.isdir(self.input_path):
                folder = Path(self.input_path)
                bags = sorted(folder.glob("*.bag"))
                if not bags:
                    self.log.emit(f"[Hata] Klasörde .bag dosyası yok: {folder}")
                    self.finished.emit()
                    return
                self.log.emit(f"[+] {len(bags)} dosya bulundu\n")
                
                for i, bag in enumerate(bags):
                    if self.stop_flag.is_set():
                        break
                    self.log.emit(f"--- Dosya {i+1}/{len(bags)} ---")
                    try:
                        convert_bag_to_mp4_logic(
                            bag_path=str(bag),
                            fps=self.fps,
                            log_cb=self.log.emit,
                            progress_cb=self.progress.emit,
                            stop_flag=self.stop_flag
                        )
                    except Exception as e:
                        self.log.emit(f"    HATA ({bag.name}): {e}")
                        self.log.emit(traceback.format_exc())
            else:
                convert_bag_to_mp4_logic(
                    bag_path=self.input_path,
                    out_path=self.output_path if self.output_path else None,
                    fps=self.fps,
                    log_cb=self.log.emit,
                    progress_cb=self.progress.emit,
                    stop_flag=self.stop_flag
                )
        except Exception as e:
            self.log.emit(f"[Hata] Beklenmeyen hata: {e}")
            self.log.emit(traceback.format_exc())
        finally:
            self.finished.emit()
