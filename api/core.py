"""
AutoValuate — iş mantığı (Streamlit'ten bağımsız, pandas/sklearn gerektirmez).
Çalışma zamanı bağımlılıkları: numpy, xgboost-cpu, httpx.
"""
from __future__ import annotations

import base64
import datetime
import json
import os
import random
from functools import lru_cache
from pathlib import Path

import numpy as np

from kodlar import (CEKIS_ENC, DURUM_ENC, KASA_ENC, MARKA_ENC, RENK_ENC,
                    SERI_ENC, VITES_ENC, YAKIT_ENC)

DATA = Path(__file__).resolve().parent.parent / "data"
MODEL_YILI = 2026            # model arac_yasi = 2026 - yil ile eğitildi
VERI_SETI_TABAN = (2026, 3)  # arabam_temiz.csv: Mart 2026 sonu

LUKS_MARKALAR = {
    "Ferrari", "Lamborghini", "Bentley", "Rolls-Royce", "Maserati",
    "Aston Martin", "McLaren", "Bugatti", "Koenigsegg", "Pagani",
    "Maybach", "Lotus",
}
AY_ADLARI = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def _json(ad):
    return json.loads((DATA / ad).read_text(encoding="utf-8"))


# ── Piyasa enflasyon endeksi (birden çok kaynağın ortalaması) ─────────
def _anahtar(k):
    return tuple(map(int, k.split("-")))


@lru_cache(maxsize=1)
def _kaynaklar():
    """{kaynak: {(yil, ay): yüzde}} — endeks.json 'kaynaklar' bölümü (eski tek kaynaklı biçim de okunur)."""
    ham = _json("endeks.json")
    kaynaklar = ham.get("kaynaklar") or {"tek": {"ad": "Endeks", "aylik_yuzde": ham.get("aylik_yuzde", {})}}
    return {ad: {_anahtar(k): float(v) for k, v in k_["aylik_yuzde"].items()} for ad, k_ in kaynaklar.items()}


@lru_cache(maxsize=1)
def _endeks():
    """Her ay için, o ayı yayımlamış kaynakların ortalaması."""
    aylar = {}
    for seri in _kaynaklar().values():
        for ay, v in seri.items():
            aylar.setdefault(ay, []).append(v)
    return {ay: float(np.mean(v)) for ay, v in aylar.items()}


def _ay_ekle(yil, ay, n=1):
    ay += n
    while ay > 12:
        ay -= 12
        yil += 1
    while ay < 1:
        ay += 12
        yil -= 1
    return yil, ay


def _aylik_yollar(hedef=None):
    """Taban aydan hedef aya kadar [(ay, yüzde, tahmini_mi)] — yayımlanmamış aylar son 3 ayın ortalaması."""
    endeks = _endeks()
    bugun = hedef or datetime.date.today()
    hy, ha = bugun.year, bugun.month
    son3 = sorted(endeks)[-3:]
    varsayilan = float(np.mean([endeks[k] for k in son3]))
    y, a = VERI_SETI_TABAN
    yol, guvenlik = [], 0
    while (y, a) != (hy, ha) and guvenlik < 240:
        y, a = _ay_ekle(y, a, 1)
        yol.append(((y, a), endeks.get((y, a), varsayilan), (y, a) not in endeks))
        guvenlik += 1
    return yol


def enflasyon_katsayisi(hedef=None):
    """Taban aydan hedef aya (varsayılan: bugün) bileşik katsayı."""
    kat = 1.0
    for _, yuzde, _ in _aylik_yollar(hedef):
        kat *= 1 + yuzde / 100.0
    return kat


