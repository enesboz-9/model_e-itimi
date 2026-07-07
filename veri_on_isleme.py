"""
MODÜL 1 — Veri Ön İşleme ve Temizleme
Arabam.com ham CSV → arabam_temiz.csv
"""

import pandas as pd
import numpy as np
import re
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

print("=" * 60)
print("MODÜL 1 — Veri Ön İşleme ve Temizleme")
print("=" * 60)

# ── 1. Ham veriyi yükle ──────────────────────────────────────
print("\n[1/8] Ham veri yükleniyor...")
df = pd.read_csv("arabam.com-otomobil-veri-seti-csv.csv", encoding="utf-8-sig", low_memory=False)
print(f"      {len(df):,} satır, {df.shape[1]} sütun")

# ── 2. Gereksiz sütunlar ─────────────────────────────────────
print("\n[2/8] Gereksiz sütunlar kaldırılıyor...")
drop_cols = [
    "listing_id", "url", "scraped_at", "ilan_basligi", "ilan_aciklamasi",
    "ilan_tarihi", "boya_degisen", "model", "ilce",
    "ort_yakit_tuketimi", "yakit_deposu",
]
df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)
print(f"      Kalan sütun: {df.shape[1]}")

# ── 3. Motor bilgilerini parse et ────────────────────────────
print("\n[3/8] Motor bilgileri işleniyor...")

def parse_hacim(val):
    """'1.598 cc', '1600', '1.5 - 1.6' gibi formatları sayıya çevir."""
    if pd.isna(val): return np.nan
    val = str(val).replace(".", "").replace(",", ".")
    m = re.search(r"(\d+)\s*cc", val, re.I)
    if m: return int(m.group(1))
    m = re.search(r"(\d+)\s*-\s*(\d+)", val)
    if m: return (int(m.group(1)) + int(m.group(2))) // 2
    m = re.search(r"(\d+)", val)
    if m: return int(m.group(1))
    return np.nan

def parse_guc(val):
    """'110 hp', '85-110', '110' gibi formatları sayıya çevir."""
    if pd.isna(val): return np.nan
    val = str(val)
    m = re.search(r"(\d+)\s*hp", val, re.I)
    if m: return int(m.group(1))
    m = re.search(r"(\d+)\s*-\s*(\d+)", val)
    if m: return (int(m.group(1)) + int(m.group(2))) // 2
    m = re.search(r"(\d+)", val)
    if m: return int(m.group(1))
    return np.nan

if "motor_hacmi" in df.columns:
    df["motor_hacmi_cc"] = df["motor_hacmi"].apply(parse_hacim)
    df.drop(columns=["motor_hacmi"], inplace=True)
if "motor_gucu" in df.columns:
    df["motor_gucu_hp"] = df["motor_gucu"].apply(parse_guc)
    df.drop(columns=["motor_gucu"], inplace=True)

# Çekiş tipi encode
cekis_map = {"Önden Çekiş": 0, "Arkadan İtiş": 1, "4WD (Sürekli)": 2, "AWD (Elektronik)": 3, "-": 0}
if "cekis" in df.columns:
    df["cekis_enc"] = df["cekis"].map(cekis_map).fillna(0).astype(int)
    df.drop(columns=["cekis"], inplace=True)

print(f"      Motor hacmi dolu: {df['motor_hacmi_cc'].notna().sum():,}")
print(f"      Motor gücü dolu:  {df['motor_gucu_hp'].notna().sum():,}")

# ── 4. Hasar skoru ───────────────────────────────────────────
print("\n[4/8] Hasar skoru hesaplanıyor...")
HASAR_COLS = [
    "sag_arka_camurluk", "arka_kaput", "sol_arka_camurluk",
    "sag_arka_kapi", "sag_on_kapi", "tavan", "sol_arka_kapi",
    "sol_on_kapi", "sag_on_camurluk", "motor_kaputu",
    "sol_on_camurluk", "on_tampon", "arka_tampon",
]
mevcut_hasar = [c for c in HASAR_COLS if c in df.columns]

def hasar_puani(row):
    """Boyanmış=1 puan, Değişmiş=2 puan, Lokal Boyanmış=1 puan."""
    toplam = 0
    for s in mevcut_hasar:
        d = str(row.get(s, "")).strip()
        if d in ("Boyanmış", "Lokal Boyanmış"): toplam += 1
        elif d == "Değişmiş": toplam += 2
    return toplam

df["hasar_skoru"] = df.apply(hasar_puani, axis=1)
df.drop(columns=mevcut_hasar, inplace=True)
print(f"      Hasar skoru aralığı: 0 – {int(df['hasar_skoru'].max())}")

