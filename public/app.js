/* AutoValuate — arayüz (bağımlılıksız). Tüm hesaplamalar /api/* uçlarından gelir. */
'use strict';

const $ = (id) => document.getElementById(id);
const e = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const sayi = (x, d = 0) => Number(x).toLocaleString('tr-TR', { maximumFractionDigits: d, minimumFractionDigits: d });
const tl = (x) => `${sayi(x)} TL`;
const BELIRTILMEMIS = 'Belirtilmemiş';
let cfg = null;

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
  btn.disabled = true; btn.textContent = 'Hesaplanıyor…';
  hataGoster('');
  try { await fn(); } catch (err) { hataGoster(err.message); } finally { btn.disabled = false; btn.innerHTML = eski; }
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
  paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { color: '#9ca3af' },
  margin: { t: 44, b: 30, l: 50, r: 10 }, ...ek,
});
const CIZ = { displaylogo: false, responsive: true };

/* ── Ortak parçalar ────────────────────────────────────────────── */
const f = (v, birim = '') => (v === null || v === undefined || v === '' || String(v).toLowerCase() === 'nan') ? '—' : `${e(v)}${birim}`;

function motorKart(m, marka, kisa) {
  if (!m) return '';
  const k = m.kayit, renk = { 'Yüksek': '#34d399', 'Orta': '#fbbf24', 'Düşük': '#f87171' }[m.guven];
  return `<div class="gcard" style="margin-top:20px">
    <div class="gcard-title">🔧 Motor Modeli Bilgisi <small>(en yakın eşleşen kayıt · güven: <b style="color:${renk}">${m.guven}</b>)</small></div>
    <div style="font-size:1.05rem;font-weight:600;margin-bottom:10px">${e(marka)} ${f(k.motor_kodu)} <span style="color:#6b7280;font-weight:400;font-size:.82rem">(${f(k.uretim_yillari)})</span></div>
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
  if (id === 't3') analizCalistir();
  if (id === 't4' && !yuklendi.t4) { yuklendi.t4 = true; modelSekmesi(); }
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
const seriListesi = (marka) => cfg.seri_haritasi[marka] || cfg.tum_seriler;

function t1SeriDoldur(secili) {
  const liste = seriListesi($('t1-marka').value);
  doldur($('t1-seri'), liste, secili);
}

function digerSekmelerleSenkronla() {
  const marka = $('t1-marka').value, seri = $('t1-seri').value;
  if (!cfg.ilan_markalari.includes(marka)) return;
  for (const p of ['t2', 't3']) {
    $(`${p}-marka`).value = marka;
    seriSecenekleri(p, seri);
  }
}
function seriSecenekleri(p, secili) {
  const marka = $(`${p}-marka`).value;
  const liste = ['Tümü', ...(cfg.seri_haritasi[marka] || [])];
  doldur($(`${p}-seri`), liste, secili && liste.includes(secili) ? secili : 'Tümü');
}

async function fotoYukle(dosya) {
  const kutu = $('foto-sonuc');
  kutu.innerHTML = '<div class="loading">🤖 AI analiz ediyor…</div>';
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
    durum: gv('t1-durum'), kimden: segDeger('kimden'), agir_hasar: segDeger('agir'), takasa: segDeger('takas'),
    hasar_skoru: +gv('t1-hasar'), motor_hacmi_cc: +gv('t1-cc') || 0, motor_gucu_hp: +gv('t1-hp') || 0,
    cekis: gv('t1-cekis'), yakit: gv('t1-yakit'), vites: gv('t1-vites'), kasa: gv('t1-kasa'), renk: gv('t1-renk'),
  };
  if (!(govde.yil >= 1985 && govde.yil <= 2026)) throw new Error('Yıl 1985–2026 aralığında olmalı.');
  const r = await api('/api/tahmin', govde);
  const g = r.girdi, v = r.verdict;
  const vcls = { uygun: 'verdict-uygun', pahali: 'verdict-pahali', normal: 'verdict-normal' }[v.tip];
  const oneriler = r.oneriler.length ? `<div class="gcard"><div class="gcard-title">💡 Benzer Araç Önerileri (Aynı Kasa, Farklı Marka)</div>${
    r.oneriler.map((o) => {
      const fark = r.tahmin > 0 ? (o.fiyat - r.tahmin) / r.tahmin * 100 : 0;
      return `<div class="oneri-card"><div class="oneri-ust"><span><b>${e(o.marka)} ${e(o.seri)}</b>
        <span style="color:#6b7280;font-size:.82rem;margin-left:10px">${e(o.yil ?? '')} · ${sayi(o.km)} km</span></span>
        <span style="color:${fark < 0 ? '#34d399' : '#f87171'};font-weight:600">${tl(o.fiyat)}</span></div>
        <div style="color:#6b7280;font-size:.8rem;margin-top:4px">${e(o.yakit)} · ${e(o.vites)} · ${e(o.kasa)}</div></div>`;
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
      <div class="mkart"><div class="mkart-val">${g.motor_hacmi_cc} cc / ${g.motor_gucu_hp} HP</div><div class="mkart-lbl">Motor</div></div>
      <div class="mkart"><div class="mkart-val">${r.arac_yasi} yıl</div><div class="mkart-lbl">Araç Yaşı</div></div>
    </div>
    ${motorKart(r.motor, g.marka, false)}
    ${r.piyasa && r.piyasa.adet ? `<div class="gcard" style="margin-top:20px"><div class="gcard-title">📊 Piyasa Özeti (${e(g.marka)} · ${g.yil - 2}–${g.yil + 2})</div><div class="kv">${ozetSatiri(r.piyasa)}</div></div>` : ''}
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
      const [cls, fark] = p <= -10 ? ['ilan-uygun', `<span style="color:#34d399;font-size:.8rem;font-weight:600">▼ %${Math.abs(p).toFixed(1)} ucuz</span>`]
        : p >= 10 ? ['ilan-pahali', `<span style="color:#f87171;font-size:.8rem;font-weight:600">▲ %${Math.abs(p).toFixed(1)} pahalı</span>`]
          : ['ilan-normal', '<span style="color:#fbbf24;font-size:.8rem;font-weight:600">≈ Ortalama</span>'];
      return `<div class="ilan ${cls}"><div class="ilan-ust"><div><b>${e(i.marka)} ${e(i.seri)}</b>
        <span style="color:#6b7280;font-size:.85rem;margin-left:8px">${e(i.yil ?? '')}</span></div>
        <div style="text-align:right"><div class="ilan-fiyat">${tl(i.fiyat)}</div>${fark}</div></div>
        <div class="ilan-meta"><span class="badge b-green">Sahibinden</span> 🛣️ ${sayi(i.km)} km · ⛽ ${e(i.yakit)} · 🔧 ${e(i.vites)} · 🚘 ${e(i.kasa)}</div></div>`;
    }).join('')}`;
}

/* ── Sekme 3 — Piyasa analizi ──────────────────────────────────── */
let analizSayac = 0;
async function analizCalistir() {
  const kutu = $('t3-sonuc'), sira = ++analizSayac;
  kutu.innerHTML = '<div class="loading">Yükleniyor…</div>';
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
      marker: { color: r.yil_medyan.map((d) => d.medyan), colorscale: [[0, '#312e81'], [0.5, '#6366f1'], [1, '#34d399']] },
      hovertemplate: '%{x}: %{y:,.0f} TL<extra></extra>',
    }], DUZEN({ title: { text: `${marka} — Yıl Bazlı Medyan Fiyat`, font: { size: 14 } } }), CIZ);
    const yk = Object.entries(a.yakit);
    P.newPlot('g2', [{
      type: 'pie', hole: 0.45, labels: yk.map((x) => x[0]), values: yk.map((x) => x[1]),
      marker: { colors: ['#6366f1', '#34d399', '#f59e0b', '#f87171', '#818cf8'] }, textinfo: 'label+percent',
    }], DUZEN({ title: { text: 'Yakıt Tipi Dağılımı', font: { size: 14 } }, showlegend: false }), CIZ);
    const { kenar, sayim } = r.histogram;
    P.newPlot('g3', [{
      type: 'bar', x: sayim.map((_, i) => (kenar[i] + kenar[i + 1]) / 2), y: sayim,
      width: sayim.map((_, i) => kenar[i + 1] - kenar[i]), marker: { color: '#6366f1' },
      hovertemplate: '%{x:,.0f} TL civarı: %{y} ilan<extra></extra>',
    }], DUZEN({
      title: { text: `${marka} — Fiyat Dağılımı`, font: { size: 14 } }, bargap: 0.02,
      shapes: [{ type: 'line', x0: a.medyan, x1: a.medyan, yref: 'paper', y0: 0, y1: 1, line: { color: '#34d399', dash: 'dash' } }],
      annotations: [{ x: a.medyan, yref: 'paper', y: 1, text: 'Medyan', showarrow: false, font: { color: '#34d399' }, yanchor: 'bottom' }],
    }), CIZ);
  } catch (err) {
    if (sira === analizSayac) kutu.innerHTML = `<div class="msg err">⚠️ ${e(err.message)}</div>`;
  }
}
let analizZaman;
const analizErtele = () => { clearTimeout(analizZaman); analizZaman = setTimeout(analizCalistir, 350); };

/* ── Sekme 4 — Model bilgisi ───────────────────────────────────── */
async function modelSekmesi() {
  const kutu = $('t4-ic'), m = cfg.model;
  const t = m.test_metrikleri;
  kutu.innerHTML = `<div class="gcard-title">🤖 Model Performansı</div>
    ${t ? `<div class="mgrid">
      <div class="mkart"><div class="mkart-val">${tl(t.mae)}</div><div class="mkart-lbl">MAE (Test)</div></div>
      <div class="mkart"><div class="mkart-val">${tl(t.rmse)}</div><div class="mkart-lbl">RMSE (Test)</div></div>
      <div class="mkart"><div class="mkart-val">%${sayi(t.mape, 1)}</div><div class="mkart-lbl">MAPE (Test)</div></div>
      <div class="mkart"><div class="mkart-val">${sayi(t.r2, 4)}</div><div class="mkart-lbl">R² (Test)</div></div></div>` : ''}
    <div id="g-imp" class="chart"></div>
    ${m.en_iyi_parametreler ? `<div class="gcard-title" style="margin-top:16px">⚙️ Hiperparametreler</div><pre>${e(JSON.stringify(m.en_iyi_parametreler, null, 2))}</pre>` : ''}`;
  if (!m.ozellik_onemi.length) return;
  try {
    const P = await plotly();
    const d = m.ozellik_onemi;
    P.newPlot('g-imp', [{
      type: 'bar', orientation: 'h', x: d.map((x) => x.deger), y: d.map((x) => x.ad),
      marker: { color: d.map((x) => x.deger), colorscale: [[0, '#312e81'], [0.5, '#6366f1'], [1, '#34d399']] },
    }], DUZEN({ title: { text: 'En Önemli 15 Özellik', font: { size: 14 } }, yaxis: { autorange: 'reversed' }, xaxis: { title: 'Önem Skoru' }, margin: { t: 44, b: 40, l: 140, r: 10 } }), CIZ);
  } catch (err) { $('g-imp').innerHTML = `<div class="msg err">⚠️ ${e(err.message)}</div>`; }
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
    html += `<div class="gcard"><div class="gcard-title">📊 Veri Seti Özeti — ${e(marka)} ${e($('t5-model').value)}
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
async function basla() {
  try { cfg = await api('/api/ayarlar'); } catch (err) {
    $('hero-note').textContent = '';
    hataGoster('Sunucuya bağlanılamadı: ' + err.message);
    return;
  }
  $('hero-note').textContent = `📊 Veri Tabanı: Mart 2026 (arabam.com) · Fiyatlar VavaAI Fiyat Endeksi ile ${cfg.ay_etiketi} seviyesine güncellendi (x${cfg.katsayi.toFixed(4)})`;

  const markalar = cfg.markalar.filter((m) => m !== 'nan');
  doldur($('t1-marka'), markalar, 'Toyota'); t1SeriDoldur();
  doldur($('t1-durum'), cfg.durum, 'İkinci El');
  doldur($('t1-cekis'), [BELIRTILMEMIS, ...cfg.cekis]);
  doldur($('t1-yakit'), [BELIRTILMEMIS, ...cfg.yakit]);
  doldur($('t1-vites'), [BELIRTILMEMIS, ...cfg.vites]);
  doldur($('t1-kasa'), [BELIRTILMEMIS, ...cfg.kasa.filter((k) => k !== 'Bilinmiyor'), 'Bilinmiyor']);
  doldur($('t1-renk'), [BELIRTILMEMIS, ...cfg.renk]);
  segment($('g-kimden'), 'kimden', ['Sahibinden', 'Galeriden', 'Yetkili Bayiden'], 'Sahibinden');
  segment($('g-agir'), 'agir', ['Hayır', 'Evet'], 'Hayır');
  segment($('g-takas'), 'takas', ['Hayır', 'Evet'], 'Hayır');
  aralik('t1-km', (v) => `${sayi(v)} km`); aralik('t1-hasar', String); aralik('t2-km', (v) => `${sayi(v)} km`);

  for (const p of ['t2', 't3']) {
    doldur($(`${p}-marka`), cfg.ilan_markalari, 'Toyota'); seriSecenekleri(p);
    $(`${p}-marka`).addEventListener('change', () => { seriSecenekleri(p); if (p === 't3') analizErtele(); });
  }
  ['t3-seri', 't3-ymin', 't3-ymax'].forEach((id) => $(id).addEventListener('input', analizErtele));

  $('t1-marka').addEventListener('change', () => { t1SeriDoldur(); digerSekmelerleSenkronla(); });
  $('t1-seri').addEventListener('change', digerSekmelerleSenkronla);
  digerSekmelerleSenkronla();
  $('foto').addEventListener('change', (ev) => { if (ev.target.files[0]) fotoYukle(ev.target.files[0]); });
  $('t1-git').addEventListener('click', (ev) => calistir(ev.currentTarget, degerle));
  $('t2-git').addEventListener('click', (ev) => calistir(ev.currentTarget, ilanAra));
  $('t5-git').addEventListener('click', (ev) => calistir(ev.currentTarget, performansAnalizi));

  const pm = Object.keys(cfg.performans);
  doldur($('t5-marka'), pm);
  const t5Modeller = () => doldur($('t5-model'), cfg.performans[$('t5-marka').value] || []);
  t5Modeller(); $('t5-marka').addEventListener('change', t5Modeller);

  const hash = location.hash.slice(1);
  if (['t2', 't3', 't4', 't5'].includes(hash)) sekmeAc(hash);
}
basla();