def endeks_ozeti(hedef=None):
    """Arayüz için: kaynak listesi, ay ay kaynak değerleri + ortalama, tahmini aylar, katsayı."""
    ham = _json("endeks.json")
    kay = ham.get("kaynaklar") or {}
    seriler, endeks = _kaynaklar(), _endeks()
    aylik = [{"ay": f"{y}-{a:02d}", "ortalama": round(endeks[(y, a)], 3),
              **{ad: seriler[ad].get((y, a)) for ad in seriler}} for (y, a) in sorted(endeks)]
    yol = _aylik_yollar(hedef)
    return {
        "kaynaklar": [{"anahtar": ad, "ad": kay.get(ad, {}).get("ad", ad), "url": kay.get(ad, {}).get("url")} for ad in seriler],
        "taban_ay": ham.get("taban_ay"),
        "aylik": aylik,
        "tahmini_aylar": [f"{y}-{a:02d}" for (y, a), _, t in yol if t],
        "katsayi": enflasyon_katsayisi(hedef),
    }


def ay_etiketi(hedef=None):
    b = hedef or datetime.date.today()
    return f"{AY_ADLARI[b.month]} {b.year}"


# ── Kaynakların yüklenmesi (soğuk başlangıçta bir kez) ───────────────
@lru_cache(maxsize=1)
def model():
    import xgboost as xgb
    b = xgb.Booster()
    b.load_model(str(DATA / "model.ubj"))
    return b


@lru_cache(maxsize=1)
def meta():
    return _json("meta.json")


@lru_cache(maxsize=1)
def marka_pop():
    return _json("marka_meta.json").get("popularite", {})


@lru_cache(maxsize=1)
def motor_db():
    return _json("motor.json")


@lru_cache(maxsize=1)
def performans_db():
    return _json("performans.json")


class Ilanlar:
    """arabam_temiz.csv'nin sütunlu (numpy) hali. Fiyatlar güncel aya taşınmış."""

    def __init__(self):
        z = np.load(DATA / "ilanlar.npz")
        self.t = _json("ilan_tablolari.json")
        self.marka, self.seri = z["marka"], z["seri"]
        self.yakit, self.vites, self.kasa = z["yakit"], z["vites"], z["kasa"]
        self.yil, self.km = z["yil"].astype(np.int32), z["km"]
        self.taban_fiyat = z["fiyat"].astype(np.float64)
        # Motor hacmi/gücü ve çekiş: boş bırakılan alanlar piyasadaki gerçek dağılımdan tamamlanır.
        # (Eski data/ilanlar.npz'de yoksa None kalır; bu durumda eski sabit varsayılanlar kullanılır.)
        self.hacim = z["hacim"].astype(np.int32) if "hacim" in z.files else None
        self.guc = z["guc"].astype(np.int32) if "guc" in z.files else None
        self.cekis = z["cekis"] if "cekis" in z.files else None
        self._kat = None
        self._fiyat = None
        # küçük harfli ad → kod
        self.marka_kod = {a.lower(): i for i, a in enumerate(self.t["marka"])}
        self.seri_kod = {a.lower(): i for i, a in enumerate(self.t["seri"])}
        self.kasa_kod = {a.lower(): i for i, a in enumerate(self.t["kasa"])}
        # marka → seriler (arayüz listeleri)
        harita = {}
        for mk in np.unique(self.marka):
            seriler = np.unique(self.seri[self.marka == mk])
            adlar = sorted(self.t["seri"][s] for s in seriler
                           if self.t["seri"][s] and self.t["seri"][s].lower() != "nan")
            if adlar:
                harita[self.t["marka"][mk]] = adlar
        self.harita = harita

    @property
    def fiyat(self):
        kat = enflasyon_katsayisi()
        if self._fiyat is None or self._kat != kat:   # ay değişirse yeniden hesapla
            self._fiyat = self.taban_fiyat * kat
            self._kat = kat
        return self._fiyat

    def maske(self, marka, seri=None, yil_min=None, yil_max=None):
        mk = self.marka_kod.get(str(marka).lower())
        if mk is None:
            return np.zeros(len(self.yil), dtype=bool)
        m = self.marka == mk
        if seri:
            sk = self.seri_kod.get(str(seri).lower())
            if sk is None:
                return np.zeros(len(self.yil), dtype=bool)
            m &= self.seri == sk
        if yil_min is not None:
            m &= self.yil >= yil_min
        if yil_max is not None:
            m &= self.yil <= yil_max
        return m & (self.yil > 0)


