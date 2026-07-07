"""
Motor Veri Seti — Temizleme
"Engine Data.xlsx" (mymotorlist.com kaynaklı, 1024 sütunlu ham kazıma verisi)
içinden kullanılabilir motor bilgilerini çıkarıp tek, temiz bir tabloya indirger.

Çıktı: motor_verisi_temiz.csv
Sütunlar:
    marka, motor_kodu, uretim_yillari, hacim_cc, guc_hp, tork_nm,
    yakit_tipi, silindir_konf, silindir_sayisi, blok_malzemesi,
    turbo, kompresyon_orani, tavsiye_edilen_yag, yag_kapasitesi_l,
    motor_omru_km, agirlik_kg, euro_standardi
"""
import pandas as pd
import numpy as np
import re

print("=" * 55)
print("1. Motor veri seti yukleniyor...")
df = pd.read_excel("Engine_Data.xlsx")
print(f"   Ham veri: {len(df):,} satir, {df.shape[1]} sutun")

# ──────────────────────────────────────────────────────────────
# 2. Marka + motor kodu, "Title" alanindan cikariliyor
#    Format: "Engine <Marka> <Kod>"  (bazen marka iki kelimeli)
# ──────────────────────────────────────────────────────────────
print("\n2. Marka / motor kodu ayristiriliyor...")

# arabam.com / uygulamadaki MARKA_ENC ile hizalanmis marka esleme sozlugu.
# Anahtar: motor veri setindeki ham marka ifadesi (kucuk harf) -> uygulama marka adi
MARKA_ESLEME = {
    "alfa romeo": "Alfa Romeo", "audi": "Audi", "bmw": "BMW",
    "chevrolet": "Chevrolet", "chrysler": "Chrysler", "daewoo": "Daewoo",
    "dodge": "Dodge", "fiat": "Fiat", "ford": "Ford", "geely": "Geely",
    "great wall": "Geely",  # Great Wall app listesinde yok; en yakin grup disi birak
    "honda": "Honda", "hyundai": "Hyundai", "hyundai-kia": "Hyundai",
    "hyundai-genesis": "Hyundai", "jaguar": "Jaguar", "jeep": "Jeep",
    "kia": "Kia", "land rover": "Land Rover", "mazda": "Mazda",
    "mercedes": "Mercedes - Benz", "mercedes-benz": "Mercedes - Benz",
    "mini": "Mini", "mitsubishi": "Mitsubishi", "nissan": "Nissan",
    "opel": "Opel", "peugeot": "Peugeot", "porsche": "Porsche",
    "renault": "Renault", "rover": "Rover", "saab": "Saab",
    "ssangyong": "SsangYong", "subaru": "Subaru", "suzuki": "Suzuki",
    "toyota": "Toyota", "volkswagen": "Volkswagen", "volvo": "Volvo",
    "isuzu": "Isuzu", "gm": "Chevrolet", "daf": "DAF", "man": "MAN",
    "scania": "Scania", "cummins": "Cummins", "caterpillar": "Caterpillar",
    "kamaz": "KamAZ", "mmz": "MMZ",
}
# Uzun (coklu kelime) markalar once denenmeli
_MARKA_ANAHTAR = sorted(MARKA_ESLEME.keys(), key=len, reverse=True)


def marka_kod_ayikla(title):
    """'Engine Audi BDW' -> ('Audi', 'BDW')"""
    t = str(title).replace("Engine", "", 1).strip()
    t_low = t.lower()
    for anahtar in _MARKA_ANAHTAR:
        if t_low.startswith(anahtar):
            marka = MARKA_ESLEME[anahtar]
            kod = t[len(anahtar):].strip()
            return marka, kod if kod else None
    # eslesme yoksa ilk kelimeyi marka kabul et
    parcalar = t.split(None, 1)
    if len(parcalar) == 2:
        return parcalar[0], parcalar[1]
    return (parcalar[0] if parcalar else None), None


ayiklanan = df["Title"].apply(marka_kod_ayikla)
df["marka"] = [a[0] for a in ayiklanan]
df["motor_kodu"] = [a[1] for a in ayiklanan]
print(f"   Taninan marka sayisi: {df['marka'].isin(MARKA_ESLEME.values()).sum():,} / {len(df):,}")

# Sadece bilinen (uygulamadaki marka listesiyle eslesen) markalari tut —
# aksi halde eslesmeyen/gurultulu satirlar yanlis eslestirme yapar
df = df[df["marka"].isin(set(MARKA_ESLEME.values()))].copy()
print(f"   Bilinen markalarla kalan satir: {len(df):,}")


# ──────────────────────────────────────────────────────────────
# 3. Sayisal alanlarin ayiklanmasi ("116 /5500 rpm", "177 - 218" gibi)
# ──────────────────────────────────────────────────────────────
def ilk_sayi(val):
    """'116 /5500 rpm' -> 116.0 ; '177 - 218' -> 197.5 (ortalama) ; '256' -> 256.0"""
    if pd.isna(val):
        return np.nan
    s = str(val).replace(",", ".")
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    m = re.match(r"\s*(\d+(?:\.\d+)?)", s)
    if m:
        return float(m.group(1))
    return np.nan


