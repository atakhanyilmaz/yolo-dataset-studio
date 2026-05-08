# YOLO Dataset Studio

YOLO tabanlı nesne tespiti projeleri için uçtan uca veri hazırlama araç seti.  
Video'dan frame çekme, otomatik etiketleme ve veri artırma işlemlerini tek arayüzde sunan PyQt5 masaüstü uygulaması.

---

## Özellikler

### 1 · Frame Extractor
Video dosyalarından eğitim için frame çıkarır.
- **Her N. frame** — sabit aralıklı örnekleme
- **Saniyede X frame** — zaman bazlı örnekleme
- **Hareket eşiği** — fark skoru düşük olan benzer kareleri atlar, yalnızca farklı sahneleri kaydeder
- Video bilgisi otomatik doldurma (süre, FPS, çözünürlük, tahmini çıktı)
- 6 rastgele frame önizleme

### 2 · Auto Label
Eğitilmiş YOLO modeli ile toplu otomatik etiketleme.
- YOLO `.txt` + JSON etiket dosyası üretimi
- Bounding box çizilmiş görsel kaydetme
- CUDA (RTX 4060) hızlandırma
- HTML + PNG istatistik raporu

**Varsayılan sınıflar:** `ballistic_missile` · `helicopter` · `f-16` · `drone`

### 3 · Augmentation
albumentations tabanlı veri artırma pipeline'ı.

| Grup | Dönüşümler |
|---|---|
| Geometrik | HorizontalFlip, Affine |
| Fotometrik — Lineer | BrightnessContrast |
| Fotometrik — Gamma | RandomGamma, CLAHE |
| Fotometrik — Renk | HueSaturationValue, ColorJitter |
| Bulanıklık | MotionBlur, GaussianBlur, Defocus |
| Sensör Gürültüsü | GaussNoise, ImageCompression |

Her dönüşüm grup ve bireysel düzeyde açılıp kapatılabilir; parametreler UI'dan ayarlanır.

---

## Kurulum

### Gereksinimler
- Python 3.10+
- CUDA 12.x + NVIDIA driver (GPU hızlandırma için)

### Adımlar

```bash
# 1. Repoyu klonla
git clone https://github.com/KULLANICI_ADI/yolo-dataset-studio.git
cd yolo-dataset-studio

# 2. PyTorch CUDA build kur (CPU kullanacaksan bu adımı atla)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 3. Diğer bağımlılıklar
pip install -r requirements.txt

# 4. CUDA kontrolü
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 5. Klasör yapısını oluştur
.\setup_dirs.ps1

# 6. Uygulamayı başlat
python app.py
```

---

## Proje Yapısı

```
iyhss_data_prepare/
│
├── app.py                  # Giriş noktası — QApplication, dark tema
├── main_window.py          # Ana pencere, sekme yönetimi, GPU badge
│
├── tabs/
│   ├── extract_tab.py      # Frame Extractor sekmesi
│   ├── label_tab.py        # Auto Label sekmesi
│   └── augment_tab.py      # Augmentation sekmesi
│
├── workers/
│   ├── extract_worker.py   # QThread — video frame çıkarma
│   ├── label_worker.py     # QThread — YOLO inference
│   └── augment_worker.py   # QThread — albumentations pipeline
│
├── core/
│   ├── extractor.py        # Frame çıkarma mantığı
│   ├── labeler.py          # Auto-label pipeline (callback tabanlı)
│   └── augmentor.py        # Augmentation pipeline
│
├── config.yaml             # Model ve klasör yapılandırması
├── auto_label.py           # Bağımsız CLI scripti (GUI olmadan çalışır)
├── setup_dirs.ps1          # Windows klasör kurulum scripti
└── requirements.txt
```

---

## Yapılandırma

`config.yaml` düzenleyerek model yolunu ve çıktı klasörlerini ayarlayın:

```yaml
model:
  path: "C:/Users/KULLANICI/Documents/iyhss/weights/yolo26s/best.pt"
  img_size: 640
  conf_threshold: 0.5
  iou_threshold: 0.45

input:
  images_dir: "C:/Users/KULLANICI/datasets/to_label/images"

output:
  labels_txt_dir:  "C:/Users/KULLANICI/results/auto_label/labels_txt"
  labels_json_dir: "C:/Users/KULLANICI/results/auto_label/labels_json"
  annotated_dir:   "C:/Users/KULLANICI/results/auto_label/annotated"
  report_dir:      "C:/Users/KULLANICI/results/auto_label/report"
```

---

## CLI Kullanımı (GUI olmadan)

```bash
# config.yaml'ı düzenledikten sonra
python auto_label.py
```

---

## .exe Derleme

```bash
pip install pyinstaller

pyinstaller --noconfirm --onedir --windowed \
    --name "IYHSS_DataPrepare" \
    --add-data "config.yaml;." \
    --hidden-import=PyQt5.sip \
    --collect-all=ultralytics \
    --collect-all=albumentations \
    app.py
```

Çıktı: `dist/IYHSS_DataPrepare/IYHSS_DataPrepare.exe`

---

## Bağımlılıklar

| Paket | Amaç |
|---|---|
| PyQt5 | Masaüstü GUI |
| ultralytics | YOLO model inference |
| torch + torchvision | CUDA hızlandırma |
| opencv-python | Görüntü işleme, video okuma |
| albumentations | Veri artırma dönüşümleri |
| matplotlib | Rapor grafikleri |
| pyyaml | Yapılandırma dosyası |

---

## Lisans

MIT