@lru_cache(maxsize=1)
def ilanlar() -> Ilanlar:
    return Ilanlar()


# ── Tahmin ───────────────────────────────────────────────────────────
def _yas_seg(y):  return 0 if y <= 2 else 1 if y <= 5 else 2 if y <= 10 else 3 if y <= 15 else 4
def _guc_seg(h):  return 0 if h < 90 else 1 if h < 140 else 2 if h < 220 else 3
def _hacim_seg(c): return 0 if c < 1000 else 1 if c < 1400 else 2 if c < 1800 else 3 if c < 2500 else 4


def _km_anomali(km, arac_yasi):
    """Eğitimdeki km_anomali ile AYNI formül: (yıllık km − yaşa göre medyan yıllık km) / genel std, [-3, 3].
    Eskiden tahminde hep 0 veriliyordu: düşük km'li araç 'ortalama km'li' görünüyor, fiyatı düşük çıkıyordu."""
    fe = meta().get("fe_sabitler", {})
    tablo, std = fe.get("yas_km_medyan"), fe.get("yillik_km_std")
    if not tablo or not std:
        return 0.0
    yaslar = sorted(int(k) for k in tablo)
    yas = min(yaslar, key=lambda a: abs(a - arac_yasi))   # tabloda olmayan yaşta en yakın yaş
    yillik = km / max(arac_yasi, 1)
    return float(np.clip((yillik - tablo[str(yas)]) / (std + 1e-9), -3, 3))


def _tahmin_tek(f: dict, monoton: bool = False) -> float:
    """Tüm alanları dolu tek bir araç yapılandırması için fiyat (güncel aya taşınmış).

    monoton=True: hasar skoru arttıkça tahmin ARTMAZ. Model eski skalada (0–26) eğitildi; yüksek skorlar
    çok az örnekle temsil edildiği için ağaçlar ~22 üstünde fiyatı tekrar yükseltebiliyor ve 26 üstünde
    sabitleniyor. Arayüzdeki ağırlıklı skor 42'ye çıktığından 0..skor aralığındaki en düşük tahmin alınır."""
    import xgboost as xgb
    arac_yasi = MODEL_YILI - f["yil"]
    hacim, guc = f["motor_hacmi_cc"], f["motor_gucu_hp"]
    guc_hacim = guc / hacim if hacim > 0 else 0

    fe = meta().get("fe_sabitler", {})
    gh_med, gh_std = fe.get("guc_hacim_median", 0.0693), fe.get("guc_hacim_std", 0.0388)
    guc_hacim_norm = float(np.clip((guc_hacim - gh_med) / (gh_std + 1e-9), -3, 3))

    pop = marka_pop()
    mx = max(pop.values()) if pop else 1
    mpop = pop.get(f["marka"], 0) / mx if mx > 0 else 0.5

    satir = {
        "arac_yasi": arac_yasi, "km": f["km"],
        "yillik_km": f["km"] / max(arac_yasi, 1),
        "hasar_skoru": f["hasar_skoru"],
        "motor_hacmi_cc": hacim, "motor_gucu_hp": guc, "guc_hacim_orani": guc_hacim,
        "cekis_enc": CEKIS_ENC.get(f["cekis"], 0),
        "kimden_galeri": 1 if f["kimden"] == "Galeriden" else 0,
        "kimden_bayi": 1 if f["kimden"] == "Yetkili Bayiden" else 0,
        "agir_hasarli_evet": 1 if f["agir_hasar"] == "Evet" else 0,
        "takasa_uygun_evet": 1 if f["takasa"] == "Evet" else 0,
        "marka_enc": MARKA_ENC.get(f["marka"], 0),
        "seri_enc": SERI_ENC.get(f["seri"], 0),
        "yakit_tipi_enc": YAKIT_ENC.get(f["yakit"], 0),
        "vites_tipi_enc": VITES_ENC.get(f["vites"], 0),
        "kasa_tipi_enc": KASA_ENC.get(f["kasa"], 0),
        "renk_enc": RENK_ENC.get(f["renk"], 2),
        "arac_durumu_enc": DURUM_ENC.get(f["durum"], 2),
        "yas_segment": _yas_seg(arac_yasi), "guc_hacim_norm": guc_hacim_norm,
        "guc_segment": _guc_seg(guc), "hacim_segment": _hacim_seg(hacim),
        "marka_popularite": mpop, "km_anomali": _km_anomali(f["km"], arac_yasi),
    }
    oz = meta()["ozellikler"]
    hasarlar = range(0, min(int(f["hasar_skoru"]), 26) + 1) if monoton else [f["hasar_skoru"]]
    x = np.array([[{**satir, "hasar_skoru": h}.get(k, 0) for k in oz] for h in hasarlar], dtype=np.float32)
    tahminler = np.expm1(model().predict(xgb.DMatrix(x, feature_names=oz)))
    ham = float(tahminler.min() if monoton else tahminler[0])
    return ham * enflasyon_katsayisi()


