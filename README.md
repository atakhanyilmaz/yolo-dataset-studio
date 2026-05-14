# 🚀 YOLO Dataset Studio

<div align="center">
  <p><strong>End-to-end dataset preparation toolkit for YOLO-based object detection projects.</strong></p>
  
  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
  [![PyQt5](https://img.shields.io/badge/GUI-PyQt5-brightgreen.svg?style=flat-square&logo=qt)](https://www.riverbankcomputing.com/software/pyqt/)
  [![PyTorch](https://img.shields.io/badge/Framework-PyTorch-ee4c2c.svg?style=flat-square&logo=pytorch)](https://pytorch.org/)
  [![YOLO](https://img.shields.io/badge/Model-YOLOv8%20%2F%20YOLO11-orange.svg?style=flat-square)](https://github.com/ultralytics/ultralytics)
  [![License](https://img.shields.io/badge/License-MIT-success.svg?style=flat-square)](LICENSE)
</div>

---

A powerful, dark-themed desktop application built with **PyQt5** that streamlines the computer vision workflow. It unifies **🎥 Video Frame Extraction**, **🤖 Automatic Labeling (Inference)**, and **🌟 Advanced Data Augmentation** into a single graphical interface, complemented by full Command-Line Interface (CLI) support.

<p align="center">
  <img width="100%" alt="YOLO Dataset Studio GUI Main" src="https://github.com/user-attachments/assets/5ac047c5-9331-4d5b-91b7-dda118f5ff4e" />
</p>
<p align="center">
  <img width="100%" alt="YOLO Dataset Studio GUI Settings" src="https://github.com/user-attachments/assets/aee76832-9f67-4bd2-8fa0-9b8ea021b77e" />
</p>

---

## 📑 Table of Contents

- [✨ Key Features](#-key-features)
- [⚡ Quick Start](#-quick-start)
- [🛠️ Installation](#️-installation)
  - [Prerequisites](#prerequisites)
  - [Step-by-Step Guide](#step-by-step-guide)
- [⚙️ Configuration](#️-configuration)
- [🖥️ GUI Reference](#️-gui-reference)
  - [🎥 Tab 1 — Frame Extract](#-tab-1--frame-extract)
  - [🤖 Tab 2 — Auto Label](#-tab-2--auto-label)
  - [🌟 Tab 3 — Augmentation](#-tab-3--augmentation)
- [💻 CLI Usage](#-cli-usage)
- [📦 Output Formats](#-output-formats)
- [📚 API Documentation](#-api-documentation)
- [🏗️ Project Architecture](#️-project-architecture)
- [🚀 Building the Executable (.exe)](#-building-the-executable-exe)
- [📦 Dependencies](#-dependencies)
- [🐛 Known Issues & Technical Solutions](#-known-issues--technical-solutions)
- [📜 License](#-license)

---

## ✨ Key Features

| Core Module | Core Capabilities |
| :--- | :--- |
| **🎥 Frame Extractor** | Extract frames using **Every-Nth**, **Target-FPS**, or **Motion-Threshold** sampling from any video file. Includes visual pre-sampling preview. |
| **🤖 Auto Labeler** | Batch inference using any YOLO model → generates `.txt` (YOLO format), structured `.json`, visualized images with drawn bounding boxes, and rich HTML/Chart reports. |
| **🌟 Data Augmentor** | 12 configurable **Albumentations** transforms grouped into Geometric, Photometric, Blur, and Noise. Independent sub-toggles and dataset scaling via custom multiplier. |

### 🔒 Enterprise & Technical Refinements
- **Hardware Acceleration:** Seamless **CUDA / CPU** device toggling per workflow.
- **Asynchronous GUI:** Multi-threaded architecture utilizing `QThread` and custom workers prevents UI freezes during long-running tasks.
- **Model Agnostic:** Out-of-the-box compatibility with **YOLOv8**, **YOLO11**, or custom fine-tuned `.pt` weights. Includes full default mapping for all 80 COCO classes.
- **Robust Path Handling:** Fully supports Unicode and emoji file/directory paths on Windows via native `GetShortPathNameW` pre-resolution for OpenCV integration.
- **Stability Safeguards:** Built-in mitigation for OpenMP multiple-runtime collisions (`KMP_DUPLICATE_LIB_OK`).

---

## ⚡ Quick Start

Get up and running immediately using the terminal:

```bash
git clone https://github.com/atakhanyilmaz/yolo-dataset-studio.git
cd yolo-dataset-studio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python app.py
```

---

## 🛠️ Installation

### Prerequisites
- **Operating System:** Windows, Linux, or macOS.
- **Python:** Version **3.10** or higher.
- **Hardware:** NVIDIA GPU with CUDA 12.x support highly recommended for fast inference (seamless CPU fallback available).

### Step-by-Step Guide

```bash
# 1. Clone the repository
git clone https://github.com/atakhanyilmaz/yolo-dataset-studio.git
cd yolo-dataset-studio

# 2. Install PyTorch with CUDA acceleration (omit --index-url for CPU-only environments)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 3. Install core application dependencies
pip install -r requirements.txt

# 4. Verify GPU availability
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"

# 5. Initialize project output folder hierarchy (Windows PowerShell)
.\setup_dirs.ps1

# 6. Launch the desktop studio
python app.py
```

> **💡 Conda Users:** Ensure your terminal environment is fully activated before running installation commands and execution scripts.

---

## ⚙️ Configuration

The central `config.yaml` file defines default behaviors, initial neural network parameters, input/output structures, and custom annotation visual color overlays. Every configuration value loaded at startup can be directly overridden within the application's graphical user interface.

<details>
<summary><b>Click to view default <code>config.yaml</code> structure</b></summary>

```yaml
project_name: "VisionFlow Auto Label"
device: "cuda"          # "cuda" | "cpu"

model:
  path: "yolo11n.pt"    # Relative or absolute path to target weights
  img_size: 640
  conf_threshold: 0.5
  iou_threshold: 0.45

# COCO-80 target class indices corresponding to model outputs
classes:
  - person
  - bicycle
  - car
  # ... remaining 77 classes

# Annotation overlay visualization BGR hex codes
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
  skip_empty:     false   # Set to true to filter out zero-detection frames
  warmup_images:  5       # Excluded from active inference profiling
```
</details>

---

## 🖥️ GUI Reference

### 🎥 Tab 1 — Frame Extract
Extract optimal image frames from raw video sources using customizable sampling algorithms.

| Interface Element | Operational Description |
| :--- | :--- |
| **Video path** | Accepts standard container formats supported by OpenCV (`.mp4`, `.avi`, `.mkv`, `.mov`). |
| **Output folder** | Designated local target directory for written `.jpg` image sequence frames. |
| **Mode Selection** | Choose between `every_nth` (interval), `fps` (temporal target), or `motion` (dynamic change). |
| **Nth frame** | Specifies frame gap distance when mode is set to `every_nth`. |
| **Target FPS** | Downsamples video playback temporal speed to absolute frames per second. |
| **Motion threshold** | Absolute pixel delta differential limit filter for capturing scene activity. |

> **🚀 Pro-tip:** Press **▶ Başlat** to instantiate extraction. A responsive 6-frame randomized grid preview previews footage content dynamically prior to disk writes.

### 🤖 Tab 2 — Auto Label
Automate object bounding box annotation workflows across vast unlabelled directories using raw inference power.

| Interface Element | Operational Description |
| :--- | :--- |
| **Görsel klasörü** | Directory path holding source frames/images awaiting machine detection. |
| **Model yolu** | Local file system trajectory to selected YOLO weights file (`.pt`). |
| **Çıktı kök klasörü** | Base location where partitioned structural sub-folders are constructed automatically. |
| **Conf eşiği** | Detection filter threshold value rejecting untrusted background classifications. |
| **IOU eşiği** | Non-Maximum Suppression overlap threshold preventing duplicate overlapping predictions. |
| **Görsel boyutu** | Square pixel target dimension fed directly into network processing layers. |
| **Device Toggle** | Direct computational device target override (`cuda` vs `cpu`). |
| **Output Flags** | Checkbox toggles enabling concurrent output stream writes (`TXT`, `JSON`, `Annotated`). |
| **Skip Empty** | Skip writing outputs for images with zero valid detections. |

### 🌟 Tab 3 — Augmentation
Multiply dataset scale and network robustness through tailored synthetic transformations.

| Interface Element | Operational Description |
| :--- | :--- |
| **Görsel klasörü** | Source directory containing ground-truth unaugmented base images. |
| **Etiket klasörü (.txt)** | Folder housing matched standard YOLO label files. |
| **Çıktı klasörü** | Destination root path outputting parallel expanded `images/` and `labels/` structures. |
| **Multiplier** | Integer defining output count factor generation per singular input item. |

> **🎛️ Modular Toggling:** Primary filter blocks (*Geometrik*, *Fotometrik*, *Bulanıklık*, *Gürültü*) toggle collectively. Embedded granular variations configure independent application probabilities (`p`) and transformation intensities.

---

## 💻 CLI Usage

Execute headless high-performance batch auto-labeling directly from standard shells using the standalone script. Parameters automatically inherit configurations defined in `config.yaml`.

```bash
python auto_label.py
```

**Real-time Console Output Trace:**
```text
[GPU] CUDA: True
[GPU] NVIDIA GeForce RTX 4060
[Basliyor] 120 gorsel isleniyor...
  [10/120] frame_000090.jpg — 3 tespit, 12.4ms
  [20/120] frame_000100.jpg — 5 tespit, 11.8ms
  ...
[Rapor] outputs/auto_label/report/report_20260513_143200.html
[Tamamlandi] Gorsel: 120 | Bos: 4
  FPS: 80.6 | Ort. sure: 12.4ms
  Tespit: {'person': 87, 'bicycle': 23, 'car': 44}
```

---

## 📦 Output Formats

### 1. Standard YOLO `.txt` Label
Formatted explicitly for model input training pipelines. Every line reflects a singular detected object class alongside its normalized spatial constraints: `class_id cx cy w h` (domain mapped between `0.0` and `1.0`).

```text
0 0.512300 0.438700 0.124500 0.213400
2 0.723400 0.612300 0.087600 0.145600
```

### 2. Comprehensive JSON Payload
Enriched data outputs highly optimized for external integration, persistent database ingestion, and detailed analytics tracking.

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

### 3. Analytics Report Bundle
Executions generate an associated snapshot bundle utilizing cohesive shared timestamps (`report_YYYYMMDD_HHMMSS`):
- **`.json`**: Serialized absolute operational statistics array.
- **`.png`**: Crisp graphical distribution histogram plotting target object presence metrics.
- **`.html`**: Highly stylized executive visual dashboard presentation integrating embedded chart distributions.

---

## 📚 API Documentation

Integrate studio backends programmatically into external scripting routines.

### `core.extractor`
```python
from core.extractor import get_video_info, get_preview_frames, run_extraction
```

#### `get_video_info(video_path: str | Path) -> dict | None`
Parses physical video container parameters directly via low-level stream reading. Resolves Windows absolute Unicode strings securely. Returns metadata dictionary containing `total_frames`, `fps`, `width`, `height`, and `duration`.

#### `get_preview_frames(video_path: str | Path, n: int = 6) -> list[np.ndarray]`
Extracts random, non-contiguous raw memory representations (BGR `numpy` multidimensional matrices) across video boundaries for UI rendering pipelines.

#### `run_extraction(cfg: dict, log_cb: Callable, progress_cb: Callable, stop_flag: threading.Event) -> int`
Executes configured sequential frame captures driven by requested algorithmic sampling modes. Safe thread execution allows unconstrained cross-thread interrupts. Returns final output written frame quantity.

---

### `core.labeler`
```python
from core.labeler import run_pipeline
```

#### `run_pipeline(cfg: dict, log_cb: Callable, progress_cb: Callable, stop_flag: threading.Event) -> dict | None`
Instantiates local torch memory architectures, ingests configuration maps, sweeps directories sequentially executing NMS threshold filtering, and handles parallel storage pipelines. Returns finalized dictionary summary structures.

---

### `core.augmentor`
```python
from core.augmentor import run_augmentation
```

#### `run_augmentation(cfg: dict, log_cb: Callable, progress_cb: Callable, stop_flag: threading.Event) -> None`
Deploys dynamically created complex composition pipelines utilizing **Albumentations**. Reads companion coordinate map annotations and executes precise bounding-box spatial recalculations across multiple multiplied output variants simultaneously.

---

### `workers`
All underlying processing modules utilize robust threading constructs extending `QThread` combined with standard `pyqtSignal` events for thread-safe cross-boundary communication.

#### Background Execution Controllers
- **`LabelWorker(cfg)`**: Wraps `core.labeler.run_pipeline` execution. Dispatches `log`, `progress`, and `finished` signals asynchronously.
- **`ExtractWorker(cfg)`**: Offloads `core.extractor.run_extraction` video decoding loops. Prevents interactive UI frame-drops.
- **`PreviewWorker(video_path)`**: Concurrently retrieves video sample arrays populating preview layout placeholders dynamically.
- **`AugmentWorker(cfg)`**: Handles high-throughput synthetic operations across expansive disk files concurrently.

---

## 🏗️ Project Architecture

A clean, highly modular architecture decoupling core processing logic from view rendering layers.

```text
yolo-dataset-studio/
│
├── app.py                  # Primary application loop initializer, stylesheet injection
├── main_window.py          # View container orchestrating modular tab navigation interfaces
├── auto_label.py           # Standalone command-line inference script runner
├── config.yaml             # Source-of-truth application configuration defaults
├── requirements.txt        # Verified dependency execution locking array
├── setup_dirs.ps1          # Initial automated local directory scaffolding helper
│
├── tabs/                   # Visual presentation and layout definitions
│   ├── extract_tab.py      # Video source ingestion and interval configuration form
│   ├── label_tab.py        # Automated labeling controls and override bindings
│   └── augment_tab.py      # Albumentations parameters state interface
│
├── workers/                # Concurrency handlers implementing thread boundaries
│   ├── extract_worker.py   # Background processing layer handling frame extraction
│   ├── label_worker.py     # Inference execution context keeping UI active
│   └── augment_worker.py   # Synthetic pipeline processing thread manager
│
└── core/                   # Underlying engine logic and analytical operations
    ├── extractor.py        # Container analysis and raw frame parsing algorithms
    ├── labeler.py          # YOLO model interfacing, output styling, and reporting
    └── augmentor.py        # Spatial array transforms and multi-tier composition
```

---

## 🚀 Building the Executable (.exe)

Convert the modular project repository into an isolated standalone Windows binary app for simplified distribution across production environments.

```powershell
# 1. Install packaging toolkit
pip install pyinstaller

# 2. Compile standalone binary application bundle
pyinstaller --onefile --windowed --name "YoloDatasetStudio" `
  --add-data "config.yaml;." `
  --add-data "yolo11n.pt;." `
  app.py
```

Target Executable Location: `dist\YoloDatasetStudio.exe`

> **⚠️ Deployment Footprint Alert:** Bundling comprehensive computer vision backends (*PyTorch*, *OpenCV*, *Albumentations*) results in binary build packages approx. **~700 MB** in total size. Full linking phases require roughly **10–15 minutes** compilation time depending on local CPU capabilities.

### 💡 Lightweight Local Alternative (Desktop Shortcut)
For rapid local iterative staging without building a heavy standalone payload, instantiate a dedicated runtime launcher shortcut:

```powershell
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("$env:USERPROFILE\Desktop\YoloDatasetStudio.lnk")
$s.TargetPath = "C:\path\to\anaconda3\pythonw.exe"
$s.Arguments = "C:\path\to\yolo-dataset-studio\app.py"
$s.WorkingDirectory = "C:\path\to\yolo-dataset-studio"
$s.Save()
```

---

## 📦 Dependencies

| Verified Package | Minimum Target | Purpose / Operational Boundary |
| :--- | :--- | :--- |
| `PyQt5` | ≥ 5.15 | Provides core desktop layout management and thread loop handling. |
| `ultralytics` | latest | Interfacing target deep-learning network architectures and forward layers. |
| `torch` + `torchvision` | CUDA build | Tensor math processing leveraging underlying hardware silicon. |
| `opencv-python` | latest | Matrix frame decoding, pre-scaling, and visual drawing operations. |
| `albumentations` | ≥ 2.0 | Mathematical structural coordinate manipulation and matrix filters. |
| `matplotlib` | latest | High-fidelity graph construction and analytics visualization. |
| `pyyaml` | latest | Structural configuration parsing and disk persistent storage. |
| `numpy` | latest | Contiguous multidimensional numeric array storage and indexing. |

---

## 🐛 Known Issues & Technical Solutions

| Identifiable Behavior | Underlying Technical Catalyst | Automated Engineering Fix Applied |
| :--- | :--- | :--- |
| **Application aborts during augmentation** | Dual redundant load events of `libiomp5md.dll` via separate compilation hooks in PyTorch and OpenCV. | Runtime environment variable mutation injected during core initialization: `os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'` |
| **Path access fails on non-standard strings** | Standard Windows system API wrappers struggle resolving Unicode path spaces inside low-level C++ calls. | Dynamic implementation of Win32 kernel function `GetShortPathNameW` generating robust legacy 8.3 short paths. |
| **Report build errors across extensive sets** | Default baseline Matplotlib charts exhaust basic palette maps across 80-item classifications. | Enhanced visual color matrix implementation using `tab20` dynamically restricted to actively present labels. |

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for further information.

<p align="center">
  Made with ❤️ for the Computer Vision Community.
</p>
