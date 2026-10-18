# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Alperen İVAK
"""
UYAP Evrak Asistanı
Avukatlar için PDF / görsel / UDF evrak hazırlama aracı.

Geliştirici : Alperen İVAK
GitHub      : bkz. config.GITHUB_URL
"""
import os
import sys
import time
import queue
import ctypes
import threading
import traceback
import webbrowser
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from tkinterdnd2 import TkinterDnD, DND_FILES
import sv_ttk
from PIL import Image, ImageTk

import core
import udf
import config
from core import IslemHatasi

DESTEKLENEN = (".pdf", ".docx", ".udf") + core.GORSEL_UZANTILARI

# Renk paleti
LACIVERT, LACIVERT2, ALTIN = "#0B1F3A", "#16345C", "#E3B04B"
ZEMIN, BEYAZ, KENAR, YAZI, GRI = "#F4F7FB", "#FFFFFF", "#D9E0EC", "#16233A", "#6B7690"
MAVI, MOR, KIRMIZI, YESIL, TURKUAZ = "#2563EB", "#7C3AED", "#D9304F", "#059669", "#0891B2"


def acik_ton(hex_renk, oran=0.9):
    r, g, b = (int(hex_renk[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(c + (255 - c) * oran) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def dpi_netlestir():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def kaynak_yolu(goreli):
    taban = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(taban, goreli)


# ----------------------------------------------------------------------------
# Renk kodlu araç kartı
# ----------------------------------------------------------------------------
class Kart(tk.Frame):
    def __init__(self, ana, metin, simge, renk, komut):
        super().__init__(ana, bg=BEYAZ, highlightthickness=1, highlightbackground=KENAR, cursor="hand2")
        self.renk, self.komut, self.aktif = renk, komut, True
        self.serit = tk.Frame(self, bg=renk, width=6)
        self.serit.pack(side="left", fill="y")
        self.ikon = tk.Label(self, text=simge, font=("Segoe UI Emoji", 13), fg=renk, bg=BEYAZ, width=3)
        self.ikon.pack(side="left", pady=5)
        self.yazi = tk.Label(self, text=metin, font=("Segoe UI Semibold", 9), fg=YAZI, bg=BEYAZ, anchor="w")
        self.yazi.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._p = (self, self.ikon, self.yazi)
        for p in self._p:
            p.bind("<Enter>", self._gir)
            p.bind("<Leave>", self._cik)
            p.bind("<Button-1>", self._tikla)

    def _boya(self, bg, kenar):
        for p in self._p:
            p.configure(bg=bg)
        self.configure(highlightbackground=kenar)

    def _gir(self, _):
        if self.aktif:
            self._boya(acik_ton(self.renk, 0.9), self.renk)

    def _cik(self, _):
        x, y = self.winfo_pointerxy()
        if self.winfo_containing(x, y) in self._p:
            return
        self._boya(BEYAZ, KENAR)

    def _tikla(self, _):
        if self.aktif:
            self.komut()

    def durum(self, aktif):
        self.aktif = aktif
        self._boya(BEYAZ, KENAR)
        self.ikon.configure(fg=self.renk if aktif else "#B8C0D0")
        self.yazi.configure(fg=YAZI if aktif else "#B8C0D0")
        self.configure(cursor="hand2" if aktif else "arrow")


# ----------------------------------------------------------------------------
# Basit form penceresi
# ----------------------------------------------------------------------------
class Form(tk.Toplevel):
    """alanlar: [{"ad","etiket","tur": entry|check|radio, "varsayilan", "secenekler":[(deger,etiket)]}]"""

    def __init__(self, ana, baslik, alanlar, tamam="Tamam", aciklama=None, renk=MAVI):
        super().__init__(ana)
        self.title(baslik)
        self.transient(ana)
        self.resizable(False, False)
        self.sonuc = None
        self._v = {}
        tk.Frame(self, bg=renk, height=5).pack(fill="x")
        cerceve = ttk.Frame(self, padding=20)
        cerceve.pack(fill="both", expand=True)
        ttk.Label(cerceve, text=baslik, font=("Segoe UI Semibold", 12)).pack(anchor="w")
        if aciklama:
            ttk.Label(cerceve, text=aciklama, wraplength=400, justify="left",
                      foreground=GRI).pack(anchor="w", pady=(4, 6))
        ilk_entry = None
        for a in alanlar:
            tur = a["tur"]
            if tur == "check":
                v = tk.BooleanVar(value=a.get("varsayilan", False))
                ttk.Checkbutton(cerceve, text=a["etiket"], variable=v).pack(anchor="w", pady=3)
            elif tur == "entry":
                ttk.Label(cerceve, text=a["etiket"]).pack(anchor="w", pady=(8, 2))
                v = tk.StringVar(value=a.get("varsayilan", ""))
                e = ttk.Entry(cerceve, textvariable=v, width=50)
                e.pack(fill="x")
                ilk_entry = ilk_entry or e
            elif tur == "radio":
                ttk.Label(cerceve, text=a["etiket"]).pack(anchor="w", pady=(8, 2))
                v = tk.StringVar(value=a.get("varsayilan", a["secenekler"][0][0]))
                sat = ttk.Frame(cerceve)
                sat.pack(anchor="w")
                for deger, et in a["secenekler"]:
                    ttk.Radiobutton(sat, text=et, variable=v, value=deger).pack(side="left", padx=(0, 14))
            self._v[a["ad"]] = v
        alt = ttk.Frame(cerceve)
        alt.pack(fill="x", pady=(18, 0))
        ttk.Button(alt, text=tamam, style="Accent.TButton", command=self._tamam).pack(side="right")
        ttk.Button(alt, text="İptal", command=self.destroy).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda e: self._tamam())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        x = ana.winfo_rootx() + (ana.winfo_width() - self.winfo_width()) // 2
        y = ana.winfo_rooty() + (ana.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.wait_visibility()
        self.grab_set()
        (ilk_entry or self).focus_set()
        ana.wait_window(self)

    def _tamam(self):
        self.sonuc = {k: v.get() for k, v in self._v.items()}
        self.destroy()


# ----------------------------------------------------------------------------
# Ana pencere
# ----------------------------------------------------------------------------
class UyapEvrakAsistani(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.APP_AD)
        sv_ttk.set_theme("light")
        self.configure(bg="#FAFAFA")
        self._ikon()
        self.ayar = config.ayarlari_yukle()
        if self.ayar.get("kase_renk") not in core.RENKLER:
            self.ayar["kase_renk"] = "kirmizi"
        self.dosyalar = []
        self.kuyruk = queue.Queue()
        self.mesgul = False
        self.kartlar = []
        self._islem_adi = "İşlem"
        self._t0 = 0.0

        self._baslik()
        self._ayar_seridi()
        self._alt_bilgi()
        self._govde()
        self.protocol("WM_DELETE_WINDOW", self._kapat)
        self.after(80, self._kuyruk_dinle)
        self._boyutlandir()
        self._log("Hazır. Tüm işlemler bu bilgisayarda yerel olarak yapılır.", "ok")

    # ---- pencere ------------------------------------------------------------
    def _ikon(self):
        yol = kaynak_yolu("logo.ico")
        if os.path.exists(yol):
            try:
                self.iconbitmap(yol)
            except Exception:
                pass

    def _boyutlandir(self):
        """İçerik her DPI'da sığsın diye pencere, istenen boyuta göre ayarlanır."""
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        rw, rh = self.winfo_reqwidth(), self.winfo_reqheight()
        self.minsize(min(rw, sw - 40), min(rh, sh - 80))
        w, h = min(max(rw, 1100), sw - 40), min(max(rh, 700), sh - 80)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max((sh - h) // 3, 0)}")

    # ---- yapı ---------------------------------------------------------------
    def _baslik(self):
        ust = tk.Frame(self, bg=LACIVERT)
        ust.pack(fill="x")
        ic = tk.Frame(ust, bg=LACIVERT)
        ic.pack(fill="x", padx=20, pady=9)
        try:
            img = Image.open(kaynak_yolu("logo.png")).resize((46, 46), Image.LANCZOS)
            self._logo = ImageTk.PhotoImage(img)
            tk.Label(ic, image=self._logo, bg=LACIVERT).pack(side="left", padx=(0, 12))
        except Exception:
            pass
        metin = tk.Frame(ic, bg=LACIVERT)
        metin.pack(side="left")
        tk.Label(metin, text=config.APP_AD_BUYUK, font=("Segoe UI Semibold", 16), fg="white",
                 bg=LACIVERT).pack(anchor="w")
        tk.Label(metin, text="Avukatlar için evrak hazırlama istasyonu", font=("Segoe UI", 9),
                 fg=ALTIN, bg=LACIVERT).pack(anchor="w")
        tk.Button(ic, text="  Kılavuz  ", command=self._kilavuz, bg=LACIVERT2, fg="white",
                  activebackground="#1F4678", activeforeground="white", relief="flat",
                  font=("Segoe UI Semibold", 9), cursor="hand2", pady=5).pack(side="right")
        tk.Label(ic, text="🔒  Çevrimdışı çalışır · Evrak dışarı gönderilmez", font=("Segoe UI", 9),
                 fg="#6EE7B7", bg="#0E3B33", padx=12, pady=5).pack(side="right", padx=14)
        tk.Frame(ust, bg=ALTIN, height=3).pack(fill="x")

    def _ayar_seridi(self):
        serit = tk.Frame(self, bg=BEYAZ, highlightthickness=1, highlightbackground=KENAR)
        serit.pack(fill="x", padx=20, pady=(14, 0))
        ic = ttk.Frame(serit, padding=(14, 8))
        ic.pack(fill="x")
        ttk.Label(ic, text="Kalite", foreground=GRI).pack(side="left")
        self.profil = tk.StringVar(value=self.ayar["profil"] if self.ayar["profil"] in core.PROFILLER
                                   else list(core.PROFILLER)[0])
        ttk.Combobox(ic, textvariable=self.profil, values=list(core.PROFILLER), state="readonly",
                     width=30).pack(side="left", padx=(8, 18))
        self.bates = tk.BooleanVar(value=self.ayar["bates"])
        ttk.Checkbutton(ic, text="Sayfa no", variable=self.bates,
                        command=self._bates_durum).pack(side="left")
        self.on_ek = ttk.Entry(ic, width=8)
        self.on_ek.insert(0, self.ayar["on_ek"])
        self.on_ek.pack(side="left", padx=(8, 18))
        self._bates_durum()
        self.icindekiler = tk.BooleanVar(value=self.ayar["icindekiler"])
        ttk.Checkbutton(ic, text="İçindekiler (birleştirmede)", variable=self.icindekiler).pack(
            side="left", padx=(0, 18))
        self.meta = tk.BooleanVar(value=self.ayar["meta_temizle"])
        ttk.Checkbutton(ic, text="Üst verileri temizle", variable=self.meta).pack(side="left")

    def _alt_bilgi(self):
        alt = tk.Frame(self, bg=LACIVERT)
        alt.pack(fill="x", side="bottom")
        ic = tk.Frame(alt, bg=LACIVERT)
        ic.pack(fill="x", padx=20, pady=6)
        self.durum = tk.Label(ic, text="Hazır.", fg="white", bg=LACIVERT, font=("Segoe UI", 9))
        self.durum.pack(side="left")
        kimlik = tk.Label(ic, text=config.YAPIMCI, fg=ALTIN, bg=LACIVERT, font=("Segoe UI", 8))
        kimlik.pack(side="right")
        if config.github_tanimli():
            kimlik.configure(cursor="hand2")
            kimlik.bind("<Button-1>", lambda e: webbrowser.open(config.GITHUB_URL))
            kimlik.bind("<Enter>", lambda e: kimlik.configure(font=("Segoe UI", 8, "underline"), fg="white"))
            kimlik.bind("<Leave>", lambda e: kimlik.configure(font=("Segoe UI", 8), fg=ALTIN))
        self.ilerleme = ttk.Progressbar(ic, length=170, mode="determinate", maximum=100)
        self.ilerleme.pack(side="right", padx=(0, 20))

    def _govde(self):
        govde = ttk.Frame(self, padding=(20, 14, 20, 14))
        govde.pack(fill="both", expand=True)
        govde.columnconfigure(0, weight=1)
        govde.columnconfigure(1, minsize=470)
        govde.rowconfigure(0, weight=1)

        # ---- sol: dosyalar + günlük
        sol = ttk.Frame(govde)
        sol.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        sol.rowconfigure(1, weight=1)
        sol.columnconfigure(0, weight=1)
        ttk.Label(sol, text="DOSYALAR", font=("Segoe UI Semibold", 9), foreground=MAVI).grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(sol, text="PDF, Word, UDF veya görsel sürükleyip bırakın", foreground=GRI).grid(
            row=0, column=0, sticky="e", pady=(0, 4))
        self.agac = ttk.Treeview(sol, columns=("ad", "tur", "sayfa", "boyut"), show="headings",
                                 selectmode="browse", height=9)
        for k, b, g, a in (("ad", "Dosya", 320, "w"), ("tur", "Tür", 55, "center"),
                           ("sayfa", "Sayfa", 55, "center"), ("boyut", "Boyut", 85, "e")):
            self.agac.heading(k, text=b)
            self.agac.column(k, width=g, anchor=a, stretch=(k == "ad"))
        self.agac.grid(row=1, column=0, sticky="nsew")
        kay = ttk.Scrollbar(sol, orient="vertical", command=self.agac.yview)
        kay.grid(row=1, column=1, sticky="ns")
        self.agac.configure(yscrollcommand=kay.set)
        self.agac.drop_target_register(DND_FILES)
        self.agac.dnd_bind("<<Drop>>", self._birak)
        self.agac.bind("<Delete>", lambda e: self._kaldir())

        ara = ttk.Frame(sol)
        ara.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(ara, text="Dosyalarda ara", foreground=GRI).pack(side="left")
        self.ara_var = tk.StringVar()
        giris = ttk.Entry(ara, textvariable=self.ara_var)
        giris.pack(side="left", fill="x", expand=True, padx=8)
        giris.bind("<Return>", lambda e: self._tikla("İçerikte Ara", self._icerikte_ara))
        ttk.Button(ara, text="Ara", command=lambda: self._tikla("İçerikte Ara", self._icerikte_ara)).pack(side="left")

        btn = ttk.Frame(sol)
        btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 10))
        ttk.Button(btn, text="＋ Dosya Ekle", style="Accent.TButton", command=self._ekle_dialog).pack(side="left")
        ttk.Button(btn, text="▲", width=3, command=lambda: self._tasi(-1)).pack(side="left", padx=(10, 2))
        ttk.Button(btn, text="▼", width=3, command=lambda: self._tasi(1)).pack(side="left")
        ttk.Button(btn, text="Evrak Dizini (Excel)", command=lambda: self._tikla("Evrak Dizini", self._dizin_excel)
                   ).pack(side="left", padx=(14, 0))
        ttk.Button(btn, text="Listeyi Temizle", command=self._temizle).pack(side="right")
        ttk.Button(btn, text="Seçileni Kaldır", command=self._kaldir).pack(side="right", padx=(0, 8))

        gunluk_ust = ttk.Frame(sol)
        gunluk_ust.grid(row=4, column=0, columnspan=2, sticky="ew")
        ttk.Label(gunluk_ust, text="İŞLEM GÜNLÜĞÜ", font=("Segoe UI Semibold", 9),
                  foreground=YESIL).pack(side="left")
        ttk.Label(gunluk_ust, text="  yalnızca bellekte tutulur, kapanınca silinir",
                  foreground=GRI).pack(side="left")
        ttk.Button(gunluk_ust, text="Temizle", command=self._gunluk_temizle).pack(side="right")
        self.log = tk.Text(sol, height=6, bg=LACIVERT, fg="#C9D6EA", font=("Consolas", 9), relief="flat",
                           padx=10, pady=8, state="disabled", wrap="word")
        self.log.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        for t, r in (("zaman", "#6F86A8"), ("ok", "#6EE7B7"), ("hata", "#FCA5A5"), ("bilgi", "#C9D6EA"),
                     ("uyari", ALTIN)):
            self.log.tag_configure(t, foreground=r)

        # ---- sağ: renk kodlu araçlar
        sag = ttk.Frame(govde)
        sag.grid(row=0, column=1, sticky="nsew")
        self._grup(sag, "BİRLEŞTİR VE KÜÇÜLT", MAVI, [
            ("PDF'leri Birleştir", "📑", self._birlestir), ("PDF Sıkıştır", "🗜", self._sikistir),
            ("Akıllı UYAP Boyut Bölücüsü", "⚖", self._boyuta_bol)])
        self._grup(sag, "SAYFA İŞLEMLERİ", MOR, [
            ("Sayfa Böl", "✂", self._tek_tek_bol), ("Aralık Ayır / Sil", "🎯", self._sayfa_ayir),
            ("Sayfa Döndür", "🔄", self._dondur), ("Boş Sayfaları Temizle", "🧹", self._bos_temizle)])
        self._grup(sag, "EVRAK HAZIRLAMA", KIRMIZI, [
            ("'Aslı Gibidir' Kaşesi", "🛡", self._kase), ("Filigran", "💧", self._filigran)])
        self._grup(sag, "KVKK · KİŞİSEL VERİ", YESIL, [
            ("KVKK Tara (rapor)", "🔎", self._kvkk_tara), ("KVKK Akıllı Karartma", "🕶", self._karartma)])
        self._grup(sag, "DÖNÜŞTÜR VE OKU", TURKUAZ, [
            ("UDF ➔ Word (.docx)", "📄", self._udf_word), ("UDF ➔ PDF", "📕", self._udf_pdf),
            ("Word ➔ UDF (deneysel)", "🧪", self._word_udf), ("Word ➔ PDF", "📝", self._word_pdf),
            ("PDF ➔ Görsel", "🖼", self._pdf_gorsel), ("Metin Kopyala / Göster", "📋", self._metin_goster)])

    def _grup(self, ust, baslik, renk, ogeler):
        tk.Label(ust, text=baslik, font=("Segoe UI Semibold", 9), fg=renk, bg="#FAFAFA").pack(
            anchor="w", pady=(6, 2))
        cerceve = ttk.Frame(ust)
        cerceve.pack(fill="x")
        cerceve.columnconfigure((0, 1), weight=1, uniform="k")
        for i, (metin, simge, komut) in enumerate(ogeler):
            tek_son = i == len(ogeler) - 1 and len(ogeler) % 2 == 1
            k = Kart(cerceve, metin, simge, renk, lambda m=metin, c=komut: self._tikla(m, c))
            k.grid(row=i // 2, column=0 if tek_son else i % 2, columnspan=2 if tek_son else 1,
                   sticky="ew", padx=3, pady=2)
            self.kartlar.append(k)

    def _tikla(self, ad, komut):
        if self.mesgul:
            return
        self._islem_adi = ad
        komut()

    # ---- günlük / yardımcılar ---------------------------------------------
    def _log(self, mesaj, tur="bilgi"):
        self.log.configure(state="normal")
        self.log.insert("end", time.strftime("%H:%M:%S  "), "zaman")
        self.log.insert("end", mesaj + "\n", tur)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _gunluk_temizle(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _bates_durum(self):
        self.on_ek.configure(state="normal" if self.bates.get() else "disabled")

    def _ortak_ayar(self):
        return {"profil": self.profil.get(), "bates": self.bates.get(),
                "on_ek": self.on_ek.get().strip(), "meta_temizle": self.meta.get(),
                "icindekiler": self.icindekiler.get()}

    def _kapat(self):
        self.ayar.update(profil=self.profil.get(), bates=self.bates.get(),
                         on_ek=self.on_ek.get().strip() or "EK-1", meta_temizle=self.meta.get(),
                         icindekiler=self.icindekiler.get())
        config.ayarlari_kaydet(self.ayar)
        self.destroy()

    def _kayit_yolu(self, baslik, ad, kaynak=None, uzanti=".pdf", tur=("PDF", "*.pdf")):
        klasor = os.path.dirname(kaynak) if kaynak else self.ayar.get("son_klasor") or None
        yol = filedialog.asksaveasfilename(title=baslik, initialfile=ad, defaultextension=uzanti,
                                           filetypes=[tur], initialdir=klasor)
        if yol:
            self.ayar["son_klasor"] = os.path.dirname(yol)
        return yol

    def _klasor_sec(self, baslik, kaynak=None):
        return filedialog.askdirectory(title=baslik, initialdir=os.path.dirname(kaynak) if kaynak else None) or None

    def _pdf_sec(self):
        i = self._secili()
        if i is None:
            messagebox.showinfo("Dosya seçin", "Önce soldaki listeden bir dosya seçin.")
            return None
        yol = self.dosyalar[i]["yol"]
        if not yol.lower().endswith(".pdf"):
            messagebox.showinfo("PDF gerekli", "Bu işlem yalnızca PDF dosyaları içindir.")
            return None
        return yol

    # ---- liste yönetimi -----------------------------------------------------
    def _dosya_ekle(self, yol):
        yol = os.path.normpath(yol.strip("{}"))
        uzanti = os.path.splitext(yol)[1].lower()
        if uzanti not in DESTEKLENEN or not os.path.isfile(yol) or any(d["yol"] == yol for d in self.dosyalar):
            return False
        sayfa = "–"
        if uzanti == ".pdf":
            try:
                sayfa = core.sayfa_sayisi(yol)
            except IslemHatasi as e:
                sayfa = "!"
                self._log(str(e).split("\n")[0], "uyari")
        elif uzanti in core.GORSEL_UZANTILARI:
            sayfa = 1
        boyut = os.path.getsize(yol)
        ozet = core.sha256_dosya(yol) if boyut < 300 * 1048576 else None
        if ozet:
            for o in self.dosyalar:
                if o.get("hash") == ozet:
                    self._log(f"{os.path.basename(yol)}, {os.path.basename(o['yol'])} ile aynı içerikte (kopya).",
                              "uyari")
                    break
        self.dosyalar.append({"yol": yol, "tur": uzanti[1:].upper(), "sayfa": sayfa,
                              "mb": boyut / 1048576, "hash": ozet})
        return True

    def _yenile(self, sec=None):
        self.agac.delete(*self.agac.get_children())
        for d in self.dosyalar:
            self.agac.insert("", "end", values=(os.path.basename(d["yol"]), d["tur"], d["sayfa"],
                                                f'{d["mb"]:.2f} MB'))
        if sec is not None and 0 <= sec < len(self.dosyalar):
            self.agac.selection_set(self.agac.get_children()[sec])
        self.durum.config(text=f"{len(self.dosyalar)} dosya  ·  {sum(d['mb'] for d in self.dosyalar):.2f} MB")

    def _secili(self):
        s = self.agac.selection()
        return self.agac.index(s[0]) if s else None

    def _eklendi(self, adet):
        self._yenile()
        if adet:
            self._log(f"{adet} dosya listeye eklendi.")

    def _birak(self, olay):
        adet = 0
        for yol in self.tk.splitlist(olay.data):
            if os.path.isdir(yol):
                for ad in sorted(os.listdir(yol)):
                    adet += self._dosya_ekle(os.path.join(yol, ad))
            else:
                adet += self._dosya_ekle(yol)
        self._eklendi(adet)

    def _ekle_dialog(self):
        adet = 0
        for yol in filedialog.askopenfilenames(
                title="Dosya seçin", initialdir=self.ayar.get("son_klasor") or None,
                filetypes=[("Desteklenen dosyalar", "*.pdf *.docx *.udf *.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")]):
            adet += self._dosya_ekle(yol)
        self._eklendi(adet)

    def _kaldir(self):
        i = self._secili()
        if i is not None:
            del self.dosyalar[i]
            self._yenile(min(i, len(self.dosyalar) - 1))

    def _temizle(self):
        self.dosyalar.clear()
        self._yenile()
        self._log("Dosya listesi temizlendi.")

    def _tasi(self, yon):
        i = self._secili()
        if i is None:
            return
        j = i + yon
        if 0 <= j < len(self.dosyalar):
            self.dosyalar[i], self.dosyalar[j] = self.dosyalar[j], self.dosyalar[i]
            self._yenile(j)

    # ---- arka plan çalıştırıcı ---------------------------------------------
    def _calistir(self, is_fn, bitis_fn):
        if self.mesgul:
            return
        self.mesgul = True
        self._t0 = time.time()
        for k in self.kartlar:
            k.durum(False)
        self.ilerleme["value"] = 0
        self._log(f"▶ {self._islem_adi} başladı...")

        def hedef():
            try:
                sonuc = is_fn(lambda o, m="": self.kuyruk.put(("ilerle", o, m)))
                self.kuyruk.put(("bitti", bitis_fn, sonuc))
            except IslemHatasi as e:
                self.kuyruk.put(("hata", str(e), None))
            except Exception as e:
                self.kuyruk.put(("hata", f"Beklenmeyen hata: {e}", traceback.format_exc()))

        threading.Thread(target=hedef, daemon=True).start()

    def _kuyruk_dinle(self):
        try:
            while True:
                tip, a, b = self.kuyruk.get_nowait()
                if tip == "ilerle":
                    self.ilerleme["value"] = a * 100
                    if b:
                        self.durum.config(text=b)
                    continue
                self.mesgul = False
                for k in self.kartlar:
                    k.durum(True)
                sure = time.time() - self._t0
                if tip == "bitti":
                    self.ilerleme["value"] = 100
                    self._log(f"✔ {self._islem_adi} tamamlandı ({sure:.1f} sn)", "ok")
                    a(b)
                else:
                    self.ilerleme["value"] = 0
                    self.durum.config(text="İşlem tamamlanamadı.")
                    self._log(f"✖ {self._islem_adi}: {a.splitlines()[0]}", "hata")
                    messagebox.showerror("Hata", a)
        except queue.Empty:
            pass
        self.after(80, self._kuyruk_dinle)

    def _bitti(self, mesaj, hedef=None, eski_mb=None, uyari=None):
        satirlar = [mesaj]
        if hedef and os.path.isfile(hedef):
            yeni = os.path.getsize(hedef) / 1048576
            if eski_mb:
                satirlar.append(f"Boyut: {eski_mb:.2f} MB → {yeni:.2f} MB")
                self._log(f"{os.path.basename(hedef)}: {eski_mb:.2f} MB → {yeni:.2f} MB")
            else:
                self._log(f"Kaydedildi: {os.path.basename(hedef)}")
            satirlar.append(os.path.basename(hedef))
        if uyari:
            satirlar.append("\n" + uyari)
            self._log(uyari.split("\n")[0], "uyari")
        self.durum.config(text=mesaj)
        messagebox.showinfo(config.APP_AD, "\n".join(satirlar))

    # ====================== İŞLEMLER ========================================
    def _birlestir(self):
        girdiler = [d["yol"] for d in self.dosyalar
                    if d["yol"].lower().endswith((".pdf", ".udf") + core.GORSEL_UZANTILARI)]
        atlanan = len(self.dosyalar) - len(girdiler)
        if atlanan:
            self._log(f"{atlanan} Word dosyası birleştirmeye dahil edilmedi (önce Word ➔ PDF yapın).", "uyari")
        if any(g.lower().endswith(".udf") for g in girdiler):
            self._log("UDF belgeleri okunabilir PDF kopyası olarak eklenir; imzalı asıl değildir.", "uyari")
        if not girdiler:
            messagebox.showinfo("Dosya yok", "Birleştirmek için PDF veya görsel ekleyin.")
            return
        hedef = self._kayit_yolu("Birleştirilmiş PDF'i kaydet", "birlestirilmis_evrak.pdf", girdiler[0])
        if not hedef:
            return
        ayar = self._ortak_ayar()
        eski = sum(os.path.getsize(y) for y in girdiler) / 1048576
        self._calistir(lambda il: core.birlestir(girdiler, ayar, hedef, il),
                       lambda h: self._bitti(f"{len(girdiler)} dosya birleştirildi.", h, eski))

    def _sikistir(self):
        yol = self._pdf_sec()
        if not yol:
            return
        hedef = self._kayit_yolu("Sıkıştırılmış PDF'i kaydet", "kucuk_" + os.path.basename(yol), yol)
        if not hedef:
            return
        ayar = self._ortak_ayar()
        eski = os.path.getsize(yol) / 1048576
        self._calistir(lambda il: core.sikistir(yol, ayar, hedef, il),
                       lambda h: self._bitti("Sıkıştırma tamamlandı.", h, eski))

    def _boyuta_bol(self):
        yol = self._pdf_sec()
        if not yol:
            return
        mb = os.path.getsize(yol) / 1048576
        f = Form(self, "Akıllı UYAP boyut bölücüsü", [
            {"ad": "mb", "etiket": "Her parçanın en büyük boyutu (MB)", "tur": "entry",
             "varsayilan": self.ayar["hedef_mb"]}], "Böl",
                 f"Dosya boyutu: {mb:.2f} MB. UYAP'ın güncel ek sınırını kontrol edip değeri buna göre "
                 "girin; sınırın biraz altı önerilir.", MAVI)
        if not f.sonuc:
            return
        try:
            limit = float(f.sonuc["mb"].replace(",", "."))
            assert limit > 0
        except Exception:
            messagebox.showerror("Hata", "Geçerli bir MB değeri girin. Örnek: 9.5")
            return
        self.ayar["hedef_mb"] = f.sonuc["mb"]
        klasor = self._klasor_sec("Parçaların kaydedileceği klasör", yol)
        if not klasor:
            return
        meta = self.meta.get()

        def bitir(sonuc):
            ozet = "\n".join(f"• {ad}: {m:.2f} MB" + ("  (sınırı aşıyor)" if asti else "")
                             for ad, m, asti in sonuc)
            uyari = ("Sınırı aşan parçada tek sayfa bile sınırdan büyük; önce PDF Sıkıştır'ı deneyin."
                     if any(a for _, _, a in sonuc) else None)
            self._log(f"{len(sonuc)} parça oluşturuldu.")
            self.durum.config(text=f"{len(sonuc)} parçaya bölündü.")
            messagebox.showinfo(config.APP_AD, f"{len(sonuc)} parça oluşturuldu:\n\n{ozet}" +
                                (f"\n\n{uyari}" if uyari else ""))

        self._calistir(lambda il: core.boyuta_gore_bol(yol, limit, klasor, meta, il), bitir)

    def _sayfa_ayir(self):
        yol = self._pdf_sec()
        if not yol:
            return
        n = core.sayfa_sayisi(yol)
        f = Form(self, "Aralık ayır / sil", [
            {"ad": "mod", "etiket": "İşlem", "tur": "radio", "varsayilan": "ayir",
             "secenekler": [("ayir", "Bu sayfaları al"), ("sil", "Bu sayfaları sil")]},
            {"ad": "aralik", "etiket": f"Sayfalar (toplam {n})", "tur": "entry", "varsayilan": ""}],
                 "Uygula", "Örnek: 1-3, 5. 'Al' seçeneğinde yazdığınız sıra korunur (ör. 4, 1 → 4. sayfa önce gelir).",
                 MOR)
        if not f.sonuc:
            return
        sil = f.sonuc["mod"] == "sil"
        hedef = self._kayit_yolu("Kaydet", ("sayfasiz_" if sil else "ayrilan_") + os.path.basename(yol), yol)
        if not hedef:
            return
        meta, aralik = self.meta.get(), f.sonuc["aralik"]
        self._calistir(lambda il: core.sayfa_sec(yol, aralik, hedef, sil, meta),
                       lambda s: self._bitti(f"Çıktıda {s} sayfa var.", hedef))

    def _tek_tek_bol(self):
        yol = self._pdf_sec()
        klasor = yol and self._klasor_sec("Sayfaların kaydedileceği klasör", yol)
        if not klasor:
            return
        meta = self.meta.get()

        def bitir(n):
            self._log(f"{n} sayfa ayrı dosyalar olarak kaydedildi.")
            self.durum.config(text=f"{n} sayfa ayrıldı.")
            messagebox.showinfo(config.APP_AD, f"{n} sayfa ayrı dosyalar olarak kaydedildi.")

        self._calistir(lambda il: core.sayfa_sayfa_bol(yol, klasor, meta, il), bitir)

    def _dondur(self):
        yol = self._pdf_sec()
        if not yol:
            return
        n = core.sayfa_sayisi(yol)
        f = Form(self, "Sayfa döndür", [
            {"ad": "derece", "etiket": "Yön", "tur": "radio", "varsayilan": "90",
             "secenekler": [("90", "90° sağa"), ("270", "90° sola"), ("180", "180°")]},
            {"ad": "aralik", "etiket": f"Sayfalar (boş bırakırsanız tümü, toplam {n})", "tur": "entry",
             "varsayilan": ""}], "Döndür", None, MOR)
        if not f.sonuc:
            return
        hedef = self._kayit_yolu("Kaydet", "dondurulmus_" + os.path.basename(yol), yol)
        if not hedef:
            return
        meta, aralik, derece = self.meta.get(), f.sonuc["aralik"], int(f.sonuc["derece"])
        self._calistir(lambda il: core.dondur(yol, aralik, derece, hedef, meta),
                       lambda s: self._bitti(f"{s} sayfa döndürüldü.", hedef))

    def _bos_temizle(self):
        yol = self._pdf_sec()
        if not yol:
            return
        meta = self.meta.get()

        def bulundu(sonuc):
            bos, toplam = sonuc
            if not bos:
                self._log("Boş sayfa bulunamadı.", "ok")
                self.durum.config(text="Boş sayfa bulunamadı.")
                messagebox.showinfo(config.APP_AD, "Boş sayfa bulunamadı.")
                return
            if len(bos) == toplam:
                messagebox.showwarning(config.APP_AD, "Tüm sayfalar boş görünüyor; silme yapılmadı.")
                return
            sf = ", ".join(map(str, bos[:20])) + ("…" if len(bos) > 20 else "")
            self._log(f"{len(bos)} boş sayfa bulundu: {sf}", "uyari")
            if not messagebox.askyesno("Boş sayfalar bulundu",
                                       f"{len(bos)} boş sayfa bulundu (sayfa {sf}).\n\nBunlar silinsin mi?\n"
                                       "(Orijinal dosya değişmez, yeni bir dosya kaydedilir.)"):
                return
            hedef = self._kayit_yolu("Kaydet", "temiz_" + os.path.basename(yol), yol)
            if not hedef:
                return
            self._islem_adi = "Boş sayfaları sil"
            self._calistir(lambda il: core.sayfalari_sil(yol, bos, hedef, meta),
                           lambda n: self._bitti(f"{n} boş sayfa silindi.", hedef))

        self._calistir(lambda il: core.bos_sayfalari_bul(yol, il), bulundu)

    def _kase(self):
        yol = self._pdf_sec()
        if not yol:
            return
        n = core.sayfa_sayisi(yol)
        f = Form(self, "'Aslı Gibidir' kaşesi", [
            {"ad": "baslik", "etiket": "Başlık", "tur": "entry", "varsayilan": self.ayar["kase_baslik"]},
            {"ad": "ad", "etiket": "Ad soyad / unvan", "tur": "entry", "varsayilan": self.ayar["kase_ad"]},
            {"ad": "sicil", "etiket": "Sicil / baro no (isteğe bağlı)", "tur": "entry",
             "varsayilan": self.ayar["kase_sicil"]},
            {"ad": "ek", "etiket": "Tarih / ek bilgi", "tur": "entry",
             "varsayilan": "Tarih: " + datetime.date.today().strftime("%d.%m.%Y")},
            {"ad": "renk", "etiket": "Kaşe rengi", "tur": "radio", "varsayilan": self.ayar["kase_renk"],
             "secenekler": [("kirmizi", "Kırmızı"), ("siyah", "Siyah"), ("lacivert", "Lacivert"), ("mavi", "Mavi")]},
            {"ad": "ad_renk", "etiket": "Ad soyad satırının rengi", "tur": "radio",
             "varsayilan": self.ayar["kase_ad_renk"],
             "secenekler": [("ayni", "Kaşe ile aynı"), ("kirmizi", "Kırmızı"), ("siyah", "Siyah"),
                            ("lacivert", "Lacivert"), ("mavi", "Mavi")]},
            {"ad": "konum", "etiket": "Konum", "tur": "radio", "varsayilan": self.ayar["kase_konum"],
             "secenekler": [("sag_alt", "Sağ alt"), ("sol_alt", "Sol alt"), ("alt_orta", "Alt orta"),
                            ("sag_ust", "Sağ üst")]},
            {"ad": "aralik", "etiket": f"Sayfalar (boş bırakırsanız tümü, toplam {n})", "tur": "entry",
             "varsayilan": ""}], "Kaşeyi bas", None, KIRMIZI)
        if not f.sonuc:
            return
        r = f.sonuc
        self.ayar.update(kase_baslik=r["baslik"], kase_ad=r["ad"], kase_sicil=r["sicil"], kase_renk=r["renk"],
                         kase_ad_renk=r["ad_renk"], kase_konum=r["konum"])
        hedef = self._kayit_yolu("Kaydet", "kaseli_" + os.path.basename(yol), yol)
        if not hedef:
            return
        meta = self.meta.get()
        sicil = f"Sicil No: {r['sicil'].strip()}" if r["sicil"].strip() else ""
        satirlar = [(r["baslik"], None), (r["ad"], None if r["ad_renk"] == "ayni" else r["ad_renk"]),
                    (sicil, None), (r["ek"], None)]
        self._calistir(
            lambda il: core.kase_bas(yol, hedef, satirlar, r["renk"], r["konum"],
                                     r["aralik"].strip() or None, meta),
            lambda s: self._bitti(f"Kaşe {s} sayfaya basıldı.", hedef))

    def _filigran(self):
        yol = self._pdf_sec()
        if not yol:
            return
        f = Form(self, "Filigran", [
            {"ad": "metin", "etiket": "Filigran metni", "tur": "entry", "varsayilan": self.ayar["filigran_metin"]},
            {"ad": "renk", "etiket": "Renk", "tur": "radio", "varsayilan": self.ayar["filigran_renk"],
             "secenekler": [("gri", "Gri"), ("kirmizi", "Kırmızı"), ("siyah", "Siyah"), ("lacivert", "Lacivert"),
                            ("mavi", "Mavi")]}],
                 "Uygula", "Metin tüm sayfalara çapraz ve soluk olarak eklenir.", KIRMIZI)
        if not f.sonuc:
            return
        self.ayar.update(filigran_metin=f.sonuc["metin"], filigran_renk=f.sonuc["renk"])
        hedef = self._kayit_yolu("Kaydet", "filigranli_" + os.path.basename(yol), yol)
        if not hedef:
            return
        meta, metin, renk = self.meta.get(), f.sonuc["metin"], f.sonuc["renk"]
        self._calistir(lambda il: core.filigran_bas(yol, hedef, metin, 0.25, meta, il, renk),
                       lambda s: self._bitti(f"Filigran {s} sayfaya eklendi.", hedef))

    # ---- KVKK --------------------------------------------------------------
    def _kvkk_form(self, baslik, tamam, aciklama):
        f = Form(self, baslik, [
            {"ad": "tc", "etiket": "T.C. kimlik numaraları (11 hane)", "tur": "check", "varsayilan": True},
            {"ad": "iban", "etiket": "IBAN numaraları", "tur": "check", "varsayilan": True},
            {"ad": "tel", "etiket": "Telefon numaraları", "tur": "check", "varsayilan": True},
            {"ad": "eposta", "etiket": "E-posta adresleri", "tur": "check", "varsayilan": True},
            {"ad": "tcd", "etiket": "T.C. için yalnızca geçerli (algoritmaya uyan) numaralar", "tur": "check",
             "varsayilan": True},
            {"ad": "ozel", "etiket": "Özel ad / kelimeler (virgülle ayırın)", "tur": "entry", "varsayilan": ""}],
                 tamam, aciklama, YESIL)
        if not f.sonuc:
            return None
        r = f.sonuc
        desenler = [k for k in ("tc", "iban", "tel", "eposta") if r[k]]
        ozel = [k.strip() for k in r["ozel"].split(",") if k.strip()]
        if not desenler and not ozel:
            messagebox.showinfo("Seçim yok", "En az bir veri türü veya kelime seçin.")
            return None
        return desenler, ozel, r["tcd"]

    def _kvkk_tara(self):
        yol = self._pdf_sec()
        if not yol:
            return
        secim = self._kvkk_form("KVKK tarama", "Tara",
                                "Dosya değiştirilmez. Hangi kişisel verilerin nerede geçtiğini raporlar.")
        if not secim:
            return

        def bitir(rapor):
            satirlar = []
            for tur, adet in rapor["sayim"].items():
                sf = rapor["sayfalar"][tur]
                sayfa = ", ".join(map(str, sf[:12])) + ("…" if len(sf) > 12 else "")
                satirlar.append(f"• {core.ETIKETLER[tur]}: {adet} adet  (sayfa {sayfa})")
                self._log(f"{core.ETIKETLER[tur]}: {adet} adet", "uyari")
            if not satirlar:
                satirlar = ["Seçilen türlerde eşleşme bulunmadı."]
                self._log("Eşleşme bulunmadı.", "ok")
            if rapor["metinsiz"]:
                m = rapor["metinsiz"]
                satirlar.append(f"\nDİKKAT: {len(m)} sayfa taranmış görüntü (sayfa {', '.join(map(str, m[:12]))}"
                                f"{'…' if len(m) > 12 else ''}). Bu sayfalar taranamadı.")
                self._log(f"{len(m)} sayfa taranmış görüntü, taranamadı.", "uyari")
            self.durum.config(text="KVKK taraması tamamlandı.")
            messagebox.showinfo("KVKK tarama raporu", "\n".join(satirlar))

        self._calistir(lambda il: core.kvkk_tara(yol, secim[0], secim[1], il, secim[2]), bitir)

    def _karartma(self):
        yol = self._pdf_sec()
        if not yol:
            return
        secim = self._kvkk_form(
            "KVKK akıllı karartma", "Karart",
            "Karartma kalıcıdır; metin dosyadan silinir ve çıktı yeniden taranarak doğrulanır. "
            "Yalnızca metin katmanı olan sayfalarda çalışır.")
        if not secim:
            return
        desenler, ozel, tcd = secim
        hedef = self._kayit_yolu("Kaydet", "karartilmis_" + os.path.basename(yol), yol)
        if not hedef:
            return

        def bitir(sonuc):
            adet, metinsiz, kalan = sonuc
            uyarilar = []
            if kalan:
                uyarilar.append(f"DOĞRULAMA UYARISI: çıktıda hâlâ {kalan} eşleşme görünüyor "
                                "(satır sonuna bölünmüş veri olabilir). Elle kontrol edin.")
            else:
                self._log("Doğrulama: çıktıda eşleşme kalmadı ✓", "ok")
            if metinsiz:
                sf = ", ".join(map(str, metinsiz[:12])) + ("…" if len(metinsiz) > 12 else "")
                uyarilar.append(f"DİKKAT: {len(metinsiz)} sayfa taranmış görüntü (sayfa {sf}); "
                                "bu sayfalardaki yazılar karartılamadı.")
            self._bitti(f"{adet} alan kalıcı olarak karartıldı." +
                        ("  Doğrulama: temiz ✓" if not kalan else ""), hedef,
                        uyari="\n".join(uyarilar) or None)

        self._calistir(lambda il: core.karart(yol, hedef, desenler, ozel, il, tcd), bitir)

    # ---- dönüştür / oku ----------------------------------------------------
    def _udf_word(self):
        i = self._secili()
        if i is None or not self.dosyalar[i]["yol"].lower().endswith(".udf"):
            messagebox.showinfo("UDF seçin", "Listeden bir UDF dosyası seçin.")
            return
        yol = self.dosyalar[i]["yol"]
        hedef = self._kayit_yolu("Word olarak kaydet", os.path.splitext(os.path.basename(yol))[0] + ".docx",
                                 yol, ".docx", ("Word belgesi", "*.docx"))
        if not hedef:
            return
        self._calistir(lambda il: udf.udf_to_docx(yol, hedef),
                       lambda h: self._bitti("UDF, Word'e aktarıldı.", h,
                                             uyari="Dönüşümden sonra belgeyi Word'de gözden geçirin."))

    def _word_pdf(self):
        i = self._secili()
        if i is None or not self.dosyalar[i]["yol"].lower().endswith(".docx"):
            messagebox.showinfo("Word seçin", "Listeden bir Word (.docx) dosyası seçin.")
            return
        yol = self.dosyalar[i]["yol"]
        hedef = self._kayit_yolu("PDF olarak kaydet", os.path.splitext(os.path.basename(yol))[0] + ".pdf", yol)
        if not hedef:
            return

        def is_(il):
            il(0.2, "Microsoft Word ile dönüştürülüyor...")
            return core.docx_to_pdf(yol, hedef)

        self._calistir(is_, lambda h: self._bitti("Word, PDF'e dönüştürüldü.", h))

    def _udf_pdf(self):
        i = self._secili()
        if i is None or not self.dosyalar[i]["yol"].lower().endswith(".udf"):
            messagebox.showinfo("UDF seçin", "Listeden bir UDF dosyası seçin.")
            return
        yol = self.dosyalar[i]["yol"]
        hedef = self._kayit_yolu("PDF olarak kaydet", os.path.splitext(os.path.basename(yol))[0] + ".pdf", yol)
        if not hedef:
            return

        def is_(il):
            il(0.3, "UDF PDF'e çiziliyor...")
            return udf.udf_to_pdf(yol, hedef)

        self._calistir(is_, lambda h: self._bitti(
            "UDF, PDF'e dönüştürüldü.", h, uyari="Bu PDF okunabilir bir kopyadır; UDF'deki elektronik imzayı "
                                                 "taşımaz. İmzalı asıl gerekiyorsa UDF dosyasını kullanın."))

    def _word_udf(self):
        i = self._secili()
        if i is None or not self.dosyalar[i]["yol"].lower().endswith(".docx"):
            messagebox.showinfo("Word seçin", "Listeden bir Word (.docx) dosyası seçin.")
            return
        yol = self.dosyalar[i]["yol"]
        hedef = self._kayit_yolu("UDF olarak kaydet", os.path.splitext(os.path.basename(yol))[0] + ".udf", yol,
                                 ".udf", ("UDF belgesi", "*.udf"))
        if not hedef:
            return

        def bitir(sonuc):
            h, uyarilar = sonuc
            self._bitti("Word, UDF'ye dönüştürüldü (deneysel).", h,
                        uyari="\n".join(uyarilar + ["Kullanmadan önce UYAP Doküman Editörü'nde açıp kontrol edin."]))

        self._calistir(lambda il: udf.docx_to_udf(yol, hedef), bitir)

    def _dizin_excel(self):
        if not self.dosyalar:
            messagebox.showinfo("Dosya yok", "Dizin için önce dosya ekleyin.")
            return
        hedef = self._kayit_yolu("Evrak dizinini kaydet", "evrak_dizini.xlsx", self.dosyalar[0]["yol"], ".xlsx",
                                 ("Excel çalışma kitabı", "*.xlsx"))
        if not hedef:
            return
        kayitlar = [dict(d) for d in self.dosyalar]
        self._calistir(lambda il: core.dizin_xlsx(kayitlar, hedef, il),
                       lambda n: self._bitti(f"{n} dosyalık evrak dizini oluşturuldu.", hedef))

    def _icerikte_ara(self):
        sorgu = self.ara_var.get().strip()
        dosyalar = [d["yol"] for d in self.dosyalar if d["yol"].lower().endswith((".pdf", ".udf", ".docx"))]
        if not dosyalar:
            messagebox.showinfo("Dosya yok", "Aramak için listeye PDF, UDF veya Word ekleyin.")
            return
        if len(sorgu) < 2:
            messagebox.showinfo("Arama", "Aranacak ifadeyi (en az 2 karakter) yazın.")
            return

        def bitir(sonuc):
            bulunan, taranmis = sonuc
            if taranmis:
                self._log(f"{len(taranmis)} dosyada taranmış (görüntü) sayfa var, bunların içinde aranamadı.",
                          "uyari")
            self._log(f"'{sorgu}': {len(bulunan)} eşleşme.", "ok" if bulunan else "uyari")
            if not bulunan:
                messagebox.showinfo("Arama", "Eşleşme bulunamadı." +
                                    ("\n\nTaranmış sayfaların içinde arama yapılamaz." if taranmis else ""))
                return
            self._arama_sonuclari(sorgu, bulunan)

        self._calistir(lambda il: core.icerikte_ara(dosyalar, sorgu, il), bitir)

    def _arama_sonuclari(self, sorgu, bulunan):
        p = tk.Toplevel(self)
        p.title(f"Arama sonuçları — {sorgu}")
        p.geometry("860x460")
        p.transient(self)
        tk.Frame(p, bg=MAVI, height=5).pack(fill="x")
        kutu = ttk.Frame(p, padding=12)
        kutu.pack(fill="both", expand=True)
        ttk.Label(kutu, text=f"{len(bulunan)} eşleşme (Türkçe karakter ve büyük/küçük harf fark etmez)",
                  foreground=GRI).pack(anchor="w", pady=(0, 6))
        agac = ttk.Treeview(kutu, columns=("dosya", "yer", "alinti"), show="headings")
        for k, b, g in (("dosya", "Dosya", 200), ("yer", "Yer", 80), ("alinti", "Geçtiği yer", 520)):
            agac.heading(k, text=b)
            agac.column(k, width=g, anchor="w", stretch=(k == "alinti"))
        for r in bulunan:
            agac.insert("", "end", values=(r["dosya"], r["yer"], r["alinti"]))
        kay = ttk.Scrollbar(kutu, command=agac.yview)
        agac.configure(yscrollcommand=kay.set)
        kay.pack(side="right", fill="y")
        agac.pack(fill="both", expand=True)

    def _udf_goster(self, yol):
        """UDF'yi biçimiyle (kalın, italik, hizalama, punto) gösterir."""
        bloklar = udf.udf_oku(yol)
        p = tk.Toplevel(self)
        p.title(os.path.basename(yol))
        p.geometry("760x640")
        p.transient(self)
        tk.Frame(p, bg=TURKUAZ, height=5).pack(fill="x")
        kutu = ttk.Frame(p, padding=12)
        kutu.pack(fill="both", expand=True)
        alt = ttk.Frame(kutu)
        alt.pack(side="bottom", fill="x", pady=(10, 0))
        txt = tk.Text(kutu, wrap="word", font=("Times New Roman", 12), relief="flat", padx=24, pady=16,
                      bg="white")
        kay = ttk.Scrollbar(kutu, command=txt.yview)
        txt.configure(yscrollcommand=kay.set)
        kay.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        for ad, j in (("hz1", "center"), ("hz2", "right"), ("hz3", "left")):
            txt.tag_configure(ad, justify=j)
        olusan = set()

        def etiket(x):
            ad = f"f{int(bool(x.get('b')))}{int(bool(x.get('i')))}{int(bool(x.get('u')))}_{x.get('boyut') or 12}"
            if ad not in olusan:
                stil = " ".join(k for k, v in (("bold", x.get("b")), ("italic", x.get("i"))) if v)
                txt.tag_configure(ad, font=("Times New Roman", int(x.get("boyut") or 12), *( (stil,) if stil else ())),
                                  underline=bool(x.get("u")))
                olusan.add(ad)
            return ad

        def yaz(pr):
            bas = txt.index("end-1c")
            for x in pr["parcalar"]:
                txt.insert("end", x["m"] if not x.get("resim") else "[görsel]", etiket(x))
            txt.insert("end", "\n")
            if pr["hiza"] in ("1", "2"):
                txt.tag_add("hz" + pr["hiza"], bas, txt.index("end-1c"))

        for b in bloklar:
            if b["tur"] == "p":
                yaz(b)
            elif b["tur"] == "tablo":
                for satir in b["satirlar"]:
                    txt.insert("end", " | ".join(" ".join(udf.paragraf_metni(pp) for pp in h) for h in satir) + "\n")
            elif b["tur"] == "sayfa_sonu":
                txt.insert("end", "\n" + "─" * 40 + "\n\n")
        txt.configure(state="disabled")

        def kopyala():
            p.clipboard_clear()
            p.clipboard_append(udf.udf_metni(yol))
            kop.config(text="Metin kopyalandı ✓")

        kop = ttk.Button(alt, text="Düz metni kopyala", style="Accent.TButton", command=kopyala)
        kop.pack(side="right")

    def _pdf_gorsel(self):
        yol = self._pdf_sec()
        if not yol:
            return
        f = Form(self, "PDF ➔ Görsel", [
            {"ad": "bicim", "etiket": "Biçim", "tur": "radio", "varsayilan": "png",
             "secenekler": [("png", "PNG"), ("jpg", "JPG")]},
            {"ad": "dpi", "etiket": "Çözünürlük (DPI)", "tur": "entry", "varsayilan": "150"}],
                 "Dönüştür", None, TURKUAZ)
        if not f.sonuc:
            return
        try:
            dpi = int(f.sonuc["dpi"])
            assert 36 <= dpi <= 600
        except Exception:
            messagebox.showerror("Hata", "DPI 36 ile 600 arasında bir sayı olmalı.")
            return
        klasor = self._klasor_sec("Görsellerin kaydedileceği klasör", yol)
        if not klasor:
            return
        bicim = f.sonuc["bicim"]

        def bitir(n):
            self._log(f"{n} sayfa görsel olarak kaydedildi.")
            self.durum.config(text=f"{n} görsel kaydedildi.")
            messagebox.showinfo(config.APP_AD, f"{n} sayfa görsel olarak kaydedildi.")

        self._calistir(lambda il: core.gorsele_cevir(yol, klasor, bicim, dpi, il), bitir)

    def _metin_goster(self):
        i = self._secili()
        if i is None:
            messagebox.showinfo("Dosya seçin", "Listeden bir PDF, Word veya UDF seçin.")
            return
        yol = self.dosyalar[i]["yol"]
        if yol.lower().endswith(".udf"):
            try:
                self._udf_goster(yol)
            except IslemHatasi as e:
                messagebox.showerror("Hata", str(e))
            return
        try:
            if yol.lower().endswith(".pdf"):
                metin = core.metin_cikar(yol)
            elif yol.lower().endswith(".udf"):
                metin = udf.udf_metni(yol)
            elif yol.lower().endswith(".docx"):
                metin = udf.docx_metni(yol)
            else:
                messagebox.showinfo("Desteklenmiyor", "Metin okuma PDF, Word ve UDF için geçerlidir.")
                return
        except IslemHatasi as e:
            messagebox.showerror("Hata", str(e))
            return
        if not metin.strip():
            metin = "Kopyalanabilir metin bulunamadı. Dosya taranmış görüntüden oluşuyor olabilir."
        p = tk.Toplevel(self)
        p.title(os.path.basename(yol))
        p.geometry("700x520")
        p.transient(self)
        tk.Frame(p, bg=TURKUAZ, height=5).pack(fill="x")
        kutu = ttk.Frame(p, padding=12)
        kutu.pack(fill="both", expand=True)
        alt = ttk.Frame(kutu)
        alt.pack(side="bottom", fill="x", pady=(10, 0))
        txt = tk.Text(kutu, wrap="word", font=("Consolas", 10), relief="flat", padx=8, pady=8)
        txt.pack(side="left", fill="both", expand=True)
        kay = ttk.Scrollbar(kutu, command=txt.yview)
        kay.pack(side="right", fill="y")
        txt.configure(yscrollcommand=kay.set)
        txt.insert("1.0", metin)

        def kopyala():
            p.clipboard_clear()
            p.clipboard_append(txt.get("1.0", "end-1c"))
            kop.config(text="Kopyalandı ✓")

        kop = ttk.Button(alt, text="Tümünü kopyala", style="Accent.TButton", command=kopyala)
        kop.pack(side="right")

    # ====================== KILAVUZ =========================================
    def _kilavuz(self):
        p = tk.Toplevel(self)
        p.title(f"{config.APP_AD} — Kılavuz")
        p.geometry("740x620")
        p.transient(self)
        nb = ttk.Notebook(p)
        nb.pack(fill="both", expand=True, padx=12, pady=12)
        for ad, metin in (("Kullanım", KILAVUZ_METNI), ("KVKK ve Gizlilik", GIZLILIK_METNI)):
            cerceve = ttk.Frame(nb, padding=6)
            nb.add(cerceve, text=ad)
            txt = tk.Text(cerceve, wrap="word", font=("Segoe UI", 10), relief="flat", padx=10, pady=8,
                          spacing3=3)
            kay = ttk.Scrollbar(cerceve, command=txt.yview)
            txt.configure(yscrollcommand=kay.set)
            kay.pack(side="right", fill="y")
            txt.pack(fill="both", expand=True)
            txt.tag_configure("b", font=("Segoe UI Semibold", 11), spacing1=10, foreground=MAVI)
            for satir in metin.strip("\n").split("\n"):
                if satir.startswith("# "):
                    txt.insert("end", satir[2:] + "\n", "b")
                else:
                    txt.insert("end", satir + "\n")
            txt.configure(state="disabled")
        self._hakkinda_sekmesi(nb)

    def _hakkinda_sekmesi(self, nb):
        cerceve = ttk.Frame(nb, padding=24)
        nb.add(cerceve, text="Hakkında")
        ust = ttk.Frame(cerceve)
        ust.pack(anchor="w")
        try:
            img = Image.open(kaynak_yolu("logo.png")).resize((64, 64), Image.LANCZOS)
            self._logo_hakkinda = ImageTk.PhotoImage(img)
            ttk.Label(ust, image=self._logo_hakkinda).pack(side="left", padx=(0, 14))
        except Exception:
            pass
        isim = ttk.Frame(ust)
        isim.pack(side="left")
        ttk.Label(isim, text=config.APP_AD, font=("Segoe UI Semibold", 15)).pack(anchor="w")
        ttk.Label(isim, text=f"Sürüm {config.SURUM}  ·  Geliştirici: {config.YAPIMCI}",
                  foreground=GRI).pack(anchor="w")
        metin = ("Bağımsız yardımcı yazılımdır; UYAP veya T.C. Adalet Bakanlığı ile bağlantılı değildir.\n\n"
                 "Belgeler yerel bilgisayarda işlenir. Uygulama telemetri içermez.\n"
                 "Elektronik imzalı UDF'nin PDF/Word kopyası imzalı asıl belge yerine geçmez.\n\n"
                 "Çıktıları UYAP'a yüklemeden önce kontrol etmek kullanıcının sorumluluğundadır.")
        ttk.Label(cerceve, text=metin, justify="left", wraplength=620).pack(anchor="w", pady=(22, 18))
        if config.github_tanimli():
            ttk.Button(cerceve, text="GitHub Profili", style="Accent.TButton",
                       command=lambda: webbrowser.open(config.GITHUB_URL)).pack(anchor="w")
            ttk.Label(cerceve, text=config.GITHUB_URL.split("//")[-1], foreground=GRI).pack(anchor="w", pady=(6, 0))


KILAVUZ_METNI = """
# Başlarken
Dosyaları soldaki listeye sürükleyin (PDF, Word, UDF, JPG, PNG, WEBP, BMP; klasör de bırakabilirsiniz) veya "Dosya Ekle"yi kullanın. Sıralamayı ▲ ▼ ile değiştirin. Tek dosya işlemleri için önce listeden dosyayı seçin. Tüm çıktılar yeni bir dosya olarak kaydedilir; orijinal dosyanıza dokunulmaz. Kayıt penceresi, kaynak dosyanın klasöründe açılır.

# Üstteki ayarlar
Kalite: "Akıllı" mod metni seçilebilir bırakır, yalnızca içindeki görselleri küçültür. "Dengeli" ve "Maksimum" modlar her sayfayı görüntüye çevirir; taranmış evrakta daha küçük dosya verir ama metin aranamaz hale gelir.
Sayfa no / ek etiketi: Her sayfanın altına "EK-1 | Sayfa 3 / 15" yazar.
Üst verileri temizle: Çıktıdan yazar, oluşturan program gibi bilgileri siler. Varsayılan olarak açıktır.

# Birleştir ve küçült
PDF'leri Birleştir: Listedeki PDF, UDF ve görselleri sırayla tek PDF yapar. Görseller A4'e ortalanır, telefon fotoğraflarının yönü otomatik düzeltilir; çok sayfalı TIFF taramalar sayfa sayfa eklenir. Her dosya için PDF içinde yer imi oluşturulur. Üstteki "İçindekiler" kutusu işaretliyse başa, her dosyanın başlangıç sayfasına tıklanabilir bağlantılar veren bir içindekiler sayfası eklenir. UDF belgeleri okunabilir PDF kopyası olarak katılır; imzalı asıl değildir. Word dosyalarını önce Word ➔ PDF ile çevirin.
PDF Sıkıştır: Seçili PDF'i seçilen kalite moduyla küçültür.
Akıllı UYAP Boyut Bölücüsü: Dosyayı, her parça belirttiğiniz MB sınırını aşmayacak şekilde sırayla böler. UYAP'ın güncel ek boyut sınırını kontrol edip değeri buna göre girin.

# Sayfa işlemleri
Sayfa Böl: Her sayfayı ayrı PDF olarak kaydeder.
Aralık Ayır / Sil: "1-3, 5" gibi aralıklarla sayfaları alır veya siler. "Al" seçeneğinde yazdığınız sıra korunur; sayfaları yeniden sıralamak için de kullanılabilir.
Sayfa Döndür: Seçili sayfaları (boşsa tümünü) 90° sağa, sola veya 180° çevirir.
Boş Sayfaları Temizle: Çift yüzlü taramalardaki boş arka sayfaları algılar, numaralarını gösterir ve siz onaylayınca siler.

# Evrak hazırlama
'Aslı Gibidir' Kaşesi: Başlık, ad soyad, sicil no ve tarihi çerçeveli kaşe olarak basar; bilgiler bir kez girilince hatırlanır. Kaşe rengini (kırmızı, siyah, lacivert, mavi) seçebilirsiniz; ad soyad satırı için ayrı bir renk de seçilebilir. Konum ve sayfa kapsamı seçilebilir. Döndürülmüş sayfalarda da kaşe doğru köşeye ve dik basılır; Türkçe karakterler desteklenir.
Filigran: Tüm sayfalara çapraz, soluk bir metin ekler; rengi (gri, kırmızı, siyah, lacivert, mavi) seçilebilir.

# Dönüştür ve oku
UDF ➔ Word: UDF içeriğini .docx olarak aktarır (paragraf, hizalama, kalın/italik/altı çizili, tablo). Çıktıyı Word'de gözden geçirin.
UDF ➔ PDF: UDF'yi biçimini koruyarak PDF'e çizer. Bu PDF okunabilir bir kopyadır; UDF'deki elektronik imzayı taşımaz.
Word ➔ UDF (deneysel): .docx dosyasını UDF'ye çevirir; metin, hizalama, kalın/italik/altı çizili, punto, yazı tipi ve sayfa kenar boşlukları taşınır. Tablolar ' | ' ile ayrılmış satırlara, görseller atlanarak çevrilir; her çıktı yazıldıktan sonra yeniden okunup doğrulanır. UYAP Doküman Editörü'nde açıp kontrol etmeden kullanmayın.
Word ➔ PDF: Seçili .docx dosyasını PDF'e çevirir. Bilgisayarınızda Microsoft Word kurulu olmalıdır.
PDF ➔ Görsel: Her sayfayı PNG veya JPG olarak kaydeder.
Metin Kopyala / Göster: PDF ve Word'deki metni gösterir ve panoya kopyalar; UDF'yi biçimiyle (kalın, italik, hizalama) görüntüler. Taranmış PDF'lerde metin bulunmaz.

# Dosya paneli
Dosyalarda ara: Listedeki PDF, UDF ve Word dosyalarının içinde arar; Türkçe karakter ve büyük/küçük harf fark etmez (ör. "sikayet", "ŞİKAYET" ile eşleşir). Taranmış (görüntü) sayfaların içinde arama yapılamaz; uygulama bunu bildirir.
Evrak Dizini (Excel): Listedeki dosyalar için sıra, ad, tür, sayfa, boyut, tarih ve SHA-256 özetini içeren filtrelenebilir bir Excel dizini yazar; dosya adları belgeyi açan bağlantıdır.
Aynı içerik uyarısı: Aynı içeriğe sahip iki dosya eklenirse (farklı adla olsa bile) günlükte uyarı verilir.

# Kısayollar
Delete: seçili dosyayı listeden kaldırır.
"""

GIZLILIK_METNI = """
# Veri evrakınızda kalır
Uygulama internet bağlantısı kurmaz; tüm işlemler bu bilgisayarda yapılır. UYAP portalına bağlanmaz, giriş bilgilerinizi veya şifrenizi istemez. Evrak içeriği hiçbir yere gönderilmez.

# KVKK Tara
Dosyayı değiştirmeden T.C. kimlik no, IBAN, telefon, e-posta ve girdiğiniz özel kelimelerin kaç kez ve hangi sayfalarda geçtiğini raporlar. Paylaşmadan önce neyin gizlenmesi gerektiğini görmek için kullanın.

# KVKK Akıllı Karartma
Bulunan verileri siyah kutuyla kapatır ve metni dosyadan kalıcı olarak siler; ardından çıktıyı yeniden tarayarak doğrular. Çıktıda eşleşme kaldıysa size bildirir. Gizli metin, üst veri ve eklentiler de temizlenir.
SINIRLAR: Yalnızca metin katmanı olan sayfalarda çalışır. Taranmış (görüntü) sayfalardaki yazılar bulunamaz; uygulama bu sayfaları size bildirir. Satıra bölünmüş veya alışılmadık biçimdeki veriler kaçabilir. Çıktıyı paylaşmadan önce mutlaka gözle kontrol edin.

# T.C. kimlik numarası doğrulaması
Varsayılan olarak yalnızca resmî algoritmaya uyan 11 haneli sayılar T.C. kimlik numarası kabul edilir; böylece dosya veya sipariş numarası gibi rastgele 11 haneli sayılar gereksiz yere karartılmaz. Yanlış yazılmış bir T.C. numarasının da karartılmasını istiyorsanız o kutunun işaretini kaldırın.

# İşlem günlüğü
Soldaki günlük yalnızca bellekte tutulur, diske yazılmaz ve uygulama kapanınca silinir. "Temizle" ile anında silebilirsiniz.

# Diske yazılan tek şey
Tercihleriniz (kalite modu, kaşe başlığı, avukat adı, son kullanılan klasör) kullanıcı profilinizdeki UyapEvrakAsistani klasöründe ayarlar.json dosyasında saklanır. Evrak içeriği içermez. Silerseniz uygulama varsayılanlara döner.

# Üst veriler
"Üst verileri temizle" açıkken çıktılardan yazar ve program bilgisi silinir. Bu, evrakı başka bir kişiye gönderirken istemeden bilgi sızmasını önler.
"""


if __name__ == "__main__":
    dpi_netlestir()
    UyapEvrakAsistani().mainloop()
