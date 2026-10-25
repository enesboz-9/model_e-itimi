/* AutoValuate — arayüz (bağımlılıksız). Tüm hesaplamalar /api/* uçlarından gelir. */
'use strict';

const $ = (id) => document.getElementById(id);
const e = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const sayi = (x, d = 0) => Number(x).toLocaleString('tr-TR', { maximumFractionDigits: d, minimumFractionDigits: d });
const tl = (x) => `${sayi(x)} TL`;
const BELIRTILMEMIS = 'Belirtilmemiş';
/* Tema rengi (CSS değişkeni) — Plotly CSS değişkeni okuyamadığı için değerler buradan çözülür. */
const cv = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

/* Araç animasyonu: yükleme alanları ve düğmeler için (stiller style.css → "Araç animasyonu") */
const ARAC = `<svg class="arac" viewBox="0 0 200 72" aria-hidden="true" focusable="false"><g class="isik"><polygon points="190,44 236,32 236,58"/><polygon points="190,46 214,40 214,52"/></g><path class="govde" d="M8 56V45c0-5 3-8 9-9l26-5 17-15c3-3 6-4 10-4h50c5 0 9 2 12 5l17 15 28 4c9 1 15 5 15 13v7z"/><path class="cam" d="M48 31l12-12c2-2 4-3 7-3h24v15zM98 16h22c3 0 5 1 7 3l11 12H98z"/><path class="detay" d="M94 16v38"/><rect class="far" x="184" y="40" width="8" height="5" rx="2"/><rect class="stop" x="8" y="40" width="5" height="6" rx="2"/><g><circle class="kemer" cx="50" cy="57" r="16"/><circle class="lastik" cx="50" cy="58" r="13"/><g class="jant"><circle cx="50" cy="58" r="7"/><path d="M50 51v14M43 58h14M45 53l10 10M55 53l-10 10"/></g></g><g><circle class="kemer" cx="150" cy="57" r="16"/><circle class="lastik" cx="150" cy="58" r="13"/><g class="jant"><circle cx="150" cy="58" r="7"/><path d="M150 51v14M143 58h14M145 53l10 10M155 53l-10 10"/></g></g></svg>`;
const yukleme = (mesaj, boyut = '') => `<div class="yukleme ${boyut}" role="status"><div class="yol">${ARAC}<i class="yol-serit"></i></div><p>${e(mesaj)}</p></div>`;
let cfg = null;
let cfgSoz; const cfgHazir = new Promise((r) => { cfgSoz = r; });

async function api(yol, govde) {
  const r = await fetch(yol, govde === undefined
    ? undefined
    : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(govde) });
  if (!r.ok) {
    let msg = `Sunucu hatası (${r.status})`;
    try { const j = await r.json(); if (j.detail) msg = typeof j.detail === 'string' ? j.detail : 'Girdi değerlerini kontrol edin.'; } catch (_) { /* yoksay */ }
    throw new Error(msg);
  }
  return r.json();
}