# Boş bırakılan teknik alanların tamamlanması ----------------------------------
# Eskiden boş alanlar SABİT değerle dolduruluyordu (1600 cc / 110 HP, yakıt = listenin 2. elemanı = DİZEL,
# kasa = Sedan ...). Gerçekte olmayan bu kombinasyonlar (ör. dizel Civic) modeli şaşırtıp fiyatı düşürüyordu.
# Şimdi aynı marka+model (ve yakın model yılı) ilanlarında en sık görülen GERÇEK donanımlar kullanılır.
_ESKI_VARSAYILAN = {"motor_hacmi_cc": 1600, "motor_gucu_hp": 110, "cekis": "Önden Çekiş",
                    "yakit": "Benzin", "vites": "Otomatik", "kasa": "Sedan"}


def _bos_mu(v):
    return v is None or v == "" or v == 0 or v == "Belirtilmemiş"


def _emsal_pencere(marka, seri, yil, en_az=8):
    """Marka+model için yıl penceresi giderek genişleyen ilan maskesi."""
    il = ilanlar()
    for dy in (1, 2, 4):
        m = il.maske(marka, seri or None, yil - dy, yil + dy)
        if m.sum() >= en_az:
            return m
    m = il.maske(marka, seri or None)
    if m.sum() >= en_az:
        return m
    return il.maske(marka, None, yil - 4, yil + 4)


