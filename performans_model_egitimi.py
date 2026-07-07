"""
MODÜL — Performans Analizi Modeli — Eğitim
performans_veri_seti.csv (+ performans_veri_seti_optimize.csv) içindeki
araç kullanım senaryosu verilerinden (yol tipi, hava durumu, trafik,
sürücü deneyimi, lastik/araç durumu vb.) yola çıkarak, seçilen marka/model
ve senaryo için bir "Performans Skoru" (0-100) tahmin eden bir regresyon
modeli eğitir. Ayrıca marka/model bazlı gerçek veri özet istatistiklerini
(ortalama yakıt tüketimi, güvenlik notu, motor performansı, konfor,
emisyon, güvenilirlik vb.) çıkarır.

Hedef değişken (performans_skoru), veri setindeki ölçüm sütunlarından
(Engine_Performance, Braking_Performance, Comfort_Rating, Suspension_
Performance, Acceleration, Safety_Rating, Scenario_Adaptability,
Fuel_Efficiency, Emissions) türetilen ağırlıklı bir bileşik skordur.
Bu sütunlar hedefin BİLEŞENİ olduğu için özellik (feature) olarak
kullanılmaz — model bunun yerine aracın kimliği (marka/model/motor tipi)
ve KULLANIM SENARYOSU bilgilerinden (yol tipi, hava, trafik, sıcaklık,
sürücü deneyimi, araç/lastik durumu, fiyat) skoru tahmin etmeyi öğrenir.

Çıktı:
  performans_model.pkl      -> {"model": RandomForestRegressor, "kolonlar": [...],
                                 "one_hot_kategoriler": {...}}
  performans_meta.pkl       -> test metrikleri, feature importance, marka/model listesi
  performans_ozet.pkl       -> {(marka, model): {özet istatistikler}}  (gerçek veriden)
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

RANDOM_STATE = 42

print("=" * 60)
print("1. Performans veri setleri yukleniyor...")
df = pd.read_csv("performans_veri_seti.csv")
df_opt = pd.read_csv("performans_veri_seti_optimize.csv")
print(f"   Ana veri seti : {len(df):,} satir, {df['Car_Brand'].nunique()} marka, "
      f"{df.groupby(['Car_Brand','Model']).ngroups} marka/model kombinasyonu")
print(f"   Optimize veri : {len(df_opt):,} satir (Reliability / Electric_Range icin)")

# ──────────────────────────────────────────────────────────────
# 2. Bilesik "Performans Skoru" (0-100) hesapla
# ──────────────────────────────────────────────────────────────
print("\n2. Bilesik performans skoru turetiliyor...")

def normalize(seri, ters=False):
    """Bir sutunu 0-100 araligina olcekler. ters=True ise dusuk deger iyi demektir
    (orn. emisyon) ve olcek ters cevrilir."""
    s = seri.astype(float)
    if s.max() == s.min():
        return pd.Series(50.0, index=s.index)
    norm = (s - s.min()) / (s.max() - s.min()) * 100
    return (100 - norm) if ters else norm

df["_n_engine"]   = normalize(df["Engine_Performance"])
df["_n_braking"]  = normalize(df["Braking_Performance"])
df["_n_comfort"]  = normalize(df["Comfort_Rating"])
df["_n_suspans"]  = normalize(df["Suspension_Performance"])
df["_n_accel"]    = normalize(df["Acceleration"], ters=True)   # dusuk 0-60 suresi = iyi
df["_n_safety"]   = normalize(df["Safety_Rating"])
df["_n_adapt"]    = normalize(df["Scenario_Adaptability"])
df["_n_fuel"]     = normalize(df["Fuel_Efficiency"])
df["_n_emisyon"]  = normalize(df["Emissions"], ters=True)

AGIRLIKLAR = {
    "_n_engine":  0.20, "_n_braking": 0.12, "_n_comfort": 0.12,
    "_n_suspans": 0.10, "_n_accel":   0.10, "_n_safety":  0.15,
    "_n_adapt":   0.11, "_n_fuel":    0.05, "_n_emisyon": 0.05,
}
df["performans_skoru"] = sum(df[k] * w for k, w in AGIRLIKLAR.items())
df["performans_skoru"] = df["performans_skoru"].clip(0, 100)
print(f"   Skor araligi: {df['performans_skoru'].min():.1f} - {df['performans_skoru'].max():.1f}"
      f"  (ortalama: {df['performans_skoru'].mean():.1f})")

# ──────────────────────────────────────────────────────────────
# 3. Özellik (feature) seti — SADECE kimlik + senaryo bilgileri
#    (skorun bilesenleri feature olarak KULLANILMAZ, veri sizintisi olur)
# ──────────────────────────────────────────────────────────────
KATEGORIK_KOLONLAR = [
    "Car_Brand", "Model", "Engine_Type", "Driving_Condition",
    "Road_Type", "Traffic_Level", "Weather_Condition",
    "Vehicle_Condition", "Tire_Condition", "Driver_Experience",
    "Performance_Optimization",
]
SAYISAL_KOLONLAR = ["Temperature", "Price"]

egitim_df = df[KATEGORIK_KOLONLAR + SAYISAL_KOLONLAR + ["performans_skoru"]].copy()
egitim_df_encoded = pd.get_dummies(egitim_df, columns=KATEGORIK_KOLONLAR)

X = egitim_df_encoded.drop(columns=["performans_skoru"])
y = egitim_df_encoded["performans_skoru"]
kolonlar = list(X.columns)

print(f"\n3. Egitim tablosu hazir: {X.shape[0]} satir, {X.shape[1]} ozellik "
      f"(one-hot sonrasi)")

# ──────────────────────────────────────────────────────────────
# 4. Model egitimi
# ──────────────────────────────────────────────────────────────
print("\n4. RandomForestRegressor egitiliyor...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE
)

model = RandomForestRegressor(
    n_estimators=300,
    max_depth=8,
    min_samples_leaf=3,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
model.fit(X_train, y_train)

pred = model.predict(X_test)
mae = mean_absolute_error(y_test, pred)
r2 = r2_score(y_test, pred)
print(f"   Test MAE : {mae:.2f} puan (0-100 olcek)")
print(f"   Test R²  : {r2:.3f}")

feature_imp = pd.Series(model.feature_importances_, index=kolonlar) \
    .sort_values(ascending=False)
print("\n   En onemli 10 ozellik:")
print(feature_imp.head(10).to_string())

with open("performans_model.pkl", "wb") as f:
    pickle.dump({"model": model, "kolonlar": kolonlar}, f)

meta = {
    "test_metrikleri": {"mae": float(mae), "r2": float(r2)},
    "feature_imp": feature_imp.head(15).to_dict(),
    "markalar": sorted(df["Car_Brand"].unique().tolist()),
    "agirliklar": AGIRLIKLAR,
    "kategorik_kolonlar": KATEGORIK_KOLONLAR,
    "sayisal_kolonlar": SAYISAL_KOLONLAR,
    "kaynak": "car_performance_dataset.csv (senaryo bazli arac performans veri seti)",
}
with open("performans_meta.pkl", "wb") as f:
    pickle.dump(meta, f)

print("\n✅ performans_model.pkl ve performans_meta.pkl yazildi.")

# ──────────────────────────────────────────────────────────────
# 5. Marka/Model bazli GERCEK veri ozeti (ML degil, dogrudan agregasyon)
# ──────────────────────────────────────────────────────────────
print("\n5. Marka/model bazinda ozet istatistikler cikariliyor...")

# optimize veri setinden guvenilirlik + elektrikli menzil ortalamalarini al
opt_ozet = df_opt.groupby(["Car_Brand", "Model"]).agg(
    guvenilirlik_ort=("Reliability", "mean"),
    elektrik_menzil_ort=("Electric_Range", "mean"),
).reset_index()

ozet_sozluk = {}
for (marka, mdl), grp in df.groupby(["Car_Brand", "Model"]):
    opt_satir = opt_ozet[(opt_ozet["Car_Brand"] == marka) & (opt_ozet["Model"] == mdl)]
    guvenilirlik = float(opt_satir["guvenilirlik_ort"].iloc[0]) if len(opt_satir) else None
    elektrik_menzil = (
        float(opt_satir["elektrik_menzil_ort"].iloc[0])
        if len(opt_satir) and pd.notna(opt_satir["elektrik_menzil_ort"].iloc[0])
        else None
    )
    ozet_sozluk[(marka, mdl)] = {
        "adet": int(len(grp)),
        "yakit_tuketimi_ort": float(grp["Fuel_Efficiency"].mean()),
        "guvenlik_notu_ort": float(grp["Safety_Rating"].mean()),
        "motor_performansi_ort": float(grp["Engine_Performance"].mean()),
        "frenleme_ort": float(grp["Braking_Performance"].mean()),
        "konfor_ort": float(grp["Comfort_Rating"].mean()),
        "emisyon_ort": float(grp["Emissions"].mean()),
        "0_100_ort": float(grp["Acceleration"].mean()),
        "suspansiyon_ort": float(grp["Suspension_Performance"].mean()),
        "senaryo_uyum_ort": float(grp["Scenario_Adaptability"].mean()),
        "fiyat_min": float(grp["Price"].min()),
        "fiyat_ort": float(grp["Price"].mean()),
        "fiyat_max": float(grp["Price"].max()),
        "performans_skoru_ort": float(grp["performans_skoru"].mean()),
        "guvenilirlik_ort": guvenilirlik,
        "elektrik_menzil_ort": elektrik_menzil,
        "en_yaygin_motor_tipi": grp["Engine_Type"].mode().iat[0] if not grp["Engine_Type"].mode().empty else None,
    }

with open("performans_ozet.pkl", "wb") as f:
    pickle.dump(ozet_sozluk, f)

print(f"   {len(ozet_sozluk)} marka/model kombinasyonu icin ozet cikarildi.")
print("✅ performans_ozet.pkl yazildi.")

print("\n" + "=" * 60)
print("TAMAMLANDI — Ornek ozet (Toyota, Corolla):")
print(ozet_sozluk.get(("Toyota", "Corolla")))
