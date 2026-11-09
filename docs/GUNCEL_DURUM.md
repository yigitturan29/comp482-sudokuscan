# Güncel durum

Bütün hesaplama aşamaları uygulanmıştır: Harris aday seçimi, A3/A4/H4, OCR,
Sudoku geçerliliği ve on fotoğraflık Stage 4 karşılaştırması. 28 test geçmektedir.

## Sağlanan JPEG verisi

sudoku5.zip içindeki 10 JPEG sırasıyla photo_01..10 olarak, baytları
korunarak data/received_20261109_zip/images dizinine alınmıştır. JPEG'ler önceki
PNG kopyalarıyla piksel düzeyinde aynıdır. Metadata ve SHA-256 kayıtları manifesttedir.
EXIF alanı sayısı her dosyada sıfırdır. Annotation'lar aynı görüntülerden aktarılmış
referans taslaklarıdır; öğrenci incelemesi beklemektedir.

## Ölçümler

10/10 otomatik işlem, 801/810 doğru hücre (%98,89), 6/10 exact grid,
boş/dolu F1 1,00, ortalama köşe hatası %0,658. Bütün görüntüler bu CPU
koşusunda 20 saniye altında tamamlandı. Dokuz dolu hücre okunamadı.

Stage 4: A3 %69,63, A4 %73,09, H4 %98,89. Çizgi konum hataları sırasıyla
21,35 / 14,32 / 1,94 px; aralık hataları 5,78 / 4,49 / 1,06 px. A3'te
13/200 çizgi ölçülemedi; A4/H4'te 200/200 ölçüldü. En eğik proxy photo_02'dir.
Karşılaştırma grafikleri, yirmi çizginin durumları, çizgi noktaları, bindirmeler
ve gerçek OCR gridleri results/model_comparison içindedir.

7 görüntü x 12 Harris ayarı = 84 deney ve 10 görüntü x 4 PSM x 2 hazırlama
kolu = 80 OCR deneyi tamamdır. Veriler geliştirmede de kullanıldığından
bağımsız/hidden test başarısı iddiası yapılmaz.

## Teslim kontrolünde kalan konular

Program ve karşılaştırma çalışır. Üç özgün çevrimiçi puzzle kaynağı kaydedilmemiş,
EXIF yoktur. Öğrenci annotation'ları ve yazarlık/AI beyanını gözden geçirmelidir.
LMS geliştirme kümesi sağlanmadığı için onun ayrı değerlendirmesi yapılmamıştır.
Yazılım çalışması bu veri ve ders değerlendirmesi koşullarını otomatik sağlamaz.
