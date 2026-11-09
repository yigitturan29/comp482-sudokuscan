# SudokuScan - COMP 482 proje çalışma paketi

**Durum: teslim edilecek bitmiş proje değil; çalışan ve test edilen modüller ile öğrenci çalışma alanı.**
Yönergenin 11. bölümü, AI'nın dış köşe seçimi mantığını (Stage 2) ve
affine/homography karşılaştırma analizini (Stage 4) yazmasını yasaklıyor.
Bu nedenle `student_corner_selection.py` işlevi bilinçli olarak eksik;
Stage 4 sonuçlarını ve yorumunu da sen yazmalısın. Diğer aşamalar hazır.
Fotoğraf, deney sonucu, öğrenci imzası ve geçmiş tarihli commit uydurulmadı.

## 9 Kasım güncellemesi

Kullanıcının gönderdiği 10 gerçek fotoğraf (3/3/4 dağılımında üç bulmaca) yerel
çalışmaya alındı. Dosyalar içerikleri değiştirilmeden kopyalandı; köşe ve grid
etiketleri **öğrenci incelemesi gereken AI destekli taslaklar** olarak kaydedildi.
Görüntüler ve annotation'lar public depoda bulunmaz. Gelen PNG'lerde EXIF yoktur;
telefon orijinalleri oldukları doğrulanmadı.

Elle etiketlenen köşelerle yapılan H4/OCR geliştirme testinde hazırlanmış
hücreler **802/810 (%99,01)**, ham hücreler **741/810 (%91,48)** doğru okundu.
Hazırlanmış grid exact match 6/10, boş/dolu F1 1,00 oldu. Bu sayılar otomatik
köşe tespiti veya hidden test başarısı değildir. Aynı görüntüler hazırlama
adımlarını geliştirmek için de kullanıldı; bağımsız test ölçümü sayılmaz.

Son modül test durumu: **18 passed**. Yeni regresyon testi ızgarayı kesen
gölgede dolu/boş kararını ve ham hücre yoğunluğunun korunmasını doğrular.

Yerel veri dosyaları varken denemeyi yeniden üret:

```powershell
.\.venv\Scripts\python.exe tools/preview_annotations.py --images data/received_20261109/images --annotations data/received_20261109/annotations --outdir results/annotation_preview
```

Bu komut annotation kullanır ve otomatik `sudoku_scan.py` arayüzünün yerine geçmez.
`tools/build_received_report.py`, gerçek IEEEtran sınıfıyla kullanılacak özel
rapor taslağını oluşturur. Stage 2 ve Stage 4 öğrenci alanları tamamlanmadan
bu rapor nihai teslim değildir. Fotoğraflar ve özel rapor LMS için ayrı tutulur.

## Önce bunu çalıştır

