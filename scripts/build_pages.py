"""
SEO sayfalarını data/ klasöründeki verilerden üretir (statik HTML, public/ altına).

Üretilenler
  • 4 ana sayfa : /arac-degerleme, /araba-fiyat-analizi, /piyasa-analizi, /ikinci-el-arac-fiyatlari
  • Model sayfaları      : /volkswagen-passat-fiyatlari          (marka + model)
  • Model-yıl sayfaları  : /volkswagen-passat-2019-fiyati        (uzun kuyruklu aramalar)
  • public/sitemap.xml   : tüm sayfalar

Çalıştırma (proje kökünden; yalnızca numpy gerekir):
    python scripts/build_pages.py              # bugünün ayına göre
    python scripts/build_pages.py --ay 2026-11 # belirli aya göre

NOT: Sayfalardaki fiyatlar, data/endeks.json'daki aylık endeksle güncellenmiş fiyatlardır.
Her ay endeks.json'a yeni satır ekledikten sonra bu betiği yeniden çalıştırıp commit/push edin.
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import sys
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "api"))
import core  # noqa: E402
from rehber_icerik import YAZILAR  # noqa: E402

PUBLIC = KOK / "public"
SITE = "https://bnovative.com.tr"
MIN_YIL_SAYFA = 15      # model-yıl sayfası için en az ilan
MIN_YIL_SATIR = 5       # tablolarda gösterilecek en az ilan
GUNCEL = {"ay": "", "iso": ""}     # main() doldurur: görünür güncelleme tarihi ve dateModified
ILETISIM_EPOSTA = "bnovative.destek@gmail.com"
EDITOR = {}                        # icerik/modeller.json (elle yazılmış model notları)
OZEL_MARKA = {"nan", "Bilinmiyor", ""}
OZEL_SERI = {"nan", "Diğer", "Bilinmiyor", ""}

# ── Yardımcılar ──────────────────────────────────────────────────────
_TR = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "İ": "i", "ö": "o", "ş": "s", "ü": "u",
                     "Ç": "c", "Ğ": "g", "Ö": "o", "Ş": "s", "Ü": "u", "â": "a", "î": "i", "û": "u", "é": "e"})


def slug(*parcalar) -> str:
    s = " ".join(str(p) for p in parcalar).translate(_TR).lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def sayi(x, d=0) -> str:
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def tl(x) -> str:
    return f"{sayi(round(float(x), -3))} TL"


def km_fmt(x) -> str:
    return f"{sayi(round(float(x), -3))} km"


def yuzde(x, d=1) -> str:
    return f"-%{sayi(-x, d)}" if x < 0 else f"%{sayi(x, d)}"


def marka_goster(m: str) -> str:
    return re.sub(r"\s*-\s*", "-", m)           # "Mercedes - Benz" → "Mercedes-Benz"


def arac_adi(m: str, s: str) -> str:
    m = marka_goster(m)
    return s if s.lower().startswith(m.lower()) else f"{m} {s}"


def kesit(metin: str, n=158) -> str:
    return metin if len(metin) <= n else metin[: n - 1].rsplit(" ", 1)[0] + "…"


# ── Veri ─────────────────────────────────────────────────────────────
class Veri:
    def __init__(self, hedef: datetime.date):
        self.hedef = hedef
        il = core.ilanlar()
        self.il = il
        self.fiyat = il.taban_fiyat * core.enflasyon_katsayisi(hedef)
        self.endeks = core.endeks_ozeti(hedef)
        self.ay_adi = core.ay_etiketi(hedef)
        self.mk = [str(il.t["marka"][i]) for i in range(len(il.t["marka"]))]
        self.sr = [str(il.t["seri"][i]) for i in range(len(il.t["seri"]))]
        gecerli = (il.yil > 0) & (self.fiyat > 0)
        gecerli &= np.array([self.mk[i] not in OZEL_MARKA for i in range(len(self.mk))])[il.marka]
        gecerli &= np.array([self.sr[i] not in OZEL_SERI for i in range(len(self.sr))])[il.seri]
        self.idx = np.flatnonzero(gecerli)
        self.gruplar = {}                      # (marka_adı, seri_adı) -> {yıl: indeks dizisi}
        mk_k, sr_k, yl = il.marka[self.idx], il.seri[self.idx], il.yil[self.idx]
        sira = np.lexsort((yl, sr_k, mk_k))
        i_s = self.idx[sira]
        anahtar = (il.marka[i_s].astype(np.int64) * 100000 + il.seri[i_s]) * 10000 + il.yil[i_s]
        _, bas = np.unique(anahtar, return_index=True)
        for a, b in zip(bas, list(bas[1:]) + [len(i_s)]):
            ii = i_s[a:b]
            k = (self.mk[il.marka[ii[0]]], self.sr[il.seri[ii[0]]])
            self.gruplar.setdefault(k, {})[int(il.yil[ii[0]])] = ii

    def ozet(self, ii) -> dict:
        p = self.fiyat[ii]
        return {"adet": int(len(ii)), "min": float(p.min()), "max": float(p.max()), "medyan": float(np.median(p)),
                "ort": float(p.mean()), "q25": float(np.percentile(p, 25)), "q75": float(np.percentile(p, 75)),
                "km_medyan": float(np.median(self.il.km[ii]))}

    def dagilim(self, ii, alan, n=4, yok=("Bilinmiyor", "nan", "")):
        dizi = getattr(self.il, alan)[ii]
        ad = self.il.t[alan]
        sayac = np.bincount(dizi, minlength=len(ad))
        top = [(ad[i], int(c)) for i, c in sorted(enumerate(sayac), key=lambda t: -t[1]) if c and ad[i] not in yok]
        toplam = sum(c for _, c in top) or 1
        return [(a, c, c / toplam * 100) for a, c in top[:n]]

    def km_bantlari(self, ii):
        km, p = self.il.km[ii], self.fiyat[ii]
        out = []
        for lo, hi, ad in ((0, 50_000, "0 – 50.000 km"), (50_000, 100_000, "50.000 – 100.000 km"),
                           (100_000, 150_000, "100.000 – 150.000 km"), (150_000, 200_000, "150.000 – 200.000 km"),
                           (200_000, 10**9, "200.000 km üzeri")):
            m = (km >= lo) & (km < hi)
            if m.sum() >= MIN_YIL_SATIR:
                out.append((ad, int(m.sum()), float(np.median(p[m]))))
        return out


# ── Sayfa iskeleti ───────────────────────────────────────────────────
_m = re.search(r'<svg class="logo".*?</svg>', (PUBLIC / "index.html").read_text(encoding="utf-8"), re.S)
LOGO = _m.group(0) if _m else ""   # ana sayfadaki logo SVG'si
NAV = (("/arac-degerleme", "Araç Değerleme"), ("/araba-fiyat-analizi", "Fiyat Analizi"),
       ("/piyasa-analizi", "Piyasa Analizi"), ("/ikinci-el-arac-fiyatlari", "İkinci El Fiyatları"), ("/rehber", "Rehber"))
TEMA_JS = ("(function(){try{var t=localStorage.getItem('tema');if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: light)')"
           ".matches?'light':'dark';document.documentElement.setAttribute('data-tema',t);}catch(e){document.documentElement.setAttribute('data-tema','dark');}})();")
TEMA_BTN_JS = ("document.getElementById('tema').addEventListener('click',function(){var d=document.documentElement,"
               "t=d.getAttribute('data-tema')==='dark'?'light':'dark';d.setAttribute('data-tema',t);try{localStorage.setItem('tema',t)}catch(e){}});")


def sayfa(yol: str, baslik: str, aciklama: str, icerik: str, ld: list | None = None, kirinti=None) -> str:
    url = f"{SITE}{yol}"
    graf = [{"@type": "WebPage", "name": baslik, "url": url, "inLanguage": "tr", "description": aciklama, "dateModified": GUNCEL["iso"],
             "isPartOf": {"@type": "WebSite", "name": "EderiNe", "url": SITE + "/"}}]
    if kirinti:
        graf.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": ad, "item": SITE + u} for i, (ad, u) in enumerate(kirinti)]})
    graf += ld or []
    aktif = ' aria-current="page"'
    nav = "".join(f'<a href="{u}"{aktif if u == yol else ""}>{esc(a)}</a>' for u, a in NAV)
    krm = ""
    if kirinti:
        krm = '<nav class="crumb" aria-label="Sayfa yolu">' + " › ".join(
            f'<a href="{u}">{esc(a)}</a>' if i < len(kirinti) - 1 else f"<span>{esc(a)}</span>"
            for i, (a, u) in enumerate(kirinti)) + "</nav>"
    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(baslik)}</title>
  <meta name="description" content="{esc(aciklama)}">
  <meta name="theme-color" content="#0b0d12">
  <script>{TEMA_JS}</script>
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="EderiNe">
  <meta property="og:title" content="{esc(baslik)}">
  <meta property="og:description" content="{esc(aciklama)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE}/og-image.png">
  <meta property="og:locale" content="tr_TR">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graf}, ensure_ascii=False, separators=(",", ":"))}</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Figtree:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/style.css">
  <link rel="stylesheet" href="/sayfa.css">
</head>
<body>
<div class="wrap">
  <header class="ust">
    <a class="marka" href="/" aria-label="EderiNe ana sayfa">{LOGO}<span>EderiNe</span></a>
    <nav class="ust-nav" aria-label="Ana bölümler">{nav}</nav>
    <button class="tema" id="tema" type="button" aria-label="Temayı değiştir" title="Temayı değiştir">
      <svg class="gunes" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      <svg class="ay" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 13A9 9 0 1 1 11 3a7 7 0 0 0 10 10z"/></svg>
    </button>
  </header>
  <div class="serit-cizgi" aria-hidden="true"></div>
  <main class="sayfa">
{krm}
{icerik}
  </main>
  <footer><p>EderiNe · Son güncelleme: {GUNCEL["ay"]} · Fiyatlar, Mart 2026 ilan verisinin aylık fiyat endeksleriyle güncellenmiş tahmini değerleridir; bilgilendirme amaçlıdır, bağlayıcı değildir.</p>
  <p><a href="/hakkimizda">Hakkımızda</a> · <a href="/metodoloji">Metodoloji</a> · <a href="/rehber">Rehber</a> · <a href="/iletisim">İletişim</a> · <a href="/">Uygulamaya git</a></p></footer>
</div>
<script>{TEMA_BTN_JS}</script>
</body>
</html>
"""


