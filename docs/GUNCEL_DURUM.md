# Güncel durum - 9 Kasım 2026

Tam otomatik teslim henüz hazır değildir. Çalışan destek kodu, 10 fotoğraf için
AI destekli annotation taslakları ve gerçek OCR geliştirme ölçümleri hazırlandı.

## Tamamlanan işler

- Kullanıcının yeni 10 dosyası orijinal gelen baytları ve SHA-256 hash'leri korunarak kopyalandı.
- Üç bulmaca için 9x9 givens ve 10 kare için köşe/koşul etiketleri taslak olarak girildi.
- Elle verilen köşelerle A3/A4/H4 görüntüleri, matrisler ve debug çıktıları üretildi.
- OCR hazırlamasında gölge düzeltme ve %8 marj eklendi; ham görüntü deney kolunda korunuyor.
- Aynı PSM 10, whitelist ve okunamayan hücreye 2x tekrar kuralıyla ham/hazırlanmış ablation yapıldı.
- Hazırlanmış hücreler 802/810 (%99,01), ham hücreler 741/810 (%91,48) doğru okundu.
- Sekiz hata, dolu bulunan ama Tesseract'ın okuyamadığı hücrelerde kaldı. Boş/dolu F1 1,00.
- 18 test geçti; güçlü gölge ve çok sayfalı OCR indekslemesi için regresyon kontrolleri mevcut.
- IEEEtran rapor taslağı gerçek ölçümleri ve eksik öğrenci alanlarını içeriyor.

Bu sayılar elle verilen köşelerle elde edilen geliştirme ölçümleridir. Bu veride
ayar değiştirildiği için bağımsız test veya hidden-set başarı iddiası değildir.
Otomatik arayüz, eksik öğrenci işlevini 10 karede de student_stage2_required olarak bildiriyor.

## Öğrencinin tamamlayacağı işler

1. `student_corner_selection.py` içine kendi otomatik seçim mantığını yazmak.
2. Gerçek otomatik seçimle Harris parametre çalışmasını ve tüm değerlendirmeleri çalıştırmak.
3. Stage 4 çizgi ölçümleri, karşılaştırma grafikleri ve analizini kendisinin yazması.
4. Annotation taslaklarını görsel olarak inceleyip doğrulamak/düzeltmek.
5. Telefonda duran orijinalleri EXIF korunarak ayrı teslim etmek.
6. Geliştirme kümesini LMS'den edinip ayrı ölçmek; nihai rapor ve AI beyanını tamamlamak.

Kaynak notu: kullanıcı üç Sudoku'yu ayrı belgelerde düzenleyip çıktı aldığını belirtti.
Özgün internet kaynakları kaydedilmedi; bağlantı teslimi açıkça zorunlu olmasa da
üç farklı kaynak şartı bu bilgilerle doğrulanamıyor. Üç dosya, kendiliğinden üç
farklı özgün kaynak anlamına gelmez. Bir kaynak uydurulmadı.

Fotoğraf 02-04 yatay dosyalarda yan duruyor. Downstream önizleme için etiket
sırası açıkça dik bulmacaya göre verildi. Otomatik yön seçimi veya bonus olarak sunulmadı.
Fotoğrafların üzerindeki el yazısı numara/tarih korunuyor; ayrı kart şartının
katı yorumu için ders ekibinin değerlendirmesi geçerlidir.
