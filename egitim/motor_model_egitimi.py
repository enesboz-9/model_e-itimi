"""
Motor Eşleştirme Modeli — Eğitim
Kullanıcının girdiği (marka, motor hacmi cc, motor gücü hp) bilgisine göre,
motor_verisi_temiz.csv içindeki en yakın gerçek motor kaydını bulan bir
K-En Yakın Komşu (KNN) modeli eğitir. Her marka için ayrı bir model kurulur,
çünkü eşleştirme sadece aynı marka içinde anlamlıdır.

Çıktı: motor_model.pkl  -> {marka: {"knn": NearestNeighbors, "scaler": StandardScaler,
                                     "veri": DataFrame}}
       motor_model_meta.pkl -> genel istatistikler / marka listesi
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

print("=" * 55)
print("1. Temiz motor verisi yukleniyor...")
df = pd.read_csv("motor_verisi_temiz.csv")
print(f"   {len(df):,} satir, markalar: {df['marka'].nunique()}")

print("\n2. Marka basina KNN modeli egitiliyor (hacim_cc + guc_hp)...")
modeller = {}
atlanan = []

for marka, grup in df.groupby("marka"):
    grup = grup.dropna(subset=["hacim_cc", "guc_hp"]).reset_index(drop=True)
    if len(grup) < 1:
        atlanan.append(marka)
        continue

    X = grup[["hacim_cc", "guc_hp"]].values.astype(float)
    scaler = StandardScaler()
    # Tek ornekli markalarda std=0 olabilir; StandardScaler bunu 1'e sabitler
    if len(grup) == 1:
        Xs = X - X.mean(axis=0)
    else:
        Xs = scaler.fit_transform(X)

    n_neighbors = min(3, len(grup))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
    knn.fit(Xs)

    modeller[marka] = {
        "knn": knn,
        "scaler": scaler if len(grup) > 1 else None,
        "veri": grup,
    }

print(f"   Egitilen marka sayisi: {len(modeller)}")
if atlanan:
    print(f"   Atlanan (yetersiz veri): {atlanan}")

with open("motor_model.pkl", "wb") as f:
    pickle.dump(modeller, f)

meta = {
    "markalar": sorted(modeller.keys()),
    "toplam_motor_kaydi": len(df),
    "kaynak": "mymotorlist.com (Engine Data.xlsx)",
}
with open("motor_model_meta.pkl", "wb") as f:
    pickle.dump(meta, f)

print(f"\n✅ motor_model.pkl ve motor_model_meta.pkl yazildi ({len(modeller)} marka).")


# ──────────────────────────────────────────────────────────────
# Hizli test
# ──────────────────────────────────────────────────────────────
def motor_bul(marka, hacim_cc, guc_hp, model_sozluk):
    if marka not in model_sozluk:
        return None
    kayit = model_sozluk[marka]
    knn, scaler, veri = kayit["knn"], kayit["scaler"], kayit["veri"]
    x = np.array([[hacim_cc, guc_hp]], dtype=float)
    xs = scaler.transform(x) if scaler is not None else x - veri[["hacim_cc", "guc_hp"]].values.mean(axis=0)
    mesafe, idx = knn.kneighbors(xs, n_neighbors=1)
    en_yakin = veri.iloc[idx[0][0]]
    return en_yakin, mesafe[0][0]

print("\n--- Test: BMW, 2000cc, 190hp ---")
sonuc = motor_bul("BMW", 2000, 190, modeller)
if sonuc:
    kayit, mesafe = sonuc
    print(kayit[["motor_kodu", "hacim_cc", "guc_hp", "yakit_tipi", "uretim_yillari"]])
    print(f"Mesafe skoru: {mesafe:.3f}")
