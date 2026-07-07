"""
MODÜL — Performans Analizi — Veri Özeti Çıkarma
performans_veri_seti.csv (+ performans_veri_seti_optimize.csv) içindeki
gerçek ölçüm değerlerinden, marka/model bazında ortalama istatistikler
(özet) çıkarır.

NOT: Önceki sürümde burada ayrıca senaryo bilgilerinden (yol tipi, hava
durumu, trafik vb.) bir "performans skoru" tahmin eden bir regresyon
modeli de eğitiliyordu. Veri seti sadece 500 satır ve büyük ölçüde
rastgele/senaryo tabanlı olduğu için o modelin test R² değeri ~0'a
yakındı — yani gerçekçi bir tahminde bulunmuyordu. Kullanıcıyı yanlış
yönlendirmemek için bu skor tahmini tamamen kaldırıldı. Uygulama artık
sadece veri setindeki GERÇEK ortalama değerleri (agregasyon) gösteriyor;
uydurma bir "skor" üretmiyor.

Çıktı:
  performans_ozet.pkl -> {(marka, model): {özet istatistikler}}
"""
import pandas as pd
import pickle

print("=" * 60)
print("1. Performans veri setleri yukleniyor...")
df = pd.read_csv("performans_veri_seti.csv")
df_opt = pd.read_csv("performans_veri_seti_optimize.csv")
print(f"   Ana veri seti : {len(df):,} satir, {df['Car_Brand'].nunique()} marka, "
      f"{df.groupby(['Car_Brand','Model']).ngroups} marka/model kombinasyonu")
print(f"   Optimize veri : {len(df_opt):,} satir (Guvenilirlik / Elektrikli Menzil icin)")

# ──────────────────────────────────────────────────────────────
# Marka/Model bazli GERCEK veri ozeti (dogrudan agregasyon, ML yok)
# ──────────────────────────────────────────────────────────────
print("\n2. Marka/model bazinda ozet istatistikler cikariliyor...")

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
