# Değişiklik günlüğü

Biçim [Keep a Changelog](https://keepachangelog.com/tr/1.1.0/) esaslarına, sürümleme [SemVer](https://semver.org/lang/tr/) esaslarına dayanır.

## [2.1.0] — 2026-10

### Eklendi
- Birleştirmeye UDF (biçimli PDF kopyası olarak) ve çok sayfalı TIFF desteği.
- Birleştirmede isteğe bağlı tıklanabilir içindekiler sayfası.
- UDF ➔ PDF dönüştürücü; UDF'yi biçimiyle gösteren görüntüleyici.
- Word ➔ UDF dönüştürücü (deneysel, yazım sonrası doğrulamalı).
- PDF/UDF/Word içinde Türkçe karakter duyarsız arama.
- SHA-256'lı Excel evrak dizini ve aynı içerikli dosya uyarısı.
- Kaşe için kırmızı/siyah/lacivert/mavi, filigran için gri dahil beş renk seçeneği; ad soyad satırı için ayrı renk.
- Kılavuza "Hakkında" sekmesi; alt bilgideki ad ve düğme geliştirici profiline bağlanır.
- pytest ile 30 çekirdek testi ve GitHub Actions test iş akışı.

## [2.0.0] — 2026-10

### Değişti
- Uygulama baştan yazıldı: arayüz (`app.py`), PDF motoru (`core.py`), UDF modülü (`udf.py`) ve ayarlar (`config.py`) ayrıldı.
- Renk kodlu araç kartları, koyu başlık, bellekte tutulan işlem günlüğü.
- İşlemler arka plan thread'inde; arayüz donmaz, ilerleme çubuğu vardır.
- "Akıllı" sıkıştırma metin katmanını korur.
- Kaşe, filigran ve sayfa numarası fontları yalnızca kullanılan harflerle gömülür.
- Hatalı sayfa aralıkları sessizce atlanmaz, açık hata verir.

### Eklendi
- KVKK tarama (rapor) ve karartma sonrası doğrulama; T.C. kimlik algoritma doğrulaması; taranmış sayfa uyarısı.
- Boş sayfa silmeden önce onay; Word ➔ PDF; Word metin okuma; kaşede sicil no ve sayfa yönüne duyarlı yerleşim.
- Yer imi, filigran, PDF ➔ Görsel, üst veri temizliği, UYAP boyut bölücüde tahminli ölçüm.