def tamamla(f: dict, en_fazla: int = 6):
    """[(ağırlık, tam_yapılandırma)] — boş teknik alanları piyasadaki gerçek donanım dağılımından doldurur.

    Kullanıcının verdiği alanlar korunur; verilmeyenler için en yaygın donanımlar (en çok `en_fazla`),
    ilan sayısıyla orantılı ağırlıkla döner. Birinci eleman en yaygın donanımdır."""
    il = ilanlar()
    f = dict(f)
    alanlar = {"motor_hacmi_cc": "hacim", "motor_gucu_hp": "guc", "yakit": "yakit",
               "vites": "vites", "kasa": "kasa", "cekis": "cekis"}
    bos = [a for a in alanlar if _bos_mu(f.get(a))]
    if not bos:
        return [(1.0, f)]
    if il.hacim is None or il.guc is None or il.cekis is None:   # eski veri dosyası
        return [(1.0, {**f, **{a: _ESKI_VARSAYILAN[a] for a in bos}})]

    pencere = _emsal_pencere(f["marka"], f.get("seri"), f["yil"])
    sec = np.flatnonzero(pencere)
    if sec.size == 0:
        return [(1.0, {**f, **{a: _ESKI_VARSAYILAN[a] for a in bos}})]

    sutun = {"hacim": il.hacim, "guc": il.guc, "yakit": il.yakit, "vites": il.vites,
             "kasa": il.kasa, "cekis": il.cekis}
    # Geçerli motor kaydı olan ilanlar (hacim/güç eksik olanlar tamamlamada kullanılamaz)
    if "motor_hacmi_cc" in bos or "motor_gucu_hp" in bos:
        gecerli = sec[(il.hacim[sec] > 0) & (il.guc[sec] > 0)]
        if gecerli.size >= 3:
            sec = gecerli
    # Kullanıcının verdiği alanlara uyan ilanlara daralt; çok az ilan kalıyorsa o filtreyi atla
    for a, anahtar in alanlar.items():
        if a in bos:
            continue
        if a == "motor_hacmi_cc":
            uy = np.abs(il.hacim[sec] - f[a]) <= max(f[a] * 0.05, 1)
        elif a == "motor_gucu_hp":
            uy = np.abs(il.guc[sec] - f[a]) <= max(f[a] * 0.10, 1)
        else:
            tablo = il.t[anahtar]
            kod = tablo.index(f[a]) if f[a] in tablo else None
            if kod is None:
                continue
            uy = sutun[anahtar][sec] == kod
        if uy.sum() >= 3:
            sec = sec[uy]

    # Yalnızca BOŞ alanlara göre benzersiz yapılandırmalar ve sayıları
    kolonlar = np.stack([sutun[alanlar[a]][sec].astype(np.int64) for a in bos], axis=1)
    benzersiz, sayim = np.unique(kolonlar, axis=0, return_counts=True)
    sira = np.argsort(-sayim, kind="stable")[:en_fazla]
    toplam = float(sayim[sira].sum())
    sonuc = []
    for i in sira:
        g = dict(f)
        for a, kod in zip(bos, benzersiz[i]):
            anahtar = alanlar[a]
            g[a] = int(kod) if anahtar in ("hacim", "guc") else il.t[anahtar][int(kod)]
        sonuc.append((float(sayim[i]) / toplam, g))
    return sonuc


def tahmin_yap(f: dict, monoton: bool = False, konfigler=None) -> float:
    """Fiyat tahmini. Boş teknik alanlar varsa, piyasadaki yaygın donanımların ağırlıklı ortalaması alınır."""
    konfigler = konfigler or tamamla(f)
    return float(sum(w * _tahmin_tek(g, monoton) for w, g in konfigler))


# ── Piyasa analizi / öneri ───────────────────────────────────────────
def piyasa_analiz(marka, seri=None, yil_min=2010, yil_max=2026):
    il = ilanlar()
    m = il.maske(marka, seri, yil_min, yil_max)
    if not m.any():
        return {}
    p = il.fiyat[m]
    yakit = np.bincount(il.yakit[m], minlength=len(il.t["yakit"]))
    kasa = np.bincount(il.kasa[m], minlength=len(il.t["kasa"]))
    sirala = lambda sayac, ad: {ad[i]: int(n) for i, n in sorted(enumerate(sayac), key=lambda t: -t[1]) if n}
    return {
        "adet": int(m.sum()), "min": float(p.min()), "max": float(p.max()),
        "medyan": float(np.median(p)), "ort": float(p.mean()),
        "q25": float(np.percentile(p, 25)), "q75": float(np.percentile(p, 75)),
        "yakit": sirala(yakit, il.t["yakit"]), "kasa": sirala(kasa, il.t["kasa"]),
    }


def ilan_satiri(i):
    il = ilanlar()
    return {
        "marka": il.t["marka"][il.marka[i]], "seri": il.t["seri"][il.seri[i]],
        "yil": int(il.yil[i]) if il.yil[i] > 0 else None, "km": int(il.km[i]),
        "fiyat": float(il.fiyat[i]), "yakit": il.t["yakit"][il.yakit[i]],
        "vites": il.t["vites"][il.vites[i]], "kasa": il.t["kasa"][il.kasa[i]],
    }


