# UYAP Evrak Asistanı

![Testler](https://github.com/alperenivak/uyap-evrak-asistani/actions/workflows/test.yml/badge.svg)
![Lisans](https://img.shields.io/badge/lisans-AGPL--3.0--or--later-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

Avukatlar için **çevrimdışı** evrak hazırlama aracı: UYAP'a yüklemeden önce PDF, görsel, UDF ve Word
belgelerini birleştirir, küçültür, böler, kaşeler, kişisel verilerden arındırır ve dönüştürür.

Belgeler bilgisayarınızdan çıkmaz. Uygulama internete bağlanmaz, UYAP'a giriş yapmaz, telemetri içermez.

> Bağımsız bir yardımcı yazılımdır; UYAP veya T.C. Adalet Bakanlığı ile bağlantılı değildir.

## Öne çıkanlar

| Alan | Neler yapar |
|---|---|
| **Birleştir ve küçült** | PDF, UDF, JPG/PNG/WEBP/BMP ve çok sayfalı TIFF'i tek PDF'te birleştirir; dosya başına yer imi, isteğe bağlı tıklanabilir içindekiler sayfası ve sayfa numarası. "Akıllı" sıkıştırma metin katmanını korur. UYAP'ın MB sınırına göre dosyayı parçalara böler. |
| **Sayfa işlemleri** | Sayfa ayırma, silme ve yeniden sıralama; döndürme; boş sayfaları (onay alarak) temizleme; sayfa sayfa bölme. |
| **Evrak hazırlama** | "Aslı gibidir" kaşesi (başlık, ad soyad, sicil no, tarih; renk ve konum seçilebilir; döndürülmüş sayfalarda da doğru yönde); renkli çapraz filigran. |
| **KVKK** | T.C. kimlik no (algoritma doğrulamalı), IBAN, telefon, e-posta ve özel kelimeleri **taranır** (rapor) veya **kalıcı olarak karartılır**; çıktı yeniden taranarak doğrulanır; üst veriler temizlenir. |
| **Dönüştür ve oku** | UDF ➔ Word, UDF ➔ PDF, Word ➔ PDF, Word ➔ UDF *(deneysel)*, PDF ➔ Görsel; UDF'yi biçimiyle görüntüleme. |
| **Dosya paneli** | PDF/UDF/Word içinde Türkçe karakter duyarsız arama; SHA-256'lı Excel evrak dizini; aynı içerikli dosya uyarısı; bellekte tutulan işlem günlüğü. |

## Kurulum

### Hazır çalıştırılabilir dosya (Windows)

[Releases](https://github.com/alperenivak/uyap-evrak-asistani/releases) sayfasından `UYAP_Evrak_Asistani.exe`
dosyasını indirip çalıştırın; kurulum gerekmez. Program imzasız olduğu için ilk açılışta Windows
**"Ek bilgi → Yine de çalıştır"** uyarısı verebilir.

### Kaynaktan

```bash
git clone https://github.com/alperenivak/uyap-evrak-asistani.git
cd uyap-evrak-asistani
pip install -r requirements.txt
python app.py
```

Python 3.10 veya üstü gerekir. **Word ➔ PDF** dönüştürmesi Windows'ta kurulu Microsoft Word kullanır.

### EXE derleme

Windows'ta `build.bat` dosyasına çift tıklayın; çıktı `dist\UYAP_Evrak_Asistani.exe` olur.
GitHub'da **Actions → Windows EXE derle → Run workflow** ile de derlenebilir.

## KVKK ve gizlilik

- Tüm işlemler yereldir; ağ bağlantısı kodu yoktur (tek istisna: "Alperen İVAK" yazısına veya
  "GitHub Profili" düğmesine tıklarsanız tarayıcınız profil sayfamı açar).
- Diske yalnızca tercihler yazılır: `%APPDATA%\UyapEvrakAsistani\ayarlar.json` (kalite modu, kaşe başlığı,
  avukat adı, son klasör). Evrak içeriği saklanmaz.
- İşlem günlüğü yalnızca bellekte tutulur ve uygulama kapanınca silinir.
- Çıktılardan yazar ve program bilgisi (üst veri) varsayılan olarak temizlenir.
- **Karartmanın sınırı:** yalnızca metin katmanı olan sayfalarda çalışır. Taranmış (görüntü) sayfalardaki
  yazılar bulunamaz; uygulama bu sayfaları bildirir. Çıktıyı paylaşmadan önce gözle kontrol edin.

## Mimari

```
app.py     Arayüz (Tkinter + sv-ttk). İş mantığı içermez.
core.py    PDF motoru. Arayüzden bağımsız; tkinter içermez.
udf.py     UDF okuma/yazma, UDF/Word/PDF dönüşümleri.
config.py  Kurumsal kimlik ve kalıcı ayarlar.
tests/     pytest ile çekirdek testleri (30 test).
```

**İş parçacığı modeli.** Uzun işlemler ayrı bir thread'de çalışır; arayüze `queue.Queue` ile ilerleme ve
sonuç iletir, ana thread bunu `after(80 ms)` ile boşaltır. Tk nesnelerine yalnızca ana thread dokunur;
iş başlamadan önce tüm ayarlar okunup thread'e değer olarak verilir.

**Çekirdek sözleşmesi.** `core` fonksiyonları yol ve parametre alır, sonucu döndürür, `ilerle(oran, mesaj)`
geri çağrısı ile ilerleme bildirir. Kullanıcıya gösterilebilecek hatalar `IslemHatasi` ile fırlatılır.
Hiçbir işlem orijinal dosyanın üzerine yazmaz.

**UDF blok modeli.** `udf.udf_oku`, UDF'yi (paragraf, tablo, sayfa sonu) bloklarına çevirir; Word, PDF ve
ekran görüntüleyici aynı modeli kullanır.

**Bilinçli tasarım kararları**

- Kaşe, filigran ve sayfa numarası fontları her işlemde benzersiz adla gömülür ve kaydederken yalnızca
  kullanılan harflere indirgenir; aksi halde PDF şişer veya önceki bir alt kümeyle çakışıp harfler kutuya döner.
- Kaşe, döndürülmüş sayfalarda `derotation_matrix` ile ekrandaki köşeye ve dik basılır.
- Karartma: eşleşmeleri siler, gizli metin/üst veriyi `scrub` ile temizler, çıktıyı **yeniden tarar** ve
  kalan eşleşmeyi raporlar.
- T.C. kimlik numarası varsayılan olarak resmî algoritmayla doğrulanır (dosya/sipariş numaraları karartılmaz);
  kapatılabilir.
- Boyut bölücü, her sayfada tüm dosyayı yeniden ölçmek yerine ortalama sayfa boyutundan tahmin yapar ve
  yalnızca sınıra yaklaşınca ölçer.
- Word ➔ UDF çıktısı yazıldıktan sonra yeniden okunup kaynakla karşılaştırılır; uyuşmazsa dosya yazılmaz.

## Test

```bash
pip install -r requirements-dev.txt
pytest
```

Testler çekirdeği ve UDF modülünü kapsar ve her push'ta GitHub Actions'ta çalışır. Arayüz ve
Word ➔ PDF (Microsoft Word gerektirir) Windows'ta elle denenmelidir.

## Bilinen sınırlar

- UDF ➔ PDF/Word çıktısı **okunabilir bir kopyadır**; UDF'deki elektronik imzayı taşımaz ve imzalı asıl yerine geçmez.
- **Word ➔ UDF deneyseldir.** Metin, hizalama, kalın/italik/altı çizili, punto, yazı tipi ve kenar boşlukları
  taşınır; tablolar satır satır metne çevrilir, görseller ve üstbilgi/altbilgi taşınmaz. UYAP Doküman
  Editörü'nde açıp kontrol etmeden kullanmayın.
- UDF okuma/yazma, biçimin yayımlanmış bir şartnamesi olmadığı için bilinen yapıya dayanır; farklı UDF
  sürümlerinde eksik kalabilir. Sorun yaşadığınız bir UDF varsa (kişisel veriler çıkarılmış olarak) issue açın.
- Taranmış (görüntü) sayfalarda karartma ve arama yapılamaz; OCR yoktur.
- Şifreli PDF desteklenmez.

## Lisans

**GNU Affero Genel Kamu Lisansı v3 veya sonrası (AGPL-3.0-or-later)** — bkz. [`LICENSE`](LICENSE).

Uygulama, AGPL-3.0 veya ticari lisansla sunulan [PyMuPDF](https://pymupdf.readthedocs.io/) kullanır;
bu nedenle birlikte dağıtılan çalışma da AGPL koşullarına tabidir. Kullanım ve değişiklik serbesttir;
değiştirilmiş sürümü dağıtanlar kaynak kodu aynı lisansla açmak ve telif bildirimlerini korumak zorundadır.
Farklı lisans koşulları için yazara GitHub profilinden ulaşın (PyMuPDF'in kendi koşulları ayrıca geçerli kalır).
Üçüncü taraf bileşenler: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Kaynaklar ve esin

Bu proje, aşağıdaki açık projelerin çözdüğü ihtiyaçlardan esinlenmiştir. Özellik fikirleri ve kullanıcı
akışları bu projelerden gelir; **kaynak kod kopyalanmamış, bağımsız olarak yeniden yazılmıştır.**

- [tolunayakay/uyap-evrak-asistani](https://github.com/tolunayakay/uyap-evrak-asistani) — masaüstü evrak asistanı
- [MERBACO/uyap-evrak-asistani](https://github.com/MERBACO/uyap-evrak-asistani) — dizinleme, içindekiler, arama fikirleri
- [mertcelen/udf-okuyucu](https://github.com/mertcelen/udf-okuyucu) — UDF görüntüleme
- [miasimbilir/udf-cevirici](https://github.com/miasimbilir/udf-cevirici) — Word ↔ UDF dönüşümü

## Geliştirici

**Alperen İVAK** — [github.com/alperenivak](https://github.com/alperenivak)