def tablo(basliklar, satirlar, sag=()):
    s_ = ' class="s"'
    th = "".join(f'<th{s_ if i in sag else ""}>{esc(b)}</th>' for i, b in enumerate(basliklar))
    tr = "".join("<tr>" + "".join(f'<td{s_ if i in sag else ""}>{h}</td>' for i, h in enumerate(r)) + "</tr>" for r in satirlar)
    return f'<div class="tbl-sar"><table class="tbl"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def kartlar(liste):
    return '<div class="stats">' + "".join(
        f'<div class="stat"><span>{esc(a)}</span><b>{esc(d)}</b></div>' for a, d in liste) + "</div>"


def sss(liste):
    """[(soru, cevap)] → (görünür HTML, FAQPage JSON-LD)."""
    h = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in liste)
    ld = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q,
                                               "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in liste]}
    return f'<section class="gcard"><h2 class="gcard-title">Sık sorulan sorular</h2>{h}</section>', ld


def dagilim_html(baslik, liste):
    if not liste:
        return ""
    li = "".join(f"<li><span>{esc(a)}</span><b>{yuzde(p, 0)}</b></li>" for a, _, p in liste)
    return f'<div class="dag"><h3>{esc(baslik)}</h3><ul>{li}</ul></div>'


def cta(metin, href, ikincil=None):
    ek = f'<a class="btn-link ikincil" href="{ikincil[1]}">{esc(ikincil[0])}</a>' if ikincil else ""
    return f'<div class="cta"><a class="btn-link" href="{href}">{esc(metin)}</a>{ek}</div>'


def uygulama_url(m, s=None, y=None, sekme="t1"):
    from urllib.parse import quote
    q = f"marka={quote(m)}" + (f"&seri={quote(s)}" if s else "") + (f"&yil={y}" if y else "")
    return f"/?{q}#{sekme}"


# ── Sayfa adresleri ──────────────────────────────────────────────────
def yol_model(m, s):
    return f"/{slug(m, s)}-fiyatlari"


def yol_yil(m, s, y):
    return f"/{slug(m, s)}-{y}-fiyati"