def oneri_bul(kasa, fiyat_ust, fiyat_alt, marka_haric=None, n=5, yil_ref=None, min_ilan=3):
    """Benzer araç önerisi: tek bir ilana değil, marka+model GRUBUNUN ortalama fiyatına bakar.

    Aynı kasa tipinde ve model yılı (yil_ref ± 3) aralığındaki ilanlar marka+seri bazında
    gruplanır; grubun ortalama fiyatı [fiyat_alt, fiyat_ust] bandına düşen (ve en az
    `min_ilan` ilanı olan) gruplar, ortalaması tahmine en yakın olandan başlayarak döner.
    Fiyatlar il.fiyat üzerinden gelir: taban ay fiyatı x güncel enflasyon katsayısı.
    """
    il = ilanlar()
    hedef = (fiyat_ust + fiyat_alt) / 2
    m = il.yil > 0
    if kasa and kasa != "Bilinmiyor":
        kk = il.kasa_kod.get(kasa.lower())
        m &= (il.kasa == kk) if kk is not None else np.zeros_like(m)
    if marka_haric:
        mk = il.marka_kod.get(marka_haric.lower())
        if mk is not None:
            m &= il.marka != mk
    if yil_ref:
        m &= (il.yil >= yil_ref - 3) & (il.yil <= yil_ref + 3)
    idx = np.flatnonzero(m)
    if idx.size == 0:
        return []
    anahtar = il.marka[idx].astype(np.int64) * 10000 + il.seri[idx]
    grup, ters = np.unique(anahtar, return_inverse=True)
    adet = np.bincount(ters)
    ort = np.bincount(ters, weights=il.fiyat[idx]) / adet
    ort_km = np.bincount(ters, weights=il.km[idx].astype(float)) / adet
    sonuc = []
    for g in np.flatnonzero((adet >= min_ilan) & (ort >= fiyat_alt) & (ort <= fiyat_ust)):
        uyeler = idx[ters == g]
        p = il.fiyat[uyeler]
        sonuc.append({
            "marka": il.t["marka"][il.marka[uyeler[0]]], "seri": il.t["seri"][il.seri[uyeler[0]]],
            "ort_fiyat": float(ort[g]), "min_fiyat": float(p.min()), "max_fiyat": float(p.max()),
            "yil_min": int(il.yil[uyeler].min()), "yil_max": int(il.yil[uyeler].max()),
            "ort_km": int(ort_km[g]), "adet": int(adet[g]),
            "yakit": il.t["yakit"][np.bincount(il.yakit[uyeler]).argmax()],
            "vites": il.t["vites"][np.bincount(il.vites[uyeler]).argmax()],
            "kasa": il.t["kasa"][il.kasa[uyeler[0]]],
        })
    sonuc.sort(key=lambda s: abs(s["ort_fiyat"] - hedef))
    return sonuc[:n]


def emsal_aralik(marka, seri, yil, km, min_ilan=15):
    """Aynı marka+model, benzer model yılı ve kilometredeki ilanların fiyat aralığı (min–maks).

    Emsal bulunamazsa pencere kademeli genişler: (yıl ±1, km ±%40) → (±2, %60) → (±3, %100) → (±5, km sınırı yok).
    Fiyat girişi hatası gibi aşırı uç değerler (Q1−3×IQR altı / Q3+3×IQR üstü) aralığa dahil edilmez.
    Model yok ya da 5'ten az emsal varsa None döner (aralık sınırı uygulanmaz)."""
    il = ilanlar()
    if not seri:
        return None
    for adim, (dy, kw) in enumerate(((1, 0.4), (2, 0.6), (3, 1.0), (5, None))):
        m = il.maske(marka, seri, yil - dy, yil + dy)
        if kw is not None:
            pay = km * kw + 15000
            m &= (il.km >= km - pay) & (il.km <= km + pay)
        n = int(m.sum())
        if n >= min_ilan or adim == 3:
            break
    if n < 5:
        return None
    p = il.fiyat[m]
    q1, q3 = np.percentile(p, [25, 75])
    iqr = q3 - q1
    tut = (p >= q1 - 3 * iqr) & (p <= q3 + 3 * iqr)
    p, k, y = p[tut], il.km[m][tut], il.yil[m][tut]
    return {
        "min": float(p.min()), "max": float(p.max()), "medyan": float(np.median(p)), "adet": int(p.size),
        "yil_min": int(y.min()), "yil_max": int(y.max()),
        "km_min": int(k.min()), "km_max": int(k.max()), "genis": adim > 0,
    }


