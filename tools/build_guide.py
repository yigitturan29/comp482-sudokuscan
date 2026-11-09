"""Build the Turkish getting-started PDF; not the final IEEE project report."""
from pathlib import Path
from html import escape
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "SudokuScan_Baslangic_Rehberi.pdf"
INK, TEAL, LIGHT = colors.HexColor("#16324F"), colors.HexColor("#087F8C"), colors.HexColor("#EFF6F8")


def register_fonts():
    for name, windows, linux in [
        ("Body", "arial.ttf", "DejaVuSans.ttf"),
        ("Bold", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
        ("Mono", "consola.ttf", "DejaVuSansMono.ttf"),
    ]:
        options = [Path("C:/Windows/Fonts") / windows,
                   Path("/usr/share/fonts/truetype/dejavu") / linux]
        path = next((p for p in options if p.exists()), None)
        if path is None:
            raise RuntimeError("Arial or DejaVu fonts are required for Turkish glyphs")
        pdfmetrics.registerFont(TTFont(name, str(path)))


def build():
    register_fonts()
    styles = {
        "title": ParagraphStyle("title", fontName="Bold", fontSize=27, leading=32, textColor=INK, spaceAfter=12),
        "subtitle": ParagraphStyle("subtitle", fontName="Body", fontSize=12, leading=17, textColor=TEAL, spaceAfter=18),
        "h": ParagraphStyle("h", fontName="Bold", fontSize=13, leading=18, textColor=TEAL, spaceBefore=12, spaceAfter=7),
        "body": ParagraphStyle("body", fontName="Body", fontSize=10.3, leading=15, textColor=INK, spaceAfter=8),
        "small": ParagraphStyle("small", fontName="Body", fontSize=8.4, leading=12, textColor=INK, spaceAfter=5),
        "code": ParagraphStyle("code", fontName="Mono", fontSize=8.2, leading=12, textColor=INK, backColor=LIGHT,
                               borderPadding=8, spaceBefore=5, spaceAfter=12),
    }
    flow = []

    def p(text, style="body"):
        flow.append(Paragraph(escape(text).replace("\n", "<br/>"), styles[style]))

    def title(number, text):
        p(f"{number:02d} / SUDOKUSCAN", "subtitle")
        p(text, "title")

    def heading(text):
        p(text, "h")

    title(1, "Önce çalışan demoyu gör")
    p("COMP 482 - 7 Kasım 2026 | Türkçe başlangıç rehberi", "subtitle")
    p("Bu paket hazır modüller ve öğrenci çalışma alanı içerir. Bitmiş teslim projesi değildir. "
      "Otomatik dış köşe seçimi ve Stage 4 analizi, yönergeye göre öğrenci tarafından yazılmalıdır.")
    heading("Bu bilgisayarda başlat")
    p("PowerShell'i SudokuScan klasöründe aç. Aşağıdaki komut sentetik test görüntüsünü "
      "oluşturur; dönüşümleri, OCR'ı ve Sudoku kontrolünü çalıştırır.")
    p("powershell -ExecutionPolicy Bypass -File .\\demo.ps1", "code")
    p("Demo bilinen sentetik köşeleri kullanır. Kendi telefon fotoğraflarında otomatik "
      "köşe seçiminin çalıştığını veya gizli test başarısını kanıtlamaz.")
    demo = ROOT / "results/demo/demo_summary.json"
    if demo.exists():
        data = json.loads(demo.read_text(encoding="utf-8"))
        if data.get("ocr_tested"):
            heading("Bu ortamda ölçülen sentetik test")
            p(f"Hazırlanmış hücre doğruluğu: %{100 * data['prepared_metrics']['cell_accuracy']:.2f}. "
              f"Ham hücre doğruluğu: %{100 * data['raw_metrics']['cell_accuracy']:.2f}. "
              f"Harris aday sayısı: {data['harris_candidate_count']}. "
              f"Demo süresi: {data['runtime_s']:.2f} saniye (iki OCR denemesi dahil).")
    heading("Bakılacak çıktılar")
    p("results/demo/known_GT_debug.png: okunan rakamlar ve çakışmalar.\n"
      "results/demo/known_GT_grid.txt: 9x9 dijital ızgara.\n"
      "results/demo/harris_candidates_only.png: yalnızca Harris adayları.\n"
      "results/demo/demo_summary.json: gerçek demo ölçümleri.", "small")
    montage = ROOT / "results/demo/rectification_montage.png"
    if montage.exists():
        flow.append(Spacer(1, 9))
        flow.append(Image(str(montage), width=500, height=181.5))
        p("A3 / A4 / H4 - bilinen sentetik köşelerle geliştirme testi. Kişisel veri analizi değil.", "small")
    flow.append(PageBreak())

    title(2, "Kendi verini hazırla")
    p("En az üç farklı kaynaktan üç basılı Sudoku ve kendi telefonunla en az on fotoğraf gerekiyor. "
      "Her karede, ızgaranın dışında, öğrenci numaran ve gerçek çekim tarihin yazılı el kartı bulunmalı.")
    rows = [["Kare", "Bulmaca", "Koşul"], ["01-03", "P1 / P2 / P3", "C1 - karşıdan"],
            ["04-06", "P1 / P2 / P3", "C2 - üç farklı eğik açı"],
            ["07", "P1", "C3 - 15-30 derece dönme"], ["08", "P2", "C4 - gölge veya az ışık"],
            ["09", "P3", "C5 - yazı/eşya/başka dikdörtgen"], ["10", "P1", "C2 + C4 veya C5"]]
    table = Table([[Paragraph(escape(cell), styles["small"]) for cell in row] for row in rows],
                  colWidths=[55, 115, 330], hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8)]))
    flow.append(table)
    heading("Orijinalleri koru")
    p("Fotoğrafları düzenlemeden ve EXIF'i silmeden data/personal/images/ içine kopyala. "
      "Ekran görüntüsü veya mesajlaşma uygulamasının sıkıştırılmış kopyasını kullanma. "
      "Dosyayı döndürerek kaydetme; etiketleme ve program aynı saklanan piksel düzenini kullanır.")
    heading("Köşeleri ve rakamları etiketle")
    p(".\\.venv\\Scripts\\python.exe tools/annotate.py\n"
      "  --input data/personal/images/photo01.jpg\n"
      "  --outdir data/personal/annotations", "code")
    p("Üstteki komutu PowerShell'de tek satırda yaz. TL, TR, BR, BL sırasıyla tıkla; "
      "sağ tık son noktayı siler. Hücrelere fotoğraftaki sayıları gir, boşları 0 bırak. "
      "Koşulları, kaynağı ve tarihi gir; fotoğraftaki kartı gözünle kontrol edip JSON'u kaydet.")
    p("Etiketleme tıklamaları sadece ground truth içindir. Otomatik grader arayüzünde kullanılmaz.", "small")
    heading("Kontrol")
    p(".\\.venv\\Scripts\\python.exe tools/check_dataset.py", "code")
    p("Geliştirme kümesinin bağlantısını LMS'den al. Geliştirme ve kişisel küme sonuçlarını ayrı tut.")
    flow.append(PageBreak())

    title(3, "Kodu öğren ve tamamla")
    heading("Senin işlevin: dış dört köşeyi seçme")
    p("student_corner_selection.py içindeki select_outer_corners işlevini kendin yaz. "
      "Girdi: ön işlenmiş görüntü, Harris adayları ve ortak ayarlar. Çıktı: "
      "harris.candidates dizisinden dört farklı tam sayı indeksi, TL/TR/BR/BL sırasıyla. "
      "Bulamıyorsan None döndür. Hazır seçim mantığı bu pakette bulunmuyor.")
    p("Bu işlev annotation açamaz, dosya adına göre davranamaz, elle nokta alamaz ve "
      "görüntüye özel sabit koordinat kullanamaz. Son koordinatlar Harris'ten gelmeli.")
    heading("Hazır modüller ne yapıyor?")
    p("preprocessing.py: boyuta göre filtreler ve aydınlatma düzeltmesi.\n"
      "harris.py: cevap, göreli eşik, NMS ve yerel subpixel iyileştirme.\n"
      "geometry.py: A3, dört noktalı least squares A4 ve H4.\n"
      "recognition.py: iç marj, dolu/boş, rakam hazırlama ve Tesseract.\n"
      "validity.py: satır, sütun ve 3x3 kutu tekrarları.")
    heading("Otomatik komutlar - seçim işlevinden sonra")
    p("python sudoku_scan.py --input photo.jpg --outdir out/\n"
      "python sudoku_scan.py --batch images_dir/ --outdir results/", "code")
    p("Seçim eksikken sonuç student_stage2_required olur. Bu davranış, tamamlanmamış "
      "kodu başarılıymış gibi göstermemek içindir. Köşeler orijinal piksel koordinatlarında yazılır.")
    heading("Ölçüm ve test araçları")
    p("tools/evaluate.py: tüm metrikler ve C1-C5 kırılımı.\n"
      "tools/harris_study.py: en az altı karede parametre ölçümleri.\n"
      "tools/ocr_study.py: ham/hazırlanmış hücre ve PSM çalışması.\n"
      "python -m pytest -q: modüllerin otomatik testleri.")
    p("Bu araçların tam komutları README.md içinde. Stage 4'ün ölçüm tasarımını, "
      "çizgi hatası hesaplarını, grafiklerini ve sonuç yorumlarını kendin tamamlamalısın.")
    heading("Başlangıç ayarını sonuç sanma")
    p("6 piksellik iç marj ve bileşen eşikleri başlangıç değerleridir. Kendi verinde "
      "neden iyi veya kötü çalıştıklarını ölç. OCR 'valid' dese bile ızgaranın doğru okunduğu "
      "veya tek çözümlü olduğu sonucu çıkmaz.")
    flow.append(PageBreak())

    title(4, "Rapor ve savunma")
    heading("Rapor iskeleti")
    p("report/report_template.tex resmi IEEEtran konferans sınıfını kullanır. Overleaf'teki "
      "IEEE Conference Template içinde açabilirsin. Kırmızı DRAFT alanlarını gerçek "
      "yöntem ve sonuçlarınla değiştir. Ana metin en çok altı sayfa; ekler ayrıca.")
    p("Giriş; köşe tespiti; rectification; kendi affine/homography analizin; recognition; "
      "sonuçlar; en az dört gerçek başarısızlık örneği; sonuç ve sınırlamalar bulunmalı. "
      "AI beyanı son ek olmalı. Bu rehber proje raporunun yerine teslim edilmez.")
    heading("Eksik kalmaması gerekenler")
    p("Kendi fotoğrafların ve annotation'lar; kendi seçim kodun; en az altı görüntüde Harris "
      "çalışması; en az sekiz görüntüde kendi Stage 4 analizin; OCR hazırlama etkisi; "
      "C1-C5 metrikleri; debug çıktıları; CPU süre ölçümleri; gerçek geliştirme geçmişi.")
    heading("AI beyanını doğru doldur")
    p("docs/AI_KULLANIM_BEYANI.md bu oturumun katkı kaydını içerir. AI tarafından üretilen "
      "uygulama kodlarının izin kapsamını ders ekibiyle netleştir. Köşe seçimi ve karşılaştırma "
      "analizini kendin yazmadığın sürece, kendim yazdım onayını imzalama.")
    heading("10 dakikalık prova")
    p("2 dakika: yeni fotoğrafta canlı çalıştır.\n"
      "3 dakika: özellikle kendi seçim işlevini açıkla.\n"
      "3 dakika: AI kullanmadan bir parametre veya dönüşüm değiştir.\n"
      "2 dakika: kendi ölçüm sonuçlarını savun.")
    heading("Tarih ve not")
    p("Yönergede teslim 5 Kasım 2026 23:59, savunma 9-13 Kasım olarak belirtiliyor. "
      "Bu rehber 7 Kasım'da hazırlandı. Geç teslim ve güncel duyuruları LMS'den doğrula. "
      "Yönergedeki geç teslim kesintileri ve sözlü savunma çarpanı nedeniyle tam puan garantisi yok.")
    heading("Kaynak ve sonraki adım")
    p("Kaynak: sağladığın COMP482 Project 1 SudokuScan yönergesi, özellikle bölümler 3-11 ve Ek A-C. "
      "API belgeleri README.md'de bağlantılı. Şimdi demoyu aç, kendi fotoğraflarını çek ve "
      "BURADAN_BASLA.md ile kendi seçim işlevini öğrenerek tamamla.", "small")

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(TEAL)
        canvas.line(46, 45, 549, 45)
        canvas.setFont("Body", 8)
        canvas.setFillColor(INK)
        canvas.drawString(46, 30, "COMP 482 | Çalışma rehberi - nihai rapor değil")
        canvas.drawRightString(549, 30, str(document.page))
        canvas.restoreState()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(OUT), pagesize=(595.28, 841.89), leftMargin=46, rightMargin=46,
                      topMargin=43, bottomMargin=60, title="SudokuScan Başlangıç Rehberi",
                      author="COMP 482 çalışma paketi").build(flow, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    build()