# ── Model-yıl sayfası ────────────────────────────────────────────────
def model_yil_sayfasi(V: Veri, m, s, y, yillar, ozetler, tum_gruplar):
    ii = yillar[y]
    o = ozetler[y]
    ad = arac_adi(m, s)
    ay = V.ay_adi
    yol = yol_yil(m, s, y)
    km_b = V.km_bantlari(ii)
    yakit, vites, kasa = V.dagilim(ii, "yakit", 3), V.dagilim(ii, "vites", 3), V.dagilim(ii, "kasa", 3)

    onceki = ozetler.get(y - 1)
    fark_html = ""
    if onceki and onceki["adet"] >= MIN_YIL_SATIR:
        f = (o["medyan"] / onceki["medyan"] - 1) * 100
        fark_html = (f" Bir yıl eski ({y - 1}) modele göre medyan fiyat {yuzde(abs(f), 1)} "
                     f"{'daha yüksek' if f > 0 else 'daha düşük'}.")
    giris = (f"{ay} itibarıyla {y} model {ad} için {sayi(o['adet'])} ilan incelendi. Medyan fiyat "
             f"<b>{tl(o['medyan'])}</b>; ilanların yarısı {tl(o['q25'])} – {tl(o['q75'])} aralığında. "
             f"Medyan kilometre {km_fmt(o['km_medyan'])}.{fark_html}")

    # Yıllara göre tablo
    satir = []
    for yy in sorted(ozetler, reverse=True):
        oo = ozetler[yy]
        if oo["adet"] < MIN_YIL_SATIR:
            continue
        etiket = f'<b>{yy}</b>' if yy == y else (f'<a href="{yol_yil(m, s, yy)}">{yy}</a>' if oo["adet"] >= MIN_YIL_SAYFA else str(yy))
        satir.append([etiket, sayi(oo["adet"]), tl(oo["medyan"]), km_fmt(oo["km_medyan"])])
    yil_tablo = tablo(["Model yılı", "İlan", "Medyan fiyat", "Medyan km"], satir, sag=(1, 2, 3))

    km_html = ""
    if len(km_b) >= 2:
        km_html = ('<section class="gcard"><h2 class="gcard-title">Kilometreye göre fiyat</h2>'
                   + tablo(["Kilometre aralığı", "İlan", "Medyan fiyat"], [[a, sayi(n), tl(p)] for a, n, p in km_b], sag=(1, 2))
                   + "</section>")

    dag = "".join([dagilim_html("Yakıt", yakit), dagilim_html("Vites", vites), dagilim_html("Kasa tipi", kasa)])
    dag_html = f'<section class="gcard"><h2 class="gcard-title">İlanların özellikleri</h2><div class="dagilimlar">{dag}</div></section>' if dag else ""

    # Aynı yıl, aynı markanın diğer modelleri
    diger = []
    for (mm, ss), yl in tum_gruplar.items():
        if mm == m and ss != s and y in yl and len(yl[y]) >= MIN_YIL_SAYFA:
            diger.append((len(yl[y]), ss))
    diger = sorted(diger, reverse=True)[:8]
    diger_html = ""
    if diger:
        chips = "".join(f'<a class="chip" href="{yol_yil(m, ss, y)}">{esc(arac_adi(m, ss))} {y}</a>' for _, ss in diger)
        diger_html = f'<section class="gcard"><h2 class="gcard-title">{esc(marka_goster(m))} {y} modeller</h2><div class="chips">{chips}</div></section>'

    sorular = [
        (f"{y} model {ad} fiyatı ne kadar?",
         f"{ay} itibarıyla {sayi(o['adet'])} ilana göre {y} model {ad} için medyan fiyat {tl(o['medyan'])}; "
         f"ilanların yarısı {tl(o['q25'])} ile {tl(o['q75'])} arasında. Hasar, boya, donanım ve kilometreye göre değişir."),
        (f"{y} model {ad} genelde kaç km'de satılıyor?",
         f"İlanlardaki medyan kilometre {km_fmt(o['km_medyan'])}."),
    ]
    if len(km_b) >= 2:
        d, u = km_b[0], km_b[-1]
        sorular.append((f"{ad} {y} fiyatı kilometreye göre nasıl değişir?",
                        f"{d[0]} aralığındaki ilanların medyanı {tl(d[2])}, {u[0]} aralığında {tl(u[2])}."))
    sorular.append((f"Hasar ve boya {ad} {y} fiyatını nasıl etkiler?",
                    "Boyalı ya da değişen parça ve ağır hasar kaydı fiyatı düşürür. EderiNe değerleme aracında parçaları şema üzerinde "
                    "işaretleyerek aracınızın tahmini değerini hesaplayabilirsiniz."))
    sss_html, sss_ld = sss(sorular)

    icerik = f"""
    <h1 class="s-baslik">{esc(ad)} {y} Fiyatı</h1>
    <p class="giris">{giris}</p>
    {kartlar([("Medyan fiyat", tl(o["medyan"])), ("Tipik aralık (ilanların %50'si)", f"{tl(o['q25'])} – {tl(o['q75'])}"),
              ("İlan sayısı", sayi(o["adet"])), ("Medyan km", km_fmt(o["km_medyan"]))])}
    {cta(f"{y} {ad} aracımı değerle", uygulama_url(m, s, y), ("Bu modelin ilanlarını listele", uygulama_url(m, s, y, "t2")))}
    {km_html}
    {dag_html}
    <section class="gcard"><h2 class="gcard-title">{esc(ad)} model yılına göre fiyatlar</h2>{yil_tablo}
      <p class="small"><a href="{yol_model(m, s)}">Tüm {esc(ad)} fiyatları →</a></p></section>
    {diger_html}
    {editor_html(m, s)}{rehber_linkleri()}
    {sss_html}"""
    baslik = f"{ad} {y} Fiyatı ve Fiyat Analizi | EderiNe"
    acik = kesit(f"{y} model {ad} fiyatı ne kadar? {ay} itibarıyla {sayi(o['adet'])} ilana göre medyan fiyat {tl(o['medyan'])}, "
                 f"tipik aralık {tl(o['q25'])} – {tl(o['q75'])}. Kilometreye göre fiyatlar ve ücretsiz değerleme.")
    kirinti = [("Ana sayfa", "/"), ("İkinci El Araç Fiyatları", "/ikinci-el-arac-fiyatlari"),
               (ad, yol_model(m, s)), (f"{y}", yol)]
    return yol, sayfa(yol, baslik, acik, icerik, [sss_ld], kirinti)


# ── Model sayfası ────────────────────────────────────────────────────
def model_sayfasi(V: Veri, m, s, yillar, ozetler):
    ad = arac_adi(m, s)
    ay = V.ay_adi
    yol = yol_model(m, s)
    tum = np.concatenate([yillar[y] for y in yillar])
    o = V.ozet(tum)
    yil_ler = sorted(y for y in yillar if len(yillar[y]) >= MIN_YIL_SATIR)
    en_yeni, en_eski = max(yil_ler), min(yil_ler)

    satir = []
    for y in sorted(yil_ler, reverse=True):
        oo = ozetler[y]
        etiket = f'<a href="{yol_yil(m, s, y)}">{y}</a>' if oo["adet"] >= MIN_YIL_SAYFA else str(y)
        satir.append([etiket, sayi(oo["adet"]), tl(oo["medyan"]), f'{tl(oo["q25"])} – {tl(oo["q75"])}', km_fmt(oo["km_medyan"])])
    yil_tablo = tablo(["Model yılı", "İlan", "Medyan fiyat", "Tipik aralık", "Medyan km"], satir, sag=(1, 2, 3, 4))

    yakit, vites, kasa = V.dagilim(tum, "yakit", 4), V.dagilim(tum, "vites", 3), V.dagilim(tum, "kasa", 3)
    dag = "".join([dagilim_html("Yakıt", yakit), dagilim_html("Vites", vites), dagilim_html("Kasa tipi", kasa)])
    dag_html = f'<section class="gcard"><h2 class="gcard-title">İlanların özellikleri</h2><div class="dagilimlar">{dag}</div></section>' if dag else ""

    # En çok ilanlı model yılları için hızlı bağlantılar
    pop = sorted((y for y in yil_ler if ozetler[y]["adet"] >= MIN_YIL_SAYFA), key=lambda y: -ozetler[y]["adet"])[:8]
    chips = "".join(f'<a class="chip" href="{yol_yil(m, s, y)}">{y} {esc(ad)} fiyatı</a>' for y in sorted(pop, reverse=True))

    ucuz, pahali = min(yil_ler, key=lambda y: ozetler[y]["medyan"]), max(yil_ler, key=lambda y: ozetler[y]["medyan"])
    sorular = [
        (f"{ad} fiyatları ne kadar?",
         f"{ay} itibarıyla {sayi(o['adet'])} ilana göre {ad} için medyan fiyat {tl(o['medyan'])}. Model yılına göre "
         f"{tl(ozetler[ucuz]['medyan'])} ({ucuz}) ile {tl(ozetler[pahali]['medyan'])} ({pahali}) arasında değişiyor."),
        (f"{ad} için hangi model yılları var?",
         f"İncelenen ilanlarda {en_eski} – {en_yeni} model yılları arasında {ad} bulunuyor."),
        (f"{ad} aracımın değerini nasıl öğrenirim?",
         "Marka, model, yıl ve kilometreyi girip boyalı/değişen parçaları işaretleyerek EderiNe değerleme aracından ücretsiz tahmini değer alabilirsiniz."),
    ]
    sss_html, sss_ld = sss(sorular)

    icerik = f"""
    <h1 class="s-baslik">{esc(ad)} Fiyatları</h1>
    <p class="giris">{ay} itibarıyla {esc(ad)} için {sayi(o['adet'])} ilan incelendi. Tüm model yıllarında medyan fiyat <b>{tl(o['medyan'])}</b>;
    {en_eski} – {en_yeni} model yılları arasında fiyatlar {tl(ozetler[ucuz]['medyan'])} ile {tl(ozetler[pahali]['medyan'])} (medyan) arasında değişiyor.</p>
    {kartlar([("Medyan fiyat", tl(o["medyan"])), ("İlan sayısı", sayi(o["adet"])),
              ("Model yılları", f"{en_eski} – {en_yeni}"), ("Medyan km", km_fmt(o["km_medyan"]))])}
    {cta(f"{ad} değerle", uygulama_url(m, s), ("İlanları listele", uygulama_url(m, s, None, "t2")))}
    <section class="gcard"><h2 class="gcard-title">Model yılına göre {esc(ad)} fiyatları</h2>{yil_tablo}</section>
    <section class="gcard"><h2 class="gcard-title">Popüler model yılları</h2><div class="chips">{chips}</div></section>
    {dag_html}
    {editor_html(m, s)}{rehber_linkleri()}
    {sss_html}"""
    baslik = f"{ad} Fiyatları — Model Yılına Göre İkinci El Fiyat Analizi | EderiNe"
    acik = kesit(f"{ad} fiyatları {ay}: {sayi(o['adet'])} ilana göre medyan {tl(o['medyan'])}. {en_eski} – {en_yeni} model yılı fiyat tablosu, "
                 f"yakıt/vites dağılımı ve ücretsiz araç değerleme.")
    kirinti = [("Ana sayfa", "/"), ("İkinci El Araç Fiyatları", "/ikinci-el-arac-fiyatlari"), (ad, yol)]
    return yol, sayfa(yol, baslik, acik, icerik, [sss_ld], kirinti)


