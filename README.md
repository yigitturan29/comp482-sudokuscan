# SudokuScan

COMP 482 Computer Vision projesi. Basılı Sudoku fotoğraflarının geometrik olarak
düzeltilmesi, hücrelere ayrılması ve rakamların dijital 9x9 ızgaraya aktarılması
üzerine kuruludur. Python, OpenCV, NumPy ve Tesseract kullanılır; GPU gerekmez.

## Mevcut sürüm

Ön işleme, Harris cevabı ve aday üretimi, A3/A4/H4 dönüşümleri, dolu/boş hücre
kararı, OCR ve Sudoku geçerlilik kontrolü uygulanmıştır. Otomatik dış köşe seçimi
`student_corner_selection.py` içindedir: konturlar bölge önerir, son dört nokta
Harris adaylarından seçilir ve 10x10 çizgi düzeniyle puanlanır. Yön seçimi OCR
güvenine dayanır. Affine/homography karşılaştırmasının çizgi ölçümleri ve sonuç
analizi hâlâ tamamlanacaktır.

## Kurulum

Python 3.10+ ve English verisiyle Tesseract OCR 5.x gerekir. Windows:

```powershell
winget install --exact --id UB-Mannheim.TesseractOCR
powershell -ExecutionPolicy Bypass -File .\kurulum.ps1
```

Tesseract zaten kuruluysa ilk komut gerekli değildir. Farklı bir konum için
`TESSERACT_CMD` değişkeni veya `--tesseract-cmd` seçeneği kullanılabilir.
Yalnızca `pytesseract` paketini yüklemek OCR motorunu kurmaz.

Linux/macOS:

```bash
# Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-eng python3-tk
# macOS: brew install tesseract
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Çalıştırma

Sentetik görüntü üzerinde dönüşüm, OCR ve geçerlilik denemesi:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo.ps1
```

Demo bilinen sentetik köşeleri kullanır. Otomatik arayüzün komutları:

```bash
python sudoku_scan.py --input photo.jpg --outdir out/
python sudoku_scan.py --batch images_dir/ --outdir results/
```

Seçim bulunamadığında `verdict: not_found` kaydedilir; batch diğer görüntülerle sürer.
Başarılı görüntülerde `_grid.txt`, `_result.json`, `_harris.png`, `_rect_A3.png`,
`_rect_A4.png`, `_rect_H4.png` ve `_debug.png` üretilir. Grid dosyası ayraçsız
9 satır x 9 rakamdır; boş hücre 0 ile gösterilir. Köşeler orijinal piksel
koordinatlarında, TL/TR/BR/BL sırasında yazılır. Rectification boyutu 450x450'dir.

## Veri kümesi ve ölçümler

Üç Sudoku için baskı belgeleri hazırlanmış ve toplam 10 fotoğraf 3/3/4 dağılımıyla
çekilmiştir. Bulmaca seçimi, belge/çıktı hazırlama, fotoğraf çekimi ve el yazısı
numara/tarih işaretleri proje sahibine aittir. Fotoğraflar ve annotation'lar kişisel
veri içerdiği için kod deposundan ayrı tutulur.

| Ölçüm | Ham hücre | Hazırlanmış hücre |
| --- | ---: | ---: |
| Doğru hücre | 741/810 | 802/810 |
| Hücre doğruluğu | %91,48 | %99,01 |
| Tam doğru ızgara | 0/10 | 6/10 |
| Boş hücre F1 | 1,00 | 1,00 |

Bu tablo elle verilen H4 köşeleriyle yapılan OCR geliştirme deneyini gösterir.
Aynı fotoğraflar hazırlama ayarlarının geliştirilmesinde de kullanılmıştır;
sonuçlar bağımsız test veya hidden-set performansı olarak yorumlanmamalıdır.
Annotation incelemesi ve orijinal telefon dosyalarının EXIF kontrolü beklemektedir.

Yerel veri paketi açıldıktan sonra aynı deneyi üretmek için:

