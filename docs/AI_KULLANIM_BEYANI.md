# Katkı dağılımı ve AI kullanım beyanı

## Öğrenciye ait çalışmalar

- Üç Sudoku'nun seçilmesi ve ayrı baskı belgelerinin hazırlanması.
- Baskıların alınması ve kendi telefonuyla toplam 10 fotoğrafın çekilmesi.
- Farklı açılar ve gölge koşullarının fiziksel çekim sırasında uygulanması.
- Öğrenci numarası ve tarihin ızgara dışına elle yazılması.
- Fotoğrafların proje için sağlanması.

Bu çalışmalar AI tarafından üretilen fotoğraflar veya sentetik kişisel veri değildir.

## Ek C tablosu

| Araç | Amaç / aşama | İstenen yardım | Kullanılan / değiştirilen katkı |
| --- | --- | --- | --- |
| OpenAI Codex | Yazılım altyapısı: Stage 1, 3, 5, 6 ve Harris/NMS adayları | Modüler uygulama, CLI, doğrulama ve test geliştirme | Üretilen kod, OCR hazırlama değişiklikleri ve testler projeye alındı; öğrenci kod incelemesi bekliyor |
| OpenAI Codex | Veri etiketleme desteği | Fotoğraflardan köşe ve givens taslakları hazırlama | Manuel annotation önerileri kaydedildi; öğrenci doğrulaması bekliyor |
| OpenAI Codex | Deney ve rapor desteği | Ham/hazırlanmış OCR, PSM ve Harris deneyleri, tablolar, rapor düzenleme | Gerçek ölçüm çıktıları ve rapor metni kullanıldı; manuel geometri ve otomatik sistem deneyleri ayrı raporlandı |
| OpenAI Codex | Stage 2 dış köşe seçimi | Otomatik Harris aday seçimi ve testleri | Kontur bölge önerisi, Harris indeks araması, ızgara puanlaması ve test kodu AI tarafından eklendi; bu kullanım yönergedeki öğrenci yazarlığı şartını karşılamaz |
| OpenAI Codex | Stage 4 karşılaştırma analizi | Üç dönüşümde çizgi ölçümleri, aynı OCR, grafik ve yorum | Karşılaştırma kodu, on fotoğraflık gerçek deneyler, grafikler ve rapor yorumu AI yardımıyla eklendi; bağımsız öğrenci yazarlığı şartını karşılamaz |

Öğrenciye ait veri toplama katkıları ile yazılım/rapor yardımının kapsamı ayrı
kaydedilmiştir. Nihai beyan, son değişiklikler gözden geçirildikten sonra öğrenci
tarafından tamamlanır. Yönergedeki köşe seçimi ve karşılaştırma analizi yazarlığı
onayı, öğrencinin kendi katkılarıyla uyumlu biçimde kişisel olarak tamamlanmalıdır; bir imza eklenmemiştir.
