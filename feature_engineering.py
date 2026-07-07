"""
MODÜL 2 — Özellik Mühendisliği (Feature Engineering)
arabam_temiz.csv → arabam_features.csv
"""

import pandas as pd
import numpy as np
import pickle

print("=" * 60)
print("MODÜL 2 — Özellik Mühendisliği")
print("=" * 60)

print("\n[1/6] Veri yükleniyor...")
df = pd.read_csv("arabam_temiz.csv")
print(f"      {len(df):,} satır")

# ── 1. Araç yaşı segmentleri ────────────────────────────────
print("\n[2/6] Yaş segmentleri oluşturuluyor...")
def yas_segment(yil):
    if yil <= 2:   return 0  # Sıfır/Neredeyse sıfır
    elif yil <= 5: return 1  # Genç
    elif yil <= 10:return 2  # Orta
    elif yil <= 15:return 3  # Yaşlı
    else:          return 4  # Eski

df["yas_segment"] = df["arac_yasi"].apply(yas_segment)

# ── 2. Performans katsayısı ──────────────────────────────────
print("\n[3/6] Performans özellikleri türetiliyor...")

# Güç/hacim oranı zaten var; normalize edilmiş versiyonu
df["guc_hacim_norm"] = (
    (df["guc_hacim_orani"] - df["guc_hacim_orani"].median())
    / (df["guc_hacim_orani"].std() + 1e-9)
).clip(-3, 3)

# Güç segmenti (düşük / orta / yüksek / premium)
def guc_segment(hp):
    if hp < 90:   return 0
    elif hp < 140: return 1
    elif hp < 220: return 2
    else:          return 3

df["guc_segment"] = df["motor_gucu_hp"].apply(guc_segment)

# Motor hacmi segmenti
def hacim_segment(cc):
    if cc < 1000:  return 0  # Mini
    elif cc < 1400:return 1  # Küçük
    elif cc < 1800:return 2  # Orta
    elif cc < 2500:return 3  # Büyük
    else:          return 4  # Premium

df["hacim_segment"] = df["motor_hacmi_cc"].apply(hacim_segment)

# ── 3. Marka popülaritesi ────────────────────────────────────
print("\n[4/6] Marka popülaritesi ve amortisman hesaplanıyor...")

if "marka" in df.columns:
    # İlan sayısına göre popülarite skoru (0–1)
    marka_sayisi = df["marka"].value_counts()
    df["marka_popularite"] = df["marka"].map(marka_sayisi) / marka_sayisi.max()

    # Marka bazlı medyan fiyat (piyasa beklentisi)
    marka_medyan = df.groupby("marka_enc")["fiyat"].median()
    df["marka_medyan_fiyat"] = df["marka_enc"].map(marka_medyan)

    # Amortisman hızı: (medyan - araç fiyatı) / araç yaşı
    df["amortisman_hizi"] = (
        (df["marka_medyan_fiyat"] - df["fiyat"]) / df["arac_yasi"].replace(0, 1)
    ).clip(-500_000, 500_000)

    # Kaydet (uygulama için)
    marka_meta = {
        "popularite": marka_sayisi.to_dict(),
        "medyan": df.groupby("marka")["fiyat"].median().to_dict(),
    }
    with open("marka_meta.pkl", "wb") as fh:
        pickle.dump(marka_meta, fh)
    print("      marka_meta.pkl kaydedildi")
else:
    df["marka_popularite"]  = 0.5
    df["marka_medyan_fiyat"] = df["fiyat"].median()
    df["amortisman_hizi"]    = 0

# ── 4. KM anomali skoru ──────────────────────────────────────
print("\n[5/6] KM anomali skoru hesaplanıyor...")
# Aynı yaştaki araçların ortalama km'si ile karşılaştır
yas_km_medyan = df.groupby("arac_yasi")["yillik_km"].transform("median")
df["km_anomali"] = (df["yillik_km"] - yas_km_medyan) / (df["yillik_km"].std() + 1e-9)
df["km_anomali"] = df["km_anomali"].clip(-3, 3)

# ── 5. Kaydet ────────────────────────────────────────────────
print("\n[6/6] Kaydediliyor...")
YENI_OZELLIKLER = [
    "yas_segment", "guc_hacim_norm", "guc_segment",
    "hacim_segment", "marka_popularite", "km_anomali",
]
print(f"      Eklenen özellik sayısı: {len(YENI_OZELLIKLER)}")
df.to_csv("arabam_features.csv", index=False)
print("✅ Kaydedildi: arabam_features.csv")
print("\n" + "=" * 60)
print("Sıradaki: python3 3_model_egitim.py")
