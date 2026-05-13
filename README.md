# YOLO Dataset Studio

End-to-end dataset preparation toolkit for YOLO-based object detection projects.
A PyQt5 desktop application that combines **video frame extraction**, **automatic labeling** and **data augmentation** in a single dark-themed GUI — with full CLI support.

<img width="1919" height="374" alt="image" src="https://github.com/user-attachments/assets/5ac047c5-9331-4d5b-91b7-dda118f5ff4e" />
<img width="1915" height="677" alt="image" src="https://github.com/user-attachments/assets/aee76832-9f67-4bd2-8fa0-9b8ea021b77e" />

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [GUI Usage](#gui-usage)
- [CLI Usage](#cli-usage)
- [API Documentation](#api-documentation)
  - [core.extractor](#coreextractor)
  - [core.labeler](#corelabeler)
  - [core.augmentor](#coreaugmentor)
  - [workers](#workers)
- [Output Formats](#output-formats)
- [Project Structure](#project-structure)
- [Building .exe](#building-exe)
- [Dependencies](#dependencies)
- [License](#license)

---

## Features

| Module | Capability |
|---|---|
| **Frame Extractor** | Every-Nth, target-FPS, motion-threshold sampling from any video |
| **Auto Label** | Batch YOLO inference → `.txt` + `.json` + annotated images + HTML report |
| **Augmentation** | 12 configurable albumentations transforms, per-group enable/disable, adjustable multiplier |

- CUDA / CPU device selection per run
- Non-blocking threaded execution — UI stays responsive during long jobs
- Supports any YOLO model (YOLOv8, YOLO11, custom fine-tuned weights)
- All 80 COCO classes built-in; `config.yaml` override for custom class lists
- Unicode & emoji path support (Windows `GetShortPathNameW` fix for OpenCV)
- OpenMP dual-load crash prevention (`KMP_DUPLICATE_LIB_OK`)

---

## Quick Start

```bash
git clone https://github.com/atakhanyilmaz/yolo-dataset-studio.git
cd yolo-dataset-studio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python app.py
```

---

## Installation

### Requirements

- Python 3.10 +
- CUDA 12.x + NVIDIA driver *(optional — CPU fallback available)*

### Step-by-step

```bash
# 1. Clone
git clone https://github.com/atakhanyilmaz/yolo-dataset-studio.git
cd yolo-dataset-studio

# 2. PyTorch with CUDA (skip for CPU-only)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 3. Remaining dependencies
pip install -r requirements.txt

# 4. Verify CUDA
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 5. Create output directories (Windows)
.\setup_dirs.ps1

# 6. Launch
python app.py
```

> **Conda users:** run everything inside your activated environment.

---

## Configuration

`config.yaml` controls the default model, class list, colors, and I/O paths.
The GUI reads this file at startup; every value can be overridden from the UI.

```yaml
project_name: "VisionFlow Auto Label"
device: "cuda"          # "cuda" | "cpu"

model:
  path: "yolo11n.pt"    # relative or absolute path to .pt weights
  img_size: 640
  conf_threshold: 0.5
  iou_threshold: 0.45

# COCO-80 class list (indices must match your model's output)
classes:
  - person
  - bicycle
  - car
  # ... 77 more classes

# BGR color per class for annotated image overlays
class_colors:
  person:     [0, 255, 0]
  bicycle:    [0, 165, 255]
  car:        [255, 0, 0]
  # ...

input:
  images_dir: "uploads/to_label/images"
  extensions: [".jpg", ".jpeg", ".png"]

output:
  labels_txt_dir:  "outputs/auto_label/labels_txt"
  labels_json_dir: "outputs/auto_label/labels_json"
  annotated_dir:   "outputs/auto_label/annotated"
  report_dir:      "outputs/auto_label/report"

options:
  save_txt:       true
  save_json:      true
  save_annotated: true
  skip_empty:     false   # skip images with zero detections
  warmup_images:  5       # excluded from FPS averaging
```

---

## GUI Usage

### Tab 1 — Frame Extract

| Field | Description |
|---|---|
| Video path | Any format supported by OpenCV (mp4, avi, mkv …) |
| Output folder | Destination for extracted `.jpg` frames |
| Mode | `every_nth` / `fps` / `motion` |
| Nth frame | Used when mode = `every_nth` |
| Target FPS | Used when mode = `fps` |
| Motion threshold | Mean absolute difference score cutoff (mode = `motion`) |

Click **▶ Başlat** to start. A 6-frame random preview is shown before extraction.

### Tab 2 — Auto Label

| Field | Description |
|---|---|
| Görsel klasörü | Folder containing images to label |
| Model yolu | Path to YOLO `.pt` weights |
| Çıktı kök klasörü | Root; sub-folders `labels_txt/`, `labels_json/`, `annotated/`, `report/` are created automatically |
| Conf eşiği | Detection confidence threshold |
| IOU eşiği | NMS IOU threshold |
| Görsel boyutu | Inference input resolution |
| Device | `cuda` or `cpu` |
| Save TXT | Write YOLO `.txt` label files |
| Save JSON | Write structured JSON label files |
| Save Annotated | Write images with drawn bounding boxes |
| Skip Empty | Skip writing output for images with no detections |

### Tab 3 — Augmentation

| Field | Description |
|---|---|
| Görsel klasörü | Folder containing source images |
| Etiket klasörü (.txt) | Folder containing matching YOLO `.txt` labels (can differ from image folder) |
| Çıktı klasörü | Root output; `images/` and `labels/` sub-folders are created |
| Multiplier | Number of augmented copies per source image |

Each transform group (Geometrik, Fotometrik, Bulanıklık, Gürültü) can be toggled on/off as a whole. Individual transforms inside each group are independently switchable with adjustable parameters.

---

## CLI Usage

Run auto-labeling without the GUI using `auto_label.py`. It reads `config.yaml` from the same directory.

```bash
# Edit config.yaml first, then:
python auto_label.py
```

**Example output:**

```
[GPU] CUDA: True
[GPU] NVIDIA GeForce RTX 4060
[Basliyor] 120 gorsel isleniyor...
  [10/120] frame_000090.jpg — 3 tespit, 12.4ms
  ...
[Rapor] outputs/auto_label/report/report_20260513_143200.*
[Tamamlandi] Gorsel: 120 | Bos: 4
  FPS: 80.6 | Ort. sure: 12.4ms
  Tespit: {'person': 87, 'bicycle': 23, 'car': 44}
```

---

## API Documentation

### `core.extractor`

```python
from core.extractor import get_video_info, get_preview_frames, run_extraction
```

---

#### `get_video_info(video_path) -> dict | None`

Returns metadata for a video file.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `video_path` | `str \| Path` | Absolute or relative path to the video file. Unicode / emoji paths are handled automatically via `GetShortPathNameW`. |

**Returns** `dict` with keys:

| Key | Type | Description |
|---|---|---|
| `total_frames` | `int` | Total frame count |
| `fps` | `float` | Frames per second |
| `width` | `int` | Frame width in pixels |
| `height` | `int` | Frame height in pixels |
| `duration` | `float` | Duration in seconds |

Returns `None` if the file cannot be opened.

---

#### `get_preview_frames(video_path, n=6) -> list[np.ndarray]`

Samples `n` random frames from a video for preview purposes.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `video_path` | `str \| Path` | — | Path to video |
| `n` | `int` | `6` | Number of frames to sample |

**Returns** List of BGR `np.ndarray` frames (may be shorter than `n` if the video has fewer frames).

---

#### `run_extraction(cfg, log_cb, progress_cb, stop_flag) -> int`

Main frame extraction pipeline. Reads a video and writes frames to disk based on the selected mode.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `cfg` | `dict` | Configuration dict (see below) |
| `log_cb` | `Callable[[str], None]` | Called with log messages |
| `progress_cb` | `Callable[[int, int], None]` | Called with `(current, total)` |
| `stop_flag` | `threading.Event` | Set to request early termination |

**`cfg` keys**

| Key | Type | Description |
|---|---|---|
| `video_path` | `str` | Source video path |
| `output_dir` | `str` | Directory to write frames |
| `mode` | `str` | `"every_nth"` / `"fps"` / `"motion"` |
| `nth` | `int` | Frame interval (mode = `every_nth`) |
| `target_fps` | `float` | Target frames per second (mode = `fps`) |
| `motion_thresh` | `float` | Minimum mean-absolute-difference to save (mode = `motion`) |

**Returns** `int` — number of frames saved.

---

### `core.labeler`

```python
from core.labeler import run_pipeline
```

---

#### `run_pipeline(cfg, log_cb, progress_cb, stop_flag) -> dict | None`

Full auto-labeling pipeline: loads model, runs inference on every image in the input directory, writes labels and annotated images, and generates a report.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `cfg` | `dict` | Full configuration dict (mirrors `config.yaml` structure) |
| `log_cb` | `Callable[[str], None]` | Called with log messages |
| `progress_cb` | `Callable[[int, int], None]` | Called with `(current, total)` |
| `stop_flag` | `threading.Event` | Set to request early termination |

**`cfg` structure**

```python
{
    "device": "cuda",                  # "cuda" | "cpu"
    "model": {
        "path": "yolo11n.pt",
        "img_size": 640,
        "conf_threshold": 0.5,
        "iou_threshold": 0.45,
    },
    "classes": ["person", "bicycle", ...],   # list of class names (index = class_id)
    "class_colors": {"person": [0,255,0]},   # BGR colors for annotation overlay
    "input": {
        "images_dir": "path/to/images",
        "extensions": [".jpg", ".jpeg", ".png"],
    },
    "output": {
        "labels_txt_dir":  "out/labels_txt",
        "labels_json_dir": "out/labels_json",
        "annotated_dir":   "out/annotated",
        "report_dir":      "out/report",
    },
    "options": {
        "save_txt":       True,
        "save_json":      True,
        "save_annotated": True,
        "skip_empty":     False,
        "warmup_images":  5,
    },
}
```

**Returns** `dict` with pipeline statistics:

```python
{
    "total_images": 120,
    "detections": {"person": 87, "car": 44, ...},
    "empty_images": 4,
    "fps": 80.6,
    "avg_ms": 12.4,
}
```

Returns `None` if no images were found.

---

#### Internal helpers

| Function | Signature | Description |
|---|---|---|
| `setup_dirs` | `(cfg) -> None` | Creates output directories |
| `get_images` | `(cfg) -> list[Path]` | Returns sorted list of input images |
| `draw_bbox` | `(img, det, class_colors) -> np.ndarray` | Draws a labeled bounding box on a BGR image |
| `save_txt` | `(path, detections) -> None` | Writes YOLO `.txt` format label file |
| `save_json_label` | `(path, img_name, w, h, detections) -> None` | Writes structured JSON label file |
| `generate_report` | `(stats, cfg) -> str` | Writes JSON + PNG chart + HTML report; returns base path |

---

### `core.augmentor`

```python
from core.augmentor import run_augmentation
```

---

#### `run_augmentation(cfg, log_cb, progress_cb, stop_flag) -> None`

Applies an albumentations pipeline to every image-label pair and writes augmented copies.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `cfg` | `dict` | Configuration dict (see below) |
| `log_cb` | `Callable[[str], None]` | Log callback |
| `progress_cb` | `Callable[[int, int], None]` | Progress callback `(done, total)` |
| `stop_flag` | `threading.Event` | Stop signal |

**`cfg` keys**

| Key | Type | Description |
|---|---|---|
| `input_dir` | `str` | Folder containing source images |
| `labels_dir` | `str \| None` | Folder containing `.txt` labels. If `None`, labels are expected alongside images. |
| `output_dir` | `str` | Root output folder. `images/` and `labels/` sub-folders are created automatically. |
| `multiplier` | `int` | Number of augmented copies per image |
| `geometric` | `dict` | Geometric transform group config (see below) |
| `photometric_linear` | `dict` | Brightness/contrast config |
| `photometric_gamma` | `dict` | Gamma/CLAHE config |
| `photometric_color` | `dict` | HSV / ColorJitter config |
| `blur` | `dict` | Blur transforms config |
| `noise` | `dict` | Noise transforms config |

**Transform group schema (geometric example)**

```python
"geometric": {
    "enabled": True,
    "horizontal_flip": {"enabled": True, "p": 0.5},
    "affine": {
        "enabled": True,
        "scale_min": 0.9, "scale_max": 1.1,
        "rotate_min": -15, "rotate_max": 15,
        "shear_min": -5,  "shear_max": 5,
        "p": 0.5,
    },
},
```

All other groups follow the same `{"enabled": bool, "<transform_name>": {"enabled": bool, ...params..., "p": float}}` pattern.

**Output structure**

```
output_dir/
├── images/
│   ├── frame_000000_aug0000.jpg
│   ├── frame_000000_aug0001.jpg
│   └── ...
└── labels/
    ├── frame_000000_aug0000.txt
    ├── frame_000000_aug0001.txt
    └── ...
```

---

#### Internal helpers

| Function | Signature | Description |
|---|---|---|
| `parse_yolo_txt` | `(txt_path) -> (list, list)` | Parses a YOLO `.txt` file into `(bboxes, class_ids)` |
| `get_image_label_pairs` | `(input_dir, labels_dir=None) -> list[tuple]` | Returns `[(img_path, txt_path), ...]` pairs |
| `build_pipeline` | `(aug_cfg) -> A.Compose \| None` | Builds an albumentations `Compose` pipeline from config |

---

### `workers`

All workers extend `QThread` and use `pyqtSignal` for thread-safe UI communication.

---

#### `LabelWorker(cfg)`

Runs `core.labeler.run_pipeline` in a background thread.

```python
from workers.label_worker import LabelWorker

worker = LabelWorker(cfg)
worker.log.connect(my_log_slot)           # str
worker.progress.connect(my_prog_slot)    # (int, int)
worker.finished.connect(my_done_slot)    # dict  (stats)
worker.start()
worker.stop()   # requests cancellation via threading.Event
```

---

#### `ExtractWorker(cfg)`

Runs `core.extractor.run_extraction` in a background thread.

```python
from workers.extract_worker import ExtractWorker

worker = ExtractWorker(cfg)
worker.log.connect(...)        # str
worker.progress.connect(...)   # (int, int)
worker.finished.connect(...)   # int  (saved frame count)
worker.start()
worker.stop()
```

#### `PreviewWorker(video_path)`

Fetches 6 random preview frames without blocking the UI.

```python
from workers.extract_worker import PreviewWorker

worker = PreviewWorker(video_path)
worker.preview_ready.connect(...)  # list[np.ndarray]
worker.start()
```

---

#### `AugmentWorker(cfg)`

Runs `core.augmentor.run_augmentation` in a background thread.

```python
from workers.augment_worker import AugmentWorker

worker = AugmentWorker(cfg)
worker.log.connect(...)        # str
worker.progress.connect(...)   # (int, int)
worker.finished.connect(...)   # no args
worker.start()
worker.stop()
```

---

## Output Formats

### YOLO `.txt` label

One detection per line: `class_id cx cy w h` (all normalized 0–1).

```
0 0.512300 0.438700 0.124500 0.213400
2 0.723400 0.612300 0.087600 0.145600
```

### JSON label

```json
{
  "image": "frame_000020.jpg",
  "width": 1280,
  "height": 720,
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.9231,
      "bbox_normalized": { "cx": 0.5123, "cy": 0.4387, "w": 0.1245, "h": 0.2134 },
      "bbox_pixels":     { "x1": 541, "y1": 238, "x2": 700, "y2": 392 }
    }
  ]
}
```

### Report

Three files share the same timestamp prefix (`report_YYYYMMDD_HHMMSS`):

| File | Content |
|---|---|
| `.json` | Raw stats dict |
| `.png` | Bar chart of detections per class (detected classes only, sorted by count) |
| `.html` | Human-readable report with metrics and embedded chart |

---

## Project Structure

```
yolo-dataset-studio/
│
├── app.py                  # Entry point — QApplication, dark palette, KMP fix
├── main_window.py          # Main window, tab container, GPU status badge
├── auto_label.py           # Standalone CLI labeling script
├── config.yaml             # Default model & I/O configuration
├── requirements.txt
├── setup_dirs.ps1          # Windows directory setup
│
├── tabs/
│   ├── extract_tab.py      # Frame Extractor tab (reads config.yaml for defaults)
│   ├── label_tab.py        # Auto Label tab (reads config.yaml for classes/colors)
│   └── augment_tab.py      # Augmentation tab
│
├── workers/
│   ├── extract_worker.py   # QThread wrapper for extractor
│   ├── label_worker.py     # QThread wrapper for labeler
│   └── augment_worker.py   # QThread wrapper for augmentor
│
└── core/
    ├── extractor.py        # Video frame extraction logic
    ├── labeler.py          # YOLO inference + report generation
    └── augmentor.py        # Albumentations pipeline
```

---

## Building .exe

```powershell
# Install PyInstaller
pip install pyinstaller

# Build single-file executable
pyinstaller --onefile --windowed --name "YoloDatasetStudio" `
  --add-data "config.yaml;." `
  --add-data "yolo11n.pt;." `
  app.py
```

Output: `dist\YoloDatasetStudio.exe`

> **Note:** The executable bundles PyTorch, OpenCV, and Albumentations — expect ~700 MB output size and a 10–15 minute build time.

For faster iteration during development, create a desktop shortcut instead:

```powershell
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("$env:USERPROFILE\Desktop\YoloDatasetStudio.lnk")
$s.TargetPath = "C:\path\to\anaconda3\pythonw.exe"
$s.Arguments = "C:\path\to\yolo-dataset-studio\app.py"
$s.WorkingDirectory = "C:\path\to\yolo-dataset-studio"
$s.Save()
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `PyQt5` | ≥ 5.15 | Desktop GUI framework |
| `ultralytics` | latest | YOLO model inference |
| `torch` + `torchvision` | CUDA build | GPU acceleration |
| `opencv-python` | latest | Image & video processing |
| `albumentations` | ≥ 2.0 | Data augmentation transforms |
| `matplotlib` | latest | Report chart generation |
| `pyyaml` | latest | Configuration parsing |
| `numpy` | latest | Array operations |

---

## Known Issues & Fixes

| Issue | Cause | Fix applied |
|---|---|---|
| App crashes during augmentation | `libiomp5md.dll` loaded twice by PyTorch + OpenCV | `os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'` set at startup |
| Video with emoji/unicode filename fails | OpenCV cannot open unicode paths on Windows | `GetShortPathNameW` used to get 8.3 short path before opening |
| `generate_report` crash with 80 classes | Only 4 colors defined for bar chart | `tab20` colormap, only detected classes plotted |

---

## License

MIT
