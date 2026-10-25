# EderiNe — Vercel sürümü

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
Aylık endeks: `data/endeks.json` içinde her kaynağa (`vavaai`, `fiyatplus`) yeni ay satırı ekleyin. Değerleme fiyatları her ay için kaynakların **ortalamasıyla** güncellenir; bir kaynakta o ay yoksa diğeri, hiçbirinde yoksa son 3 ayın ortalaması kullanılır. Yeni kaynak eklemek için `kaynaklar` altına aynı biçimde bir blok yeterlidir. Fiyat Değişimi sekmesi aynı veriyi kullanır.
Eski/yeni sonuç karşılaştırması: `python scripts/test_parity.py`.

## Fiyat Değişimi sekmesi
Veri: `public/veri/fiyat_degisimi.json` (kaynak ve tarih alanlarıyla). Yeni ay yayınlanınca `vavaai.aylik_yuzde`, `fiyatplus.endeks`, `son_ay` güncellenir. SUV/sedan/elektrikli aylık fiyat serileri için: `python scripts/fiyatplus_guncelle.py` (FiyatPlus+ API, atıf gerekir).

## Değerleme mantığı düzeltmeleri (fiyatlar çok düşük çıkıyordu)
- **Boş teknik alanlar**: eskiden sabit değerle doluyordu (1600 cc / 110 HP / **Dizel** / Sedan). Artık `core.tamamla()` aynı marka+model ve yakın model yılı ilanlarında en yaygın gerçek donanımları kullanır (en çok 6 donanımın ilan sayısıyla ağırlıklı ortalaması). Sonuç ekranında hangi donanımın esas alındığı yazar.
- **`km_anomali`**: eğitimde hesaplanıyordu ama tahminde hep 0 veriliyordu (düşük km'li araç "ortalama" görünüyordu). Artık eğitimdeki formülle hesaplanır; referans değerler `meta.json → fe_sabitler` içindedir (`scripts/build_assets.py` üretir).
- **Emsal alt sınırı** yalnızca hasarsız araçlara uygulanır; hasar skoru 12 ve 30 artık aynı taban fiyata kilitlenmez.
- **"Piyasadan ucuz/pahalı"** kıyası tüm markanın medyanına değil, aynı model/yıl/km emsallerinin medyanına göre yapılır.
- Veri dosyaları değiştiği için `python scripts/build_assets.py` çalıştırılmalıdır (`data/ilanlar.npz` artık motor hacmi/gücü/çekiş de içerir).