def verdict(tahmin, medyan):
    pct = ((tahmin - medyan) / medyan) * 100 if medyan > 0 else 0
    if pct <= -10:
        return {"tip": "uygun", "metin": f"Piyasadan %{abs(pct):.1f} ucuz ✓", "pct": pct}
    if pct >= 10:
        return {"tip": "pahali", "metin": f"Piyasadan %{abs(pct):.1f} pahalı ✗", "pct": pct}
    return {"tip": "normal", "metin": f"Piyasa ortalamasına yakın (~%{abs(pct):.1f})", "pct": pct}


# ── Motor eşleştirme (sklearn KNN yerine numpy) ──────────────────────
def motor_bilgisi_bul(marka, hacim_cc, guc_hp):
    db = motor_db().get(marka)
    if not db:
        return None
    kayitlar = db["kayitlar"]
    X = np.array([[k["hacim_cc"], k["guc_hp"]] for k in kayitlar], dtype=float)
    ort, olcek = np.array(db["ort"]), np.array(db["olcek"])
    olcek = np.where(olcek == 0, 1.0, olcek)
    Xs = (X - ort) / olcek
    xs = (np.array([hacim_cc, guc_hp], dtype=float) - ort) / olcek
    d = np.sqrt(((Xs - xs) ** 2).sum(axis=1))
    i = int(np.argmin(d))
    mesafe = float(d[i])
    guven = "Yüksek" if mesafe < 0.3 else ("Orta" if mesafe < 1.0 else "Düşük")
    return {"kayit": kayitlar[i], "mesafe": mesafe, "guven": guven}


# ── Fotoğraf analizi (Groq) ──────────────────────────────────────────
# Görsel destekli modeller sırayla denenir. llama-4-scout Groq tarafından 17.07.2026'da kaldırıldı;
# model değişirse Vercel'de GROQ_VISION_MODEL ortam değişkeniyle kod değiştirmeden güncellenebilir.
FOTO_MODELLERI = ("qwen/qwen3.6-27b", "qwen/qwen3.8-27b")


def _tam_sayi(v) -> int:
    """'2017', 2017.0, '2017-2019' gibi değerlerden ilk tam sayıyı alır; olmazsa 0."""
    import re
    if isinstance(v, (int, float)):
        return int(v)
    m = re.search(r"\d+", str(v or "").replace(".", "").replace(",", ""))
    return int(m.group()) if m else 0


def _json_ayikla(metin: str) -> dict:
    """Model çıktısından JSON nesnesini çıkarır (düşünme etiketleri / ```json çitleri / ek metin olsa da)."""
    import re
    t = re.sub(r"<think>.*?</think>", "", metin or "", flags=re.S)
    t = t.replace("```json", "").replace("```", "")
    bas = t.find("{")
    if bas < 0:
        raise ValueError("Model JSON döndürmedi")
    derin = 0
    for k in range(bas, len(t)):
        derin += (t[k] == "{") - (t[k] == "}")
        if derin == 0:
            return json.loads(t[bas:k + 1])
    raise ValueError("Model JSON'u yarım kaldı")


