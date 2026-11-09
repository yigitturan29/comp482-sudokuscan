# Raporu hazırlama

`report_template.tex` resmi `IEEEtran` konferans sınıfını kullanır; nihai rapor değildir.
Overleaf'te IEEE Conference Template açıp içeriği bu dosyayla değiştirebilirsin.
Yerel TeX dağıtımında `pdflatex report_template.tex` komutunu iki defa çalıştır.
İlk iskelet hazırlandığında derleyici yoktu. 9 Kasım'da proje içindeki `.tools/tectonic/`
dizinine resmi Tectonic dağıtımı indirildi; yerel rapor bu araçla derlenebilir.

Gerçek OCR ölçümlerini içeren yerel taslak için `tools/build_received_report.py`
çalıştırılır. Üretilen `report/private/report.tex` ve PDF öğrenci numarası/kişisel
veri notları içerdiği için public depoya alınmaz. Şablondaki ve ölçümlü taslaktaki
Stage 2 / Stage 4 öğrenci alanları tamamlanmadan rapor nihai değildir.

Kırmızı DRAFT alanlarını kendi gerçek yöntem ve sonuçlarınla değiştir.
Stage 2 seçimi ve Stage 4 analizini kendin yaz. Ana rapor en çok 6 sayfa;
ekler bu sınıra dahil değil. Gerçek görselleri ve sonuç tablolarını yerleştirdikten
sonra PDF'yi görsel olarak kontrol et. Başarı yüzdesi uydurma.

Eklerin sırası: A veri/ek ölçümler, B tekrarlanabilirlik bilgileri, son ek olarak
C AI kullanım beyanı. Tablodaki katkıları gerçek kullanımına göre güncelle.

`output/pdf/SudokuScan_Baslangic_Rehberi.pdf` Türkçe kullanım rehberidir;
IEEE raporunun yerine teslim edilmez.