# ── Ana sayfalar ─────────────────────────────────────────────────────
def model_listesi(V, ozet_tum, n=12):
    """En çok ilanlı model-yıl (sayfası olan) ve modeller."""
    satir = sorted(((v["adet"], k) for k, v in ozet_tum.items()), reverse=True)[:n]
    return satir


def hub_degerleme(V, kayit):
    ay = V.ay_adi
    meta = core.meta()
    tm = meta.get("test_metrikleri", {})
    etiket = {"yas_segment": "Araç yaşı", "arac_yasi": "Araç yaşı", "yillik_km": "Araç yaşı", "vites_tipi_enc": "Vites tipi",
              "guc_segment": "Motor gücü", "motor_gucu_hp": "Motor gücü", "guc_hacim_orani": "Motor gücü", "guc_hacim_norm": "Motor gücü",
              "cekis_enc": "Çekiş", "yakit_tipi_enc": "Yakıt tipi", "arac_durumu_enc": "Araç durumu", "km": "Kilometre",
              "km_anomali": "Kilometre", "hasar_skoru": "Hasar / boya durumu", "agir_hasarli_evet": "Hasar / boya durumu",
              "marka_enc": "Marka", "marka_popularite": "Marka", "seri_enc": "Model", "kasa_tipi_enc": "Kasa tipi",
              "motor_hacmi_cc": "Motor hacmi", "hacim_segment": "Motor hacmi", "renk_enc": "Renk"}
    grup = {}
    for k, v in (meta.get("feature_imp") or {}).items():
        grup[etiket.get(k, None) or k] = grup.get(etiket.get(k, None) or k, 0) + v
    toplam = sum(grup.values()) or 1
    onem = sorted(((a, v / toplam * 100) for a, v in grup.items() if a in set(etiket.values())), key=lambda t: -t[1])[:7]
    onem_tablo = tablo(["Etken", "Modeldeki ağırlık"], [[esc(a), yuzde(p, 0)] for a, p in onem], sag=(1,))
    pop = sorted(kayit["model_yil"], key=lambda t: -t[0])[:12]
    chips = "".join(f'<a class="chip" href="{yol_yil(m, s, y)}">{esc(arac_adi(m, s))} {y}</a>' for _, (m, s, y) in pop)
    il = V.il
    toplam_ilan = len(V.idx)
    sorular = [
        ("Araç değerleme nasıl yapılır?", "Marka, model, yıl ve kilometreyi girin; isterseniz boyalı ve değişen parçaları araç şeması üzerinde işaretleyin. "
         "EderiNe, benzer ilanları ve yapay zeka modelini kullanarak tahmini piyasa değerini hesaplar."),
        ("Aracım kaç para eder?", "Aracınızın marka-model-yıl bilgisiyle benzer ilanların fiyat aralığına bakıp hasar durumunu ve kilometreyi ekleyerek "
         "yaklaşık değerini görebilirsiniz. Gerçek satış fiyatı pazarlık, bölge ve aracın durumuna göre değişir."),
        ("Araç değerleme ücretsiz mi?", "Evet, EderiNe araç değerleme, ilan arama ve piyasa analizi ücretsizdir."),
        ("Değerleme sonucu ne kadar güvenilir?", f"Model, test verisinde ortalama %{sayi(tm.get('mape', 0), 1)} mutlak yüzde hata ve "
         f"{sayi(tm.get('r2', 0), 2)} R² değerine ulaştı. Bu sonuçlar geçmiş test verisi üzerindedir; tek bir araçta sapma olabilir, tahmin kesin fiyat değildir."),
    ]
    sss_html, sss_ld = sss(sorular)
    icerik = f"""
    <h1 class="s-baslik">Ücretsiz Araç Değerleme</h1>
    <p class="giris">Aracınızın güncel piyasa değerini saniyeler içinde öğrenin. EderiNe, {sayi(toplam_ilan)} ikinci el araç ilanından öğrenen yapay zeka modeliyle
    marka, model, yıl, kilometre ve hasar/boya bilgisine göre tahmini fiyat üretir. Fiyatlar {ay} için güncellenmiştir.</p>
    {cta("Değerlemeyi başlat", "/#t1", ("Piyasa analizini gör", "/piyasa-analizi"))}
    <section class="gcard"><h2 class="gcard-title">Değerleme nasıl çalışır?</h2>
      <ol class="adim">
        <li><b>Aracı seçin.</b> Marka, model ve model yılını girin; kilometreyi kaydırıcıyla ayarlayın.</li>
        <li><b>Hasar durumunu işaretleyin.</b> Araç şemasında parçaya dokunarak <i>boyalı</i> ya da <i>değişen</i> olarak işaretleyin; ağır hasar kaydı varsa belirtin.</li>
        <li><b>İsterseniz teknik bilgi ekleyin.</b> Motor hacmi, güç, yakıt, vites ve kasa boş bırakılırsa aynı modelin ilanlarındaki en yaygın donanım kullanılır.</li>
        <li><b>Sonucu inceleyin.</b> Tahmini değer, fiyat aralığı ve benzer ilanların fiyatlarıyla karşılaştırma birlikte gösterilir.</li>
      </ol></section>
    <section class="gcard"><h2 class="gcard-title">Fiyatı en çok hangi etkenler belirler?</h2>
      <p class="hint">Modelin tahmin yaparken verdiği göreli ağırlık (özellik önemi, ilgili özellikler gruplanmıştır).</p>{onem_tablo}</section>
    <section class="gcard"><h2 class="gcard-title">Popüler araç değerleme sayfaları</h2><div class="chips">{chips}</div>
      <p class="small"><a href="/ikinci-el-arac-fiyatlari">Tüm marka ve modeller →</a></p></section>
    {sss_html}"""
    return "/arac-degerleme", sayfa(
        "/arac-degerleme", "Ücretsiz Araç Değerleme — Aracım Kaç Para Eder? | EderiNe",
        kesit(f"Ücretsiz araç değerleme: marka, model, yıl, km ve hasar bilgisiyle ikinci el aracınızın tahmini piyasa değerini yapay zeka ile öğrenin. {ay} verisi."),
        icerik, [sss_ld], [("Ana sayfa", "/"), ("Araç Değerleme", "/arac-degerleme")])


