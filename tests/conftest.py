import os
import sys
import zipfile

import pymupdf
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AYAR = {"profil": "Akıllı – metni koru (önerilen)", "bates": False, "on_ek": "EK-1",
        "meta_temizle": True, "icindekiler": False}


@pytest.fixture
def ayar():
    return dict(AYAR)


@pytest.fixture
def pdf_yap(tmp_path):
    """pdf_yap(["sayfa1 metni", None, ...]) -> yol.  None = boş sayfa."""
    def yap(sayfalar, ad="a.pdf"):
        d = pymupdf.open()
        for metin in sayfalar:
            s = d.new_page()
            if metin:
                s.insert_text((72, 100), metin, fontsize=11)
        yol = str(tmp_path / ad)
        d.save(yol)
        d.close()
        return yol
    return yap


@pytest.fixture
def udf_yap(tmp_path):
    def yap(xml, ad="t.udf"):
        yol = str(tmp_path / ad)
        with zipfile.ZipFile(yol, "w") as z:
            z.writestr("content.xml", xml)
        return yol
    return yap


ORNEK_UDF = ('<?xml version="1.0"?><template><content><![CDATA[Baslik metni\nGovde paragrafi\n]]></content>'
             '<elements><paragraph Alignment="1"><content bold="true" size="14" startOffset="0" length="13"/>'
             '</paragraph><paragraph><content italic="true" startOffset="13" length="16"/></paragraph>'
             '</elements></template>')
