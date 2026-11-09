# SudokuScan

COMP 482 Computer Vision projesi: basılı Sudoku fotoğrafından dört dış köşe,
A3/A4/H4 düzeltmeleri, 9x9 givens ve geçerlilik kararı üretir. Python, OpenCV,
NumPy ve Tesseract kullanır; CPU üzerinde çalışır.

## Hızlı çalıştırma

Tam paketi bir klasöre çıkarıp `SudokuScan/calistir.cmd` dosyasına çift tıkla.
Paketteki on JPEG otomatik işlenir. Sonuçlar `results/tarama/` klasörüne yazılır.
Kod paketini tek başına kullanıyorsan program fotoğraf veya klasör yolunu sorar.
Python 3.10+ ve Tesseract OCR 5.x (English verisiyle) kurulu olmalıdır.

Windows kurulumu:

```powershell
winget install --exact --id UB-Mannheim.TesseractOCR
powershell -ExecutionPolicy Bypass -File .\kurulum.ps1
```

Tesseract zaten kuruluysa ilk komut gerekli değildir. `TESSERACT_CMD` veya
`--tesseract-cmd` farklı motor konumunu belirtir. `pytesseract` Python paketidir;
OCR motorunun ayrıca kurulması gerekir.

Ubuntu/Debian: `sudo apt install tesseract-ocr tesseract-ocr-eng python3-tk`.
macOS: `brew install tesseract`. Ardından bir sanal ortamda
`pip install -r requirements-dev.txt` çalıştırılır.

## Zorunlu arayüz

```bash
python sudoku_scan.py --input photo.jpg --outdir out/
python sudoku_scan.py --batch images_dir/ --outdir results/
```

Windows'ta ortamı etkinleştirmeden de çalıştırabilirsin:

```powershell
.\.venv\Scripts\python.exe sudoku_scan.py --input photo.jpg --outdir out
powershell -ExecutionPolicy Bypass -File .\calistir.ps1 -Girdi "C:\fotograflar" -Cikti results/benim_taramam
```

Her görüntü için `_grid.txt`, `_result.json`, `_harris.png`, `_rect_A3.png`,
`_rect_A4.png`, `_rect_H4.png` ve `_debug.png` kaydedilir. Grid, ayraçsız dokuz
satırda dokuz rakamdır. Boş hücre 0'dır; okunamayan dolu hücre de 0 yazılır ve
JSON'daki `unread_cells` alanında ayrıca belirtilir. Bulmaca bulunamazsa
`verdict: not_found` üretilir; batch diğer fotoğraflarla sürer.

## Yöntem

1. Boyuta göre ölçeklenen ön işleme, morfolojik aydınlatma düzeltmesi ve Harris/NMS.
2. Kontur bölge önerileri, yalnız Harris adaylarından dört indeks seçimi ve
   10x10 çizgi düzeni puanı. İsteğe bağlı `cornerSubPix` iyileştirmesi.
3. A3 (TL/TR/BL), dört noktanın tümüne least-squares A4 ve H4 homography.
4. Çevrimsel köşe sıraları arasında OCR güvenine göre yön seçimi.
5. Önce açık boş/dolu kararı, sonra gri kenarları koruyan rakam hazırlama ve
   PSM 10 / 1-9 whitelist OCR. Okunamayan hücreye bir kez 2x deneme.
6. Satır/sütun/3x3 kutuda tekrarlanan givens kontrolü.

Otomatik yol annotation, fotoğraf adına bağlı koordinat veya Sudoku çözümü
kullanmaz. Hedef raster 450x450'dir; sürekli hedef sınırı residual hesabı için
0..450, raster örnekleri 0..449'dur. A4 açık dört-nokta LS refiti içerir.
`valid` yalnız tekrarlanan givens olmadığını belirtir; OCR doğruluğu veya tek
çözüm garantisi değildir.

## Son ölçümler

On sağlanan JPEG, geliştirmede de kullanılan fotoğraflardır. Aynı görüntülerde
otomatik H4 sonucu 801/810 hücre (%98,89), 6/10 tam grid, boş/dolu F1 1,00 ve
%0,658 ortalama köşe hatasıdır. On görüntünün tamamı 20 saniye sınırında işlendi.
Bunlar bağımsız test veya hidden-set sonuçları değildir. 28 test geçmektedir.