function hataGoster(m) {
  const el = $('hata');
  el.textContent = m ? `⚠️ ${m}` : '';
  el.hidden = !m;
  if (m) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

function doldur(sel, liste, secili) {
  sel.innerHTML = liste.map((x) => `<option>${e(x)}</option>`).join('');
  if (secili !== undefined && liste.includes(secili)) sel.value = secili;
}

function segment(kapsayici, ad, secenekler, varsayilan) {
  kapsayici.insertAdjacentHTML('beforeend', secenekler.map((s) =>
    `<label><input type="radio" name="${ad}" value="${e(s)}" ${s === varsayilan ? 'checked' : ''}> ${e(s)}</label>`).join(''));
}
const segDeger = (ad) => document.querySelector(`input[name="${ad}"]:checked`).value;

function aralik(id, bicim = (v) => sayi(v)) {
  const inp = $(id), out = $(id + '-o');
  const guncelle = () => { out.textContent = bicim(+inp.value); };
  inp.addEventListener('input', guncelle);
  guncelle();
}

async function calistir(btn, fn) {
  const eski = btn.innerHTML;
  btn.disabled = true; btn.innerHTML = `<span class="btn-yuk">${ARAC}<span>Hesaplanıyor…</span></span>`;
  hataGoster('');
  let kutu = btn.parentElement.querySelector(`[data-hata-icin="${btn.id}"]`);
  if (kutu) kutu.remove();
  try { await fn(); } catch (err) {
    // Hata, butonun hemen altında (kullanıcının baktığı yerde) ve "Tekrar dene" ile gösterilir
    btn.insertAdjacentHTML('afterend', `<div class="msg err hata-satir" role="alert" data-hata-icin="${btn.id}">
      <span>⚠️ ${e(err.message)}</span><button type="button" class="tekrar-k">Tekrar dene</button></div>`);
    btn.nextElementSibling.querySelector('button').addEventListener('click', () => btn.click());
  } finally { btn.disabled = false; btn.innerHTML = eski; }
}

/* ── Plotly (ilk grafik gerektiğinde yüklenir) ─────────────────── */
let plotlyP = null;
function plotly() {
  if (window.Plotly) return Promise.resolve(window.Plotly);
  plotlyP ??= new Promise((ok, hata) => {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js';
    s.onload = () => ok(window.Plotly); s.onerror = () => hata(new Error('Grafik kütüphanesi yüklenemedi'));
    document.head.appendChild(s);
  });
  return plotlyP;
}
const DUZEN = (ek = {}) => ({
  paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { color: cv('--soft'), family: 'Figtree, system-ui, sans-serif' },
  margin: { t: 44, b: 30, l: 50, r: 10 }, ...ek,
});
const CIZ = { displaylogo: false, responsive: true };

/* ── Ortak parçalar ────────────────────────────────────────────── */
const f = (v, birim = '') => (v === null || v === undefined || v === '' || String(v).toLowerCase() === 'nan') ? '—' : `${e(v)}${birim}`;

function motorKart(m, marka, kisa) {
  if (!m) return '';
  const k = m.kayit, renk = { 'Yüksek': 'var(--green)', 'Orta': 'var(--yellow)', 'Düşük': 'var(--red)' }[m.guven];
  return `<div class="gcard" style="margin-top:20px">
    <div class="gcard-title">Motor Modeli Bilgisi <small>(en yakın eşleşen kayıt · güven: <b style="color:${renk}">${m.guven}</b>)</small></div>
    <div style="font-size:1.05rem;font-weight:600;margin-bottom:10px">${e(marka)} ${f(k.motor_kodu)} <span style="color:var(--mute);font-weight:400;font-size:.82rem">(${f(k.uretim_yillari)})</span></div>
    <div class="kv">
      <span>Hacim: <b>${f(k.hacim_cc, ' cc')}</b></span><span>Güç: <b>${f(k.guc_hp, ' hp')}</b></span>
      <span>Tork: <b>${f(k.tork_nm, ' nm')}</b></span><span>Yakıt: <b>${f(k.yakit_tipi)}</b></span>
      <span>Konfigürasyon: <b>${f(k.silindir_konf)} ${f(k.silindir_sayisi)}</b></span><span>Turbo: <b>${f(k.turbo)}</b></span>
      <span>Sıkıştırma Oranı: <b>${f(k.kompresyon_orani)}</b></span><span>Tavsiye Yağ: <b>${f(k.tavsiye_edilen_yag)}</b></span>
      <span>Yağ Kapasitesi: <b>${f(k.yag_kapasitesi_l, ' L')}</b></span><span>Tahmini Motor Ömrü: <b>${f(k.motor_omru_km, ' km')}</b></span>
      <span>Euro Standardı: <b>${f(k.euro_standardi)}</b></span>
    </div>
    <div class="small">ⓘ Girdiğiniz hacim/güç değerlerine en yakın gerçek motor kaydı gösterilmektedir${kisa ? '' : '; aracınızın tam olarak bu motor koduna sahip olduğu garanti edilmez'}. Kaynak: mymotorlist.com motor veri tabanı.</div>
  </div>`;
}

/* Boş bırakılan teknik alanlar için hangi donanımın esas alındığını gösterir. */
function varsayimNotu(r) {
  const v = r.varsayim;
  if (!v) return '';
  const parcalar = [['motor', v.motor], ['yakıt', v.yakit], ['vites', v.vites], ['kasa', v.kasa]].filter(([, d]) => d).map(([ad, d]) => `${ad} <b>${e(d)}</b>`);
  if (!parcalar.length) return '';
  return `<p class="small" style="margin:0 0 16px">ⓘ Boş bıraktığınız teknik alanlar için ${e(r.girdi.marka)} ${e(r.girdi.seri)} ilanlarında en yaygın donanımlar esas alındı: ${parcalar.join(' · ')}. Daha kesin sonuç için “Teknik &amp; Ek Bilgiler” bölümünü doldurun.</p>`;
}

function emsalKarti(r) {
  const s = r.emsal;
  if (!s) return '';
  const yuzde = Math.round(Math.min(1, Math.max(0, s.konum)) * 100);
  const aralikYil = s.yil_min === s.yil_max ? `${s.yil_min}` : `${s.yil_min}–${s.yil_max}`;
  const not = r.sinirlandi
    ? `<div class="msg warn">Modelin ham tahmini (${tl(r.ham_tahmin)}) emsal ilanların ${r.sinirlandi === 'alt' ? 'en düşük' : 'en yüksek'} fiyatının ${r.sinirlandi === 'alt' ? 'altında' : 'üstünde'} kaldığı için değer aralığın ${r.sinirlandi === 'alt' ? 'alt' : 'üst'} sınırına çekildi.</div>` : '';
  const altinda = r.emsal_alti && !r.sinirlandi
    ? '<div class="msg warn">Hasar kaydı nedeniyle değerleme, emsal ilanların (çoğu hasarsız) en düşük fiyatının altında kalıyor.</div>' : '';
  return `<div class="gcard"><div class="gcard-title">Emsal ilan aralığı <small>(${e(r.girdi.marka)} ${e(r.girdi.seri)} · ${aralikYil} model · ${sayi(s.km_min)}–${sayi(s.km_max)} km · ${sayi(s.adet)} ilan)</small></div>
    <div class="aralik"><div class="aralik-cubuk"><i class="aralik-isaret ${yuzde < 15 ? 'sol' : yuzde > 85 ? 'sag' : ''}" style="left:${yuzde}%"><b>${tl(r.tahmin)}</b></i></div>
      <div class="aralik-uc"><span><small>En düşük ilan</small>${tl(s.min)}</span><span><small>En yüksek ilan</small>${tl(s.max)}</span></div></div>
    ${not}${altinda}
    <p class="small" style="margin:12px 0 0">Hasarsız araçlarda değerleme bu aralığın içinde kalır. Aralıktaki konumu hasar skoru, kilometre, yıl ve diğer bilgiler belirler.${s.genis ? ' Yeterli emsal olmadığı için yıl ve km penceresi genişletildi.' : ''}</p></div>`;
}

function ozetSatiri(a) {
  return `<span>Min: <b>${tl(a.min)}</b></span><span>%25: <b>${tl(a.q25)}</b></span><span>Medyan: <b>${tl(a.medyan)}</b></span>
    <span>%75: <b>${tl(a.q75)}</b></span><span>Max: <b>${tl(a.max)}</b></span><span>İlan: <b>${sayi(a.adet)}</b></span>`;
}

/* ── Sekmeler ──────────────────────────────────────────────────── */
const sekmeler = [...document.querySelectorAll('.tab')];
const yuklendi = {};
function sekmeAc(id) {
  sekmeler.forEach((b) => b.setAttribute('aria-selected', String(b.getAttribute('aria-controls') === id)));
  document.querySelectorAll('.panel').forEach((p) => { p.hidden = p.id !== id; });
  document.body.classList.toggle('t4-acik', id === 't4');
  if (id === 't3' && cfg) analizCalistir();
  if (id === 't4' && !yuklendi.t4) { yuklendi.t4 = true; fiyatDegisimiSekmesi(); }
  try { history.replaceState(null, '', '#' + id); } catch (_) { /* yoksay */ }
}
sekmeler.forEach((b, i) => {
  b.addEventListener('click', () => sekmeAc(b.getAttribute('aria-controls')));
  b.addEventListener('keydown', (ev) => {
    const j = ev.key === 'ArrowRight' ? i + 1 : ev.key === 'ArrowLeft' ? i - 1 : null;
    if (j === null) return;
    const hedef = sekmeler[(j + sekmeler.length) % sekmeler.length];
    hedef.focus(); hedef.click();
  });
});

/* ── Eşleştirme (fotoğraf analizi sonucunu listelerle eşle) ────── */
function markaEsles(ai, liste) {
  if (!ai) return null;
  if (liste.includes(ai)) return ai;
  const n = (s) => s.toLowerCase().replace(' - ', '').replace(/-/g, '').replace(/ /g, '');
  const a = n(ai);
  for (const m of liste) if (n(m) === a) return m;
  for (const m of liste) if (ai.toLowerCase().includes(m.toLowerCase()) || m.toLowerCase().includes(ai.toLowerCase())) return m;
  return null;
}
function seriEsles(ai, liste) {
  if (!ai || !liste.length) return null;
  if (liste.includes(ai)) return ai;
  const n = (s) => { s = s.toLowerCase().trim(); for (const t of ['-class', ' class', ' serisi', ' series', '-', ' ']) s = s.split(t).join(''); return s; };
  const a = n(ai);
  if (!a) return null;
  for (const s of liste) if (n(s) === a) return s;
  for (const s of liste) { const x = n(s); if (x && (x.includes(a) || a.includes(x))) return s; }
  return null;
}

/* ── Sekme 1 — Değerleme ───────────────────────────────────────── */
/* ── Parça parça hasar hesaplayıcı ─────────────────────────────────
   Her parça: [kimlik, ad, boyalı puanı, değişen puanı, x, y, genişlik, yükseklik, şemada yazan satırlar] (üstten görünüm, ön yukarıda).
   Puanlar index.html'deki "Hasar skoru nasıl hesaplanır?" tablosuyla aynıdır; değiştirirken ikisini birlikte güncelleyin. */
const PARCALAR = [
  ['on-tampon', 'Ön tampon', 1, 2, 84, 36, 132, 28, ['Ön tampon']],
  ['kaput', 'Motor kaputu', 2, 6, 102, 70, 96, 92, ['Motor', 'kaputu']],
  ['sol-on-camurluk', 'Sol ön çamurluk', 2, 3, 30, 70, 64, 92, ['Sol ön', 'çamurluk']],
  ['sag-on-camurluk', 'Sağ ön çamurluk', 2, 3, 206, 70, 64, 92, ['Sağ ön', 'çamurluk']],
  ['sol-on-kapi', 'Sol ön kapı', 2, 2, 30, 168, 64, 68, ['Sol ön', 'kapı']],
  ['sag-on-kapi', 'Sağ ön kapı', 2, 2, 206, 168, 64, 68, ['Sağ ön', 'kapı']],
  ['tavan', 'Tavan', 3, 10, 102, 190, 96, 116, ['Tavan']],
  ['sol-arka-kapi', 'Sol arka kapı', 2, 2, 30, 242, 64, 68, ['Sol arka', 'kapı']],
  ['sag-arka-kapi', 'Sağ arka kapı', 2, 2, 206, 242, 64, 68, ['Sağ arka', 'kapı']],
  ['sol-arka-camurluk', 'Sol arka çamurluk', 2, 2, 30, 316, 64, 110, ['Sol arka', 'çamurluk']],
  ['sag-arka-camurluk', 'Sağ arka çamurluk', 2, 2, 206, 316, 64, 110, ['Sağ arka', 'çamurluk']],
  ['bagaj', 'Arka kaput (bagaj)', 2, 4, 102, 334, 96, 92, ['Bagaj', 'kapağı']],
  ['arka-tampon', 'Arka tampon', 1, 2, 84, 436, 132, 28, ['Arka tampon']],
];
const HP_DURUM = ['orijinal', 'boyalı', 'değişen'];
const hp = Object.fromEntries(PARCALAR.map((p) => [p[0], 0]));
let hpYaziyor = false;

function hpKur() {
  // Tekerlekler gövdenin altında çizilir (dışarı taşan kısım görünür); ön = farlar + "ÖN", arka = stop lambaları + "ARKA"
  const tekerlek = [[10, 86], [276, 86], [10, 342], [276, 342]].map(([x, y]) => `<rect class="hp-teker" x="${x}" y="${y}" width="14" height="56" rx="5"/>`).join('');
  const parcalar = PARCALAR.map(([id, , , , x, y, w, h, satirlar]) => {
    // İnce tek satırlı parçada (tampon) puan adın yanına yazılır; diğerlerinde ad bloğu puan varken biraz yukarı kayar
    const cx = x + w / 2, cy = y + h / 2, tek = satirlar.length === 1 && h < 40;
    const ad = satirlar.map((t, i) => `<text class="hp-ad" data-i="${i}" x="${cx}" y="${cy + 4 + (i - (satirlar.length - 1) / 2) * 13}" text-anchor="middle">${e(t)}</text>`).join('');
    return `<g class="parca" data-id="${id}" data-d="0" data-tek="${tek ? 1 : 0}" data-n="${satirlar.length}" data-cy="${cy}" tabindex="0" role="button">
      <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9"/>${ad}
      <text class="hp-puan" x="${cx}" y="${cy + 4 + satirlar.length * 6.5 + 8}" text-anchor="middle"></text></g>`;
  }).join('');
  $('hp-svg').innerHTML = `${tekerlek}<rect class="hp-govde" x="22" y="28" width="256" height="444" rx="64"/>
    <path class="hp-cam" d="M102 165h96l-6 22h-84z"/><path class="hp-cam" d="M108 309h84l6 22h-96z"/>
    <ellipse class="hp-far" cx="62" cy="52" rx="14" ry="6" transform="rotate(-20 62 52)"/><ellipse class="hp-far" cx="238" cy="52" rx="14" ry="6" transform="rotate(20 238 52)"/>
    <rect class="hp-stop" x="46" y="440" width="26" height="8" rx="3"/><rect class="hp-stop" x="228" y="440" width="26" height="8" rx="3"/>
    <text class="hp-yon" x="150" y="17" text-anchor="middle">▲ ÖN</text><text class="hp-yon" x="150" y="494" text-anchor="middle">ARKA ▼</text>
    ${parcalar}`;
  $('hp-svg').querySelectorAll('.parca').forEach((g) => {
    const don = () => { const id = g.dataset.id; hp[id] = (hp[id] + 1) % 3; hpCiz(true); };
    g.addEventListener('click', don);
    g.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); don(); } });
  });
  $('hp-sifirla').addEventListener('click', () => { PARCALAR.forEach((p) => { hp[p[0]] = 0; }); hpCiz(true); });
  // Slider elle oynatılırsa parça işaretleri artık geçerli olmaz
  $('t1-hasar').addEventListener('input', () => { if (!hpYaziyor) { PARCALAR.forEach((p) => { hp[p[0]] = 0; }); hpCiz(false); } });
  hpCiz(false);
}

