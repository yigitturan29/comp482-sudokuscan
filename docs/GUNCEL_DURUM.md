# Geliştirme durumu

## Uygulanan modüller

Ön işleme, Harris adayları, A3/A4/H4 dönüşümleri, hücre çıkarma, dolu/boş
kararı, Tesseract OCR, givens doğrulaması ve istenen çıktı arayüzü mevcuttur.
Otomatik dış köşe seçimi uygulanmıştır. Stage 4 analizi henüz tamamlanmamıştır.

## Veri ve deney

Üç baskı belgesi ve 10 fotoğraf proje sahibi tarafından hazırlanmıştır.
Görüntüler SHA-256 ile kontrol edilerek değiştirilmeden çalışma dizinine alınmıştır.
Köşe/grid annotation'ları taslak durumundadır ve inceleme beklemektedir.

Manuel H4 köşeleriyle 802/810 hücre (%99,01) doğru okunmuştur; ham kolda
741/810 (%91,48) elde edilmiştir. Hazırlanmış grid exact match 6/10,
boş/dolu F1 1,00'dır. Bu, aynı görüntülerle geliştirilen OCR aşamasının
ölçümüdür; otomatik sistem veya bağımsız test sonucu değildir.
21 test geçmektedir. IEEEtran raporu veri toplama katkısını, yöntemi,
ölçümleri, dört hata örneğini, sınırlamaları ve Ek C beyanını içerir.

## Kalan işler

1. En az sekiz görüntüde Stage 4 çizgi ölçümleri, grafikler ve analizi tamamlamak.
2. Annotation taslaklarını gözden geçirmek ve tüm otomatik metrikleri yeniden ölçmek.
3. Telefon orijinallerini EXIF korunarak veri teslimine eklemek.
4. LMS geliştirme kümesini ayrı değerlendirmek; nihai rapor ve beyanı sonlandırmak.

02-04 numaralı görüntülerde dik bulmaca yönü annotation sırasıyla tanımlanmıştır;
bu manuel önizleme ayrı bir deneydir. Otomatik program yönü OCR güveniyle seçer. Gelen PNG'lerde EXIF
bulunmamaktadır. Üç özgün çevrimiçi kaynak, veri kaydında henüz yer almamaktadır.

## Otomatik seçim

`student_corner_selection.py` son dört koordinatı Harris adaylarından seçer.
Kontur köşeleri yalnızca bölge araması içindir. Izgara puanı ve aday indeksleri
JSON çıktısına yazılır. Dört yönün OCR güveni değerlendirilir; yeterince güvenli
bir okuma bulunduğunda diğer yönler denenmez. Yöntem ve sınırlamalar
`KOSE_SECIMI.md` dosyasında açıklanmıştır.

## Otomatik geliştirme kümesi ölçümü

10/10 fotoğraf annotation okumadan işlendi. Hücre doğruluğu 801/810 (%98,89),
exact grid 6/10, boş/dolu F1 1,00; ortalama köşe hatası %0,658. Süre aralığı
5.69-15.79 saniyedir. Bu aynı geliştirme görüntülerindeki sonuçtur.

Yedi dik görüntüde 12 ortak Harris ayarı (84 deney) ölçüldü; ham kayıt
`results/harris_study.csv` içindedir. Kayıp tespitler ortalama hatadan ayrı sayılmıştır.

## OCR ayar çalışması

Otomatik H4 çıktılarında PSM 7/8/10/13 ve ham/hazırlanmış hücreler için 80 deney
tamamlandı. Hazırlanmış hücre doğruluğu PSM 7 ve 10 için %98,89; PSM 8 ve 13
için %70,00. Ham hücre doğrulukları sırasıyla %89,26 / %82,35 / %89,75 / %82,47.
Tüm sonuçlar `results/ocr_study/measurements.json` içindedir. PSM 10 hazırlanmış
koldaki dokuz hata 6->0 (6), 9->0 (2), 1->0 (1) biçimindedir.
