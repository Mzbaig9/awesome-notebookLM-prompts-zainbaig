// Builds print-ready 6x9 front covers (0.125in bleed) for The Ihsan Series.
// Usage: node build.js  ->  writes pdf/ and preview/ next to this file.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const AUTHOR = 'Imam Ayman Al-Taher, RP';

const SERIES = {
  foundations: {
    title: 'Sacred Foundations',
    subtitle: 'An Islamic and Clinical Guide to a Successful Matrimony',
    arabic: 'سَكِينَة', ref: 'Al-Rum 30:21', arSize: 0.95,
    bg: ['#11493a', '#082a20', '#04170f'],
  },
  rabbani: {
    title: 'The Rabbani Generation',
    subtitle: 'An Islamic and Clinical Guide to Adolescent Formation',
    tagline: 'For parents, imams, and community leaders',
    arabic: 'الجِيلُ الرَّبَّانِيّ', ref: '', arSize: 0.75,
    bg: ['#1a3466', '#0d1d3d', '#060f22'],
  },
  youAre: {
    title: 'You Are the Rabbani Generation',
    subtitle: 'An Islamic and Clinical Guide for Teenagers and Young Adults',
    arabic: 'كُونُوا رَبَّانِيِّين', ref: 'Al-Imran 3:79', arSize: 0.75,
    bg: ['#3a2a6b', '#21163f', '#120b24'],
  },
  resilience: {
    title: 'Sacred Resilience',
    subtitle: 'An Islamic and Clinical Guide During Marital Hardship',
    arabic: 'صَبْرٌ جَمِيل', ref: 'Yusuf 12:18', arSize: 0.8,
    bg: ['#6a1b2c', '#3e0e19', '#22060d'],
  },
  salah: {
    title: 'Salah bi Khushu‘',
    subtitle: 'A Therapeutic Manual Integrating Mindfulness-Based Cognitive Therapy (MBCT) with Islamic Prayer Practice',
    arabic: 'خَاشِعُون', ref: 'Al-Mu’minun 23:2', arSize: 0.92,
    bg: ['#1c2738', '#0e1520', '#05080d'],
  },
};

const BOOKS = [
  { n: 1, s: 'foundations', vol: 'I', volTitle: 'Partner Selection and Pre-Marriage Preparation' },
  { n: 2, s: 'foundations', vol: 'II', volTitle: 'Nurturing Marriage, Family, and Mental Health' },
  { n: 3, s: 'rabbani', vol: 'I', volTitle: 'Understanding Who Your Teenager Is and What They Need' },
  { n: 4, s: 'rabbani', vol: 'II', volTitle: 'Navigating the Threats and the Prophetic Response' },
  { n: 5, s: 'youAre', vol: 'I', volTitle: 'I Am a Muslim Teenager: My Purpose, Identity, and Faith', audience: 'For Muslim teenagers, ages 13–18' },
  { n: 6, s: 'youAre', vol: 'II', volTitle: 'Early Adulthood: Rabbani Identity Formation and Mental Health', audience: 'For university students and young adults, ages 18–25' },
  { n: 7, s: 'resilience', vol: 'I', volTitle: 'Finding Strength Through Faith and Mental Health' },
  { n: 8, s: 'resilience', vol: 'II', volTitle: 'Family Dissolution, Divorce, and Post-Marital Healing' },
  { n: 9, s: 'salah', slug: 'salah-bi-khushu' },
];

