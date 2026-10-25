"""
EderiNe — Vercel Python (FastAPI) giriş noktası.
vercel.json, /api/* isteklerini bu dosyadaki `app`e yönlendirir.
"""
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import core  # noqa: E402
from kodlar import (CEKIS_ENC, DURUM_ENC, KASA_ENC, MARKA_ENC, RENK_ENC,  # noqa: E402
                    VITES_ENC, YAKIT_ENC)

app = FastAPI(title="EderiNe API", docs_url=None, redoc_url=None)


# ── Girdi modelleri ──────────────────────────────────────────────────
class TahminIstegi(BaseModel):
    marka: str
    seri: str
    yil: int = Field(ge=1985, le=2026)
    km: int = Field(ge=0, le=2_000_000)
    durum: str = "İkinci El"
    kimden: str = "Sahibinden"
    agir_hasar: str = "Hayır"
    takasa: str = "Hayır"
    hasar_skoru: int = Field(0, ge=0, le=42)   # parça ağırlıklı skor; bkz. public/index.html
    motor_hacmi_cc: int = Field(0, ge=0, le=7000)   # 0 = belirtilmemiş
    motor_gucu_hp: int = Field(0, ge=0, le=1500)
    cekis: Optional[str] = None
    yakit: Optional[str] = None
    vites: Optional[str] = None
    kasa: Optional[str] = None
    renk: Optional[str] = None


class IlanIstegi(BaseModel):
    marka: str
    seri: Optional[str] = None
    yil_min: int = 2015
    yil_max: int = 2026
    max_km: int = 200_000
    max_fiyat: int = 0
    sirala: str = "En Düşük Fiyat"
    limit: Optional[int] = 50      # None = tümü


class AnalizIstegi(BaseModel):
    marka: str
    seri: Optional[str] = None
    yil_min: int = 2015
    yil_max: int = 2026


class PerformansIstegi(BaseModel):
    marka: str
    model: str
    motor_hacmi_cc: int = 1600
    motor_gucu_hp: int = 110


class FotoIstegi(BaseModel):
    goruntu: str   # data:image/jpeg;base64,....


def _bos(v):
    return v is None or v == "" or v == "Belirtilmemiş"


# ── Uçlar ────────────────────────────────────────────────────────────
@app.get("/api/saglik")
def saglik():
    return {"durum": "ok"}


@app.get("/api/ayarlar")
def ayarlar():
    il = core.ilanlar()
    m = core.meta()
    imp = sorted((m.get("feature_imp") or {}).items(), key=lambda t: -t[1])[:15]
    perf = core.performans_db()
    return {
        "ay_etiketi": core.ay_etiketi(),
        "katsayi": core.enflasyon_katsayisi(),
        "endeks": core.endeks_ozeti(),
        "markalar": sorted(MARKA_ENC),
        "seri_haritasi": il.harita,
        "tum_seriler": sorted(k for k in __import__("kodlar").SERI_ENC if k != "nan"),
        "ilan_markalari": sorted(il.harita),
        "yakit": list(YAKIT_ENC), "vites": list(VITES_ENC), "kasa": list(KASA_ENC),
        "renk": sorted(RENK_ENC), "durum": list(DURUM_ENC), "cekis": list(CEKIS_ENC),
        "foto_aktif": bool(os.environ.get("GROQ_API_KEY")),
        "model": {
            "test_metrikleri": m.get("test_metrikleri"),
            "ozellik_onemi": [{"ad": k, "deger": v} for k, v in imp],
            "en_iyi_parametreler": m.get("best_params"),
        },
        "performans": {mk: sorted(mdl) for mk, mdl in sorted(perf.items())},
    }


