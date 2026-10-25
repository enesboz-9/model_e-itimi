# AutoValuate — Vercel sürümü

Streamlit uygulaması Vercel'de çalışmadığı için (sürekli açık WebSocket sunucusu gerektirir) iki parçaya ayrıldı:

- `public/` — statik arayüz (HTML/CSS/JS). Anında açılır, "uyku" ekranı yoktur.
- `api/` — Python (FastAPI) fonksiyonu: tahmin, ilan arama, analiz, fotoğraf uçları.
- `data/` — `scripts/build_assets.py` ile üretilen hafif model/veri dosyaları (pickle yok, pandas/sklearn gerekmez).
- `egitim/` — eski eğitim betikleri, ham CSV ve pkl'ler (Vercel'e yüklenmez, bkz. `.vercelignore`).

## Yayına alma
1. Bu klasörü GitHub'a push edin.
2. vercel.com → Add New → Project → repoyu seçin. Framework: **Other**. Başka ayar gerekmez.
3. (İsteğe bağlı) Settings → Environment Variables → `GROQ_API_KEY` ekleyin (fotoğraftan araç tanıma). Ekledikten sonra yeniden deploy edin.
4. Settings → Domains → `bnovative.com.tr` ve `www.bnovative.com.tr` ekleyin. Vercel'in gösterdiği DNS kayıtlarını alan adı sağlayıcınızda girin
   (genelde apex için `A  @  76.76.21.21`, www için `CNAME  www  cname.vercel-dns.com`; **ekranda gösterilen değerler geçerlidir**).
   Yayılması dakikalar–saatler sürebilir; SSL otomatik gelir.

## Yerelde deneme
`pip install fastapi uvicorn numpy xgboost-cpu httpx` → `python yerel.py` → http://localhost:8000

## Modeli / veriyi güncelleme
`egitim/` içinde yeniden eğitin → `pip install pandas scikit-learn` → `python scripts/build_assets.py` → commit/push.
Aylık endeks: `data/endeks.json` içine yeni ay satırı ekleyin (yoksa son 3 ayın ortalaması kullanılır).
Eski/yeni sonuç karşılaştırması: `python scripts/test_parity.py`.