def hub_fiyat_analizi(V, kayit):
    ay = V.ay_adi
    il = V.il
    tum = V.idx
    o = V.ozet(tum)
    # Marka tablosu
    marka_ozet = {}
    for (m, s), yl in V.gruplar.items():
        marka_ozet.setdefault(m, []).extend(np.concatenate(list(yl.values())).tolist())
    marka_ozet = {m: V.ozet(np.array(ix)) for m, ix in marka_ozet.items()}
    top = sorted(marka_ozet.items(), key=lambda t: -t[1]["adet"])[:20]
    mt = tablo(["Marka", "İlan", "Medyan fiyat", "Tipik aralık"],
               [[esc(marka_goster(m)), sayi(v["adet"]), tl(v["medyan"]), f'{tl(v["q25"])} – {tl(v["q75"])}'] for m, v in top], sag=(1, 2, 3))
    # Yaşa göre medyan
    yl = il.yil[tum]
    sat = []
    for y in range(2026, 2009, -1):
        mk = tum[yl == y]
        if len(mk) >= 100:
            sat.append([str(y), sayi(len(mk)), tl(np.median(V.fiyat[mk])), km_fmt(np.median(il.km[mk]))])
    yt = tablo(["Model yılı", "İlan", "Medyan fiyat", "Medyan km"], sat, sag=(1, 2, 3))
    # Popüler modeller
    pop = sorted(kayit["model"].items(), key=lambda t: -t[1]["adet"])[:15]
    pt = tablo(["Model", "İlan", "Medyan fiyat"],
               [[f'<a href="{yol_model(m, s)}">{esc(arac_adi(m, s))}</a>', sayi(v["adet"]), tl(v["medyan"])] for (m, s), v in pop], sag=(1, 2))
    sorular = [
        ("Araba fiyat analizi nasıl yapılır?", "Aynı marka, model ve yıldaki ilanların fiyat dağılımına (medyan ve çeyrekler) bakılır; kilometre, yakıt, vites ve hasar durumu "
         "bu aralıkta aracın nerede durduğunu belirler. EderiNe bu karşılaştırmayı veriden otomatik yapar."),
        ("Medyan fiyat neden ortalamadan daha anlamlı?", "Birkaç çok pahalı ya da çok ucuz ilan ortalamayı çarpıtabilir. Medyan, ilanların tam ortasındaki fiyattır ve uç değerlerden daha az etkilenir."),
        ("Fiyatlar ne kadar güncel?", f"Fiyatlar Mart 2026 ilan verisinin, aylık ikinci el araç fiyat endeksleriyle {ay} için güncellenmiş halidir; canlı ilan fiyatı değildir."),
    ]
    sss_html, sss_ld = sss(sorular)
    icerik = f"""
    <h1 class="s-baslik">Araba Fiyat Analizi</h1>
    <p class="giris">{ay} itibarıyla incelenen {sayi(o['adet'])} ikinci el araç ilanında medyan fiyat <b>{tl(o['medyan'])}</b>; ilanların yarısı
    {tl(o['q25'])} – {tl(o['q75'])} aralığında. Aşağıda markaya, model yılına ve en çok ilanlı modellere göre fiyat analizini bulabilirsiniz.</p>
    {kartlar([("Medyan fiyat", tl(o["medyan"])), ("Tipik aralık", f"{tl(o['q25'])} – {tl(o['q75'])}"), ("İlan sayısı", sayi(o["adet"])), ("Medyan km", km_fmt(o["km_medyan"]))])}
    {cta("Aracımın fiyatını analiz et", "/#t1", ("Piyasa grafikleri", "/#t3"))}
    <section class="gcard"><h2 class="gcard-title">Markaya göre fiyatlar (en çok ilanlı 20 marka)</h2>{mt}</section>
    <section class="gcard"><h2 class="gcard-title">Model yılına göre fiyatlar (tüm markalar)</h2>{yt}
      <p class="hint" style="margin-top:10px">Tüm markalar birlikte hesaplandığı için model karışımı fiyatı etkiler; belirli bir model için model sayfalarına bakın.</p></section>
    <section class="gcard"><h2 class="gcard-title">En çok ilanlı modellerin fiyatları</h2>{pt}
      <p class="small"><a href="/ikinci-el-arac-fiyatlari">Tüm marka ve modeller →</a></p></section>
    {sss_html}"""
    return "/araba-fiyat-analizi", sayfa(
        "/araba-fiyat-analizi", "Araba Fiyat Analizi — Marka ve Model Bazında İkinci El Fiyatlar | EderiNe",
        kesit(f"Araba fiyat analizi {ay}: {sayi(o['adet'])} ikinci el ilana göre medyan fiyat {tl(o['medyan'])}. Marka, model yılı ve model bazında fiyat tabloları."),
        icerik, [sss_ld], [("Ana sayfa", "/"), ("Araba Fiyat Analizi", "/araba-fiyat-analizi")])