def fotograf_analiz(img_bytes: bytes, mime: str = "image/jpeg") -> dict:
    import httpx
    yedek = {"kasa_tipi": "Bilinmiyor", "renk": "Diğer", "marka": "", "seri": "",
             "yil": 0, "km": 0}
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return {**yedek, "aciklama": "GROQ_API_KEY tanımlı değil (Vercel → Settings → Environment Variables)"}
    b64 = base64.standard_b64encode(img_bytes).decode()
    marka_listesi = sorted(MARKA_ENC.keys())
    guncel_yil = MODEL_YILI
    prompt = f"""Bu araç fotoğrafını analiz et. SADECE JSON döndür, başka hiçbir şey yazma.

ÖNEMLİ KURALLAR:
1. Aracı mutlaka tanımaya çalış: görselde tek bir araç görünüyorsa marka ve modeli en iyi tahminle yaz. "marka" alanını yalnızca fotoğrafta hiç araç yoksa boş bırak.
2. Bu aracın kasasının/neslinin (generation) piyasaya sürüldüğü YIL ARALIĞINI belirle (örn: 2015-2019).
3. "yil" alanına bu aralığın ORTASI olan yılı yaz (örn: 2017).
4. "yil_aralik_baslangic" ve "yil_aralik_bitis" alanlarına kasa üretim yıllarını yaz.
5. arac_yasi = {guncel_yil} - yil. arac_yasi <= 10 ise km = arac_yasi × 17500, değilse km = arac_yasi × 12500 (tam sayı).

JSON formatı:
{{
  "marka": "araç markası (örn: Toyota, BMW, Mercedes - Benz — bilinen markalar: {', '.join(marka_listesi[:40])} vb.)",
  "seri": "model/seri adı (örn: Corolla, CLA, Golf)",
  "yil_aralik_baslangic": kasa üretim başlangıç yılı (tam sayı),
  "yil_aralik_bitis": kasa üretim bitiş yılı (tam sayı),
  "yil": aralığın ortası (tam sayı),
  "km": tahmini kilometre (tam sayı),
  "kasa_tipi": "Sedan|Hatchback/5|Hatchback/3|SUV|Coupe|Station wagon|MPV|Cabrio|Pick-up|Bilinmiyor",
  "renk": "Beyaz|Siyah|Gri|Kırmızı|Mavi|Lacivert|Kahverengi|Bordo|Yeşil|Sarı|Turuncu|Mor|Bej|Şampanya|Füme|Diğer",
  "aciklama": "kısa Türkçe açıklama (kasa dönemi ve km tahmini dahil)"
}}"""
    modeller = [m for m in (os.environ.get("GROQ_VISION_MODEL", "").strip(), *FOTO_MODELLERI) if m]
    modeller = list(dict.fromkeys(modeller))
    son_hata = "bilinmeyen hata"
    res = None
    for model_adi in modeller:
        try:
            r = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                json={
                    "model": model_adi,
                    "temperature": 0.2,
                    "max_tokens": 4000,   # düşünen (reasoning) modeller cevaptan önce token harcar
                    "messages": [{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {"type": "text", "text": prompt},
                    ]}],
                },
                timeout=50,
            )
            veri = r.json()
            if r.status_code != 200 or "choices" not in veri:
                ayrinti = (veri.get("error") or {}).get("message") if isinstance(veri, dict) else None
                raise RuntimeError(f"Groq hatası {r.status_code} ({model_adi}): {ayrinti or r.text[:200]}")
            res = _json_ayikla(veri["choices"][0]["message"].get("content"))
            break
        except Exception as e:  # bu model olmadı → sıradakini dene
            son_hata = str(e)
    if res is None:
        return {**yedek, "aciklama": son_hata}

    import re
    sayilar = [int(x) for x in re.findall(r"\d{4}", str(res.get("yil") or ""))]
    yil = (sayilar[0] + sayilar[-1]) // 2 if len(sayilar) >= 2 else _tam_sayi(res.get("yil"))   # "2012-2018" → 2015
    if not (1985 <= yil <= guncel_yil):
        bas, bit = _tam_sayi(res.get("yil_aralik_baslangic")), _tam_sayi(res.get("yil_aralik_bitis"))
        yil = (bas + bit) // 2 if bas > 0 and bit > 0 else 0
        if not (1985 <= yil <= guncel_yil):
            yil = 0
    arac_yasi = guncel_yil - yil if yil > 0 else 0

    km = _tam_sayi(res.get("km"))
    if km <= 0 or km > 1_000_000:
        km = arac_yasi * (17500 if arac_yasi <= 10 else 12500) if arac_yasi > 0 else 0
    res["marka"] = str(res.get("marka") or "").strip()
    res["seri"] = str(res.get("seri") or "").strip()
    res["yil"], res["km"] = yil, km
    return res
