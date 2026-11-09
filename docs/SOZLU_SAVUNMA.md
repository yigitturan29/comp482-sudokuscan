# 10 dakikalık savunmaya hazırlanma

## Kendi başına prova

1. Bir fotoğrafı komut satırından çalıştır; Harris ve debug çıktısını aç.
2. `student_corner_selection.py` içindeki kendi kararını satır satır açıkla.
3. Harris parametrelerinden birini değiştir; aday sayısı ve hata üzerindeki etkisini ölç.
4. A3'ün hangi üç noktayı kullandığını bul; başka üçlüyle nasıl kuracağını AI olmadan uygula.
5. `Config(target_size=576)` ayarının 64 piksel/hücre verdiğini açıkla ve çıktıyı kontrol et.
6. Bir OCR hatasını ham/hazırlanmış hücrede göster; boş/dolu kararıyla rakam okuma hatasını ayır.

## Bilmen gereken temel cevaplar

- Harris R = det(M) - k*trace(M)^2. Matris iki yöndeki yerel gradyan değişimini özetler.
- Göreli eşik maksimum cevaba göre ölçeklenir; NMS yakın tekrarları azaltır.
- Affine 6 serbestlik derecesidir; aynı doğru üzerinde olmayan üç eşleşme 6 denklem verir.
- Homography ortak ölçek dışında 8 serbestlik derecesidir; genel konumda dört eşleşme gerekir.
- `getAffineTransform` tam üç nokta alır; A4 tüm dört noktayı least squares ile uydurur.
- H4'ün kendi dört girdi noktasını sıfır residual ile eşlemesi ground truth'a doğruluğu kanıtlamaz.
- `valid`, yalnızca okunan givens'te tekrar bulunmadığını söyler. Doğru okuma ya da tek çözüm kanıtı değildir.
- 0 boş hücreyi temsil eder; okunamayan dolu hücreler JSON'da ayrıca işaretlenir.
- Demo başarısı sentetik koşullardadır; kişisel/hidden veri başarısını temsil etmez.

Stage 4'te kendi verinden ne sonuç çıkardığını kendin savunmalısın.
Bu dosyada teslim edilecek karşılaştırma sonucu veya ezberlenecek sahte başarı iddiası yoktur.
