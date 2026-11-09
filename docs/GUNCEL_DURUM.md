# Geliştirme durumu

## Uygulanan modüller

Ön işleme, Harris adayları, A3/A4/H4 dönüşümleri, hücre çıkarma, dolu/boş
kararı, Tesseract OCR, givens doğrulaması ve istenen çıktı arayüzü mevcuttur.
Otomatik dış köşe seçimi ve Stage 4 analizi geliştirme aşamasındadır.

## Veri ve deney

Üç baskı belgesi ve 10 fotoğraf proje sahibi tarafından hazırlanmıştır.
Görüntüler SHA-256 ile kontrol edilerek değiştirilmeden çalışma dizinine alınmıştır.
Köşe/grid annotation'ları taslak durumundadır ve inceleme beklemektedir.

Manuel H4 köşeleriyle 802/810 hücre (%99,01) doğru okunmuştur; ham kolda
741/810 (%91,48) elde edilmiştir. Hazırlanmış grid exact match 6/10,
boş/dolu F1 1,00'dır. Bu, aynı görüntülerle geliştirilen OCR aşamasının
ölçümüdür; otomatik sistem veya bağımsız test sonucu değildir.
18 modül testi geçmektedir. IEEEtran raporu veri toplama katkısını, yöntemi,
ölçümleri, dört hata örneğini, sınırlamaları ve Ek C beyanını içerir.

## Kalan işler

1. Harris adaylarından otomatik TL/TR/BR/BL seçimini uygulamak.
2. En az altı görüntüde Harris parametreleri ve köşe-hata çalışmasını tamamlamak.
3. En az sekiz görüntüde Stage 4 çizgi ölçümleri, grafikler ve analizi tamamlamak.
4. Annotation taslaklarını gözden geçirmek ve tüm otomatik metrikleri yeniden ölçmek.
5. Telefon orijinallerini EXIF korunarak veri teslimine eklemek.
6. LMS geliştirme kümesini ayrı değerlendirmek; nihai rapor ve beyanı sonlandırmak.

02-04 numaralı görüntülerde dik bulmaca yönü annotation sırasıyla tanımlanmıştır;
bu işlem otomatik yön bulma bonusu olarak değerlendirilmez. Gelen PNG'lerde EXIF
bulunmamaktadır. Üç özgün çevrimiçi kaynak, veri kaydında henüz yer almamaktadır.
