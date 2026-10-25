"""
model_yeniden_egit.py
─────────────────────
Tam pipeline: arabam_temiz.csv → feature engineering → model eğitimi
Çıktılar: model.pkl + model_meta.pkl  (uygulama.py ile uyumlu)

Kullanım:
    python model_yeniden_egit.py
    python model_yeniden_egit.py --hizli      # Optuna'yı atla, hızlı eğit
"""

import argparse
import pickle
import time
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# ─── Argüman ────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--hizli", action="store_true",
                    help="Optuna'yı atla, varsayılan parametrelerle hızlı eğit")
args = parser.parse_args()

# ─── Optuna (isteğe bağlı) ──────────────────────────────────────────────────
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_VAR = True and not args.hizli
except ImportError:
    OPTUNA_VAR = False

SEP = "=" * 60

# ════════════════════════════════════════════════════════════════
# BÖLÜM 1 — VERİ YÜKLE
# ════════════════════════════════════════════════════════════════
print(SEP)
print("ADIM 1 — Veri yükleniyor")
print(SEP)

try:
    df = pd.read_csv("arabam_temiz.csv", encoding="utf-8-sig", low_memory=False)
    print(f"✅ arabam_temiz.csv yüklendi: {len(df):,} satır")
except FileNotFoundError:
    print("❌ arabam_temiz.csv bulunamadı!")
    print("   Önce veri_on_isleme.py çalıştır: python veri_on_isleme.py")
    raise SystemExit(1)

# Hedef sütun kontrolü
if "fiyat_log" not in df.columns:
    if "fiyat" in df.columns:
        print("   fiyat_log sütunu yok, fiyat'tan türetiliyor...")
        df["fiyat_log"] = np.log1p(df["fiyat"])
    else:
        print("❌ 'fiyat' veya 'fiyat_log' sütunu bulunamadı!")
        raise SystemExit(1)

# ════════════════════════════════════════════════════════════════
# BÖLÜM 2 — FEATURE ENGINEERING (6 yeni özellik)
# ════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("ADIM 2 — Feature Engineering")
print(SEP)

# 1. Yaş segmenti
def yas_segment(y):
    return 0 if y <= 2 else 1 if y <= 5 else 2 if y <= 10 else 3 if y <= 15 else 4

df["yas_segment"] = df["arac_yasi"].apply(yas_segment)
print("✅ yas_segment")

# 2. Güç/Hacim normalize
guc_hacim_median = df["guc_hacim_orani"].median()
guc_hacim_std    = df["guc_hacim_orani"].std()
df["guc_hacim_norm"] = (
    (df["guc_hacim_orani"] - guc_hacim_median) / (guc_hacim_std + 1e-9)
).clip(-3, 3)
print(f"✅ guc_hacim_norm  (median={guc_hacim_median:.4f}, std={guc_hacim_std:.4f})")

# 3. Güç segmenti
def guc_segment(hp):
    return 0 if hp < 90 else 1 if hp < 140 else 2 if hp < 220 else 3

df["guc_segment"] = df["motor_gucu_hp"].apply(guc_segment)
print("✅ guc_segment")

# 4. Motor hacmi segmenti
def hacim_segment(cc):
    return 0 if cc < 1000 else 1 if cc < 1400 else 2 if cc < 1800 else 3 if cc < 2500 else 4

df["hacim_segment"] = df["motor_hacmi_cc"].apply(hacim_segment)
print("✅ hacim_segment")

# 5. Marka popülaritesi
if "marka" in df.columns:
    marka_sayisi = df["marka"].value_counts()
    df["marka_popularite"] = df["marka"].map(marka_sayisi) / marka_sayisi.max()
    # marka_meta.pkl kaydet (uygulama için)
    marka_meta = {
        "popularite": marka_sayisi.to_dict(),
        "medyan": df.groupby("marka")["fiyat"].median().to_dict() if "fiyat" in df.columns else {},
    }
    with open("marka_meta.pkl", "wb") as fh:
        pickle.dump(marka_meta, fh)
    print("✅ marka_popularite  →  marka_meta.pkl kaydedildi")
else:
    df["marka_popularite"] = 0.5
    print("⚠️  marka sütunu yok, marka_popularite=0.5 sabit atandı")

# 6. KM anomali skoru
yas_km_medyan = df.groupby("arac_yasi")["yillik_km"].transform("median")
df["km_anomali"] = (
    (df["yillik_km"] - yas_km_medyan) / (df["yillik_km"].std() + 1e-9)
).clip(-3, 3)
print("✅ km_anomali")

# ════════════════════════════════════════════════════════════════
# BÖLÜM 3 — ÖZELLİK SEÇİMİ
# ════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("ADIM 3 — Özellik seçimi")
print(SEP)

OZELLIKLER = [
    # Temel özellikler
    "arac_yasi", "km", "yillik_km", "hasar_skoru",
    "motor_hacmi_cc", "motor_gucu_hp", "guc_hacim_orani", "cekis_enc",
    "kimden_galeri", "kimden_bayi", "agir_hasarli_evet", "takasa_uygun_evet",
    "marka_enc", "seri_enc", "yakit_tipi_enc", "vites_tipi_enc",
    "kasa_tipi_enc", "renk_enc", "arac_durumu_enc",
    # Feature engineering
    "yas_segment", "guc_hacim_norm", "guc_segment",
    "hacim_segment", "marka_popularite", "km_anomali",
]

mevcut = [c for c in OZELLIKLER if c in df.columns]
eksik   = [c for c in OZELLIKLER if c not in df.columns]

print(f"✅ Kullanılacak özellik: {len(mevcut)}")
if eksik:
    print(f"⚠️  Veri setinde bulunmayan (atlandı): {eksik}")