const slug = (s) => s.toLowerCase().replace(/[‘’']/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

// Interlaced 8-point star lattice, one tile of 100 units.
function girihTile() {
  const star = (cx, cy, r) => {
    const sq = (rot) => {
      const pts = [0, 1, 2, 3].map((i) => {
        const a = rot + (i * Math.PI) / 2;
        return `${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`;
      });
      return `<polygon points="${pts.join(' ')}"/>`;
    };
    return sq(Math.PI / 4) + sq(0);
  };
  let s = '';
  for (const [x, y] of [[50, 50], [0, 0], [100, 0], [0, 100], [100, 100]]) s += star(x, y, 36);
  for (const [x, y] of [[50, 0], [0, 50], [100, 50], [50, 100]]) s += `<circle cx="${x}" cy="${y}" r="9"/>`;
  s += `<circle cx="50" cy="50" r="16"/>`;
  return s;
}

// Rub el hizb medallion (two squares + rings).
function medallion() {
  const sq = (rot, r) => {
    const pts = [0, 1, 2, 3].map((i) => {
      const a = rot + (i * Math.PI) / 2;
      return `${(100 + r * Math.cos(a)).toFixed(2)},${(100 + r * Math.sin(a)).toFixed(2)}`;
    });
    return `<polygon points="${pts.join(' ')}"/>`;
  };
  let dots = '';
  for (let i = 0; i < 8; i++) {
    const a = (i * Math.PI) / 4 + Math.PI / 8;
    dots += `<circle cx="${(100 + 74 * Math.cos(a)).toFixed(2)}" cy="${(100 + 74 * Math.sin(a)).toFixed(2)}" r="1.6" fill="url(#gold)" stroke="none"/>`;
  }
  return `
  <svg class="medallion" viewBox="0 0 200 200">
    <g fill="none" stroke="url(#gold)">
      <g stroke-width="1.6">${sq(0, 96)}${sq(Math.PI / 4, 96)}</g>
      <g stroke-width="0.6" opacity="0.8">${sq(0, 90)}${sq(Math.PI / 4, 90)}</g>
      <circle cx="100" cy="100" r="68" stroke-width="1.4"/>
      <circle cx="100" cy="100" r="63" stroke-width="0.5" opacity="0.8"/>
    </g>
    ${dots}
  </svg>`;
}

function corner(cls) {
  return `<svg class="corner ${cls}" viewBox="0 0 60 60"><g fill="none" stroke="url(#gold)" stroke-width="1.2">
    <path d="M2 40 V2 H40"/><path d="M8 30 V8 H30" stroke-width="0.6"/>
    <polygon points="14,6 22,14 14,22 6,14" transform="translate(4 4)"/>
    <circle cx="18" cy="18" r="2" fill="url(#gold)" stroke="none"/></g></svg>`;
}

function cover(b) {
  const s = SERIES[b.s];
  const [c1, c2, c3] = s.bg;
  const label = b.vol ? `The Ihsan Series &nbsp;·&nbsp; Book ${b.n}` : 'The Ihsan Series';
  const longTitle = s.title.length > 22;
  const volBlock = b.vol
    ? `<div class="vol"><div class="volnum"><span class="rule"></span>Volume ${b.vol}<span class="rule"></span></div>
         <div class="voltitle">${b.volTitle}</div>${(b.audience || s.tagline) ? `<div class="audience">${b.audience || s.tagline}</div>` : ''}</div>`
    : `<div class="vol"><div class="volnum"><span class="rule"></span>A Therapeutic Manual<span class="rule"></span></div></div>`;
  return `
  <section class="page" style="--c1:${c1};--c2:${c2};--c3:${c3}">
    <svg class="pattern" width="100%" height="100%"><rect width="100%" height="100%" fill="url(#girih)"/></svg>
    <div class="glow"></div>
    <div class="frame"></div><div class="frame inner"></div>
    ${corner('tl')}${corner('tr')}${corner('bl')}${corner('br')}
    <div class="content">
      <div class="series">${label}</div>
      <div class="medal-wrap">${medallion()}
        <div class="arabic" style="font-size:${s.arSize}in">${s.arabic}</div>
      </div>
      ${s.ref ? `<div class="ref">${s.ref}</div>` : '<div class="ref">&nbsp;</div>'}
      <h1 class="${longTitle ? 'long' : ''}">${s.title}</h1>
      <div class="subtitle">${b.vol ? s.subtitle : 'Integrating Mindfulness-Based Cognitive Therapy (MBCT) with Islamic Prayer Practice'}</div>
      ${volBlock}
      <div class="spacer"></div>
      <div class="author">${AUTHOR}</div>
      <div class="publisher">Al-Iman Family Services</div>
    </div>
  </section>`;
}

const html = `<!doctype html><html><head><meta charset="utf-8">
<style>
${fs.readFileSync(path.join(__dirname, '..', 'fonts', 'fonts.css'), 'utf8').replace(/url\(fonts\//g, 'url(../fonts/')}
@page { size: 6.25in 9.25in; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
h1, .subtitle, .voltitle, .audience { text-wrap: balance; }
html, body { background: #000; }
:root { --gold: #d9b56c; --gold-soft: #e9d3a0; }
.page { position: relative; width: 6.25in; height: 9.25in; overflow: hidden; page-break-after: always;
  background: radial-gradient(ellipse 85% 60% at 50% 34%, var(--c1) 0%, var(--c2) 55%, var(--c3) 100%); }
.pattern { position: absolute; inset: 0; opacity: 0.16; }
.glow { position: absolute; inset: 0;
  background: radial-gradient(circle at 50% 30%, rgba(233,211,160,0.16), transparent 38%),
              linear-gradient(to bottom, transparent 55%, rgba(0,0,0,0.55) 100%); }
/* trim is 0.125in in; frame sits 0.3in inside trim */
.frame { position: absolute; inset: 0.425in; border: 1.4pt solid var(--gold); }
.frame.inner { inset: 0.5in; border-width: 0.5pt; opacity: 0.75; }
.corner { position: absolute; width: 0.62in; height: 0.62in; }
.corner.tl { top: 0.36in; left: 0.36in; }
.corner.tr { top: 0.36in; right: 0.36in; transform: scaleX(-1); }
.corner.bl { bottom: 0.36in; left: 0.36in; transform: scaleY(-1); }
.corner.br { bottom: 0.36in; right: 0.36in; transform: scale(-1,-1); }
.content { position: absolute; inset: 0.78in 0.8in 0.78in; display: flex; flex-direction: column; align-items: center; text-align: center; color: var(--gold-soft); }
.series { font-family: Cinzel, serif; font-weight: 600; font-size: 9pt; letter-spacing: 0.32em; color: var(--gold); text-transform: uppercase; }
.medal-wrap { position: relative; width: 2.55in; height: 2.55in; margin-top: 0.28in; }
.medallion { position: absolute; inset: 0; width: 100%; height: 100%; }
.arabic { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; padding-bottom: 0.08in;
  font-family: Amiri, serif; font-weight: 700; color: var(--gold); direction: rtl; line-height: 1; white-space: nowrap; }
.ref { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 10pt; color: var(--gold); opacity: 0.85; margin-top: 0.08in; letter-spacing: 0.04em; }
h1 { font-family: 'Cormorant Garamond', serif; font-weight: 700; font-size: 42pt; line-height: 1.02; color: #f6e7c3; margin-top: 0.22in; letter-spacing: 0.01em; }
h1.long { font-size: 35pt; }
.subtitle { font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 500; font-size: 14.5pt; line-height: 1.25; color: var(--gold-soft); margin-top: 0.14in; max-width: 4.1in; }
.vol { margin-top: 0.3in; max-width: 4.2in; }
.volnum { font-family: Cinzel, serif; font-weight: 600; font-size: 10pt; letter-spacing: 0.3em; color: var(--gold); text-transform: uppercase; display: flex; align-items: center; justify-content: center; gap: 0.14in; }
.volnum .rule { display: inline-block; width: 0.55in; height: 0; border-top: 0.6pt solid var(--gold); }
.voltitle { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 17pt; line-height: 1.18; color: #f6e7c3; margin-top: 0.1in; }
.audience { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 12pt; color: var(--gold); margin-top: 0.06in; }
.spacer { flex: 1; }
.author { font-family: Cinzel, serif; font-weight: 600; font-size: 12.5pt; letter-spacing: 0.16em; color: #f6e7c3; text-transform: uppercase; }
.publisher { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 11pt; color: var(--gold); margin-top: 0.05in; letter-spacing: 0.06em; }
</style></head><body>
<svg width="0" height="0" style="position:absolute"><defs>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#f3dfa8"/><stop offset="0.45" stop-color="#c99a4a"/><stop offset="0.7" stop-color="#e8cc85"/><stop offset="1" stop-color="#a87a32"/>
  </linearGradient>
  <pattern id="girih" width="0.9in" height="0.9in" patternUnits="userSpaceOnUse" viewBox="0 0 100 100">
    <g fill="none" stroke="#e9d3a0" stroke-width="1.1">${girihTile()}</g>
  </pattern>
</defs></svg>
${BOOKS.map(cover).join('\n')}
</body></html>`;

(async () => {
  const out = __dirname;
  fs.mkdirSync(path.join(out, 'pdf'), { recursive: true });
  fs.mkdirSync(path.join(out, 'preview'), { recursive: true });
  fs.writeFileSync(path.join(out, 'covers.html'), html);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 600, height: 888 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.join(out, 'covers.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => {
    const ppi = 96, maxW = 1.62 * ppi;
    document.querySelectorAll('.arabic').forEach((el) => {
      const span = document.createElement('span');
      span.textContent = el.textContent; el.textContent = ''; el.appendChild(span);
      let size = parseFloat(el.style.fontSize) * ppi;
      while (span.getBoundingClientRect().width > maxW && size > 10) el.style.fontSize = (size -= 1) + 'px';
    });
  });

  const pdfOpts = { width: '6.25in', height: '9.25in', printBackground: true, preferCSSPageSize: true };
  await page.pdf({ ...pdfOpts, path: path.join(out, 'pdf', 'ihsan-series-all-covers.pdf') });

  const sections = await page.$$('section.page');
  for (let i = 0; i < BOOKS.length; i++) {
    const b = BOOKS[i];
    const name = b.slug || `book-${b.n}-${slug(SERIES[b.s].title)}-vol-${b.vol.toLowerCase()}`;
    await sections[i].screenshot({ path: path.join(out, 'preview', `${name}.png`) });
    // single-cover PDF: hide every other section
    await page.evaluate((idx) => document.querySelectorAll('section.page').forEach((el, j) => (el.style.display = j === idx ? '' : 'none')), i);
    await page.pdf({ ...pdfOpts, path: path.join(out, 'pdf', `${name}.pdf`) });
    await page.evaluate(() => document.querySelectorAll('section.page').forEach((el) => (el.style.display = '')));
  }
  await browser.close();
})();