| Model | Hücre doğruluğu | Çizgi konum hatası | Çizgi aralık hatası |
| --- | ---: | ---: | ---: |
| A3 | %69,63 | 21,35 px | 5,78 px |
| A4 | %73,09 | 14,32 px | 4,49 px |
| H4 | %98,89 | 1,94 px | 1,06 px |

A3'te 200 çizgi denemesinin 13'ü görünür destek bulamadı; A4/H4'te 200/200
ölçüldü. Konum hatası gözlenen çizgiler üzerindedir. Ek grafik, kayıp her çizgiye
50 piksel ceza ekleyerek kırpılma etkisini ayrıca gösterir. Aralık ve doğrusal
uyum hataları ayrı ölçülür; çizgiler her üç modelde de yaklaşık düz kalır.
Ölçüm yöntemi `docs/MODEL_KARSILASTIRMASI.md` içindedir.

Yedi dik görüntüde 12 Harris ayarıyla 84 deney; dört PSM ve ham/hazırlanmış
hücrelerle 80 OCR deneyi tamamlanmıştır. Hazırlanmış PSM 7/10 sonucu %98,89'dur.

## Deneyleri yeniden üretme

Tam pakette veya kod ve veri paketleri aynı klasöre çıkarıldığında:

```powershell
powershell -ExecutionPolicy Bypass -File .\deneyler.ps1 -OgrenciNo NUMARAN
```

Bu işlem otomatik tarama, değerlendirme, model karşılaştırması, manual-geometri
OCR kontrolü, PSM/Harris çalışmaları, veri denetimi ve rapor kaynağını üretir.
Çevrimdışı deneyler, 20 saniyelik zorunlu tarama komutundan ayrıdır.

Tek başına karşılaştırma:

```bash
python tools/compare_models.py --annotations data/received_20261109_zip/annotations --results results/zip_automatic --outdir results/model_comparison
python -m pytest -q
```

`results/model_comparison/` içinde bütün çizgi noktaları, 10x2 çizgi durumları,
OCR gridleri, CSV/JSON tabloları, bindirmeler, residual grafiği ve en eğik
fotoğrafın A3/A4/H4 yan yana görüntüsü vardır. Rapor derleme adımları
`report/README.md` içindedir. Etiketleri gözden geçirmek için `tools/annotate.py`
kullanılabilir; bu araç zorunlu otomatik yolun parçası değildir.

## Veri ve katkı kaydı

Üç Sudoku'nun seçimi, baskı belgeleri, baskılar, telefon çekimleri ve el yazısı
numara/tarih işaretleri proje sahibine aittir. Sağlanan ZIP'teki on JPEG'in
baytları ve SHA-256 özetleri korunmuştur; pikselleri önceki PNG kopyalarıyla
aynıdır. JPEG'lerde EXIF bulunmamaktadır. Üç özgün çevrimiçi kaynak kaydedilmemiş,
annotation'lar öğrenci incelemesi beklemektedir. Bunlar veri/yazarlık kontrolü
konularıdır; çalışan yazılım veya ölçülmüş OCR başarısıyla karıştırılmamalıdır.

Kişisel fotoğraflar, annotation'lar ve öğrenci numaralı rapor public depodan
ayrıdır. Yazılım/rapor yardımının gerçek kapsamı raporun Ek C bölümünde ve
`docs/AI_KULLANIM_BEYANI.md` dosyasında kayıtlıdır.

## Dosyalar

- `sudoku_scan.py`: tek görüntü ve batch giriş noktası.
- `student_corner_selection.py`: Harris adaylarından otomatik sınır seçimi.
- `sudokuscan/`: ön işleme, geometri, OCR, geçerlilik ve çizgi ölçümleri.
- `tools/`: etiketleme, deneyler, rapor ve paketleme.
- `tests/`: 28 doğrulama testi.
- `calistir.cmd` / `calistir.ps1`: normal tarama başlatıcıları.
- `deneyler.ps1`: bütün veri deneylerini yeniden üretme.
- `report/report_template.tex`: boş IEEE şablonu; ölçümlü rapor ayrı pakettedir.

Kaynak API belgeleri: [OpenCV özellik tespiti](https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html),
[geometrik dönüşümler](https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html),
[Tesseract komut satırı](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html).