```bash
python tools/preview_annotations.py --images data/received_20261109/images --annotations data/received_20261109/annotations --outdir results/annotation_preview
```

Güncel hazırlama: %8 iç hücre marjı, morfolojik arka plan düzeltmesi,
bağlı bileşen filtresi, gri kenarları koruyan rakam izolasyonu ve beyaz dolgu.
OCR, PSM 10 ve `123456789` whitelist kullanır. Okunamayan dolu hücreye aynı
ayarlarla bir kez 2x büyütme denemesi yapılır; ham/hazırlanmış kolların kuralı aynıdır.

## Etiketleme ve değerlendirme

```bash
python tools/annotate.py --input photo.jpg --outdir data/personal/annotations
python tools/check_dataset.py --images data/personal/images --annotations data/personal/annotations
python tools/evaluate.py --annotations data/personal/annotations --results results/personal --output results/metrics.json
python tools/harris_study.py --images data/personal/images --annotations data/personal/annotations --out results/harris_study.csv
python tools/ocr_study.py --annotations data/personal/annotations --results results/personal --outdir results/ocr_study
python -m pytest -q
```

21 modül testi geçmektedir. Testler dönüşümleri, en küçük kareler uyumunu,
koordinat ölçeklemesini, boş/bozuk görüntüleri, gölge altında hücre tespitini,
Sudoku çakışmalarını ve çok sayfalı OCR indekslemesini kapsar.
Otomatik seçim yönteminin ayrıntıları `docs/KOSE_SECIMI.md` dosyasındadır.

## Dosya düzeni

- `sudokuscan/`: ön işleme, Harris, geometri, OCR, metrikler ve doğrulama.
- `student_corner_selection.py`: Harris adaylarından otomatik dört köşe seçimi.
- `sudoku_scan.py`: tek görüntü / batch giriş noktası.
- `tools/`: etiketleme, deney, rapor ve dışa aktarma araçları.
- `tests/`: modül testleri.
- `report/report_template.tex`: IEEEtran rapor şablonu.
- `docs/`: yöntem notları ve teslim kontrolü.

Hedefin sürekli sınır koordinatları 0..450, raster örnekleri 0..449'dur.
A4, `estimateAffine2D` çağrısından sonra dört noktanın tümüne açık least squares
uyumu uygular. `valid` kararı yalnızca givens tekrarlarını kontrol eder;
doğru OCR, çözülebilirlik veya tek çözüm garantisi değildir.

## Kaynaklar ve katkı kaydı

[OpenCV özellik tespiti](https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html),
[geometrik dönüşümler](https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html)
ve [Tesseract belgeleri](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html)
API başvurularıdır. Araç kullanımı ve katkı dağılımı raporun Ek C bölümünde ve
[AI kullanım beyanında](docs/AI_KULLANIM_BEYANI.md) kayıtlıdır.

## Otomatik köşe seçimi güncellemesi

Otomatik arayüz artık annotation okumadan çalışır. Gerçek fotoğraflardaki tam
çıktılar ve değerlendirme sonuçları ayrı veri paketindeki `results/automatic_received/`
ve `results/automatic_received_metrics.json` konumlarında bulunur. Bu on fotoğraf
geliştirmede kullanılmıştır; hidden-set veya bağımsız test başarısı değildir.

Son otomatik geliştirme koşusunda 10/10 fotoğraf işlendi: 801/810 hücre (%98,89),
6/10 tam ızgara ve %0,658 ortalama köşe hatası. Süreler 5.69-15.79 saniyedir.
Yedi dik fotoğrafta Harris parametre çalışması 84 deney içerir.

Otomatik H4 çıktılarında PSM 7/8/10/13 için ham/hazırlanmış 80 OCR deneyi
tamamlandı. Hazırlanmış kolda PSM 7 ve 10 %98,89 ile eşit sonuç verdi;
PSM 8 ve 13 %70,00 değerinde kaldı. Tam kayıtlar ayrı veri paketindedir.
