"""Eski (Streamlit/pickle/pandas) sonuçlarla yeni (numpy/ubj) sonuçları karşılaştırır.
Geliştirme aracıdır; Vercel'e yüklenmez.  python scripts/test_parity.py"""
import json, pickle, random, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
K = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(K / "api"))
import core, kodlar as KD

E = K / "egitim"
model = pickle.load(open(E / "model.pkl", "rb"))
motor = pickle.load(open(E / "motor_model.pkl", "rb"))
oz = list(model.feature_names_in_)
kat = core.enflasyon_katsayisi()

# 1) Fiyat tahmini
random.seed(1); maxfark = 0
for _ in range(300):
    mk = random.choice(list(KD.MARKA_ENC)); sr = random.choice(list(KD.SERI_ENC))
    f = dict(marka=mk, seri=sr, yil=random.randint(1990, 2026), km=random.randint(0, 400000),
             yakit=random.choice(list(KD.YAKIT_ENC)), vites=random.choice(list(KD.VITES_ENC)),
             kasa=random.choice(list(KD.KASA_ENC)), durum=random.choice(list(KD.DURUM_ENC)),
             motor_hacmi_cc=random.choice([1000, 1300, 1600, 2000, 3000]),
             motor_gucu_hp=random.choice([70, 110, 150, 250, 400]),
             cekis=random.choice(list(KD.CEKIS_ENC)), renk=random.choice(list(KD.RENK_ENC)),
             kimden=random.choice(["Sahibinden", "Galeriden", "Yetkili Bayiden"]),
             agir_hasar=random.choice(["Hayır", "Evet"]), takasa=random.choice(["Hayır", "Evet"]),
             hasar_skoru=random.randint(0, 26))
    yeni = core.tahmin_yap(f)
    # eski mantık (uygulama.py: tahmin_yap) — satır sözlüğünü aynı özelliklerle kur
    ya = 2026 - f["yil"]; gh = f["motor_gucu_hp"] / f["motor_hacmi_cc"]
    fe = core.meta()["fe_sabitler"]
    pop = core.marka_pop(); mpop = pop.get(mk, 0) / max(pop.values())
    row = dict(arac_yasi=ya, km=f["km"], yillik_km=f["km"] / max(ya, 1), hasar_skoru=f["hasar_skoru"],
        motor_hacmi_cc=f["motor_hacmi_cc"], motor_gucu_hp=f["motor_gucu_hp"], guc_hacim_orani=gh,
        cekis_enc=KD.CEKIS_ENC[f["cekis"]], kimden_galeri=int(f["kimden"] == "Galeriden"),
        kimden_bayi=int(f["kimden"] == "Yetkili Bayiden"), agir_hasarli_evet=int(f["agir_hasar"] == "Evet"),
        takasa_uygun_evet=int(f["takasa"] == "Evet"), marka_enc=KD.MARKA_ENC[mk], seri_enc=KD.SERI_ENC[sr],
        yakit_tipi_enc=KD.YAKIT_ENC[f["yakit"]], vites_tipi_enc=KD.VITES_ENC[f["vites"]],
        kasa_tipi_enc=KD.KASA_ENC[f["kasa"]], renk_enc=KD.RENK_ENC[f["renk"]], arac_durumu_enc=KD.DURUM_ENC[f["durum"]],
        yas_segment=core._yas_seg(ya), guc_hacim_norm=float(np.clip((gh - fe["guc_hacim_median"]) / (fe["guc_hacim_std"] + 1e-9), -3, 3)),
        guc_segment=core._guc_seg(f["motor_gucu_hp"]), hacim_segment=core._hacim_seg(f["motor_hacmi_cc"]),
        marka_popularite=mpop, km_anomali=0.0)
    eski = float(np.expm1(model.predict(pd.DataFrame([{k: row[k] for k in oz}]))[0])) * kat
    maxfark = max(maxfark, abs(yeni - eski) / eski)
print(f"[1] tahmin: 300 rastgele girdi, en büyük bağıl fark = {maxfark:.2e}")
assert maxfark < 1e-5

# 2) Motor eşleştirme
yanlis = 0
for _ in range(500):
    mk = random.choice(list(motor)); h = random.randint(600, 6000); g = random.randint(40, 700)
    kay = motor[mk]; xs = kay["scaler"].transform(np.array([[h, g]], float))
    d, i = kay["knn"].kneighbors(xs, n_neighbors=1)
    yeni = core.motor_bilgisi_bul(mk, h, g)
    if yeni["kayit"]["motor_kodu"] != kay["veri"].iloc[i[0][0]]["motor_kodu"] or abs(yeni["mesafe"] - d[0][0]) > 1e-9:
        yanlis += 1
print(f"[2] motor KNN: 500 sorgu, uyuşmayan = {yanlis}"); assert yanlis <= 2

# 3) Piyasa analizi (pandas ile yeniden hesapla)
df = pd.read_csv(E / "arabam_temiz.csv", low_memory=False)
df = df[pd.to_numeric(df["fiyat"], errors="coerce") > 0].copy(); df["fiyat"] *= kat
df["yil"] = (2026 - pd.to_numeric(df["arac_yasi"], errors="coerce")).astype("Int64")
df["marka"] = df["marka_enc"].map({v: k for k, v in KD.MARKA_ENC.items()}).fillna("Bilinmiyor")
df["seri"] = df["seri_enc"].map({v: k for k, v in KD.SERI_ENC.items()}).fillna("Diğer")
for mk, sr, a, b in [("Toyota", None, 2015, 2026), ("BMW", "3 Serisi", 2010, 2020), ("Renault", "Clio", 2018, 2023), ("Tesla", None, 2015, 2026)]:
    m = (df["marka"].str.lower() == mk.lower()) & df["yil"].between(a, b)
    if sr: m &= df["seri"].str.lower() == sr.lower()
    d = df[m]; y = core.piyasa_analiz(mk, sr, a, b)
    assert y["adet"] == len(d), (mk, y["adet"], len(d))
    for key, val in [("medyan", d["fiyat"].median()), ("ort", d["fiyat"].mean()), ("q25", d["fiyat"].quantile(.25)),
                     ("q75", d["fiyat"].quantile(.75)), ("min", d["fiyat"].min()), ("max", d["fiyat"].max())]:
        assert abs(y[key] - val) / val < 1e-4, (mk, key, y[key], val)
print("[3] piyasa analizi: adet/medyan/ort/çeyrekler eski pandas sonuçlarıyla eşleşiyor")
print("TÜM KONTROLLER GEÇTİ")
