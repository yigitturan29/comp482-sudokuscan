# Doğrulama kaydı - 7 Kasım 2026

Güncelleme (9 Kasım): gerçek fotoğraflarla yapılan manuel ve otomatik testler ile 28 geçen
modül testi için `GUNCEL_DURUM.md` dosyasını oku. Aşağıdaki kayıt ilk sentetik
demoya aittir; önceki çalıştırmanın gerçek kaydı olarak korunmuştur.

Bu kayıt kişisel/gizli veri değerlendirmesi değildir. Gerçek telefon fotoğrafı
sağlanmadığı ve öğrenci dış köşe seçimi işlevi yazılmadığı için tam otomatik
fotoğraf -> ızgara başarısı ölçülmedi.

## Modül testleri

Komut: `.venv\Scripts\python.exe -m pytest -q`

Sonuç: **17 passed**, 2,13 saniye. Testler:

- Üç noktalı affine'nin seçilen üç noktayı eşlemesi ve dördüncü köşe residual'i.
- A4'ün gerçekten tüm dört noktada least squares normal denklemini sağlaması.
- H4'ün dört köşeyi sayısal hassasiyetle eşlemesi; affine parallelogram durumu.
- 450x450 raster ve 0..450 sürekli sınır koordinatı seçimi.
- Ayrı x/y ölçekleriyle orijinal piksel boyutuna dönüş.
- Harris adaylarının cevap haritasından gelmesi ve geçersiz indekslerin reddi.
- Beyaz görüntüde sıfır aday/dolu hücre; kontrollü not_found çıktısı.
- Temiz sentetik ızgarada açık dolu/boş kararı ve hazırlama boyutları.
- Satır, sütun ve 3x3 kutu çakışmalarının ayrı doğrulanması.
- 0 değerlerinin çakışma oluşturmaması ve geçerli givens.
- F1 ve yüzde köşe hatası tanımları.
- Bozuk görüntüde JSON hata çıktısı ve eski grid çıktısının temizlenmesi.
- Eksik öğrenci işlevinin açık student_stage2_required bildirmesi.
- Türkçe karakterli dosya yollarından okuma/yazma.
- Eksik tahminin boş hücrelerden bedava başarı almaması.
- Gerçek Tesseract ile çok sayfalı OCR sıralaması.
- Bir sayfa okunamadığında sonraki sayfanın hücre indeksinin kaymaması.

## Çalışan sentetik downstream demo

Komut: `.venv\Scripts\python.exe tools/demo.py --outdir results/demo`

Köşeler test görüntüsünün önceden bilinen sentetik ground truth koordinatlarıdır.
Harris adayları bağımsız olarak hesaplanır; demo otomatik dört köşe seçmez.

| Ölçüm | Sonuç |
| --- | --- |
| Harris aday sayısı | 246 |
| Hazırlanmış H4 hücre doğruluğu | 81/81 = %100 |
| Ham H4 hücre doğruluğu | 79/81 = %97,53 |
| Boş hücre F1 | 1,00 |
| A3 dördüncü köşe residual'i | 105,4491 px |
| A4 dört köşe RMS residual'i | 28,7905 px |
| H4 maksimum eşleme residual'i | yaklaşık 2,4e-13 px |
| İki OCR denemesi dahil demo süresi | 1,5049 s; süre çalıştırmaya göre değişir |

Rakamın ikili maskesini nearest-neighbour ile aşırı büyütmek ilk denemede
hazırlanmış hücre doğruluğunu düşürdü. Son sürüm tek bileşenin yumuşak gri
kenarlarını koruyup çevre mürekkebini temizliyor, rakamı ortalayıp beyaz alan
ekliyor. Bu sentetik testte iyileşme görüldü; gerçek font ve gölgelerde ayrıca
denenmesi gerekiyor. Stage 4 karşılaştırma sonucu bu kayıttan çıkarılmadı.

## Ortam

Windows, CPU; Python 3.11; OpenCV 4.10.0, NumPy 2.4.1, Pillow 11.1.0,
pytesseract 0.3.13, Tesseract 5.4.0.20240606, Matplotlib 3.10.8, pytest 8.4.2.
Test için kullanılan yerel .venv, mevcut temel bilimsel paketleri paylaşıyor.
Temiz bir makinede requirements ile kurulum ayrıca kullanıcı tarafından doğrulanmalı.
Tesseract kullanıcıya ait standart Programs dizinine kuruldu; kurucu özel dizin
parametresini uygulamadı. Kod kullanıcı ve sistem standart konumlarını arar.

Ek kontroller: Python kaynakları compileall ile doğrulandı; batch tüm görüntüleri
deneyip hata dosyası yazdı; Tkinter penceresi oluşturulabildi. Etiketleme aracı
gerçek öğrenci fotoğrafıyla henüz uçtan uca denenmedi.
Türkçe PDF rehber 4 sayfa olarak render edilip görsel kontrol edildi.
IEEEtran .tex rapor iskeleti yerel LaTeX derleyicisi olmadığı için derlenmedi.

## Henüz doğrulanmayanlar

Öğrencinin otomatik seçim mantığı; güçlü eğiklik/gölge/karmaşa dayanıklılığı;
kendi telefon verisindeki tüm metrikler ve 20 saniye sınırı; Stage 4 çizgi
ölçümleri/analizi; hidden test ve cross-evaluation. Bonuslar uygulanmadı.
