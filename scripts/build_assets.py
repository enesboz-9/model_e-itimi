"""
Eğitim çıktılarını (pkl/csv) Vercel için hafif, pandas/sklearn gerektirmeyen
dosyalara çevirir:  data/model.ubj, meta.json, marka_meta.json, motor.json,
performans.json, ilanlar.npz

Çalıştırma (proje kökünden):
    pip install pandas scikit-learn xgboost-cpu numpy
    python scripts/build_assets.py

Model veya veri seti her yenilendiğinde bu betik yeniden çalıştırılmalıdır.
"""
import json, pickle, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
KOK = Path(__file__).resolve().parent.parent
EGITIM = KOK / "egitim"
CIKTI = KOK / "data"
CIKTI.mkdir(exist_ok=True)
sys.path.insert(0, str(KOK / "api"))
import kodlar as K  # noqa: E402


def temiz(o):
    """JSON'a güvenle yazılabilir hale getir (numpy/NaN)."""
    if isinstance(o, dict):
        return {str(k) if not isinstance(k, str) else k: temiz(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [temiz(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.str_):
        return str(o)
    return o


def yaz(ad, nesne):
    (CIKTI / ad).write_text(json.dumps(temiz(nesne), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


# 1) Model → XGBoost yerel formatı (sürümler arası güvenli, pickle yok)
with open(EGITIM / "model.pkl", "rb") as f:
    model = pickle.load(f)
ozellikler = [str(x) for x in model.feature_names_in_]
model.get_booster().save_model(str(CIKTI / "model.ubj"))
print(f"model.ubj  ({len(ozellikler)} özellik)")

# 2) Meta
with open(EGITIM / "model_meta.pkl", "rb") as f:
    meta = pickle.load(f)
meta["ozellikler"] = ozellikler
yaz("meta.json", meta)

# 3) Marka popülaritesi
with open(EGITIM / "marka_meta.pkl", "rb") as f:
    mm = pickle.load(f)
yaz("marka_meta.json", {"popularite": mm.get("popularite", {})})

# 4) Motor eşleştirme (KNN yerine saf numpy için ölçekleyici + kayıtlar)
with open(EGITIM / "motor_model.pkl", "rb") as f:
    motor = pickle.load(f)
motor_json = {}
for marka, kayit in motor.items():
    veri = kayit["veri"].reset_index(drop=True)
    sc = kayit["scaler"]
    X = veri[["hacim_cc", "guc_hp"]].values.astype(float)
    if sc is not None:
        ort, olcek = sc.mean_.tolist(), sc.scale_.tolist()
    else:
        ort, olcek = X.mean(axis=0).tolist(), [1.0, 1.0]
    motor_json[marka] = {
        "ort": ort, "olcek": olcek,
        "kayitlar": veri.astype(object).where(veri.notna(), None).to_dict("records"),
    }
yaz("motor.json", motor_json)

# 5) Performans özeti: {(marka, model): {...}} -> {marka: {model: {...}}}
with open(EGITIM / "performans_ozet.pkl", "rb") as f:
    po = pickle.load(f)
perf = {}
for (m, mdl), v in po.items():
    perf.setdefault(m, {})[mdl] = v
yaz("performans.json", perf)

# 6) İlan veri seti (arabam_temiz.csv) → sıkıştırılmış sütunlu dizi
df = pd.read_csv(EGITIM / "arabam_temiz.csv", low_memory=False)
df = df.dropna(subset=["fiyat"])
df["fiyat"] = pd.to_numeric(df["fiyat"], errors="coerce")
df = df[df["fiyat"] > 0].copy()

yas = pd.to_numeric(df["arac_yasi"], errors="coerce")
yil = (2026 - yas).fillna(-1).astype(np.int16)
km = pd.to_numeric(df.get("km", 50000), errors="coerce").fillna(50000)

def ters(sozluk):
    return {v: k for k, v in sozluk.items()}

# Streamlit sürümündeki fillna değerleri korunur ("Bilinmiyor" / "Diğer")
tablolar = {}
def kodla(ad, kolon, sozluk, varsayilan):
    ad_haritasi = ters(sozluk)
    adlar = df[kolon].map(ad_haritasi).fillna(varsayilan)
    kategoriler = sorted(adlar.unique().tolist())
    idx = {a: i for i, a in enumerate(kategoriler)}
    tablolar[ad] = kategoriler
    return adlar.map(idx).astype(np.int16).values

arr = {
    "marka": kodla("marka", "marka_enc", K.MARKA_ENC, "Bilinmiyor"),
    "seri": kodla("seri", "seri_enc", K.SERI_ENC, "Diğer"),
    "yakit": kodla("yakit", "yakit_tipi_enc", K.YAKIT_ENC, "Bilinmiyor"),
    "vites": kodla("vites", "vites_tipi_enc", K.VITES_ENC, "Bilinmiyor"),
    "kasa": kodla("kasa", "kasa_tipi_enc", K.KASA_ENC, "Bilinmiyor"),
    "yil": yil.values,
    "km": km.astype(np.float32).values,
    "fiyat": df["fiyat"].astype(np.float32).values,   # taban ay (Mart 2026) fiyatı
}
np.savez_compressed(CIKTI / "ilanlar.npz", **arr)
yaz("ilan_tablolari.json", tablolar)
print(f"ilanlar.npz  ({len(df):,} ilan)")

for p in sorted(CIKTI.iterdir()):
    print(f"  {p.name:22s} {p.stat().st_size/1024:9.1f} KB")
