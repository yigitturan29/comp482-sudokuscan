# Önce projeyi anlamak

Bu ödev Sudoku çözmekten önce, bir fotoğraftaki ızgarayı düzgün bir dijital
ızgaraya çevirmekle ilgili. Programın başarılı sayılması için rakamları ezbere
tamamlaması değil, gerçekten fotoğraftan okuması gerekiyor.

**Hazır olan:** görüntü hazırlama, Harris adayları, A3/A4/H4 dönüşümleri, hücre
ayırma, Tesseract OCR, çakışma kontrolü, çıktı biçimi, otomatik dış köşe seçimi ve testler.
**Tamamlanan:** on JPEG üzerinde Stage 4 ölçümü, grafikler ve rapor.
**Kalan kontrol:** annotation incelemesi, kaynak/metadata ve nihai beyan. Güncel durum `GUNCEL_DURUM.md` içindedir.

## İlk çalışma oturumu

1. `demo.ps1` çalıştır. `results/demo/` görüntülerine bak.
2. `synthetic_photo.png` ile `known_GT_rect_H4.png` dosyasını karşılaştır:
   dönüşümün girdiyi nasıl değiştirdiğini gözünle gör.
3. `harris_candidates_only.png` dosyasındaki beyaz halkalar aday köşeler.
   Bunlar yalnızca dış dört köşe değil; rakamların içindeki köşeler de aday.
4. `known_GT_debug.png` ile `known_GT_grid.txt` dosyasını karşılaştır.
5. `demo_summary.json` içinde matrislerin boyutlarını ve gerçek demo ölçümlerini gör.

Demo bilinen sentetik köşelerle çalışır. Otomatik seçim için
`sudoku_scan.py --input ... --outdir ...` komutunu kullan. Bu yol annotation okumaz.

## Harris'i öğrenirken

Bir noktayı çevreleyen küçük görüntü parçasını yatay ve dikey kaydırdığında
görüntü iki yönde de belirgin değişiyorsa o yer köşe adayıdır. Harris bunu
gradyanların oluşturduğu 2x2 matristen hesaplar: R = det(M) - k * trace(M)^2.
Tek yönde değişim kenarı, iki yönde değişim köşeyi ayırmaya yardım eder.

`blockSize` komşuluğu, `ksize` türev filtresini, `k` cevap formülünü etkiler.
Göreli eşik, tepe cevabının hangi oranından güçlü noktaların tutulacağını belirler.
NMS aynı fiziksel köşenin yan yana birçok aday üretmesini azaltır. Aday sayısının
artması tek başına dış köşe doğruluğunun arttığı anlamına gelmez; bunu ölçmelisin.

Uygulanan dış köşe seçimi kontur bölge önerilerini Harris adaylarına bağlar ve
10x10 çizgi düzenini puanlar. Yöntem `KOSE_SECIMI.md` içindedir. Hangi görüntü
bilgisini kullandığını, sıralamayı ve başarısızlıklarını açıklayabilmelisin.
PDF'nin izin verdiği genel yaklaşımlar ve kısıtlar için Stage 2'yi tekrar oku.

## İşlevin sözleşmesi

`student_corner_selection.py` dosyasındaki işlev üç bilgi alır:
ön işlenmiş görüntüler, Harris adayları/cevapları ve ortak ayarlar.
Çıktısı koordinatlar değil, `harris.candidates` içinden dört farklı tam sayı indeksi.
Sıra TL, TR, BR, BL. Bulamazsa `None` dönebilir. İzleyen kod seçilen noktaları
`cornerSubPix` ile yerel olarak iyileştirir ve orijinal boyuta taşır.

Ground truth'u bu işlevde açma. Fotoğraf ismine göre nokta seçme. Görüntüye
özel sabitler yazma. Otomatik programda fare tıklaması kullanma.

## Dönüşümleri anlamak

Affine dönüşümün 2x3 matrisinde 6 bilinmeyen var. Her eşleşen nokta x ve y için
iki denklem verir; **aynı doğru üzerinde olmayan** 3 nokta yeterli.
Homography 3x3 matristir; ortak ölçek nedeniyle 8 serbestlik derecesi vardır.
Genel konumdaki 4 nokta çifti 8 bağımsız denklem verir.

Kodda A3 TL/TR/BL'yi kullanır; BR'deki hata ayrıca ölçülür. A4 dört noktayı
birlikte uydurur; RMS residual'i verir. H4 dört köşeyi hedefe taşır. Köşelerde
çok küçük residual görmek, köşelerin gerçek bulmacaya doğru seçildiğini kanıtlamaz.
Ground truth köşe hatası başka bir ölçümdür.

## Rakam okuma

450 piksel / 9 = 50 piksellik hücre. Güncel %8 iç marj her kenardan 4 piksel
atar; amaç ızgara çizgisinin OCR'a girmesini azaltmaktır. Bu başlangıç ayarıdır;
kendi fotoğraflarında test ederek gerekçelendirmen gerekir.

Boş/dolu kararı OCR'dan önce verilir: kenara değmeyen, yeterli alanı ve yüksekliği
olan bağlı bileşen aranır. Gölgeyi azaltmak için tüm düzeltilmiş görüntüde
morfolojik kapamayla arka plan kestirilir ve görüntü buna bölünür. Seçilen
bileşenin gri kenarları korunur, rakam ortalanıp 128x128 beyaz sayfaya yerleştirilir.
Dolu hücreler çok sayfalı TIFF'e yazılır;
Tesseract her sayfayı tek karakter olarak okur (`--psm 10`, whitelist `123456789`).
Okunamayan dolu hücreye aynı ayarlarla bir kez 2x büyütme denemesi yapılır;
bu kural ham ve hazırlanmış deney kollarında aynıdır.
OCR yanlışını Sudoku çözerek gizleyen bir düzeltme yoktur.

## Gerçek veriyle çalışma

Önce kendi fotoğraflarını etiketle. Otomatik çıktıyı elle düzeltip tahminmiş gibi
kaydetme. `evaluate.py` tahmin ile ground truth'u karşılaştırır. Tam başarısız bir
fotoğraf boş hücrelerin çokluğu sayesinde yüksek başarı almasın diye sıfır hücre
başarısı alır. Bulunamayan köşeler için ayrı eksik sayısı tutulur.

Stage 4 ölçümü on fotoğrafta tamamlandı. Yöntem ve sonuçlar
`MODEL_KARSILASTIRMASI.md` dosyasındadır. `deneyler.ps1` bütün deneyleri,
`calistir.cmd` sıradan fotoğraf taramasını başlatır. Sonuçları açıklayabilmek
için örnekleri ve ölçüm yöntemini gözden geçir.
