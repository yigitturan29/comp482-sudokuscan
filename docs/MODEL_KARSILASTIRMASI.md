# A3/A4/H4 ölçümü

`tools/compare_models.py` bütün on JPEG'i aynı OCR ayarlarıyla karşılaştırır.
Annotation yalnız gerçek grid ve köşe hatası değerlendirmesinde kullanılır;
dönüşümler ve çizgi arama kılavuzları otomatik sonuç JSON'undan gelir.

Eğiklik: karşılıklı kenarların büyük/küçük oranlarının maksimumu eksi bir.
Bu bir görüntü proxy'sidir; kamera açısı değildir. En büyük oran photo_02'de
0,409, en büyük A3 BR residual'i ise photo_03'te 280,7 pikseldir. Tek sayı,
bütün perspektif özelliklerini veya hataları bire bir sıralamaz.

Her modelde 10 yatay ve 10 dikey çizgi aranır. Kanonik çizgiler M*H4^-1 ile
arama konumuna taşınır. Çizgi konumu kılavuzdan kopyalanmaz: gölge-normalize
edilmiş gerçek piksellerde +/-0,22 hücre araması ve yerel izleme yapılır.
Kesişim örnekleri dışlanır, glyph/gölge aykırıları robust doğrusal uyumla
azaltılır. En az 24 örnek ve görüntü genişliğinin dörtte biri kadar görünür
uzunluk gerekir. Bulunamayan çizgi JSON'da found=false olur.

Konum hatası, ölçülen noktaların 0,50,...,450 ideal çizgilerinden ortalama mutlak
sapmasıdır. Aralık hatası, komşu gözlenen çizgilerin görüntü orta eksenindeki
aralığının 50 pikselden sapmasıdır. Düzlük, çizgi başına fit normal doğrultusunda
RMS hataların ortalamasıdır. Eksik çizgilere hücre genişliği (450 hedefte 50 px)
cezası veren ek konum puanı da saklanır. Asıl değerler ve eksik sayısı birlikte
okunmalıdır; görünmeyen çizgileri sıfır hatayla doldurma yoktur.

A3/A4/H4 OCR doğrulukları sırasıyla %69,63 / %73,09 / %98,89. A4, en düşük
eğiklikteki photo_04'te H4 ile %100'de eşittir. Bir yüzde puandan fazla OCR
kaybı olmaması ve 5 px altında ortalama konum hatası ölçütünde yalnız bu A4
örneği kabul edilir. Bu yorum için belirlenmiş toleranstır; ödev puanlama kuralı
değildir. Veriden evrensel bir açı/eğiklik eşiği çıkarılmamıştır.

Weak perspective, nesne içi derinlik farkının ortalama uzaklığa göre küçük
olduğu koşullarda ortak ortalama derinlikle affine yaklaşımı açıklar. Bu
kümede H4'ün üstünlüğü özellikle çizgi hizası ve aralığındadır. Affine ve
homography düz çizgileri korur; düşük düzlük hatası tek başına kare gridin
doğru hizalandığını göstermez.

Bu deneyler aynı geliştirme fotoğraflarındadır. Gizli test başarısı ve fotoğraf
orijinalliği bu ölçümlerden çıkarılamaz. Ham kayıt ve bindirmeler ayrı veri
paketindeki results/model_comparison dizinindedir.
