# Otomatik dış köşe seçimi

Uygulama `student_corner_selection.py` içindedir. İşlev görüntü ve Harris
adaylarını alır; TL/TR/BR/BL sıralı dört aday indeksi veya `None` döndürür.
Dosya adı, ground truth, elle girilen koordinat veya görüntüye özel ayar okumaz.

1. Adaptif eşik görüntüsündeki konturlar olası dörtgen bölgeleri önerir.
   Küçük hücreler, içbükey şekiller ve çok ince dörtgenler elenir. Kontur
   köşeleri nihai çıktı olarak kullanılmaz.
2. Karşılıklı kenar çiftlerinin yataylığı ile üst kenar belirlenir. Bu sıralama,
   güçlü perspektifte `x+y` minimumunun yanlış köşeyi seçmesini önler.
3. Her öneri köşesinin çevresinde, ortalama kenar uzunluğunun %5,5'i içindeki
   en yakın yedi Harris adayı tutulur. Dört indeksin farklı olması zorunludur.
4. Harris noktalarından oluşan dörtgen geçici bir homography ile 191x191 test
   görüntüsüne taşınır. Izgara 5..185 sınırında ve 20 piksel hücre aralığındadır.
   Yatay/dikey açma ve projeksiyonlar, beklenen 10 çizgi konumunu ölçer.
   Çizgi ortalarındaki mürekkep cezalandırılır; böylece rakamlar, sayfa kenarı
   ve boş dikdörtgenlerin ızgara gibi puan alması azaltılır.
5. En güçlü üç bölgede iki tur yerel arama yapılır. Her adım yalnızca mevcut
   Harris indekslerinden birini değiştirir. Kabul eşiği 0,24'tür.
6. Seçilen Harris noktaları `cornerSubPix` ile yerel olarak iyileştirilir.
   Ayrı x/y ölçekleriyle orijinal görüntü koordinatlarına dönülür.

Harris eşik oranı global olarak 0,0001'dir. Daha zayıf adaylar korunur;
doğru dörtgenin seçimi çizgi düzeniyle yapılır. NMS ve en fazla 2500 aday
sınırı, arama maliyetini kısıtlar. Bütün görüntüler aynı ayarları kullanır.

Program ayrıca dört köşe sırasının çevrimsel kaydırmalarını aynı OCR ayarlarıyla
değerlendirebilir (`try_quarter_turns`). Ortalama tek-karakter güveni en yüksek
yön seçilir. Bu işlem rakamları Sudoku kurallarına göre değiştirmez.

JSON'daki `harris_candidate_indices`, `harris_selected_before_refinement` ve
`corner_selection` alanları son noktaların kaynağını denetlemek içindir.
Harris haritasındaki yeşil işaretler seçilen dört noktayı gösterir.

Sınırlamalar: çok küçük/eksik ızgaralar, kuvvetle silinmiş dış çizgiler,
kavisli kâğıt ve çizgi düzenini taklit eden karmaşa başarısızlığa yol açabilir.
Sağlanan görüntüler geliştirmede kullanılmıştır; hidden-set başarısı ölçülmemiştir.