# ── 5. Aykırı değer temizleme (IQR) ─────────────────────────
print("\n[5/8] Aykırı değerler temizleniyor (IQR yöntemi)...")
before = len(df)

# Fiyat: %1 – %99 arası tut
# Alt sınır: %1 (spam/hatalı ilanları at)
# Üst sınır: %99.9 — lüks araçları (Ferrari, Bentley, Rolls-Royce vb.) koru
# 665M TL gibi gerçek aykırıları at ama 50-80M TL lüks ilanları tut
q01  = df["fiyat"].quantile(0.01)
q999 = df["fiyat"].quantile(0.999)
df = df[(df["fiyat"] >= q01) & (df["fiyat"] <= q999)]

# KM: makul üst sınır
df = df[(df["km"] >= 0) & (df["km"] <= 1_000_000)]

# Yıl: 1980–2026
df = df[(df["yil"] >= 1980) & (df["yil"] <= 2026)]

print(f"      Çıkarılan: {before - len(df):,} | Kalan: {len(df):,}")

# Log dönüşümü (sağa çarpık fiyat dağılımı için)
df["fiyat_log"] = np.log1p(df["fiyat"])

# ── 6. Yeni özellikler ───────────────────────────────────────
print("\n[6/8] Temel özellikler üretiliyor...")
df["arac_yasi"]       = 2026 - df["yil"]
df["yillik_km"]       = df["km"] / df["arac_yasi"].replace(0, 1)
df["guc_hacim_orani"] = df["motor_gucu_hp"] / df["motor_hacmi_cc"].replace(0, np.nan)

# ── 7. Eksik değer doldurma ──────────────────────────────────
print("\n[7/8] Eksik değerler dolduruluyor...")

# Kategorikler: en sık değer veya 'Bilinmiyor'
for col in ["agir_hasarli", "takasa_uygun", "kasa_tipi", "renk", "arac_durumu"]:
    if col in df.columns:
        df[col] = df[col].fillna("Bilinmiyor").replace("-", "Bilinmiyor")

# Sayısal: KNN Imputer (k=5)
num_cols = ["motor_hacmi_cc", "motor_gucu_hp", "guc_hacim_orani"]
mevcut_num = [c for c in num_cols if c in df.columns]
if mevcut_num:
    imputer = KNNImputer(n_neighbors=5)
    df[mevcut_num] = imputer.fit_transform(df[mevcut_num])
    print(f"      KNN Imputer uygulandı: {mevcut_num}")

# ── 8. Kategorik Encoding ────────────────────────────────────
print("\n[8/8] Kategorik encoding yapılıyor...")

df["kimden_galeri"]     = (df["kimden"] == "Galeriden").astype(int)
df["kimden_bayi"]       = (df["kimden"] == "Yetkili Bayiden").astype(int)
df["agir_hasarli_evet"] = (df["agir_hasarli"] == "Evet").astype(int)
df["takasa_uygun_evet"] = (df["takasa_uygun"] == "Takasa Uygun").astype(int)

for col in ["marka", "seri", "yakit_tipi", "vites_tipi", "kasa_tipi", "renk", "arac_durumu"]:
    if col in df.columns:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col].astype(str))

OZELLIKLER = [
    "arac_yasi", "km", "yillik_km", "hasar_skoru",
    "motor_hacmi_cc", "motor_gucu_hp", "guc_hacim_orani", "cekis_enc",
    "kimden_galeri", "kimden_bayi", "agir_hasarli_evet", "takasa_uygun_evet",
    "marka_enc", "seri_enc", "yakit_tipi_enc", "vites_tipi_enc",
    "kasa_tipi_enc", "renk_enc", "arac_durumu_enc",
]
mevcut_oz = [c for c in OZELLIKLER if c in df.columns]

# Ham metin sütunları da sakla (uygulama için)
METIN_COLS = ["marka", "seri", "yakit_tipi", "vites_tipi", "kasa_tipi", "renk", "arac_durumu", "sehir", "kimden"]
mevcut_metin = [c for c in METIN_COLS if c in df.columns]

temiz_df = df[mevcut_oz + mevcut_metin + ["fiyat_log", "fiyat", "yil"]].copy()
temiz_df.to_csv("arabam_temiz.csv", index=False)
print(f"\n✅ Kaydedildi: arabam_temiz.csv")
print(f"   Final: {len(temiz_df):,} satır, {len(mevcut_oz)} özellik")
print("\n" + "=" * 60)
print("Sıradaki: python3 2_feature_engineering.py")
