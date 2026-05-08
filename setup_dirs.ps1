# IYHSS Auto-Label — Klasor yapisi kurulumu
$dirs = @(
    "C:\Users\Atakan\Documents\iyhss\weights\yolo26s",
    "C:\Users\Atakan\datasets\to_label\images",
    "C:\Users\Atakan\results\auto_label\labels_txt",
    "C:\Users\Atakan\results\auto_label\labels_json",
    "C:\Users\Atakan\results\auto_label\annotated",
    "C:\Users\Atakan\results\auto_label\report"
)

foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
    Write-Host "[OK] $d"
}

Write-Host ""
Write-Host "UYARI: best.pt dosyanizi asagidaki klasore kopyalayin:" -ForegroundColor Yellow
Write-Host "  C:\Users\Atakan\Documents\iyhss\weights\yolo26s\best.pt" -ForegroundColor Cyan
Write-Host ""
Write-Host "Gorsellerinizi asagidaki klasore koyun:" -ForegroundColor Yellow
Write-Host "  C:\Users\Atakan\datasets\to_label\images\" -ForegroundColor Cyan
Write-Host ""
Write-Host "Hazir oldugunda calistirin: python auto_label.py" -ForegroundColor Green