def hub_piyasa(V, kayit):
    ay = V.ay_adi
    il = V.il
    tum = V.idx
    o = V.ozet(tum)
    yakit, vites, kasa = V.dagilim(tum, "yakit", 6), V.dagilim(tum, "vites", 4), V.dagilim(tum, "kasa", 6)
    dag = "".join([dagilim_html("Yakıt tipi", yakit), dagilim_html("Vites", vites), dagilim_html("Kasa tipi", kasa)])
    mk_say = np.bincount(il.marka[tum], minlength=len(V.mk))
    top = sorted(((V.mk[i], int(c)) for i, c in enumerate(mk_say) if c), key=lambda t: -t[1])[:10]
    mt = tablo(["Marka", "İlan", "Pazar payı (ilan)"], [[esc(marka_goster(m)), sayi(c), yuzde(c / len(tum) * 100, 1)] for m, c in top], sag=(1, 2))
    # Aylık endeks
    ei = V.endeks
    kays = ei["kaynaklar"]
    ay_adlari = core.AY_ADLARI
    sat = []
    for r in reversed(ei["aylik"]):
        y, a = r["ay"].split("-")
        etiket = f"{ay_adlari[int(a)]} {y}"
        hucreler = [yuzde(r[k["anahtar"]], 2) if r.get(k["anahtar"]) is not None else "–" for k in kays]
        sat.append([etiket, *hucreler, yuzde(r["ortalama"], 2)])
    et = tablo(["Ay", *[k["ad"] for k in kays], "Ortalama"], sat, sag=tuple(range(1, len(kays) + 2)))
    kat = ei["katsayi"]
    tahmini = ", ".join(f"{ay_adlari[int(x.split('-')[1])]} {x.split('-')[0]}" for x in ei["tahmini_aylar"])
    kaynak_link = " · ".join(f'<a href="{esc(k["url"])}" target="_blank" rel="noopener">{esc(k["ad"])}</a>' for k in kays if k.get("url"))
    sorular = [
        ("İkinci el araç piyasası nasıl analiz edilir?", "İlan sayıları, fiyat dağılımı, yakıt/vites/kasa tercihleri ve aylık fiyat endeksleri birlikte izlenir. "
         "EderiNe bu verileri marka ve model bazında filtreleyip grafiklerle gösterir."),
        ("Aylık fiyat endeksi nedir?", "İkinci el araç fiyatlarının aydan aya yüzde kaç değiştiğini gösteren seridir. EderiNe, değerleme fiyatlarını iki kaynağın aylık değişim ortalamasıyla günceller."),
        ("En çok ilanı olan marka hangisi?", f"İncelenen ilanlarda en çok ilan {marka_goster(top[0][0])} markasına ait ({sayi(top[0][1])} ilan)."),
    ]
    sss_html, sss_ld = sss(sorular)
    icerik = f"""
    <h1 class="s-baslik">İkinci El Araç Piyasa Analizi</h1>
    <p class="giris">{sayi(o['adet'])} ilanın analizine göre {ay} itibarıyla piyasada medyan fiyat {tl(o['medyan'])}. Yakıt, vites ve kasa dağılımını,
    marka paylarını ve aylık fiyat endekslerini aşağıda görebilirsiniz.</p>
    {cta("Etkileşimli piyasa analizi", "/#t3", ("Aylık fiyat değişimi", "/#t4"))}
    <section class="gcard"><h2 class="gcard-title">İlanların dağılımı</h2><div class="dagilimlar">{dag}</div></section>
    <section class="gcard"><h2 class="gcard-title">En çok ilanlı 10 marka</h2>{mt}</section>
    <section class="gcard"><h2 class="gcard-title">Aylık fiyat değişimi (TL, nominal)</h2>{et}
      <p class="small">Taban ay {core.AY_ADLARI[VERI_AY[1]]} {VERI_AY[0]}'ten {ay}'a bileşik katsayı: ×{sayi(kat, 4)} ({yuzde((kat - 1) * 100, 2)}).
      {('Yayımlanmamış aylar (' + esc(tahmini) + ') son üç ayın ortalamasıyla tahmin edilir. ') if tahmini else ''}Kaynaklar: {kaynak_link}</p></section>
    {sss_html}"""
    return "/piyasa-analizi", sayfa(
        "/piyasa-analizi", "İkinci El Araç Piyasa Analizi — Fiyat Endeksi ve Dağılımlar | EderiNe",
        kesit(f"İkinci el araç piyasa analizi {ay}: marka payları, yakıt-vites-kasa dağılımı ve aylık fiyat endeksi. {sayi(o['adet'])} ilana göre medyan {tl(o['medyan'])}."),
        icerik, [sss_ld], [("Ana sayfa", "/"), ("Piyasa Analizi", "/piyasa-analizi")])


VERI_AY = core.VERI_SETI_TABAN


def hub_fiyatlar(V, kayit):
    ay = V.ay_adi
    markalar = {}
    for (m, s), v in kayit["model"].items():
        markalar.setdefault(m, []).append((s, v))
    sirali = sorted(markalar.items(), key=lambda t: -sum(v["adet"] for _, v in t[1]))
    bloklar = []
    for i, (m, liste) in enumerate(sirali):
        liste = sorted(liste, key=lambda t: -t[1]["adet"])
        satir = [[f'<a href="{yol_model(m, s)}">{esc(arac_adi(m, s))}</a>', sayi(v["adet"]), tl(v["medyan"])] for s, v in liste]
        adet = sum(v["adet"] for _, v in liste)
        bloklar.append(f'<details class="marka-blok"{" open" if i < 6 else ""}><summary>{esc(marka_goster(m))} <small>{sayi(adet)} ilan · {len(liste)} model</small></summary>'
                       + tablo(["Model", "İlan", "Medyan fiyat"], satir, sag=(1, 2)) + "</details>")
    sorular = [
        ("İkinci el araç fiyatları nasıl belirlenir?", "Fiyatı en çok model yılı, kilometre, hasar/boya durumu, yakıt, vites ve donanım belirler. Marka ve modelin talep görme düzeyi de etkilidir."),
        ("Belirli bir modelin fiyatını nasıl bulurum?", "Aşağıdan markayı açıp modeli seçin; her model sayfasında model yılına göre medyan fiyatlar ve model-yıl sayfalarına bağlantılar bulunur."),
        ("Bu fiyatlar canlı ilan fiyatı mı?", f"Hayır. Mart 2026 ilan verisinin aylık fiyat endeksleriyle {ay} için güncellenmiş tahmini değerleridir."),
    ]
    sss_html, sss_ld = sss(sorular)
    icerik = f"""
    <h1 class="s-baslik">İkinci El Araç Fiyatları</h1>
    <p class="giris">{ay} itibarıyla {len(sirali)} marka ve {len(kayit['model'])} modelin ikinci el fiyatları. Bir marka seçin, ardından model ve model yılına göre
    medyan fiyatlara ulaşın. Kendi aracınızın değerini öğrenmek için <a href="/arac-degerleme">araç değerleme</a> sayfasını kullanın.</p>
    {cta("Aracımı değerle", "/#t1", ("İlan ara", "/#t2"))}
    <section class="gcard"><h2 class="gcard-title">Marka ve model listesi</h2>{''.join(bloklar)}</section>
    {sss_html}"""
    return "/ikinci-el-arac-fiyatlari", sayfa(
        "/ikinci-el-arac-fiyatlari", "İkinci El Araç Fiyatları — Marka, Model ve Yıla Göre | EderiNe",
        kesit(f"İkinci el araç fiyatları {ay}: {len(sirali)} marka, {len(kayit['model'])} model için model yılına göre medyan fiyatlar. Passat, Corolla, Clio ve daha fazlası."),
        icerik, [sss_ld], [("Ana sayfa", "/"), ("İkinci El Araç Fiyatları", "/ikinci-el-arac-fiyatlari")])


# ── Editör notu, rehber bağlantıları, kurumsal sayfalar ─────────────
def editor_html(m, s):
    """icerik/modeller.json içindeki elle yazılmış model notu (varsa)."""
    e = EDITOR.get(f"{m}|{s}")
    if not e:
        return ""
    ozet = f"<p class=\"giris\" style=\"margin-bottom:10px\">{esc(e['ozet'])}</p>" if e.get("ozet") else ""
    li = "".join(f"<li>{esc(x)}</li>" for x in e.get("dikkat", []))
    liste = f"<h3 class=\"alt\">Alırken dikkat edilecekler</h3><ul class=\"adim\">{li}</ul>" if li else ""
    uyari = ('<p class="msg warn" role="note">⚠️ Bu notlar, kullanıcı forumları, şikayet siteleri ve araç bilgi sitelerindeki <b>genel görüşlerin özetidir</b>; '
             'doğrulanmış teknik bilgi değildir. Anılan sorunlar her araçta görülmez ve nesle, motora, kullanıma ve bakım geçmişine göre değişir. '
             'Satın almadan önce bağımsız ekspertiz yaptırın ve resmî servis kayıtlarını kontrol edin.</p>')
    return f'<section class="gcard"><h2 class="gcard-title">{esc(arac_adi(m, s))} hakkında genel kullanıcı görüşleri</h2>{ozet}{liste}{uyari}</section>'


def rehber_linkleri():
    chips = "".join(f'<a class="chip" href="/rehber/{k}">{esc(v["baslik"].split("?")[0].split(":")[0])}</a>' for k, v in YAZILAR.items())
    return f'<section class="gcard"><h2 class="gcard-title">Satın almadan önce okuyun</h2><div class="chips">{chips}</div></section>'