/* Puan yazısını ve parça adını yerleştirir (puan varsa ad bloğu 7px yukarı kayar; tamponda puan adın yanındadır). */
function hpYerlestir(g, puan, ad) {
  const p = g.querySelector('.hp-puan'), adlar = g.querySelectorAll('.hp-ad'), n = +g.dataset.n, cy = +g.dataset.cy;
  if (g.dataset.tek === '1') {
    p.textContent = '';
    adlar[0].textContent = puan ? `${ad} +${puan}` : ad;
    return;
  }
  p.textContent = puan ? `+${puan}` : '';
  adlar.forEach((t, i) => t.setAttribute('y', cy + 4 + (i - (n - 1) / 2) * 13 - (puan ? 7 : 0)));
  p.setAttribute('y', cy + 4 + (n - 1) / 2 * 13 + 14 - 7);
}

function hpCiz(skoruYaz) {
  let skor = 0;
  const secili = [];
  for (const [id, ad, boya, degisen] of PARCALAR) {
    const d = hp[id], puan = d === 1 ? boya : d === 2 ? degisen : 0;
    skor += puan;
    const g = $('hp-svg').querySelector(`[data-id="${id}"]`);
    g.dataset.d = d;
    hpYerlestir(g, puan, ad);
    g.setAttribute('aria-label', `${ad}: ${HP_DURUM[d]}${puan ? `, +${puan} puan` : ''}. Değiştirmek için seç.`);
    if (d) secili.push(`<span class="chip d${d}">${e(ad)} · ${HP_DURUM[d]} <b>+${puan}</b></span>`);
  }
  $('hp-ozet').innerHTML = secili.length
    ? `<div class="hp-liste">${secili.join('')}</div><div class="hp-toplam">Hesaplanan hasar skoru: <b>${skor}</b> / 42</div>`
    : '<p class="hint" style="margin:8px 0">Henüz parça işaretlenmedi.</p>';
  if (skoruYaz) {
    const s = $('t1-hasar');
    hpYaziyor = true; s.value = skor; s.dispatchEvent(new Event('input')); hpYaziyor = false;
  }
}

const seriListesi = (marka) => cfg.seri_haritasi[marka] || cfg.tum_seriler;

function t1SeriDoldur(secili) {
  const liste = seriListesi($('t1-marka').value);
  doldur($('t1-seri'), liste, secili);
}

/* Araç (marka + model) üç sekme arasında ortaktır: Değerleme (t1), İlan Arama (t2), Piyasa (t3).
   Herhangi birinde değişince diğer ikisi de aynı araca geçer. Programatik .value atamaları
   change olayı tetiklemediği için döngü oluşmaz. "Tümü" = model filtresi yok (t1'de karşılığı yoktur,
   orada mevcut model korunur; marka değiştiyse listenin ilk modeli seçilir). */
const VARSAYILAN_MARKA = 'Honda', VARSAYILAN_SERI = 'Civic';

function aracSenkronla(kaynak) {
  const marka = $(`${kaynak}-marka`).value, seriHam = $(`${kaynak}-seri`).value;
  const seri = seriHam && seriHam !== 'Tümü' ? seriHam : null;
  if (kaynak !== 't1' && cfg.markalar.includes(marka)) {
    $('t1-marka').value = marka;
    t1SeriDoldur(seri ?? $('t1-seri').value);
  }
  if (!cfg.ilan_markalari.includes(marka)) return;   // ilan verisi olmayan marka: t2/t3 olduğu gibi kalır
  for (const p of ['t2', 't3']) {
    if (p === kaynak) continue;
    $(`${p}-marka`).value = marka;
    seriSecenekleri(p, seri);
  }
  if (kaynak !== 't3' && !$('t3').hidden) analizErtele();   // açık olan piyasa sekmesi yenilensin
}
const digerSekmelerleSenkronla = () => aracSenkronla('t1');
function seriSecenekleri(p, secili) {
  const marka = $(`${p}-marka`).value;
  const liste = ['Tümü', ...(cfg.seri_haritasi[marka] || [])];
  doldur($(`${p}-seri`), liste, secili && liste.includes(secili) ? secili : 'Tümü');
}

function fotoKaldir() {
  $('foto').value = '';
  $('foto-sonuc').innerHTML = '';
  $('foto-kaldir').hidden = true;
  $('l-marka').textContent = 'Marka'; $('l-seri').textContent = 'Model / Seri'; $('l-yil').textContent = 'Yıl';
  $('l-km').textContent = 'Kilometre'; $('l-kasa').textContent = 'Kasa Tipi'; $('l-renk').textContent = 'Renk';
}