@app.post("/api/tahmin")
def tahmin(r: TahminIstegi):
    f = r.model_dump()
    # Boş bırakılan teknik alanlar sabit değerle doldurulmaz (eskiden: 1600 cc / 110 HP / Dizel / Sedan ...);
    # core.tamamla() aynı marka+model ilanlarındaki en yaygın gerçek donanımlardan doldurur.
    for alan in ("cekis", "yakit", "vites", "kasa", "renk"):
        if _bos(f[alan]):
            f[alan] = None
    f["renk"] = f["renk"] or "Beyaz"
    konfigler = core.tamamla(f)
    tipik = konfigler[0][1]          # en yaygın donanım (ekranda gösterilir)
    verilen = {"motor": not (_bos(r.motor_hacmi_cc) or _bos(r.motor_gucu_hp)), "yakit": f["yakit"] is not None,
               "vites": f["vites"] is not None, "kasa": f["kasa"] is not None, "cekis": f["cekis"] is not None}
    f["motor_hacmi_cc"], f["motor_gucu_hp"] = tipik["motor_hacmi_cc"], tipik["motor_gucu_hp"]

    ham = core.tahmin_yap(f, monoton=True, konfigler=konfigler)
    # Değerleme, aynı marka/model/yıl/km'deki emsal ilanların min–maks aralığı içinde tutulur.
    # Hasar skoru, km ve diğer etkenler modelin tahminini belirler; aralık yalnızca uç sınırdır.
    emsal = core.emsal_aralik(r.marka, r.seri, r.yil, r.km)
    deger, sinir, emsal_alti = ham, None, False
    alt, ust = ham * 0.90, ham * 1.10
    if emsal:
        # Alt sınır yalnızca HASARSIZ araçlara uygulanır: emsal ilanların çoğu hasarsızdır, hasar kaydı olan bir araç
        # haklı olarak en ucuz emsalin altında olabilir (eskiden skor 12 ile 30 aynı taban fiyata kilitleniyordu).
        hasarli = r.hasar_skoru > 0 or r.agir_hasar == "Evet"
        taban = 0.0 if hasarli else emsal["min"]
        deger = min(max(ham, taban), emsal["max"])
        sinir = "alt" if ham < taban else "ust" if ham > emsal["max"] else None
        emsal_alti = bool(hasarli and ham < emsal["min"])
        alt, ust = max(deger * 0.90, taban), min(deger * 1.10, emsal["max"])
        emsal["konum"] = (deger - emsal["min"]) / (emsal["max"] - emsal["min"]) if emsal["max"] > emsal["min"] else 0.5
    ana = core.piyasa_analiz(r.marka, None, r.yil - 2, r.yil + 2)
    # "Piyasadan ucuz/pahalı" kıyası: tüm markanın medyanına değil, aynı model/yıl/km emsallerinin medyanına göre
    medyan = (emsal or {}).get("medyan") or ana.get("medyan", deger)
    return {
        "tahmin": deger, "alt": alt, "ust": ust,
        "ham_tahmin": ham, "emsal": emsal, "sinirlandi": sinir, "emsal_alti": emsal_alti,
        "luks_uyari": r.marka in core.LUKS_MARKALAR,
        "verdict": core.verdict(deger, medyan),
        "girdi": {k: f[k] for k in ("marka", "seri", "yil", "km", "motor_hacmi_cc", "motor_gucu_hp")},
        "varsayim": {
            "motor": None if verilen["motor"] else f"{tipik['motor_hacmi_cc']} cc / {tipik['motor_gucu_hp']} HP",
            "yakit": None if verilen["yakit"] else tipik["yakit"],
            "vites": None if verilen["vites"] else tipik["vites"],
            "kasa": None if verilen["kasa"] else tipik["kasa"],
        },
        "arac_yasi": core.MODEL_YILI - r.yil,
        "motor": core.motor_bilgisi_bul(r.marka, f["motor_hacmi_cc"], f["motor_gucu_hp"]),
        "piyasa": ana,
        "oneriler": core.oneri_bul(tipik["kasa"], deger * 1.10, deger * 0.90,
                                   marka_haric=r.marka, yil_ref=r.yil),
    }


@app.post("/api/ilanlar")
def ilan_ara(r: IlanIstegi):
    il = core.ilanlar()
    m = il.maske(r.marka, r.seri or None, r.yil_min, r.yil_max)
    if r.max_km < 500_000:
        m &= il.km <= r.max_km
    if r.max_fiyat > 0:
        m &= il.fiyat <= r.max_fiyat
    toplam = int(m.sum())
    if toplam == 0:
        return {"toplam": 0, "ilanlar": [], "ozet": {}}

    sutun, artan = {
        "En Düşük Fiyat": (il.fiyat, True), "En Yüksek Fiyat": (il.fiyat, False),
        "En Az KM": (il.km, True), "En Yeni": (il.yil, False),
    }.get(r.sirala, (il.fiyat, True))
    idx = np.flatnonzero(m)
    anahtar = sutun[idx].astype(float)
    sira = np.argsort(anahtar if artan else -anahtar, kind="stable")
    idx = idx[sira]
    if r.limit:
        idx = idx[: r.limit]

    ozet = core.piyasa_analiz(r.marka, r.seri or None, r.yil_min, r.yil_max)
    medyan = ozet.get("medyan") or float(np.median(il.fiyat[m]))
    satirlar = []
    for i in idx:
        s = core.ilan_satiri(int(i))
        s["fark_pct"] = (s["fiyat"] - medyan) / medyan * 100 if medyan > 0 else 0
        satirlar.append(s)
    return {"toplam": toplam, "ilanlar": satirlar,
            "ozet": {k: ozet[k] for k in ("adet", "min", "medyan", "ort", "max")} if ozet else {}}


@app.post("/api/analiz")
def analiz(r: AnalizIstegi):
    il = core.ilanlar()
    ana = core.piyasa_analiz(r.marka, r.seri or None, r.yil_min, r.yil_max)
    if not ana:
        return {"ozet": None}
    m = il.maske(r.marka, r.seri or None, r.yil_min, r.yil_max)
    fiyat, yil = il.fiyat[m], il.yil[m]
    yillar = np.unique(yil)
    yil_medyan = [{"yil": int(y), "medyan": float(np.median(fiyat[yil == y]))} for y in yillar]
    sayim, kenar = np.histogram(fiyat, bins=50)
    return {
        "ozet": ana, "yil_medyan": yil_medyan,
        "histogram": {"kenar": kenar.tolist(), "sayim": sayim.tolist()},
    }


@app.post("/api/performans")
def performans(r: PerformansIstegi):
    ozet = core.performans_db().get(r.marka, {}).get(r.model)
    return {
        "ozet": ozet,
        "motor": core.motor_bilgisi_bul(r.marka, r.motor_hacmi_cc, r.motor_gucu_hp),
    }


@app.post("/api/foto")
def foto(r: FotoIstegi):
    import base64
    try:
        bas, veri = r.goruntu.split(",", 1)
        mime = bas.split(";")[0].replace("data:", "") or "image/jpeg"
        ham = base64.b64decode(veri)
    except Exception:
        raise HTTPException(400, "Geçersiz görüntü verisi")
    if len(ham) > 4_000_000:
        raise HTTPException(413, "Görüntü çok büyük")
    return core.fotograf_analiz(ham, mime)