def sayfa_metodoloji(V, kayit):
    m = core.meta()
    tm = m.get("test_metrikleri", {})
    ei = V.endeks
    kays = ei["kaynaklar"]
    kaynak = " ve ".join(f'<a href="{esc(k["url"])}" target="_blank" rel="noopener">{esc(k["ad"])}</a>' for k in kays if k.get("url"))
    kat = ei["katsayi"]
    icerik = f"""
    <h1 class="s-baslik">Metodoloji: Fiyatlar Nasıl Hesaplanıyor?</h1>
    <p class="giris">Bu sayfa, EderiNe'deki fiyat tahminlerinin ve sayfalardaki fiyat tablolarının hangi veriyle, nasıl üretildiğini ve sınırlarını açıklar.</p>
    <section class="gcard"><h2 class="gcard-title">Veri</h2>
      <p class="giris">Fiyat analizleri, kamuya açık ikinci el araç ilanlarından derlenen ve temizlenen yaklaşık {sayi(len(V.idx))} ilanlık bir veri setine dayanır.
      Veri seti Mart 2026 sonu itibarıyladır; bu nedenle sayfalardaki rakamlar canlı ilan fiyatı değil, aşağıdaki endeksle güncellenmiş tahmini değerlerdir.</p></section>
    <section class="gcard"><h2 class="gcard-title">Fiyatların güncellenmesi</h2>
      <p class="giris">İlan fiyatları, Mart 2026 tabanından {V.ay_adi} ayına, iki kaynağın aylık ikinci el araç fiyat değişimlerinin ortalamasıyla bileşik olarak güncellenir: {kaynak}.
      Güncel katsayı ×{sayi(kat, 4)} ({yuzde((kat - 1) * 100, 2)}). Henüz yayımlanmamış aylar için son üç ayın ortalaması kullanılır. Aylık değerleri <a href="/piyasa-analizi">piyasa analizi</a> sayfasında görebilirsiniz.</p></section>
    <section class="gcard"><h2 class="gcard-title">Model sayfalarındaki rakamlar</h2>
      <p class="giris">Marka-model ve model-yıl sayfalarında gösterilen <b>medyan fiyat</b>, aynı model ve yıldaki ilanların tam ortasındaki fiyattır; uç değerlerden az etkilenir.
      <b>Tipik aralık</b>, ilanların ortadaki yarısını (25. – 75. yüzdelik) kapsar. Bir model-yıl sayfası için en az {MIN_YIL_SAYFA} ilan gerekir; tablolarda en az {MIN_YIL_SATIR} ilanlı satırlar gösterilir.</p></section>
    <section class="gcard"><h2 class="gcard-title">Değerleme modeli</h2>
      <p class="giris">Değerleme aracı, XGBoost (gradyan artırmalı karar ağaçları) ile eğitilmiş bir regresyon modeli kullanır. Girdiler arasında araç yaşı, kilometre, hasar/boya durumu,
      motor gücü ve hacmi, yakıt, vites, kasa tipi, marka ve model bulunur. Ayrıca aynı model ve yıldaki emsal ilanların fiyat aralığı sonucu sınırlar.</p>
      {tablo(["Test verisi göstergesi", "Değer"], [["Ortalama mutlak yüzde hata (MAPE)", yuzde(tm.get("mape", 0), 1)], ["Ortalama mutlak hata (MAE)", tl(tm.get("mae", 0))], ["R²", sayi(tm.get("r2", 0), 3)]], sag=(1,))}
      <p class="small">Göstergeler, modelin eğitimde görmediği test verisi üzerindedir. Tek bir araçta sapma bundan büyük olabilir.</p></section>
    <section class="gcard"><h2 class="gcard-title">Sınırlar</h2>
      <ul class="adim"><li>Sonuçlar tahmindir; gerçek satış fiyatı pazarlığa, bölgeye, donanıma ve aracın gerçek durumuna göre değişir.</li>
      <li>Ekspertiz yerine geçmez. Satın almadan önce bağımsız ekspertiz yaptırın.</li>
      <li>Az ilanı olan model ve yıllarda tahminler daha az güvenilirdir.</li>
      <li>Hasar bilgisi kullanıcı beyanına dayanır; resmî hasar kaydı sorgulanmaz.</li></ul></section>"""
    return "/metodoloji", sayfa("/metodoloji", "Metodoloji — Fiyat Analizi ve Değerleme Nasıl Çalışır? | EderiNe",
        kesit(f"EderiNe fiyat verisinin kaynağı, aylık endeksle güncelleme yöntemi, yapay zeka modelinin hata payı (MAPE {yuzde(tm.get('mape', 0), 1)}) ve sınırları."),
        icerik, None, [("Ana sayfa", "/"), ("Metodoloji", "/metodoloji")])


def sayfa_hakkimizda(V, kayit):
    icerik = """
    <h1 class="s-baslik">Hakkımızda</h1>
    <p class="giris">EderiNe, ikinci el araç alıcı ve satıcılarının fiyatı veriye dayalı değerlendirebilmesi için geliştirilen ücretsiz bir araç değerleme ve piyasa analizi platformudur.
    <a href="https://bnovative.com.tr" target="_blank" rel="noopener">BNovative</a> tarafından Türkiye pazarı için geliştirilmektedir.</p>
    <section class="gcard"><h2 class="gcard-title">Ne yapıyoruz?</h2>
      <ul class="adim"><li><a href="/arac-degerleme">Araç değerleme:</a> marka, model, yıl, kilometre ve hasar bilgisine göre tahmini piyasa değeri.</li>
      <li><a href="/ikinci-el-arac-fiyatlari">İkinci el fiyatları:</a> marka, model ve model yılına göre medyan fiyatlar.</li>
      <li><a href="/piyasa-analizi">Piyasa analizi:</a> dağılımlar ve aylık fiyat endeksi.</li>
      <li><a href="/rehber">Rehber:</a> satın alma ve ekspertiz üzerine bilgilendirici yazılar.</li></ul></section>
    <section class="gcard"><h2 class="gcard-title">Neye dikkat ediyoruz?</h2>
      <p class="giris">Araç satışı yapmıyor, ilan yayınlamıyor ve komisyon almıyoruz. Verinin kaynağını, hesaplama yöntemini ve hata payını <a href="/metodoloji">metodoloji sayfasında</a> açıkça paylaşıyoruz.
      Sonuçlarımız bilgilendirme amaçlı tahmindir; bağlayıcı değildir.</p></section>"""
    return "/hakkimizda", sayfa("/hakkimizda", "Hakkımızda | EderiNe",
        "EderiNe, BNovative tarafından geliştirilen ücretsiz araç değerleme ve ikinci el piyasa analizi platformudur.",
        icerik, None, [("Ana sayfa", "/"), ("Hakkımızda", "/hakkimizda")])


def sayfa_iletisim(V, kayit):
    eposta = (f'<li>E-posta: <a href="mailto:{esc(ILETISIM_EPOSTA)}">{esc(ILETISIM_EPOSTA)}</a></li>' if ILETISIM_EPOSTA else "")
    icerik = f"""
    <h1 class="s-baslik">İletişim</h1>
    <p class="giris">Görüş, hata bildirimi, veri düzeltme ya da iş birliği için bize ulaşabilirsiniz.</p>
    <section class="gcard"><h2 class="gcard-title">Bize ulaşın</h2>
      <ul class="adim">{eposta}<li>Web: <a href="https://bnovative.com.tr" target="_blank" rel="noopener">bnovative.com.tr</a></li></ul>
      <p class="small">Bir fiyat ya da sayfa hakkında bildirimde bulunurken sayfanın adresini de yazarsanız daha hızlı yardımcı olabiliriz.</p></section>"""
    return "/iletisim", sayfa("/iletisim", "İletişim | EderiNe",
        "EderiNe ile iletişime geçin: görüş, hata bildirimi, veri düzeltme ve iş birliği.", icerik, None, [("Ana sayfa", "/"), ("İletişim", "/iletisim")])


