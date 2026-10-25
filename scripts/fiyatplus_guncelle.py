"""FiyatPlus+ Endeksi'nden kasa tipi (SUV, sedan, hatchback...) ve yakıt (elektrikli, hibrit...) aylık
fiyat serilerini çekip public/veri/fiyat_degisimi.json içindeki 'fiyatplus_seri' bölümüne yazar.

Kullanım (internet erişimi olan bir makinede):   python scripts/fiyatplus_guncelle.py
Gereksinim: yalnızca standart kütüphane.

API: https://api.fiyatplus.com/docs/endeks  (herkese açık, IP başına dakikada 60 istek).
Atıf: yayında "FiyatPlus+ Endeksi" adı ve fiyatplus.com/endeks bağlantısı bulunmalıdır (sekmede mevcut).
NOT: Alan adları dokümandaki 'camelCase / yyyyMM' tarifine göre tolerans gösterilerek okunur;
beklenmeyen bir yanıt gelirse betik ham yanıtın başını yazdırıp durur — dosyaya bir şey yazmaz.
"""
import json
import sys
import urllib.request
from pathlib import Path

API = "https://api.fiyatplus.com/api/endeks/v1/seri?kirilim={k}"
DOSYA = Path(__file__).resolve().parent.parent / "public" / "veri" / "fiyat_degisimi.json"
BASLANGIC = 202601   # Ocak 2026 = 100 tabanı

# Slug -> görünen ad. Slug'lar API'nin döndürdüğü 'slug' alanıyla eşleştirilir; listede olmayanlar atlanır.
KASA = {"suv": "SUV", "sedan": "Sedan", "hatchback-5-kapi": "Hatchback 5 kapı", "hatchback-3-kapi": "Hatchback 3 kapı",
        "station-wagon": "Station Wagon", "coupe": "Coupe", "cabrio": "Cabrio", "crossover": "Crossover"}
YAKIT = {"elektrikli": "Elektrikli", "hibrit": "Hibrit", "dizel": "Dizel", "benzinli": "Benzinli", "benzin-lpg": "Benzin & LPG"}


def al(k):
    istek = urllib.request.Request(API.format(k=k), headers={"Accept": "application/json", "User-Agent": "EderiNe/1.0"})
    with urllib.request.urlopen(istek, timeout=30) as r:
        return json.load(r)


def deger(nokta, *adaylar):
    for a in adaylar:
        if a in nokta and nokta[a] is not None:
            return nokta[a]
    return None


def donustur(yanit, esle):
    cikti = []
    for sr in yanit.get("seriler", []):
        slug = sr.get("slug")
        if slug not in esle:
            continue
        noktalar = []
        for n in sr.get("noktalar", []):
            donem, endeks = deger(n, "donem", "period"), deger(n, "endeks", "index")
            if donem is None or endeks is None or int(donem) < BASLANGIC:
                continue
            donem = int(donem)
            noktalar.append({"ay": f"{donem // 100}-{donem % 100:02d}", "endeks": round(float(endeks), 2),
                             "aylik": deger(n, "aylikDegisim", "aylik"), "yillik": deger(n, "yillikDegisim", "yillik")})
        if noktalar:
            cikti.append({"ad": esle[slug], "slug": slug, "noktalar": sorted(noktalar, key=lambda x: x["ay"])})
    return cikti


def main():
    sonuc = {"baz": "Ocak 2026 = 100", "kaynak": "FiyatPlus+ Endeksi — fiyatplus.com/endeks"}
    for anahtar, esle in (("kasa", KASA), ("yakit", YAKIT)):
        yanit = al(anahtar)
        sonuc[anahtar] = donustur(yanit, esle)
        if not sonuc[anahtar]:
            print(f"'{anahtar}' için eşleşen seri bulunamadı. Yanıtın başı:\n{json.dumps(yanit, ensure_ascii=False)[:800]}")
            sys.exit(1)
        print(anahtar, "→", ", ".join(o["ad"] for o in sonuc[anahtar]))
    veri = json.loads(DOSYA.read_text(encoding="utf-8"))
    veri["fiyatplus_seri"] = sonuc
    DOSYA.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Yazıldı:", DOSYA)


if __name__ == "__main__":
    main()
