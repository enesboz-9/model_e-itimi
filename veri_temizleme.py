"""
Araç Fiyat Tahmini — Veri Temizleme v2
Motor bilgileri eklendi, sehir çıkarıldı
"""
import pandas as pd
import numpy as np
import re

print("=" * 55)
print("1. Veri yukleniyor...")
df = pd.read_csv("arabam.com-otomobil-veri-seti-csv.csv")
print(f"   Ham veri: {len(df):,} satir, {df.shape[1]} sutun")

print("\n2. Gereksiz sutunlar kaldirilıyor...")
drop_cols = [
    "listing_id","url","scraped_at","ilan_basligi","ilan_aciklamasi",
    "ilan_tarihi","boya_degisen","model","ilce","sehir",
    "ort_yakit_tuketimi","yakit_deposu",
]
df.drop(columns=drop_cols, inplace=True)
print(f"   Kalan sutun: {df.shape[1]}")

print("\n3. Motor bilgileri isleniyor...")
def parse_hacim(val):
    if pd.isna(val): return np.nan
    val = str(val)
    m = re.search(r'(\d+)\s*cc', val)
    if m: return int(m.group(1))
    m = re.search(r'(\d+)\s*-\s*(\d+)', val)
    if m: return (int(m.group(1)) + int(m.group(2))) // 2
    m = re.search(r'(\d+)', val)
    if m: return int(m.group(1))
    return np.nan

def parse_guc(val):
    if pd.isna(val): return np.nan
    val = str(val)
    m = re.search(r'(\d+)\s*hp', val, re.IGNORECASE)
    if m: return int(m.group(1))
    m = re.search(r'(\d+)\s*-\s*(\d+)', val)
    if m: return (int(m.group(1)) + int(m.group(2))) // 2
    m = re.search(r'(\d+)', val)
    if m: return int(m.group(1))
    return np.nan

df['motor_hacmi_cc'] = df['motor_hacmi'].apply(parse_hacim)
df['motor_gucu_hp']  = df['motor_gucu'].apply(parse_guc)
df.drop(columns=['motor_hacmi','motor_gucu'], inplace=True)
cekis_map = {'Önden Çekiş':0,'Arkadan İtiş':1,'4WD (Sürekli)':2,'AWD (Elektronik)':3,'-':0}
df['cekis_enc'] = df['cekis'].map(cekis_map).fillna(0).astype(int)
df.drop(columns=['cekis'], inplace=True)
print(f"   Motor hacmi: {df['motor_hacmi_cc'].notna().sum():,} dolu")
print(f"   Motor gucu:  {df['motor_gucu_hp'].notna().sum():,} dolu")

print("\n4. Fiyat aykiri degerler temizleniyor...")
before = len(df)
q01, q99 = df["fiyat"].quantile(0.01), df["fiyat"].quantile(0.99)
df = df[(df["fiyat"] >= q01) & (df["fiyat"] <= q99)]
print(f"   Cikarilan: {before-len(df):,} | Kalan: {len(df):,}")
df["fiyat_log"] = np.log1p(df["fiyat"])

print("\n5. KM ve yil temizleniyor...")
before = len(df)
df = df[(df["km"] <= 1_000_000) & (df["yil"] >= 1980) & (df["yil"] <= 2026)]
print(f"   Cikarilan: {before-len(df):,} | Kalan: {len(df):,}")

print("\n6. Yeni ozellikler uretiliyor...")
df["arac_yasi"]       = 2026 - df["yil"]
df["yillik_km"]       = df["km"] / df["arac_yasi"].replace(0, 1)
df["guc_hacim_orani"] = df["motor_gucu_hp"] / df["motor_hacmi_cc"].replace(0, np.nan)

hasar_sutunlari = [
    "sag_arka_camurluk","arka_kaput","sol_arka_camurluk","sag_arka_kapi",
    "sag_on_kapi","tavan","sol_arka_kapi","sol_on_kapi","sag_on_camurluk",
    "motor_kaputu","sol_on_camurluk","on_tampon","arka_tampon"
]
def hasar_puani(row):
    toplam = 0
    for s in hasar_sutunlari:
        d = str(row.get(s,"")).strip()
        if d in ["Boyanmış","Lokal Boyanmış"]: toplam += 1
        elif d == "Değişmiş": toplam += 2
    return toplam
df["hasar_skoru"] = df.apply(hasar_puani, axis=1)
df.drop(columns=hasar_sutunlari, inplace=True)

print("\n7. Eksik degerler dolduruluyor...")
for col in ["motor_hacmi_cc","motor_gucu_hp","guc_hacim_orani"]:
    df[col] = df[col].fillna(df[col].median())
for col in ["agir_hasarli","takasa_uygun","kasa_tipi"]:
    df[col] = df[col].fillna("Bilinmiyor").replace("-","Bilinmiyor")

print("\n8. Kategorik encoding...")
df["kimden_galeri"]     = (df["kimden"] == "Galeriden").astype(int)
df["kimden_bayi"]       = (df["kimden"] == "Yetkili Bayiden").astype(int)
df["agir_hasarli_evet"] = (df["agir_hasarli"] == "Evet").astype(int)
df["takasa_uygun_evet"] = (df["takasa_uygun"] == "Takasa Uygun").astype(int)

from sklearn.preprocessing import LabelEncoder
for col in ["marka","seri","yakit_tipi","vites_tipi","kasa_tipi","renk","arac_durumu"]:
    le = LabelEncoder()
    df[col+"_enc"] = le.fit_transform(df[col].astype(str))

ozellikler = [
    "arac_yasi","km","yillik_km","hasar_skoru",
    "motor_hacmi_cc","motor_gucu_hp","guc_hacim_orani","cekis_enc",
    "kimden_galeri","kimden_bayi","agir_hasarli_evet","takasa_uygun_evet",
    "marka_enc","seri_enc","yakit_tipi_enc","vites_tipi_enc",
    "kasa_tipi_enc","renk_enc","arac_durumu_enc",
]
temiz_df = df[ozellikler + ["fiyat_log","fiyat"]].copy()
temiz_df.to_csv("arabam_temiz.csv", index=False)
print(f"\n   Kaydedildi: arabam_temiz.csv")
print(f"   Final: {len(temiz_df):,} satir, {len(ozellikler)} ozellik")
print("\n" + "="*55)
print("Veri hazirlama tamamlandi! Siradaki: python3 model_egitim.py")