def rehber_index(V, kayit):
    kartlar_ = "".join(f'<section class="gcard"><h2 class="gcard-title"><a href="/rehber/{k}">{esc(v["baslik"])}</a></h2><p class="giris" style="margin:0">{esc(v["aciklama"])}</p></section>' for k, v in YAZILAR.items())
    icerik = f"""
    <h1 class="s-baslik">İkinci El Araç Rehberi</h1>
    <p class="giris">İkinci el araç alırken ve satarken işinize yarayacak kısa, anlaşılır rehberler. Fiyat karşılaştırması için <a href="/ikinci-el-arac-fiyatlari">fiyat sayfalarına</a> ya da <a href="/arac-degerleme">değerleme aracına</a> bakabilirsiniz.</p>
    {kartlar_}"""
    return "/rehber", sayfa("/rehber", "İkinci El Araç Rehberi — Alırken ve Satarken | EderiNe",
        "İkinci el araç alırken dikkat edilecekler, ekspertiz raporunun okunması ve boyalı araç fiyatı üzerine rehber yazılar.",
        icerik, None, [("Ana sayfa", "/"), ("Rehber", "/rehber")])


def rehber_yazisi(k, v):
    yol = f"/rehber/{k}"
    diger = "".join(f'<a class="chip" href="/rehber/{kk}">{esc(vv["ozet"])}</a>' for kk, vv in YAZILAR.items() if kk != k)
    icerik = f"""
    <article>
    <h1 class="s-baslik">{esc(v["baslik"])}</h1>
    <p class="small" style="margin:0 0 14px">Son güncelleme: {GUNCEL["ay"]} · Hazırlayan: EderiNe editör ekibi</p>
    <div class="yazi">{v["html"]}</div>
    </article>
    {cta("Aracımın değerini hesapla", "/#t1", ("İkinci el fiyatları", "/ikinci-el-arac-fiyatlari"))}
    <section class="gcard"><h2 class="gcard-title">Diğer rehberler</h2><div class="chips">{diger}</div></section>"""
    ld = [{"@type": "Article", "headline": v["baslik"], "description": v["aciklama"], "inLanguage": "tr",
           "dateModified": GUNCEL["iso"], "mainEntityOfPage": SITE + yol,
           "author": {"@type": "Organization", "name": "EderiNe", "url": SITE + "/"},
           "publisher": {"@type": "Organization", "name": "BNovative", "url": SITE + "/"}}]
    return yol, sayfa(yol, f'{v["baslik"]} | EderiNe', v["aciklama"], icerik, ld,
                      [("Ana sayfa", "/"), ("Rehber", "/rehber"), (v["baslik"].split("?")[0].split(":")[0], yol)])


# ── Ana akış ─────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ay", help="YYYY-AA (varsayılan: bu ay)")
    a = ap.parse_args()
    hedef = datetime.date.today()
    if a.ay:
        y, m = map(int, a.ay.split("-"))
        hedef = datetime.date(y, m, 1)
    V = Veri(hedef)
    GUNCEL["ay"], GUNCEL["iso"] = V.ay_adi, datetime.date.today().isoformat()
    ed = KOK / "icerik" / "modeller.json"
    if ed.exists():
        EDITOR.update({k: v for k, v in json.loads(ed.read_text(encoding="utf-8")).items() if not k.startswith("_")})

    # Eski üretimleri temizle (yalnızca bu betiğin ürettiği dosyalar)
    uretilen = PUBLIC / ".uretilen.txt"
    if uretilen.exists():
        for ad in uretilen.read_text(encoding="utf-8").split():
            (PUBLIC / ad).unlink(missing_ok=True)

    # Özetler
    kayit = {"model": {}, "model_yil": []}
    ozet_yil = {}
    for (m, s), yl in V.gruplar.items():
        ozet_yil[(m, s)] = {y: V.ozet(ii) for y, ii in yl.items()}
        if any(o["adet"] >= MIN_YIL_SAYFA for o in ozet_yil[(m, s)].values()):
            kayit["model"][(m, s)] = V.ozet(np.concatenate(list(yl.values())))
            for y, o in ozet_yil[(m, s)].items():
                if o["adet"] >= MIN_YIL_SAYFA:
                    kayit["model_yil"].append((o["adet"], (m, s, y)))

    sayfalar = {}
    for (m, s) in kayit["model"]:
        yol, h = model_sayfasi(V, m, s, V.gruplar[(m, s)], ozet_yil[(m, s)])
        sayfalar[yol] = h
        for y, o in ozet_yil[(m, s)].items():
            if o["adet"] >= MIN_YIL_SAYFA:
                yol, h = model_yil_sayfasi(V, m, s, y, V.gruplar[(m, s)], ozet_yil[(m, s)], V.gruplar)
                sayfalar[yol] = h
    for f in (hub_degerleme, hub_fiyat_analizi, hub_piyasa, hub_fiyatlar, sayfa_metodoloji, sayfa_hakkimizda,
              sayfa_iletisim, rehber_index):
        yol, h = f(V, kayit)
        sayfalar[yol] = h
    for k, v in YAZILAR.items():
        yol, h = rehber_yazisi(k, v)
        sayfalar[yol] = h

    # Ad çakışması / mevcut dosya kontrolü
    for yol in sayfalar:
        hedef_dosya = PUBLIC / (yol.strip("/") + ".html")
        assert not hedef_dosya.exists(), f"Çakışma: {hedef_dosya}"
        hedef_dosya.parent.mkdir(parents=True, exist_ok=True)
        hedef_dosya.write_text(sayfalar[yol], encoding="utf-8")
    uretilen.write_text("\n".join(y.strip("/") + ".html" for y in sayfalar), encoding="utf-8")

    # Sitemap
    bugun = datetime.date.today().isoformat()
    oncelik = lambda y: "0.9" if y in ("/arac-degerleme", "/araba-fiyat-analizi", "/piyasa-analizi", "/ikinci-el-arac-fiyatlari", "/rehber") else "0.7" if y.startswith("/rehber/") or y in ("/metodoloji", "/hakkimizda") else "0.3" if y == "/iletisim" else "0.6"
    satirlar = [f"  <url><loc>{SITE}/</loc><lastmod>{bugun}</lastmod><priority>1.0</priority></url>"]
    satirlar += [f"  <url><loc>{SITE}{y}</loc><lastmod>{bugun}</lastmod><priority>{oncelik(y)}</priority></url>" for y in sorted(sayfalar)]
    (PUBLIC / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                        + "\n".join(satirlar) + "\n</urlset>\n", encoding="utf-8")
    n_hub = 4 + 4 + len(YAZILAR)
    n_model = len(kayit["model"])
    print(f"{len(sayfalar)} sayfa üretildi: {n_hub} ana + {n_model} model + {len(sayfalar) - n_hub - n_model} model-yıl  ({V.ay_adi})")


if __name__ == "__main__":
    main()