async function fotoYukle(dosya) {
  $('foto-kaldir').hidden = false;
  const kutu = $('foto-sonuc');
  kutu.innerHTML = yukleme('Fotoğraf analiz ediliyor…', 'kucuk');
  try {
    // Vercel istek gövdesi sınırı ~4,5 MB: görüntüyü tarayıcıda küçültüp JPEG'e çeviriyoruz.
    const bmp = await createImageBitmap(dosya);
    const olcek = Math.min(1, 1024 / Math.max(bmp.width, bmp.height));
    const c = document.createElement('canvas');
    c.width = Math.round(bmp.width * olcek); c.height = Math.round(bmp.height * olcek);
    c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
    const url = c.toDataURL('image/jpeg', 0.85);
    const r = await api('/api/foto', { goruntu: url });

    // Alanlara uygula
    const markaE = markaEsles(r.marka, cfg.markalar);
    if (markaE) { $('t1-marka').value = markaE; t1SeriDoldur(); }
    const seriE = seriEsles(r.seri, seriListesi($('t1-marka').value));
    if (seriE) $('t1-seri').value = seriE;
    if (r.yil >= 1985 && r.yil <= 2026) $('t1-yil').value = r.yil;
    if (r.km > 0 && r.km <= 500000) {
      $('t1-km').value = Math.min(500000, Math.round(r.km / 5000) * 5000);
      $('t1-km').dispatchEvent(new Event('input'));
    }
    if (r.kasa_tipi && [...$('t1-kasa').options].some((o) => o.value === r.kasa_tipi)) $('t1-kasa').value = r.kasa_tipi;
    if (r.renk && [...$('t1-renk').options].some((o) => o.value === r.renk)) $('t1-renk').value = r.renk;
    $('l-marka').textContent = 'Marka' + (markaE ? ' 🤖' : ''); $('l-seri').textContent = 'Model / Seri' + (seriE ? ' 🤖' : '');
    $('l-yil').textContent = 'Yıl' + (r.yil ? ' 🤖' : ''); $('l-km').textContent = 'Kilometre' + (r.km ? ' 🤖' : '');
    $('l-kasa').textContent = 'Kasa Tipi' + (r.marka ? ' 🤖' : ''); $('l-renk').textContent = 'Renk' + (r.marka ? ' 🤖' : '');
    digerSekmelerleSenkronla();

    const yasAi = r.yil ? 2026 - r.yil : 0;
    const tespitYok = !r.marka;
    kutu.innerHTML = `<div class="grid2" style="margin-top:12px"><div><img class="preview" alt="Yüklenen araç fotoğrafı" src="${url}"></div><div>
      ${tespitYok ? `<div class="msg warn">⚠️ <b>AI bu fotoğraftan aracı tespit edemedi.</b> ${e(r.aciklama || '')}<br>Daha net, aracın yandan veya önden/arkadan tamamının göründüğü bir fotoğraf deneyin ya da bilgileri aşağıdan elle girin.</div>`
        : `<div class="msg ok"><b>Kasa:</b> ${e(r.kasa_tipi)} &nbsp;|&nbsp; <b>Renk:</b> ${e(r.renk)}</div>`}
      ${r.marka ? `<div class="msg info"><b>Marka:</b> ${e(r.marka)} &nbsp;|&nbsp; <b>Model:</b> ${e(r.seri)}${r.yil ? ` &nbsp;|&nbsp; <b>Yıl:</b> ${r.yil}` : ''}${r.yil_aralik_baslangic && r.yil_aralik_bitis ? ` &nbsp;|&nbsp; <b>Kasa Dönemi:</b> ${r.yil_aralik_baslangic}–${r.yil_aralik_bitis}` : ''}</div>` : ''}
      ${r.km > 0 ? `<div class="msg info"><b>Tahmini KM:</b> ${sayi(r.km)} km <i>(~${yasAi} yıl × ${yasAi <= 10 ? '15k-20k' : '10k-15k'} km/yıl)</i></div>` : ''}
      ${tespitYok ? '' : `<p class="hint">${e(r.aciklama || '')}<br>Aşağıda AI tespitlerini onaylayabilir veya değiştirebilirsin.</p>`}</div></div>`;
  } catch (err) {
    kutu.innerHTML = `<div class="msg err">⚠️ ${e(err.message)}</div>`;
  }
}

