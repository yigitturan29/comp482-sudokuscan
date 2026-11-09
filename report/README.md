# IEEE raporunu üretme

Tam pakette ölçülmüş PDF output/private/COMP482_SudokuScan_Rapor.pdf
konumundadır. Ana metin, Stage 4 karşılaştırması, gerçek ölçümler, grafikler,
dört hata örneği ve en sonda katkı/AI beyanı içerir.

Deneyleri yeniden üretmek:

```powershell
powershell -ExecutionPolicy Bypass -File .\deneyler.ps1 -OgrenciNo NUMARAN
```

Rapor kaynağı report/private/report.tex ve figures altına yazılır. Yerel
Tectonic veya bir TeX dağıtımının IEEEtran sınıfı gerekir. Bu bilgisayarda:

```powershell
.\.tools\tectonic\tectonic.exe --outdir output/private report/private/report.tex
```

Tectonic bir kerelik TeX paketlerini resmi bundle kaynağından indirebilir.
Başka bilgisayarda report/private içindeki kaynak ve figures klasörü Overleaf'in
IEEE Conference projesine birlikte yüklenebilir. report_template.tex boş
başlangıç şablonudur; ölçülmüş rapor yerine teslim edilmez.

Kişisel rapor ve fotoğraflar public depoya alınmaz. Veri kaynakları, EXIF eksikliği,
annotation incelemesi ve gerçek katkı beyanı dosyada açıkça belirtilmiştir.