X = df[mevcut].copy()
y = df["fiyat_log"].copy()

# NaN kontrolü
nan_sayisi = X.isna().sum().sum()
if nan_sayisi > 0:
    print(f"   {nan_sayisi} NaN değeri medyan ile dolduruluyor...")
    X = X.fillna(X.median())

# ════════════════════════════════════════════════════════════════
# BÖLÜM 4 — VERİ BÖLME
# ════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("ADIM 4 — Train / Val / Test ayrımı (%70 / %15 / %15)")
print(SEP)

X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=42)

print(f"   Train : {len(X_train):,}")
print(f"   Val   : {len(X_val):,}")
print(f"   Test  : {len(X_test):,}")

# ════════════════════════════════════════════════════════════════
# BÖLÜM 5 — HİPERPARAMETRE OPTİMİZASYONU
# ════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("ADIM 5 — Hiperparametre optimizasyonu")
print(SEP)

def degerlendır(y_gercek, y_tahmin, ad=""):
    yg = np.expm1(y_gercek)
    yt = np.expm1(y_tahmin)
    mae  = mean_absolute_error(yg, yt)
    rmse = np.sqrt(mean_squared_error(yg, yt))
    r2   = r2_score(yg, yt)
    mape = np.mean(np.abs((yg - yt) / (yg + 1))) * 100
    print(f"\n   [{ad}]")
    print(f"   MAE  : {mae:>12,.0f} TL")
    print(f"   RMSE : {rmse:>12,.0f} TL")
    print(f"   MAPE : {mape:>11.1f} %")
    print(f"   R²   : {r2:>12.4f}")
    return {"mae": mae, "rmse": rmse, "mape": mape, "r2": r2}

if OPTUNA_VAR:
    print("   Optuna ile 40 deneme yapılıyor...")

    def objective(trial):
        params = {
            "n_estimators"    : trial.suggest_int("n_estimators", 400, 1200),
            "learning_rate"   : trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
            "max_depth"       : trial.suggest_int("max_depth", 4, 9),
            "subsample"       : trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 3, 15),
            "reg_alpha"       : trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
            "reg_lambda"      : trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
            "random_state"    : 42,
            "n_jobs"          : -1,
            "device"          : "cpu",
        }
        m = xgb.XGBRegressor(**params)
        m.fit(X_train, y_train,
              eval_set=[(X_val, y_val)],
              verbose=False)
        pred = m.predict(X_val)
        return mean_absolute_error(np.expm1(y_val), np.expm1(pred))

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=40, show_progress_bar=True)
    best_params = study.best_params
    best_params["random_state"] = 42
    best_params["n_jobs"]       = -1
    best_params["device"]       = "cpu"
    print(f"\n   En iyi MAE (val): {study.best_value:,.0f} TL")
    print(f"   En iyi parametreler: {best_params}")
else:
    print("   Varsayılan parametreler kullanılıyor (--hizli modu veya Optuna yok)")
    best_params = {
        "n_estimators": 1000, "learning_rate": 0.05, "max_depth": 7,
        "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 5,
        "reg_alpha": 0.1, "reg_lambda": 1.0,
        "random_state": 42, "n_jobs": -1, "device": "cpu",
    }

# ════════════════════════════════════════════════════════════════
# BÖLÜM 6 — FİNAL MODEL EĞİTİMİ
# ════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("ADIM 6 — Final model eğitimi")
print(SEP)

start = time.time()
model = xgb.XGBRegressor(**best_params)
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=200,
)
sure = time.time() - start
print(f"\n   Eğitim süresi: {sure:.1f}s")

# ────────────────────────────────────────────────────────────────
# Değerlendirme
# ────────────────────────────────────────────────────────────────
tr_m = degerlendır(y_train, model.predict(X_train), "TRAIN")
vl_m = degerlendır(y_val,   model.predict(X_val),   "VALIDATION")
ts_m = degerlendır(y_test,  model.predict(X_test),  "TEST")

# Feature importance
print("\n   En önemli 10 özellik:")
imp = pd.Series(model.feature_importances_, index=mevcut).sort_values(ascending=False)
for i, (feat, skor) in enumerate(imp.head(10).items(), 1):
    bar = "█" * int(skor * 400)
    print(f"   {i:2}. {feat:<26} {bar} ({skor:.4f})")

# ════════════════════════════════════════════════════════════════
# BÖLÜM 7 — KAYDET
# ════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("ADIM 7 — Kaydediliyor")
print(SEP)

# model.pkl
with open("model.pkl", "wb") as fh:
    pickle.dump(model, fh)
print("✅ model.pkl")

# model_meta.pkl  ← uygulama.py bundan 'ozellikler' listesini okur
model_meta = {
    "ozellikler"        : mevcut,           # ← KRİTİK: tahmin_yap bunu kullanır
    "best_params"       : best_params,
    "test_metrikleri"   : ts_m,
    "feature_imp"       : imp.to_dict(),
    # Feature engineering normalizasyon sabitleri (tahmin_yap için)
    "fe_sabitler": {
        "guc_hacim_median": float(guc_hacim_median),
        "guc_hacim_std"   : float(guc_hacim_std),
    },
}
with open("model_meta.pkl", "wb") as fh:
    pickle.dump(model_meta, fh)
print("✅ model_meta.pkl")
print(f"   Kaydedilen özellik listesi ({len(mevcut)} adet): {mevcut}")

print(f"\n{SEP}")
print("🎉 Tamamlandı! Şimdi uygulamayı başlatabilirsin:")
print("   streamlit run uygulama.py")
print(SEP)
