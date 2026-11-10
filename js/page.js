/* What each constituency signs: the geography of UK Parliament petitions.
 * MapLibre on OpenFreeMap Positron. Two views of the 650 constituencies of 2024: equal-size hexagons (Open Innovations layout)
 * and real (simplified) boundaries. Colour modes: topic of each seat's most over-signed petition, one petition's map
 * (empirical Bayes location quotient, computed here from the raw counts), the first signature personality, seat groups,
 * and signatures per 2024 vote. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const PAPER = '#F2EAD3';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => n == null ? 'n/a' : Number(n).toLocaleString('en-GB');
  const DIV = ['#1F4E7A', '#2F6A9E', '#9DB9D3', '#EDE6D6', '#E8A890', '#B4442E', '#7A2414'];
  const SEQ = ['#F3E9CF', '#E9C99A', '#D99A63', '#C0663A', '#8E3B1F'];
  let map = null, D = null, SIG = null, mode = qs.get('mode') || 'top', view = 'hex', pet = null, LQ = null, HEXB = null;
  const lerp = (a, b, t) => a + (b - a) * t;
  function ramp(stops, t) { t = Math.max(0, Math.min(1, t)); const n = stops.length - 1, i = Math.min(n - 1, Math.floor(t * n)), f = t * n - i;
    const h = s => [1, 3, 5].map(k => parseInt(s.slice(k, k + 2), 16)); const a = h(stops[i]), b = h(stops[i + 1]);
    return '#' + a.map((x, k) => Math.round(lerp(x, b[k], f)).toString(16).padStart(2, '0')).join(''); }
  const lqColor = v => ramp(DIV, (Math.log2(Math.max(v, 1e-6)) + 2) / 4);
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  const keys = document.getElementById('keys');
  if (small) keys.classList.add('mini');
  document.getElementById('keyTitle').addEventListener('click', () => keys.classList.toggle('mini'));
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));
  const petById = id => D.pets.find(p => p.id === +id);
  const timesTxt = v => v >= 1.995 ? `${v.toFixed(1)} times the usual share` : v <= 0.55 ? `${Math.round(100 * v)}% of the usual share` : v >= 1.05 ? `${Math.round(100 * (v - 1))}% more than usual` : v <= 0.95 ? `${Math.round(100 * (1 - v))}% less than usual` : 'about the usual share';

  function computeLQ(p) {
    const j = D.pets.indexOf(p), s = SIG.s[j], T = D.T, Tp = p.ts, a = p.al;
    return s.map((x, i) => { const e = D.Tc[i] * Tp / T; return (x + a) / (e + a); });
  }
  function colours() {
    return D.seats.map((s, i) => {
      if (mode === 'top') return D.fam[petById(s.t[0][0]).f][1];
      if (mode === 'pet' && LQ) return lqColor(LQ[i]);
      if (mode === 'pc1') return ramp(DIV, (s.p1 + 2.5) / 5);
      if (mode === 'cl') return D.cl[String(s.k)][1];
      if (mode === 'rate') return ramp(SEQ, (s.s / s.vv - 0.5) / 1.1);
      return '#ccc';
    });
  }
  function key() {
    const t = document.getElementById('keyTitle'), b = document.getElementById('keyBody');
    let h = '';
    if (mode === 'top') { t.textContent = 'Topic of the most over-signed petition';
      const used = new Set(D.seats.map(s => petById(s.t[0][0]).f));
      h = '<div class="sw">' + Object.entries(D.fam).filter(([k]) => used.has(k)).map(([k, v]) => `<span><i style="background:${v[1]}"></i>${esc(v[0])}</span>`).join('') + '</div>'; }
    else if (mode === 'pet') { t.textContent = pet ? 'This petition against the seat’s usual share' : 'Pick a petition';
      h = `<div class="bar" style="background:linear-gradient(90deg,${DIV.join(',')})"></div><div class="ends"><span>1/4</span><span>usual</span><span>4x+</span></div>`; }
    else if (mode === 'pc1') { t.textContent = 'First signature personality';
      h = `<div class="bar" style="background:linear-gradient(90deg,${DIV.join(',')})"></div><div class="ends"><span>older, whiter seats</span><span>graduate, diverse</span></div>`; }
    else if (mode === 'cl') { t.textContent = 'Groups of seats by petition profile';
      h = '<div class="sw">' + Object.values(D.cl).map(v => `<span><i style="background:${v[1]}"></i>${esc(v[0])}</span>`).join('') + '</div>'; }
    else { t.textContent = 'Petition signatures per 2024 vote';
      h = `<div class="bar" style="background:linear-gradient(90deg,${SEQ.join(',')})"></div><div class="ends"><span>0.5</span><span>1.0</span><span>1.6</span></div>`; }
    b.innerHTML = h;
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
  }
  let FC = null;
  function refresh() {
    const col = colours();
    ['hex', 'geo'].forEach(src => { const fc = FC[src]; fc.features.forEach(f => { f.properties.col = col[f.properties.i]; }); map.getSource(src).setData(fc); });
    key(); panel();
  }
  function panel() {
    const pp = document.getElementById('pp');
    if (mode !== 'pet' || !pet || !LQ) { pp.classList.remove('on'); return; }
    const o = LQ.map((v, i) => [v, i]).filter(([, i]) => SIG.s[D.pets.indexOf(pet)][i] >= 30).sort((a, b) => b[0] - a[0]).slice(0, 3);
    const fam = D.fam[pet.f][0];
    pp.innerHTML = `<button class="x" id="ppx" aria-label="Close">×</button><b class="t">${esc(pet.a)}</b>${fmt(pet.n)} signatures · ${esc(fam)} · ${pet.st === 'open' ? 'open at retrieval' : 'closed'} · ${pet.y}<br>
      ${pet.D}% of its signatures would have to move to match the overall map. Spatial clustering (Moran's I) ${pet.I.toFixed(2)}; the 2024 vote accounts for ${pet.r2}% of its map.
      <ol>${o.map(([v, i]) => `<li>${esc(D.seats[i].n)}: ${timesTxt(v)}</li>`).join('')}</ol>
      <a href="https://petition.parliament.uk/petitions/${pet.id}" target="_blank" rel="noopener">The petition on the Parliament site</a>`;
    pp.classList.add('on');
    document.getElementById('ppx').addEventListener('click', () => pp.classList.remove('on'));
  }
  function loadSig() { return SIG ? Promise.resolve(SIG) : fetch('data/site_sig.json').then(r => r.json()).then(s => (SIG = s)); }
  function setPet(id) {
    const p = petById(id); if (!p) return;
    return loadSig().then(() => { pet = p; LQ = computeLQ(p); mode = 'pet'; refresh(); });
  }
  function setMode(m) {
    if (m === 'pet' && !pet) { setPet(700036); return; }
    mode = m; refresh();
  }
  function setView(v) {
    view = v;
    const base = map.getStyle().layers.filter(l => !['hexf', 'hexl', 'geof', 'geol', 'lblh', 'lblg', 'nat', 'background'].includes(l.id)).map(l => l.id);
    const showBase = v === 'geo' && document.getElementById('lyB').checked;
    base.forEach(id => map.setLayoutProperty(id, 'visibility', showBase ? 'visible' : 'none'));
    map.setPaintProperty('background', 'background-color', v === 'geo' ? '#F8F4EA' : PAPER);
    const S = document.getElementById('lyS').checked, O = document.getElementById('lyO').checked, L = document.getElementById('lyL').checked, N = document.getElementById('lyN').checked;
    const vis = (id, on) => map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
    vis('hexf', v === 'hex' && S); vis('hexl', v === 'hex' && O); vis('lblh', v === 'hex' && L); vis('nat', v === 'hex' && N);
    vis('geof', v === 'geo' && S); vis('geol', v === 'geo' && O); vis('lblg', v === 'geo' && L);
    map.setPaintProperty('geof', 'fill-opacity', showBase ? 0.84 : 0.94);
    map.fitBounds(v === 'hex' ? HEXB : [[-8.3, 49.9], [1.9, 58.8]], { padding: small ? { top: 200, bottom: 60, left: 10, right: 50 } : { top: 50, bottom: 50, left: 380, right: 60 }, duration: 600 });
  }
  function popup(i, ll) {
    const s = D.seats[i];
    let h = `<b class="t">${esc(s.n)}</b><div class="nt">${esc(s.rg)} · won by ${esc(D.party[s.w] || s.w.toUpperCase())} in 2024</div><table>`;
    h += `<tr><td>Signatures</td><td>${fmt(s.s)} across all ${D.pets.length} petitions</td></tr><tr><td>Per 2024 vote</td><td>${(s.s / s.vv).toFixed(2)}</td></tr>`;
    h += `<tr><td>Group</td><td>${esc(D.cl[String(s.k)][0])}</td></tr></table>`;
    if (mode === 'pet' && pet && LQ) h += `<div class="pl"><b>${esc(pet.a)}</b><br>${fmt(SIG.s[D.pets.indexOf(pet)][i])} signatures here: ${timesTxt(LQ[i])}.</div>`;
    h += `<div class="pl">Most over-signed here (petitions of 10,000+ signatures):<ol>` + s.t.map(([id, v, n]) => { const p = petById(id);
      return `<li><button class="lnk" data-p="${id}">${esc(p.a)}</button> <span class="nt">${v.toFixed(1)}x, ${fmt(n)} signatures</span></li>`; }).join('') + '</ol></div>';
    h += `<p class="nt">Tap a petition to map it. Source: UK Parliament petitions (Open Government Licence v3.0). Small counts are pulled towards the usual share.</p>`;
    const pu = new maplibregl.Popup({ maxWidth: '340px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
    pu.getElement().querySelectorAll('button[data-p]').forEach(b => b.addEventListener('click', () => { pu.remove(); setPet(b.dataset.p); }));
  }
  function setup(HEX) {
    FC = { hex: HEX.hex, geo: HEX.geo };
    HEXB = HEX.bounds;
    map.addSource('hex', { type: 'geojson', data: FC.hex, attribution: 'Petitions: UK Parliament (OGL v3.0); hexes: Open Innovations' });
    map.addSource('geo', { type: 'geojson', data: FC.geo, attribution: 'Boundaries: ONS (OGL) via voteReproject' });
    map.addSource('ph', { type: 'geojson', data: HEX.ph }); map.addSource('pg', { type: 'geojson', data: HEX.pg }); map.addSource('nat', { type: 'geojson', data: HEX.nat });
    const before = map.getStyle().layers.find(l => l.type === 'symbol');
    map.addLayer({ id: 'geof', type: 'fill', source: 'geo', paint: { 'fill-color': ['get', 'col'], 'fill-opacity': 0.92 } }, before && before.id);
    map.addLayer({ id: 'geol', type: 'line', source: 'geo', paint: { 'line-color': '#fff', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.3, 10, 1.4] } }, before && before.id);
    map.addLayer({ id: 'hexf', type: 'fill', source: 'hex', paint: { 'fill-color': ['get', 'col'] } });
    map.addLayer({ id: 'hexl', type: 'line', source: 'hex', paint: { 'line-color': PAPER, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.6, 9, 2.5] } });
    const lbl = { 'text-field': ['get', 'n'], 'text-font': ['Noto Sans Regular'], 'text-size': ['interpolate', ['linear'], ['zoom'], 7, 9.5, 10, 13], 'text-max-width': 7, 'text-optional': true };
    map.addLayer({ id: 'lblh', type: 'symbol', source: 'ph', minzoom: 7, layout: lbl, paint: { 'text-color': '#2B2119', 'text-halo-color': 'rgba(255,255,255,.85)', 'text-halo-width': 1.4 } });
    map.addLayer({ id: 'lblg', type: 'symbol', source: 'pg', minzoom: 8, layout: lbl, paint: { 'text-color': '#2B2119', 'text-halo-color': 'rgba(255,255,255,.9)', 'text-halo-width': 1.5 } });
    map.addLayer({ id: 'nat', type: 'symbol', source: 'nat', maxzoom: 8, layout: { 'text-field': ['get', 'n'], 'text-font': ['Noto Sans Regular'], 'text-size': 12, 'text-letter-spacing': 0.1, 'text-transform': 'uppercase' }, paint: { 'text-color': '#6E604E', 'text-halo-color': PAPER, 'text-halo-width': 2 } });
    ['hexf', 'geof'].forEach(l => { map.on('click', l, e => popup(e.features[0].properties.i, e.lngLat)); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    ['lyS', 'lyO', 'lyL', 'lyN', 'lyB'].forEach(id => document.getElementById(id).addEventListener('change', () => setView(view)));
    document.getElementById('vHex').addEventListener('change', () => setView('hex'));
    document.getElementById('vGeo').addEventListener('change', () => setView('geo'));
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => setMode(b.dataset.m)));
    refresh(); setView(qs.get('view') === 'geo' ? 'geo' : 'hex');
    if (qs.get('view') === 'geo') document.getElementById('vGeo').checked = true;
  }
  function goSeat(i) {
    fold(true);
    const f = FC[view].features.find(x => x.properties.i === i);
    const c = view === 'hex' ? f.geometry.coordinates[0][0] : null;
    const ll = view === 'hex' ? f.properties.c : f.properties.c;
    map.flyTo({ center: ll, zoom: view === 'hex' ? (small ? 6 : 6.4) : 9, duration: 1100, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.25 : 0.18))] });
    map.once('moveend', () => popup(i, ll));
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.seats.map((s, i) => ({ t: s.n, nn: norm(s.n), kind: 'seat', i, x: s.rg })).concat(D.pets.map(p => ({ t: p.a, nn: norm(p.a), kind: 'petition', id: p.id, x: fmt(p.n) })));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      const words = v.split(/\s+/);
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && words.every(w => x.nn.includes(w)))).slice(0, 16);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `<span class="k">${it.kind}</span>${esc(it.t)} <span>${esc(it.x)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.t; sug.style.display = 'none'; if (it.kind === 'seat') goSeat(it.i); else { fold(true); setPet(it.id); } };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }
  Promise.all([fetch('data/site.json').then(r => r.json()), fetch('data/site_geo.json').then(r => r.json())]).then(([d, hx]) => {
    D = d;
    const m0 = new maplibregl.Map({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 12, minZoom: 3.5, bounds: hx.bounds,
      fitBoundsOptions: { padding: small ? { top: 200, bottom: 60, left: 10, right: 50 } : { top: 50, bottom: 50, left: 380, right: 60 } } });
    return new Promise((res, rej) => { m0.once('load', () => res([m0, hx])); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(([mm, hx]) => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    if (!mm.getLayer('background')) mm.addLayer({ id: 'background', type: 'background', paint: { 'background-color': PAPER } }, mm.getStyle().layers[0].id);
    setup(hx); setupSearch();
    if (qs.get('p')) setPet(qs.get('p'));
    else if (mode !== 'top') setMode(mode);
    if (qs.get('seat')) { const i = D.seats.findIndex(s => norm(s.n) === norm(qs.get('seat'))); if (i >= 0) goSeat(i); }
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov-top,.lp,.keys,.pp,.mfs-btn,.maplibregl-ctrl,.maplibregl-popup')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