async function degerle() {
  const gv = (id) => $(id).value;
  const govde = {
    marka: gv('t1-marka'), seri: gv('t1-seri'), yil: +gv('t1-yil'), km: +gv('t1-km'),
    // "Kimden" ve "Takasa uygun" fiyatı etkilememesi için sabit varsayılan gönderilir.
    durum: gv('t1-durum'), kimden: 'Sahibinden', agir_hasar: segDeger('agir'), takasa: 'Hayır',
    hasar_skoru: +gv('t1-hasar'), motor_hacmi_cc: +gv('t1-cc') || 0, motor_gucu_hp: +gv('t1-hp') || 0,
    cekis: gv('t1-cekis'), yakit: gv('t1-yakit'), vites: gv('t1-vites'), kasa: gv('t1-kasa'), renk: gv('t1-renk'),
  };
  if (!(govde.yil >= 1985 && govde.yil <= 2026)) throw new Error('Yıl 1985–2026 aralığında olmalı.');
  const r = await api('/api/tahmin', govde);
  const g = r.girdi, v = r.verdict;
  const vcls = { uygun: 'verdict-uygun', pahali: 'verdict-pahali', normal: 'verdict-normal' }[v.tip];
  const oneriler = r.oneriler.length ? `<div class="gcard"><div class="gcard-title">Benzer Araç Önerileri <small>(aynı kasa, farklı marka · model yılı ${g.yil - 3}–${g.yil + 3} ilanlarının ortalamasına göre)</small></div>${
    r.oneriler.map((o) => {
      const fark = r.tahmin > 0 ? (o.ort_fiyat - r.tahmin) / r.tahmin * 100 : 0;
      return `<div class="oneri-card"><div class="oneri-ust"><span><b>${e(o.marka)} ${e(o.seri)}</b>
        <span style="color:var(--mute);font-size:.82rem;margin-left:10px">${o.yil_min === o.yil_max ? o.yil_min : `${o.yil_min}–${o.yil_max}`} model · ort. ${sayi(o.ort_km)} km</span></span>
        <span style="text-align:right"><span style="color:${fark < 0 ? 'var(--green)' : 'var(--red)'};font-weight:600">Ort. ${tl(o.ort_fiyat)}</span>
        <span style="display:block;color:var(--mute);font-size:.75rem">${fark < 0 ? '▼' : '▲'} tahmine göre %${Math.abs(fark).toFixed(1)}</span></span></div>
        <div style="color:var(--mute);font-size:.8rem;margin-top:4px">${e(o.yakit)} · ${e(o.vites)} · ${e(o.kasa)} · ${sayi(o.adet)} ilan · fiyat aralığı ${tl(o.min_fiyat)} – ${tl(o.max_fiyat)}</div></div>`;
    }).join('')}</div>` : '';
  $('t1-sonuc').innerHTML = `
    ${r.luks_uyari ? `<div class="msg warn">⚠️ <b>${e(g.marka)}</b> için tahmin güvenilirliği düşük olabilir. Eğitim verisinde bu marka için çok az ilan bulunmaktadır. Sonucu referans değil, yaklaşık bir alt/üst sınır olarak değerlendirin.</div>` : ''}
    <div class="result-hero">
      <div class="result-label">Tahmini Pazar Değeri</div>
      <div class="result-price">${tl(r.tahmin)}</div>
      <div class="result-range">Beklenen Aralık: ${tl(r.alt)} — ${tl(r.ust)}</div>
      <span class="${vcls}">${e(v.metin)}</span>
    </div>
    <div class="mkart-row">
      <div class="mkart"><div class="mkart-val">${e(g.marka)} ${e(g.seri)}</div><div class="mkart-lbl">Araç</div></div>
      <div class="mkart"><div class="mkart-val">${g.yil}</div><div class="mkart-lbl">Yıl</div></div>
      <div class="mkart"><div class="mkart-val">${sayi(g.km)} km</div><div class="mkart-lbl">Kilometre</div></div>
      <div class="mkart"><div class="mkart-val">${g.motor_hacmi_cc} cc / ${g.motor_gucu_hp} HP</div><div class="mkart-lbl">Motor${r.varsayim && r.varsayim.motor ? ' (tipik)' : ''}</div></div>
      <div class="mkart"><div class="mkart-val">${r.arac_yasi} yıl</div><div class="mkart-lbl">Araç Yaşı</div></div>
    </div>
    ${varsayimNotu(r)}
    ${emsalKarti(r)}
    ${motorKart(r.motor, g.marka, false)}
    ${r.piyasa && r.piyasa.adet ? `<div class="gcard" style="margin-top:20px"><div class="gcard-title">Piyasa Özeti (${e(g.marka)} · ${g.yil - 2}–${g.yil + 2})</div><div class="kv">${ozetSatiri(r.piyasa)}</div></div>` : ''}
    ${oneriler}`;
  $('t1-sonuc').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ── Sekme 2 — İlan arama ──────────────────────────────────────── */
async function ilanAra() {
  const lim = $('t2-limit').value;
  const r = await api('/api/ilanlar', {
    marka: $('t2-marka').value, seri: $('t2-seri').value === 'Tümü' ? null : $('t2-seri').value,
    yil_min: +$('t2-ymin').value, yil_max: +$('t2-ymax').value, max_km: +$('t2-km').value,
    max_fiyat: +$('t2-fmax').value || 0, sirala: $('t2-sira').value, limit: lim === 'Tümü' ? null : +lim,
  });
  const kutu = $('t2-sonuc');
  if (!r.toplam) { kutu.innerHTML = '<div class="msg warn">Eşleşen ilan bulunamadı.</div>'; return; }
  const o = r.ozet;
  const ozet = o && o.adet ? `<div class="gcard"><div class="mgrid" style="margin:0">${[
    [sayi(o.adet), 'Toplam İlan'], [tl(o.min), 'En Düşük'], [tl(o.medyan), 'Medyan'], [tl(o.ort), 'Ortalama'], [tl(o.max), 'En Yüksek'],
  ].map(([a, b]) => `<div class="mkart"><div class="mkart-val">${a}</div><div class="mkart-lbl">${b}</div></div>`).join('')}</div></div>` : '';
  kutu.innerHTML = `${ozet}<p class="hint" style="margin:0 0 12px"><b>${r.ilanlar.length}</b> sonuç gösteriliyor (toplam eşleşen: <b>${sayi(r.toplam)}</b>) · 🟢 Uygun 🟡 Ortalama 🔴 Pahalı</p>${
    r.ilanlar.map((i) => {
      const p = i.fark_pct;
      const [cls, fark] = p <= -10 ? ['ilan-uygun', `<span style="color:var(--green);font-size:.8rem;font-weight:600">▼ %${Math.abs(p).toFixed(1)} ucuz</span>`]
        : p >= 10 ? ['ilan-pahali', `<span style="color:var(--red);font-size:.8rem;font-weight:600">▲ %${Math.abs(p).toFixed(1)} pahalı</span>`]
          : ['ilan-normal', '<span style="color:var(--yellow);font-size:.8rem;font-weight:600">≈ Ortalama</span>'];
      return `<div class="ilan ${cls}"><div class="ilan-ust"><div><b>${e(i.marka)} ${e(i.seri)}</b>
        <span style="color:var(--mute);font-size:.85rem;margin-left:8px">${e(i.yil ?? '')}</span></div>
        <div style="text-align:right"><div class="ilan-fiyat">${tl(i.fiyat)}</div>${fark}</div></div>
        <div class="ilan-meta"><span class="badge b-green">Sahibinden</span> 🛣️ ${sayi(i.km)} km · ⛽ ${e(i.yakit)} · 🔧 ${e(i.vites)} · 🚘 ${e(i.kasa)}</div></div>`;
    }).join('')}`;
}

/* ── Sekme 3 — Piyasa analizi ──────────────────────────────────── */
let analizSayac = 0;
async function analizCalistir() {
  const kutu = $('t3-sonuc'), sira = ++analizSayac;
  kutu.innerHTML = yukleme('Piyasa verileri hazırlanıyor…');
  try {
    const [r, P] = await Promise.all([
      api('/api/analiz', {
        marka: $('t3-marka').value, seri: $('t3-seri').value === 'Tümü' ? null : $('t3-seri').value,
        yil_min: +$('t3-ymin').value, yil_max: +$('t3-ymax').value,
      }),
      plotly(),
    ]);
    if (sira !== analizSayac) return;   // daha yeni bir istek var
    if (!r.ozet) { kutu.innerHTML = '<div class="msg warn">Yeterli veri yok.</div>'; return; }
    const a = r.ozet, marka = $('t3-marka').value;
    kutu.innerHTML = `<div class="mgrid">${[
      [sayi(a.adet), 'Toplam İlan'], [tl(a.min), 'Min'], [tl(a.q25), '%25 Çeyrek'], [tl(a.medyan), 'Medyan'], [tl(a.q75), '%75 Çeyrek'], [tl(a.max), 'Max'],
    ].map(([x, y]) => `<div class="mkart"><div class="mkart-val">${x}</div><div class="mkart-lbl">${y}</div></div>`).join('')}</div>
      <div class="grid2"><div class="gcard"><div id="g1" class="chart"></div></div><div class="gcard"><div id="g2" class="chart"></div></div></div>
      <div class="gcard"><div id="g3" class="chart"></div></div>`;
    P.newPlot('g1', [{
      type: 'bar', x: r.yil_medyan.map((d) => d.yil), y: r.yil_medyan.map((d) => d.medyan),
      marker: { color: r.yil_medyan.map((d) => d.medyan), colorscale: [[0, cv('--bar-lo')], [0.5, cv('--accent')], [1, cv('--green')]] },
      hovertemplate: '%{x}: %{y:,.0f} TL<extra></extra>',
    }], DUZEN({ title: { text: `${marka} — Yıl Bazlı Medyan Fiyat`, font: { size: 14 } } }), CIZ);
    const yk = Object.entries(a.yakit);
    P.newPlot('g2', [{
      type: 'pie', hole: 0.45, labels: yk.map((x) => x[0]), values: yk.map((x) => x[1]),
      marker: { colors: [cv('--accent'), cv('--green'), cv('--yellow'), cv('--red'), '#8b7cf6'] }, textinfo: 'label+percent',
    }], DUZEN({ title: { text: 'Yakıt Tipi Dağılımı', font: { size: 14 } }, showlegend: false }), CIZ);
    const { kenar, sayim } = r.histogram;
    P.newPlot('g3', [{
      type: 'bar', x: sayim.map((_, i) => (kenar[i] + kenar[i + 1]) / 2), y: sayim,
      width: sayim.map((_, i) => kenar[i + 1] - kenar[i]), marker: { color: cv('--accent') },
      hovertemplate: '%{x:,.0f} TL civarı: %{y} ilan<extra></extra>',
    }], DUZEN({
      title: { text: `${marka} — Fiyat Dağılımı`, font: { size: 14 } }, bargap: 0.02,
      shapes: [{ type: 'line', x0: a.medyan, x1: a.medyan, yref: 'paper', y0: 0, y1: 1, line: { color: cv('--green'), dash: 'dash' } }],
      annotations: [{ x: a.medyan, yref: 'paper', y: 1, text: 'Medyan', showarrow: false, font: { color: cv('--green') }, yanchor: 'bottom' }],
    }), CIZ);
  } catch (err) {
    if (sira === analizSayac) kutu.innerHTML = `<div class="msg err">⚠️ ${e(err.message)}</div>`;
  }
}
let analizZaman;
const analizErtele = () => { clearTimeout(analizZaman); analizZaman = setTimeout(analizCalistir, 350); };

/* ── Sekme 4 — Fiyat değişimi ─────────────────────────────────── */
const AY_KISA = ['', 'Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];
const ayAd = (k) => { const [y, a] = k.split('-').map(Number); return `${AY_KISA[a]} ${String(y).slice(2)}`; };
const yuzde = (x, d = 1) => `${x < 0 ? '−' : x > 0 ? '+' : ''}%${sayi(Math.abs(x), d)}`;
/* Artış ▲ (yeşil) / düşüş ▼ (kırmızı): renge ek olarak şekil de taşır (renk körlüğü) */
const yon = (x) => (x > 0 ? '▲' : x < 0 ? '▼' : '■');
const degisim = (x, d = 1) => `${yon(x)} %${sayi(Math.abs(x), d)}`;
const degRenk = (x) => (x > 0 ? cv('--green') : x < 0 ? cv('--red') : cv('--soft'));
const HAT = { get arti() { return cv('--green'); }, get eksi() { return cv('--red'); }, get ana() { return cv('--accent'); }, get ikinci() { return cv('--yellow'); } };
const kaynakLink = (u, ad) => `<a href="${e(u)}" target="_blank" rel="noopener noreferrer">${e(ad)}</a>`;
let fiyatVeri = null;

async function fiyatDegisimiSekmesi() {
  const kutu = $('t4-ic');
  kutu.innerHTML = yukleme('Fiyat endeksleri yükleniyor…');
  try {
    fiyatVeri ??= await fetch('/veri/fiyat_degisimi.json').then((r) => { if (!r.ok) throw new Error('Fiyat değişimi verisi yüklenemedi'); return r.json(); });
    await cfgHazir;   // aylık endeks serisi API'den (değerleme katsayısıyla aynı veri)
    const [d, P] = [fiyatVeri, await plotly()];
    const ei = cfg.endeks, kay = Object.fromEntries(ei.kaynaklar.map((k) => [k.anahtar, k]));
    const aylikS = ei.aylik.filter((r) => r.ay <= d.son_ay);
    const v = d.vavaai, fp = d.fiyatplus, en = d.enflasyon, bt = d.betam_haziran_2026, ks = d.kasa_satis;
    const yil = v.yillik_yuzde[d.son_ay], reel = ((1 + yil / 100) / (1 + en.tufe_yillik_eylul_2026 / 100) - 1) * 100;
    const kart = (val, lbl, renk) => `<div class="mkart"><div class="mkart-val" ${renk ? `style="color:${renk}"` : ''}>${val}</div><div class="mkart-lbl">${lbl}</div></div>`;
    const seri = fiyatSeriBolumu(d);

    kutu.innerHTML = `
      <div class="gcard"><div class="gcard-title">Türkiye Araç Piyasası — Son 12 Ay <small>(${ayAd(d.son_ay)} itibarıyla)</small></div>
        <div class="mgrid">
          ${kart(degisim(yil), 'İkinci el araç fiyatı (12 ay, TL)', degRenk(yil))}
          ${kart(yuzde(en.tufe_yillik_eylul_2026), 'TÜFE (12 ay)')}
          ${kart(degisim(reel), 'Reel değişim (araç / TÜFE)', degRenk(reel))}
          ${kart(yuzde(en.usd_12ay), 'USD/TL (12 ay)')}
          ${kart(yuzde(en.eur_12ay), 'EUR/TL (12 ay)')}
        </div>
        <p class="hint" style="margin:0">ⓘ İkinci el fiyatlar TL bazında enflasyonun belirgin şekilde altında arttı; yani araçlar reel olarak ucuzladı. Reel değişim, 12 aylık nominal artış ile TÜFE'den hesaplanmıştır.</p>
      </div>

      <div class="gcard"><div class="gcard-title">Değerleme Fiyatları Nasıl Güncelleniyor?</div>
        <div class="kv"><span>Veri tabanı: <b>${ayAd(ei.taban_ay)}</b></span><span>Güncel katsayı: <b>×${cfg.katsayi.toFixed(4)}</b> (${yuzde((cfg.katsayi - 1) * 100, 2)})</span>
          <span>Hesaplanan ay: <b>${e(cfg.ay_etiketi)}</b></span></div>
        <p class="small" style="margin:10px 0 0;line-height:1.6">Değerleme fiyatları, her ay için <b>${ei.kaynaklar.map((k) => kaynakLink(k.url, k.ad)).join(' ve ')}</b> değişimlerinin <b>ortalaması</b> alınarak ${ayAd(ei.taban_ay)} tabanından bugüne bileşik olarak güncellenir.
        ${ei.tahmini_aylar.length ? `Henüz yayımlanmayan ay (${ei.tahmini_aylar.map(ayAd).join(', ')}) için son 3 ayın ortalaması kullanılır; gerçek veri gelince otomatik düzelir.` : ''}</p></div>

      <div class="grid2">
        <div class="gcard"><div id="g-kum" class="chart"></div></div>
        <div class="gcard"><div id="g-ay" class="chart"></div></div>
      </div>

      <div class="gcard-title" style="margin:8px 0 14px">Yakıt Tipine Göre</div>
      <div class="grid2">
        <div class="gcard"><div id="g-yakit12" class="chart"></div></div>
        <div class="gcard"><div id="g-yakit9" class="chart"></div></div>
      </div>

      <div class="gcard-title" style="margin:8px 0 14px">Segment ve Fiyat Bandına Göre</div>
      <div class="grid2">
        <div class="gcard"><div id="g-seg" class="chart"></div></div>
        <div class="gcard"><div id="g-bant" class="chart"></div></div>
      </div>

      <div class="gcard-title" style="margin:8px 0 14px">Kasa Tipine Göre (SUV · Sedan · Hatchback)</div>
      ${seri.html}
      <div class="gcard"><div id="g-kasa" class="chart" style="min-height:280px"></div>
        <p class="hint" style="margin:0">ⓘ Bu grafik <b>fiyat değil, satış adedi</b> değişimidir (${e(ks.ad)}). SUV'un ikinci eldeki payı %${sayi(ks.suv_payi.onceki, 1)} → %${sayi(ks.suv_payi.simdi, 1)}.</p></div>

      <div class="gcard"><div class="gcard-title">Nasıl Okunmalı?</div>
        <div class="small" style="margin:0;line-height:1.7">
          • <b>VavaAI</b> ve <b>FiyatPlus+</b> kalite-düzeltmeli endekslerdir (aynı araç kombinasyonunun fiyat hareketi); ikisi farklı yöntemle hesaplandığı için aynı ayda farklı değer verebilir.<br>
          • <b>BETAM–Sahibinden</b> ortalama ilan fiyatıdır; araç karması (daha pahalı/ucuz araçların payı) değiştiğinde endekslerden daha yüksek çıkabilir.<br>
          • Grafikteki kesikli çizgi, ilgili dönemin TÜFE yıllık enflasyonudur.<br>
          • Kaynaklar: ${kaynakLink(v.url, 'VavaCars')} · ${kaynakLink(fp.url, 'FiyatPlus+ Endeksi (fiyatplus.com/endeks)')} · ${kaynakLink(bt.url, 'BETAM–Sahibinden (KARAR)')} · ${kaynakLink(ks.url, 'Ticaret Gazetesi')} · TÜİK.
          Veri tarihi: ${e(d.guncelleme)}. Bilgilendirme amaçlıdır.
        </div></div>`;

    // Kümülatif endeks (Aralık 2025 = 100) — kaynaklar + değerlemede kullanılan ortalama
    const aylar = aylikS.map((r) => r.ay), x = [ayAd(d.baz_ay), ...aylar.map(ayAd)];
    const kum = (anahtar) => { let k = 100; return [100, ...aylikS.map((r) => (k *= 1 + (r[anahtar] ?? r.ortalama) / 100))]; };
    const renkler = [HAT.ana, HAT.ikinci], eksenBas = { t: 44, b: 40, l: 50, r: 10 };
    P.newPlot('g-kum', [
      ...ei.kaynaklar.map((q, i) => ({ type: 'scatter', mode: 'lines+markers', name: q.ad.replace(' Fiyat Endeksi', '').replace(' Endeksi', ''), x, y: kum(q.anahtar), line: { color: renkler[i % 2], width: 2 }, hovertemplate: `%{x}: %{y:.1f}<extra>${e(q.ad)}</extra>` })),
      { type: 'scatter', mode: 'lines+markers', name: 'Ortalama (değerlemede kullanılan)', x, y: kum('ortalama'), line: { color: cv('--ink'), width: 3, dash: 'dot' }, hovertemplate: '%{x}: %{y:.1f}<extra>Ortalama</extra>' },
    ], DUZEN({ title: { text: `Fiyat Endeksi (${ayAd(d.baz_ay)} = 100)`, font: { size: 14 } }, legend: { orientation: 'h', y: -0.22 }, margin: eksenBas, xaxis: { showgrid: false }, yaxis: { gridcolor: cv('--grid') } }), CIZ);

    P.newPlot('g-ay', [
      ...ei.kaynaklar.map((q, i) => ({ type: 'bar', name: q.ad.replace(' Fiyat Endeksi', '').replace(' Endeksi', ''), x: aylar.map(ayAd), y: aylikS.map((r) => r[q.anahtar]), marker: { color: renkler[i % 2] }, hovertemplate: `%{x}: %{y:+.2f}%<extra>${e(q.ad)}</extra>` })),
      { type: 'scatter', mode: 'markers', name: 'Ortalama', x: aylar.map(ayAd), y: aylikS.map((r) => r.ortalama), marker: { color: cv('--ink'), size: 9, symbol: 'diamond' }, hovertemplate: '%{x}: %{y:+.2f}%<extra>Ortalama</extra>' },
    ], DUZEN({ title: { text: 'Aylık Değişim (%)', font: { size: 14 } }, barmode: 'group', legend: { orientation: 'h', y: -0.22 }, margin: eksenBas, yaxis: { gridcolor: cv('--grid'), zeroline: true, zerolinecolor: cv('--zero') } }), CIZ);

    const cubuk = (id, baslik, liste, tufe, ek = {}) => {
      const s = [...liste].sort((a, b) => b.yuzde - a.yuzde);
      P.newPlot(id, [{
        type: 'bar', orientation: 'h', y: s.map((o) => o.ad), x: s.map((o) => o.yuzde),
        marker: { color: s.map((o) => (o.yuzde >= 0 ? HAT.ana : HAT.eksi)) },
        text: s.map((o) => degisim(o.yuzde)), textposition: 'outside', cliponaxis: false,
        textfont: { color: s.map((o) => degRenk(o.yuzde)), size: 12 },
        hovertemplate: '%{y}: %{x:+.1f}%<extra></extra>',
      }], DUZEN({
        title: { text: baslik, font: { size: 14 } }, yaxis: { autorange: 'reversed' },
        xaxis: { gridcolor: cv('--grid'), ticksuffix: '%', range: [Math.min(0, ...s.map((o) => o.yuzde)) - 3, Math.max(tufe ?? 0, ...s.map((o) => o.yuzde)) * 1.18] },
        margin: { t: 44, b: 30, l: 110, r: 30 },
        shapes: tufe == null ? [] : [{ type: 'line', x0: tufe, x1: tufe, yref: 'paper', y0: 0, y1: 1, line: { color: cv('--yellow'), dash: 'dash', width: 1.5 } }],
        annotations: tufe == null ? [] : [{ x: tufe, yref: 'paper', y: 1.02, text: `TÜFE %${sayi(tufe, 1)}`, showarrow: false, font: { color: cv('--yellow'), size: 11 }, yanchor: 'bottom' }],
        ...ek,
      }), CIZ);
    };
    cubuk('g-yakit12', 'Son 12 Ay · Ort. İlan Fiyatı (Haz 2026)', bt.yakit, en.tufe_yillik_haziran_2026);
    cubuk('g-yakit9', 'Ocak → Eylül 2026 · Endeks', fp.yakit_ocak_eylul, null);
    cubuk('g-seg', 'Son 12 Ay · Segment (Haz 2026)', bt.segment, en.tufe_yillik_haziran_2026);
    cubuk('g-bant', 'Ocak → Eylül 2026 · Fiyat Bandı', fp.fiyat_bandi_ocak_eylul, null);
    cubuk('g-kasa', 'Satış Adedi Değişimi · Oca–Tem 2026', ks.degisim, null);
    seri.ciz(P);
  } catch (err) { kutu.innerHTML = `<div class="msg err">⚠️ ${e(err.message)}</div>`; }
}

/* Kasa tipi / yakıt aylık fiyat serileri (scripts/fiyatplus_guncelle.py doldurur) */
function fiyatSeriBolumu(d) {
  const s = d.fiyatplus_seri || {}, gruplar = [['kasa', 'g-kasa-seri', 'Kasa Tipi'], ['yakit', 'g-yakit-seri', 'Yakıt Tipi']].filter(([k]) => (s[k] || []).length);
  if (!gruplar.length) return { html: '', ciz: () => {} };   // seri verisi yoksa bölüm hiç gösterilmez
  return {
    html: `<div class="grid2">${gruplar.map(([, id]) => `<div class="gcard"><div id="${id}" class="chart"></div></div>`).join('')}</div>`,
    ciz: (P) => gruplar.forEach(([k, id, ad]) => P.newPlot(id, s[k].map((o) => ({
      type: 'scatter', mode: 'lines+markers', name: o.ad, x: o.noktalar.map((n) => ayAd(n.ay)), y: o.noktalar.map((n) => n.endeks),
      hovertemplate: `%{x}: %{y:.1f}<extra>${e(o.ad)}</extra>`,
    })), DUZEN({ title: { text: `${ad} Fiyat Endeksi (${e(s.baz || 'Ocak 2026 = 100')})`, font: { size: 14 } }, legend: { orientation: 'h', y: -0.25 }, margin: { t: 44, b: 40, l: 50, r: 10 }, yaxis: { gridcolor: cv('--grid') } }), CIZ)),
  };
}

/* ── Sekme 5 — Performans analizi ──────────────────────────────── */
async function performansAnalizi() {
  const r = await api('/api/performans', {
    marka: $('t5-marka').value, model: $('t5-model').value,
    motor_hacmi_cc: +$('t5-cc').value || 0, motor_gucu_hp: +$('t5-hp').value || 0,
  });
  const o = r.ozet, marka = $('t5-marka').value, kutu = $('t5-sonuc');
  let html = '';
  if (o) {
    const ekstra = (o.guvenilirlik_ort != null ? `<span>Güvenilirlik (1-3): <b>${sayi(o.guvenilirlik_ort, 1)}</b></span>` : '')
      + (o.elektrik_menzil_ort ? `<span>Elektrikli Menzil: <b>${sayi(o.elektrik_menzil_ort)} km</b></span>` : '');
    html += `<div class="gcard"><div class="gcard-title">Veri Seti Özeti — ${e(marka)} ${e($('t5-model').value)}
      <small>(${o.adet} kayıt · en yaygın motor: ${e(o.en_yaygin_motor_tipi ?? '-')})</small></div>
      <div class="kv">
        <span>Yakıt Tüketimi: <b>${sayi(o.yakit_tuketimi_ort, 1)}</b></span><span>Güvenlik Notu: <b>${sayi(o.guvenlik_notu_ort, 1)} / 5</b></span>
        <span>Motor Performansı: <b>${sayi(o.motor_performansi_ort)}</b></span><span>Frenleme: <b>${sayi(o.frenleme_ort)}</b></span>
        <span>Konfor: <b>${sayi(o.konfor_ort, 1)} / 10</b></span><span>0-100 Hızlanma: <b>${sayi(o['0_100_ort'], 1)} sn</b></span>
        <span>Süspansiyon: <b>${sayi(o.suspansiyon_ort, 1)}</b></span><span>Emisyon: <b>${sayi(o.emisyon_ort)} g/km</b></span>
        <span>Senaryo Uyumu: <b>${sayi(o.senaryo_uyum_ort, 1)} / 10</b></span>${ekstra}
      </div>
      <div class="small">Fiyat aralığı: ${sayi(o.fiyat_min)} — ${sayi(o.fiyat_max)} (ortalama ${sayi(o.fiyat_ort)})</div></div>`;
  }
  html += r.motor ? motorKart(r.motor, marka, true)
    : `<div class="msg info">ℹ️ ${e(marka)} markası için motor veri tabanında eşleşen kayıt bulunamadı.</div>`;
  kutu.innerHTML = html;
}

/* ── Başlangıç ─────────────────────────────────────────────────── */
const bekle = (ms) => new Promise((r) => setTimeout(r, ms));
let ipucuZaman;
function ipucuBaslat() {
  const adimlar = ['Sunucu uyandırılıyor…', 'Fiyat modeli yükleniyor…', 'Piyasa verileri hazırlanıyor…'];
  const t0 = Date.now(); let i = 0;
  const yaz = () => {
    $('iskelet-baslik').textContent = adimlar[Math.min(i++, adimlar.length - 1)];
    $('iskelet-ipucu').textContent = Date.now() - t0 > 8000 ? 'İlk açılış biraz uzun sürebilir, neredeyse hazır.' : '';
  };
  clearInterval(ipucuZaman); yaz(); ipucuZaman = setInterval(yaz, 2400);
}
function iskeletDurum(hata) {
  const k = $('iskelet');
  k.querySelector('.iskelet-yuk').hidden = !!hata;
  k.querySelector('.iskelet-hata').hidden = !hata;
  if (hata) { clearInterval(ipucuZaman); $('iskelet-mesaj').textContent = hata; } else ipucuBaslat();
}
async function ayarlariYukle() {
  iskeletDurum(null);
  for (let deneme = 0; ; deneme++) {
    try { cfg = await api('/api/ayarlar'); cfgSoz(); clearInterval(ipucuZaman); return true; } catch (err) {
      if (deneme === 0) { await bekle(1500); continue; }   // soğuk başlangıç için sessizce bir kez daha dene
      iskeletDurum(`Sunucuya ulaşılamadı (${err.message}). İnternet bağlantınızı kontrol edip tekrar deneyin.`);
      return false;
    }
  }
}
$('tekrar').addEventListener('click', async (ev) => {
  const dugme = ev.currentTarget;   // await sonrası currentTarget null olur
  dugme.disabled = true;
  const ok = await ayarlariYukle();
  dugme.disabled = false;
  if (ok) basla();
});

async function basla() {
  if (!cfg && !(await ayarlariYukle())) return;
  document.body.classList.remove('yukleniyor');

  const markalar = cfg.markalar.filter((m) => m !== 'nan');
  doldur($('t1-marka'), markalar, VARSAYILAN_MARKA); t1SeriDoldur(VARSAYILAN_SERI);
  doldur($('t1-durum'), cfg.durum, 'İkinci El');
  doldur($('t1-cekis'), [BELIRTILMEMIS, ...cfg.cekis]);
  doldur($('t1-yakit'), [BELIRTILMEMIS, ...cfg.yakit]);
  doldur($('t1-vites'), [BELIRTILMEMIS, ...cfg.vites]);
  doldur($('t1-kasa'), [BELIRTILMEMIS, ...cfg.kasa.filter((k) => k !== 'Bilinmiyor'), 'Bilinmiyor']);
  doldur($('t1-renk'), [BELIRTILMEMIS, ...cfg.renk]);
  segment($('g-agir'), 'agir', ['Hayır', 'Evet'], 'Hayır');
  aralik('t1-km', (v) => `${sayi(v)} km`); aralik('t1-hasar', String); hpKur(); aralik('t2-km', (v) => `${sayi(v)} km`);

  for (const p of ['t2', 't3']) {
    doldur($(`${p}-marka`), cfg.ilan_markalari, VARSAYILAN_MARKA); seriSecenekleri(p, VARSAYILAN_SERI);
    $(`${p}-marka`).addEventListener('change', () => { seriSecenekleri(p); aracSenkronla(p); if (p === 't3') analizErtele(); });
    $(`${p}-seri`).addEventListener('change', () => aracSenkronla(p));
  }
  ['t3-seri', 't3-ymin', 't3-ymax'].forEach((id) => $(id).addEventListener('input', analizErtele));

  $('t1-marka').addEventListener('change', () => { t1SeriDoldur(); aracSenkronla('t1'); });
  $('t1-seri').addEventListener('change', () => aracSenkronla('t1'));
  aracSenkronla('t1');
  $('foto').addEventListener('change', (ev) => { if (ev.target.files[0]) fotoYukle(ev.target.files[0]); else fotoKaldir(); });
  $('foto-kaldir').addEventListener('click', fotoKaldir);
  $('t1-git').addEventListener('click', (ev) => calistir(ev.currentTarget, degerle));
  $('t2-git').addEventListener('click', (ev) => calistir(ev.currentTarget, ilanAra));
  $('t5-git').addEventListener('click', (ev) => calistir(ev.currentTarget, performansAnalizi));

  const pm = Object.keys(cfg.performans);
  doldur($('t5-marka'), pm);
  const t5Modeller = () => doldur($('t5-model'), cfg.performans[$('t5-marka').value] || []);
  t5Modeller(); $('t5-marka').addEventListener('change', t5Modeller);

  // Yükleme sırasında başka sekmeye geçildiyse ya da adreste #sekme varsa oraya git
  const hash = location.hash.slice(1), aktif = document.querySelector('.tab[aria-selected="true"]').getAttribute('aria-controls');
  const hedef = ['t2', 't3', 't4', 't5'].includes(hash) ? hash : aktif;
  if (hedef !== 't1') sekmeAc(hedef);
}
/* ── Tema (koyu / açık) ────────────────────────────────────────── */
function temaUygula(t, kaydet) {
  document.documentElement.dataset.tema = t;
  const m = document.querySelector('meta[name="theme-color"]'); if (m) m.content = cv('--bg');
  const b = $('tema'), ad = t === 'dark' ? 'Açık temaya geç' : 'Koyu temaya geç';
  b.setAttribute('aria-label', ad); b.title = ad;
  if (kaydet) { try { localStorage.setItem('tema', t); } catch (_) { /* yoksay */ } }
  if (!cfg) return;
  // Plotly renkleri çizim anında okunur: açık grafik sekmesi yeniden çizilir, diğeri bir sonraki açılışta
  yuklendi.t4 = false;
  const aktif = document.querySelector('.tab[aria-selected="true"]').getAttribute('aria-controls');
  if (aktif === 't3' || aktif === 't4') sekmeAc(aktif);
}
$('tema').addEventListener('click', () => temaUygula(document.documentElement.dataset.tema === 'dark' ? 'light' : 'dark', true));
temaUygula(document.documentElement.dataset.tema === 'light' ? 'light' : 'dark', false);
try {
  matchMedia('(prefers-color-scheme: light)').addEventListener('change', (ev) => {
    if (!localStorage.getItem('tema')) temaUygula(ev.matches ? 'light' : 'dark', false);   // kullanıcı seçmediyse sistemi izle
  });
} catch (_) { /* yoksay */ }

ipucuBaslat();
basla();