Bu bilgisayarda proje için `.venv` ortamı hazırlandı. PowerShell'i bu klasörde aç:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo.ps1
```

Demo gerçek Tesseract ile rakam okur; Harris adaylarını ve üç dönüşümü kaydeder.
**Demo köşeleri sentetik görüntünün bilinen koordinatlarıdır. Otomatik köşe
seçiminin tamamlandığını veya kişisel fotoğraflardaki başarıyı göstermez.**
`results/demo/demo_summary.json` gerçek test sonuçlarını içerir.
`results/demo/known_GT_debug.png` üzerindeki küçük yeşil rakamlar OCR çıktısıdır;
`?` okunamayan dolu hücreyi, kırmızı dolgu Sudoku çakışmasını gösterir.

## Yeni bilgisayarda kurulum

Python 3.10+ ve Tesseract OCR 5.x gerekir. GPU kullanılmaz.

Windows için Tesseract'ın [resmi kurulum sayfasından](https://tesseract-ocr.github.io/tessdoc/Installation.html)
bağlantı verilen Windows dağıtımını kur; English (`eng.traineddata`) verisi seçili olsun.
Alternatif olarak Windows Package Manager kullanılabilir:

```powershell
winget install --exact --id UB-Mannheim.TesseractOCR
powershell -ExecutionPolicy Bypass -File .\kurulum.ps1
```

Standart konumlar otomatik aranır. Farklı kurulum için komuta
`--tesseract-cmd "C:\konum\tesseract.exe"` ekle veya `TESSERACT_CMD` ortam değişkenini ayarla.

Linux/macOS:

```bash
# Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-eng python3-tk
# macOS: brew install tesseract
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python tools/demo.py --outdir results/demo
```

Tesseract bir sistem programıdır; yalnızca `pip install pytesseract` yeterli değildir.

## Tamamlaman gereken sıra

1. `docs/BURADAN_BASLA.md` dosyasını oku ve demoyu çalıştır.
2. En az 3 farklı kaynaktan 3 bulmaca bas; en az 10 kendi telefon fotoğrafını çek.
   Her karede, ızgaranın dışında öğrenci numaran ve çekim tarihi yazılı el kartı olsun.
3. Düzenlenmemiş orijinalleri `data/personal/images/` içine kopyala; EXIF'i koru.
4. Her fotoğrafı aşağıdaki araçla etiketle. Tıklamak sadece ground truth içindir.
5. `student_corner_selection.py` içindeki işlevi kendin yaz. Dört Harris adayının
   indeksini TL/TR/BR/BL sırasında döndür. Aday noktaların yerine yeni koordinat üretme.
6. Otomatik komutları, parametre ve OCR deneylerini çalıştır.
7. Stage 4 ölçümlerini ve yorumlarını kendin tamamla; raporu gerçek sonuçlarla doldur.
8. `docs/TESLIM_KONTROL.md` ve AI beyanını kontrol et; sözlü savunmaya çalış.

## Fotoğraf etiketleme

```powershell
.\.venv\Scripts\python.exe tools/annotate.py --input data/personal/images/photo01.jpg --outdir data/personal/annotations
.\.venv\Scripts\python.exe tools/check_dataset.py --images data/personal/images --annotations data/personal/annotations
```

Köşelere TL, TR, BR, BL sırasında tıkla; sağ tıkla son tıklamayı geri al.
9x9 kutulara fotoğraftaki givens rakamlarını gir, boşları 0 bırak. Koşul etiketlerini,
bulmaca kimliğini, kaynağını ve tarihi yaz. Kaydetmeden önce hepsini kontrol et.
JSON şeması PDF Ek A ile uyumludur; ek metadata alanları veri kontrolünü kolaylaştırır.
Fotoğraf dosyası değiştirilmez. Koordinatlar EXIF ile otomatik döndürülmüş görünümde
değil, dosyanın **saklanan piksel düzeninde** kaydedilir. Aynı okuma kuralı otomatik
programda da kullanılır. EXIF nedeniyle yan görünen dosyalarda değerlendirme sisteminin
koordinat kuralını ders ekibiyle netleştir; orijinali düzenleyerek EXIF'i kaybetme.

## Hocanın otomatik arayüzü

Köşe seçimi işlevini tamamlayıp ortamı etkinleştirdikten sonra:

```powershell
.\.venv\Scripts\Activate.ps1
python sudoku_scan.py --input photo.jpg --outdir out/
python sudoku_scan.py --batch images_dir/ --outdir results/
```

Her başarılı görüntü için `<name>_grid.txt`, `_result.json`, `_harris.png`,
`_rect_A3.png`, `_rect_A4.png`, `_rect_H4.png`, `_debug.png` yazılır.
Izgarada ayraçsız 9 satır x 9 rakam bulunur. Matrisler ve köşeler JSON'a yazılır;
köşeler orijinal görüntü piksellerindedir. Seçim başarısızsa `verdict: not_found` döner.
Henüz öğrenci işlevi yazılmadıysa ayrıca `error_code: student_stage2_required` görülür.
Tek fotoğrafın hatası tüm batch'i durdurmaz; başarısız batch sonunda çıkış kodu 1 olur.

Bu otomatik arayüz annotation okumaz ve elle verilen köşe kabul etmez.
`tools/demo.py` bağımsız geliştirme aracıdır; grader yoluna bağlanmaz.
Varsayılan üretim yolu H4 için bir çok sayfalı TIFF/Tesseract çağrısı yapar.
Çalışma süresi JSON'a yazılır; gerçek fotoğraflarda 20 saniye sınırı ayrıca doğrulanmalıdır.
Uygulama içi OCR zaman aşımı vardır; tüm sürece sert işletim sistemi zaman sınırı uygulanmaz.

## Ölçüm araçları

```powershell
python tools/evaluate.py --annotations data/personal/annotations --results results/personal --output results/personal_metrics.json
python tools/harris_study.py --images data/personal/images --annotations data/personal/annotations --out results/harris_study.csv
python tools/ocr_study.py --annotations data/personal/annotations --results results/personal --outdir results/ocr_study
python -m pytest -q
```

`harris_study.py` en az 6 annotation ister. Bir seferde bir parametreyi değiştirerek
aday sayısı ve köşe hatasını ölçer; öğrenci seçimi eksikse açıkça durur.
`ocr_study.py`, otomatik elde edilmiş H4 görüntülerinde PSM 7/8/10/13 ile
hazırlanmış/ham hücreleri ölçer; hatalı örnek kırpımlarını kaydeder.
Bu OCR çalışmasında bulunamayan H4 görüntüleri ayrı listelenir.
`evaluate.py` ise başarısız görüntüleri genel başarıdan düşürür; C1-C5 kırılımı üretir.
Empty-cell F1'da boş hücre pozitif sınıftır; belirsizliği önlemek için dolu hücre F1'ı da verilir.
Köşe hatası bulunamayan görüntülerde tanımsızdır; eksik sayısı ayrıca raporlanır.
Stage 4 analizi ve bunun çizgi aralığı/doğrusallık ölçümleri öğrenci çalışma alanıdır;
bu paket onların tamamlandığını iddia etmez.

## Kodun haritası

| Dosya | Görev |
| --- | --- |
| `sudoku_scan.py` | Tek görüntü ve batch CLI |
| `sudokuscan/preprocessing.py` | Boyuta göre ölçeklenen filtreler ve aydınlatma düzeltme |
| `sudokuscan/harris.py` | `cornerHarris`, göreli eşik, NMS, aday kaynağı kontrolü, subpixel |
| `student_corner_selection.py` | **Senin yazacağın otomatik dört köşe kuralı** |
| `sudokuscan/geometry.py` | A3, tüm noktalı LS A4, H4 ve residual |
| `sudokuscan/recognition.py` | İç marj, dolu/boş, hazırlama, çok sayfalı OCR |
| `sudokuscan/validity.py` | Satır, sütun, kutu tekrarları |
| `sudokuscan/pipeline.py` | Aşamaların bağlantısı ve dosya çıktıları |
| `tools/` | Demo, ground truth, veri kontrolü ve ölçüm |
| `report/report_template.tex` | IEEEtran rapor iskeleti; sonuç bölümleri doldurulacak |
| `docs/` | Türkçe başlangıç, veri planı, teslim ve savunma notları |

A4 için `estimateAffine2D` çağrısının ardından tüm dört noktaya açık least squares
yeniden uyumu uygulanır. Varsayılan RANSAC'ın dördüncü noktayı dışlaması önlenir.
450x450 rasterda son piksel 449'dur; PDF'de BR residual'i (450,450)'ye göre istendiği
için dönüşüm hedefi sürekli sınır koordinatları 0..450 olarak tanımlandı. Hücre sınırları
0,50,...,450'dir. Raporunda bu seçimi belirt.

## Kaynaklar ve AI kullanımı

Kod bu çalışma için yazıldı; Sudoku-scanner depolarından alınmadı. Başvurulan API belgeleri:

- [OpenCV Harris ve subpixel](https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html)
- [OpenCV geometrik dönüşümler](https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html)
- [OpenCV estimateAffine2D](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)
- [Tesseract komutlar ve TSV](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html)
- [Tesseract görüntü hazırlama](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html)

`docs/AI_KULLANIM_BEYANI.md` bu oturumun katkısını açıklar. PDF AI'yı öğrenme
desteği olarak tanımladığı için, burada üretilen uygulama kodlarını teslimde kullanmadan
önce izin kapsamını ders ekibiyle netleştir. Özellikle beyandaki öğrenci imzasını
yalnızca ifadeler gerçekten doğru olduğunda tamamla. Sahte geçmiş oluşturma;
kalan gerçek çalışmayı anlamlı commit'lerle kaydet.
