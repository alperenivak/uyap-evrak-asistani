# Katkı rehberi

Hata bildirimleri ve öneriler issue olarak çok değerlidir.

**Gizlilik uyarısı:** Bu uygulama hukuki evrakla çalışır. Issue'ya ekran görüntüsü, dosya veya günlük eklemeden önce
müvekkil adı, T.C. kimlik no, IBAN, telefon ve benzeri kişisel verileri **mutlaka çıkarın**. Hatayı yeniden üretmek için
gerçek belge yerine içeriği değiştirilmiş örnek bir belge kullanın.

## Geliştirme

```bash
pip install -r requirements-dev.txt
pytest          # çekirdek testleri
python app.py   # arayüz
```

- İş mantığı `core.py` / `udf.py` içinde olmalı; `app.py` yalnızca arayüzdür. `core` içinde `tkinter` kullanmayın.
- Yeni bir işlem eklerken `tests/` altına test ekleyin.
- Kullanıcıya gösterilecek hatalar için `core.IslemHatasi` kullanın.
- Hiçbir işlem orijinal dosyanın üzerine yazmamalıdır.

Katkılar projenin lisansı olan AGPL-3.0-or-later altında kabul edilir.