print("\n3. Sayisal motor degerleri ayikliniyor...")
df["hacim_cc"] = df["displacement, cc"].apply(ilk_sayi)
df["guc_hp"] = df["power output, hp"].apply(ilk_sayi)
df["tork_nm"] = df["torque output, nm"].apply(ilk_sayi)
df["yag_kapasitesi_l"] = df["engine oil capacity, liter"].apply(ilk_sayi)
df["agirlik_kg"] = df["weight, kg"].apply(ilk_sayi)


def kompresyon_ayikla(val):
    if pd.isna(val):
        return np.nan
    m = re.match(r"\s*(\d+(?:[.,]\d+)?)", str(val).replace(",", "."))
    return float(m.group(1)) if m else np.nan


df["kompresyon_orani"] = df["compression ratio"].apply(kompresyon_ayikla)


def km_ayikla(val):
    """'~280 000' -> 280000"""
    if pd.isna(val):
        return np.nan
    s = re.sub(r"[^\d]", "", str(val))
    return float(s) if s else np.nan


df["motor_omru_km"] = df["engine lifespan, km"].apply(km_ayikla)

# ──────────────────────────────────────────────────────────────
# 4. Blok / silindir bilgisi ("aluminum v6" -> malzeme + konfig + sayi)
# ──────────────────────────────────────────────────────────────
print("\n4. Silindir/blok bilgisi cikariliyor...")
KONF_HARITASI = {"r": "Sıra (Inline)", "v": "V", "h": "Boxer (H)", "w": "W", "vr": "VR"}


def blok_ayikla(val):
    if pd.isna(val):
        return pd.Series([np.nan, np.nan, np.nan])
    s = str(val).lower()
    malzeme = "Alüminyum" if "alumin" in s else ("Dökme Demir" if "cast" in s else np.nan)
    m = re.search(r"\b(vr|[rvhw])\s?(\d{1,2})\b", s)
    if m:
        konf = KONF_HARITASI.get(m.group(1), m.group(1).upper())
        silindir = int(m.group(2))
        return pd.Series([malzeme, konf, silindir])
    return pd.Series([malzeme, np.nan, np.nan])


df[["blok_malzemesi", "silindir_konf", "silindir_sayisi"]] = df["cylinder block"].apply(blok_ayikla)

# ──────────────────────────────────────────────────────────────
# 5. Yakit tipi normalizasyonu
# ──────────────────────────────────────────────────────────────
def yakit_normalize(val):
    if pd.isna(val):
        return np.nan
    s = str(val).lower()
    if "diesel" in s:
        return "Dizel"
    if "petrol" in s or "gasoline" in s:
        return "Benzin"
    if re.match(r"^\d+(\.\d+)?$", s.strip()):  # sadece oktan sayisi (95, 98..) -> benzin
        return "Benzin"
    return np.nan


df["yakit_tipi"] = df["fuel type"].apply(yakit_normalize)


def turbo_normalize(val):
    if pd.isna(val):
        return "Bilinmiyor"
    s = str(val).lower().strip()
    if s == "no":
        return "Hayır (Atmosferik)"
    return "Evet"


df["turbo"] = df["turbocharging"].apply(turbo_normalize)

# ──────────────────────────────────────────────────────────────
# 6. Son tablo
# ──────────────────────────────────────────────────────────────
FINAL_COLS = [
    "marka", "motor_kodu", "production years", "hacim_cc", "guc_hp", "tork_nm",
    "yakit_tipi", "silindir_konf", "silindir_sayisi", "blok_malzemesi", "turbo",
    "kompresyon_orani", "recommended engine oil", "yag_kapasitesi_l",
    "motor_omru_km", "agirlik_kg", "euro standards",
]
df_final = df[FINAL_COLS].rename(columns={
    "production years": "uretim_yillari",
    "recommended engine oil": "tavsiye_edilen_yag",
    "euro standards": "euro_standardi",
})

# Hacim veya guc bilgisi olmayan satirlarin eslestirmede kullanim degeri yok
before = len(df_final)
df_final = df_final.dropna(subset=["hacim_cc", "guc_hp"], how="all")
print(f"\n5. Hacim+guc ikisi de bos olan satirlar cikarildi: {before - len(df_final):,}")

df_final = df_final.drop_duplicates(subset=["marka", "motor_kodu", "hacim_cc", "guc_hp"])
df_final.to_csv("motor_verisi_temiz.csv", index=False)

print(f"\n✅ motor_verisi_temiz.csv yazildi: {len(df_final):,} satir, {df_final.shape[1]} sutun")
print(df_final["marka"].value_counts())
