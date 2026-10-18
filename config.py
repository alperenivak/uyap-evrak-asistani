# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Alperen İVAK
"""
UYAP Evrak Asistanı — kurumsal kimlik ve kalıcı ayarlar.

Geliştirici : Alperen İVAK
GitHub      : GITHUB_URL sabitini kendi adresinizle değiştirin
"""
import os
import json

APP_AD = "UYAP Evrak Asistanı"
APP_AD_BUYUK = "UYAP EVRAK ASİSTANI"
SURUM = "2.1.0"
YAPIMCI = "Alperen İVAK"
GITHUB_URL = "https://github.com/alperenivak"


def github_tanimli():
    return "KULLANICI_ADI" not in GITHUB_URL


VARSAYILAN = {
    "profil": "Akıllı – metni koru (önerilen)",
    "meta_temizle": True,
    "bates": False,
    "icindekiler": False,
    "on_ek": "EK-1",
    "hedef_mb": "9.5",
    "kase_baslik": "ASLI GİBİDİR",
    "kase_ad": "",
    "kase_sicil": "",
    "kase_renk": "kirmizi",
    "kase_ad_renk": "ayni",
    "filigran_metin": "ÖRNEKTİR",
    "filigran_renk": "gri",
    "kase_konum": "sag_alt",
    "son_klasor": "",
}


def _ayar_dosyasi():
    taban = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    klasor = os.path.join(taban, "UyapEvrakAsistani")
    os.makedirs(klasor, exist_ok=True)
    return os.path.join(klasor, "ayarlar.json")


def ayarlari_yukle():
    ayar = dict(VARSAYILAN)
    try:
        with open(_ayar_dosyasi(), "r", encoding="utf-8") as f:
            ayar.update({k: v for k, v in json.load(f).items() if k in VARSAYILAN})
    except Exception:
        pass
    return ayar


def ayarlari_kaydet(ayar):
    try:
        with open(_ayar_dosyasi(), "w", encoding="utf-8") as f:
            json.dump(ayar, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
