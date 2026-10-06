// Full-wrap print covers (back + spine + front) for The Ihsan Series, 6x9 trim, 0.125in bleed.
// Usage: node build.js  ->  pdf/<book>.pdf plus preview/<book>-front.png and preview/<book>-wrap.png
// Set PAGES per book once page counts are final; spine width = pages x PAPER_IN_PER_PAGE.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const TRIM_W = 6, TRIM_H = 9, BLEED = 0.125;
const PAPER_IN_PER_PAGE = 0.002252; // KDP/IngramSpark white paper
const DEFAULT_PAGES = 250;          // placeholder until real counts are known
const PAGES = { 1: null, 2: null, 3: null, 4: null, 5: null, 6: null, 7: null, 8: null, 9: null };

const AUTHOR = 'Ayman Al-Taher';
const CREDS = ['RP · Registered Psychotherapist', 'Founder of Al Iman Family Services', 'Former Clinician, 27 Years at SickKids Hospital'];
const PUBLISHER = 'Published by Al Iman Family Services (AIFS) · aifs.ca';
const TAGLINE = 'Through Faith, Science and Clinical Practice';
const NUM = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];

const QUOTES = [
  'He has taken a non-traditional approach that still remains grounded in Islamic values and our way of life… He listens with intention, creates a space that feels safe and balanced for both of us, and encourages empathy in a way that feels practical and deeply respectful.',
  'His approach is calm, clear, and compassionate, and always rooted in what will benefit the marriage, not just the individual.',
  'He combines his excellent grasp of the subject matter with a high level of empathy, kindness, trustworthiness and respect for his clientele.',
];

// top = upper field, bottom = lower field (also the title colour), ink = pattern tint, wall/table = illustration scene
const SERIES = {
  foundations: { title: 'Sacred Foundations', guide: 'An Islamic Guide to a Successful Matrimony',
    top: '#a9ae78', bottom: '#e5603d', bottom2: '#d9472f', accent: '#d8452c', ink: '#8f9560', motif: 'pomegranate',
    wall: ['#4a5655', '#2b3434'], table: ['#6f7675', '#4c5352'], category: 'Religion / Islam / Marriage & Family' },
  rabbani: { title: 'The Rabbani Generation', guide: 'An Islamic and Clinical Guide to Adolescent Formation',
    top: '#a9c1c8', bottom: '#245a7d', bottom2: '#1b4764', accent: '#20577a', ink: '#8eaab3', motif: 'olive',
    wall: ['#3f4f5a', '#26323b'], table: ['#6c757a', '#495156'], category: 'Religion / Islam / Parenting' },
  youAre: { title: 'You Are the Rabbani Generation', guide: 'An Islamic and Clinical Guide for Teenagers and Young Adults',
    top: '#e3cd98', bottom: '#1f7a70', bottom2: '#17635b', accent: '#1b6e65', ink: '#cdb47b', motif: 'star',
    wall: ['#3c4a4c', '#243032'], table: ['#7a6d5c', '#54493c'], category: 'Religion / Islam / Young Adult' },
  resilience: { title: 'Sacred Resilience', guide: 'An Islamic and Clinical Guide During Marital Hardship',
    top: '#d8b3a6', bottom: '#7b2f40', bottom2: '#652434', accent: '#7b2f40', ink: '#c39a8c', motif: 'olive',
    wall: ['#4a4041', '#2e2627'], table: ['#77695f', '#544941'], category: 'Family & Relationships / Divorce & Separation' },
  salah: { title: 'Salah bi Khushu‘', guide: 'A Therapeutic Manual for Islamic Prayer',
    top: '#c9d4c2', bottom: '#2f5c48', bottom2: '#244a3a', accent: '#2c5a45', ink: '#adbca5', motif: 'arch',
    wall: ['#3c4a41', '#242e28'], table: ['#6e6152', '#4c4237'], category: 'Religion / Islam / Prayer & Spirituality' },
};

const BOOKS = [
  { n: 1, s: 'foundations', vol: 'I', volTitle: 'Partner Selection and Pre-Marriage Preparation',
    hook: 'Before you say yes, know what you are building.',
    blurb: [
      'In this practical guide, Imam Ayman Al-Taher draws on decades of clinical experience and Islamic scholarship to help Muslims choose a spouse with clarity, and prepare for marriage with intention. Integrating traditional Islamic teachings with evidence-based psychology, it gives individuals and families the questions, the tools and the self-knowledge they need before the nikah, not after it.',
      'From knowing yourself and your own family patterns to discerning character, compatibility and readiness, <i>Sacred Foundations</i> addresses what pre-marriage preparation should actually look like.'],
    close: 'Whether you are searching, already speaking with someone, or guiding a son or daughter, this book offers faith-aligned, scientifically grounded support for a marriage built on <i>sakinah</i>, <i>mawaddah</i> and <i>rahmah</i>.' },
  { n: 2, s: 'foundations', vol: 'II', volTitle: 'Nurturing Marriage, Family, and Mental Health',
    hook: 'The wedding celebration has ended. Now the real journey begins.',
    blurb: [
      'In this transformative guide, Imam Ayman Al-Taher draws on decades of clinical experience and Islamic scholarship to help couples build marriages that last a lifetime. Integrating traditional Islamic teachings with evidence-based psychology and neuroscience, it gives couples the practical wisdom they need to navigate the critical years of marriage and family life.',
      'From healthy communication and conflict to in-laws, parenthood and mental health, <i>Sacred Foundations</i> addresses the real challenges couples face when “I do” becomes daily life.'],
    close: 'Whether you are in your first year of marriage or strengthening the foundations you have already built, this book offers faith-aligned, scientifically grounded support for a partnership filled with <i>sakinah</i>, <i>mawaddah</i> and <i>rahmah</i>.' },
  { n: 3, s: 'rabbani', vol: 'I', volTitle: 'Understanding Who Your Teenager Is and What They Need', audience: 'For parents, imams, and community leaders',
    hook: 'Your teenager is not a problem to solve. They are an amanah to understand.',
    blurb: [
      'Adolescence is where faith, identity and mental health are formed, and where many Muslim families feel they lose their children. Imam Ayman Al-Taher brings together the Prophetic model of raising young people with what clinical psychology and neuroscience now teach about the teenage brain.',
      'Written for parents, imams and community leaders, this volume explains who teenagers really are, what they need at each stage, and how adults can build the trust that makes guidance possible.'],
    close: 'A faith-aligned, clinically grounded roadmap for raising a generation that is <i>rabbani</i>: rooted in Allah, secure in who they are, and ready for the world they live in.' },
  { n: 4, s: 'rabbani', vol: 'II', volTitle: 'Navigating the Threats and the Prophetic Response', audience: 'For parents, imams, and community leaders',
    hook: 'The threats are real. So is the Prophetic response.',
    blurb: [
      'Screens, pornography, substances, identity confusion, anxiety and doubt reach Muslim teenagers earlier and harder than ever. In this second volume, Imam Ayman Al-Taher names these threats plainly and explains, as a clinician, how they take hold of a young mind.',
      'He then sets out the Prophetic response: how the Messenger of Allah ﷺ guided young people with mercy, firmness and trust, and how parents, imams and communities can apply that model today.'],
    close: 'For every adult who wants to protect young people without pushing them away, this book offers faith-aligned, clinically grounded strategies that work in real homes and real masajid.' },
  { n: 5, s: 'youAre', vol: 'I', volTitle: 'I Am a Muslim Teenager: My Purpose, Identity, and Faith', audience: 'For Muslim teenagers, ages 13–18',
    hook: 'You were made for more than the noise around you.',
    blurb: [
      'Who am I? Why am I here? Does my faith actually fit the life I am living? Written directly for Muslim teenagers, this book takes those questions seriously and answers them honestly, through the Quran, the Sunnah and what psychology teaches about growing up.',
      'Imam Ayman Al-Taher helps young readers understand their emotions, their friendships, their pressures and their relationship with Allah, and shows them how to build an identity that is strong, calm and their own.'],
    close: 'A faith-aligned, clinically grounded companion for every Muslim teenager who wants to know who they are, and who they are meant to become.' },
  { n: 6, s: 'youAre', vol: 'II', volTitle: 'Early Adulthood: Rabbani Identity Formation and Mental Health', audience: 'For university students and young adults, ages 18–25',
    hook: 'Between childhood and adulthood, your identity is being written.',
    blurb: [
      'University, work, independence, marriage questions and mental health all arrive at once in early adulthood, often far from home and far from support. Imam Ayman Al-Taher speaks directly to Muslim students and young adults navigating that transition.',
      'Bringing together Islamic scholarship and clinical practice, he explains how a <i>rabbani</i> identity is formed, how anxiety, burnout and doubt can be faced with faith and evidence-based tools, and how to build a life of purpose.'],
    close: 'For every young Muslim between 18 and 25 who wants a faith that holds, and a mind that is well.' },
  { n: 7, s: 'resilience', vol: 'I', volTitle: 'Finding Strength Through Faith and Mental Health',
    hook: 'When a marriage is tested, faith does not have to break.',
    blurb: [
      'Every marriage meets hardship: conflict that will not resolve, distance, betrayal, illness, financial strain. In this volume, Imam Ayman Al-Taher offers spouses a way through that is honest about the pain and grounded in both Islamic teaching and clinical practice.',
      'Drawing on decades of counselling Muslim couples, he shows how <i>sabr</i>, <i>tawakkul</i> and evidence-based mental health care work together to protect the heart, the marriage and the children.'],
    close: 'For any spouse who feels alone in a difficult marriage, this book offers faith-aligned, clinically grounded strength for the road ahead.' },
  { n: 8, s: 'resilience', vol: 'II', volTitle: 'Family Dissolution, Divorce, and Post-Marital Healing',
    hook: 'An ending is not the end of your story.',
    blurb: [
      'Divorce is permitted in Islam, yet it is often lived in silence and shame. Imam Ayman Al-Taher addresses family dissolution with the care of a clinician and the clarity of an imam: the Islamic framework, the emotional reality, and the impact on children.',
      'From the decision itself to co-parenting and rebuilding, this volume guides individuals and families through grief toward healing, dignity and renewed faith.'],
    close: 'A faith-aligned, clinically grounded companion for anyone walking through divorce, and for the families and imams who support them.' },
  { n: 9, s: 'salah', slug: 'salah-bi-khushu', volTitle: 'Integrating Mindfulness-Based Cognitive Therapy with Islamic Prayer',
    hook: 'Bring your heart back to your prayer.',
    blurb: [
      'Many Muslims pray five times a day and still feel distracted, anxious or absent in their salah. In this therapeutic manual, Imam Ayman Al-Taher integrates Mindfulness-Based Cognitive Therapy (MBCT) with the practice of Islamic prayer.',
      'Step by step, it shows how attention, breath, thought and emotion can be gently trained so that each prayer becomes a place of presence, calm and connection with Allah.'],
    close: 'For individuals, clinicians and imams seeking a faith-aligned, evidence-based path to <i>khushu‘</i>, and to the healing it brings.' },
];

// ---------- illustration helpers (viewBox 0 0 400 400) ----------
const f = (n) => +n.toFixed(1);
function leaf(x, y, len, ang, id, w = 0.32) {
  const h = len * w;
  return `<g transform="translate(${f(x)} ${f(y)}) rotate(${f(ang)})">
    <path d="M0 0 Q${f(len * 0.45)} ${f(-h)} ${f(len)} 0 Q${f(len * 0.45)} ${f(h)} 0 0Z" fill="url(#${id}-leaf)"/>
    <path d="M0 0 L${f(len * 0.92)} 0" stroke="#2f3a1f" stroke-opacity=".35" stroke-width="1"/></g>`;
}
function shadow(cx, cy, rx, ry, o = 0.32) {
  return `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#000" opacity="${o}"/>`;
}
function pomegranate(cx, cy, r, id) {
  return `<g>
    <path d="M${f(cx - r * .24)} ${f(cy - r * .86)} L${f(cx - r * .3)} ${f(cy - r * 1.2)} L${f(cx - r * .13)} ${f(cy - r * 1.04)} L${f(cx)} ${f(cy - r * 1.26)} L${f(cx + r * .13)} ${f(cy - r * 1.04)} L${f(cx + r * .3)} ${f(cy - r * 1.2)} L${f(cx + r * .24)} ${f(cy - r * .86)}Z" fill="url(#${id}-crown)"/>
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#${id}-pom)"/>
    <ellipse cx="${f(cx - r * .36)}" cy="${f(cy - r * .38)}" rx="${f(r * .24)}" ry="${f(r * .12)}" fill="#fff" opacity=".28" transform="rotate(-35 ${f(cx - r * .36)} ${f(cy - r * .38)})"/>
  </g>`;
}
function ring(cx, cy, rx, ry, id) {
  return `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="#6b4f1e" stroke-width="8"/>
    <ellipse cx="${cx}" cy="${cy - 1}" rx="${rx}" ry="${ry}" fill="none" stroke="url(#${id}-gold)" stroke-width="6"/>`;
}

function illustration(b) {
  const s = SERIES[b.s], id = `i${b.n}`, v2 = b.vol === 'II';
  const defs = `<defs>
    <clipPath id="${id}-clip"><circle cx="200" cy="200" r="200"/></clipPath>
    <linearGradient id="${id}-wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${s.wall[1]}"/><stop offset="1" stop-color="${s.wall[0]}"/></linearGradient>
    <linearGradient id="${id}-table" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${s.table[0]}"/><stop offset="1" stop-color="${s.table[1]}"/></linearGradient>
    <radialGradient id="${id}-light" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#fff" stop-opacity=".16"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".38"/></radialGradient>
    <radialGradient id="${id}-pom" cx=".38" cy=".34" r=".7"><stop offset="0" stop-color="#f28466"/><stop offset=".45" stop-color="#d4453a"/><stop offset=".85" stop-color="#9a2128"/><stop offset="1" stop-color="#6a1418"/></radialGradient>
    <linearGradient id="${id}-crown" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c2493c"/><stop offset="1" stop-color="#7d1d20"/></linearGradient>
    <linearGradient id="${id}-leaf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a7a65c"/><stop offset=".5" stop-color="#6f7a3a"/><stop offset="1" stop-color="#3f4a26"/></linearGradient>
    <linearGradient id="${id}-oleaf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#b9c4a8"/><stop offset="1" stop-color="#5f7259"/></linearGradient>
    <linearGradient id="${id}-gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f5e1a4"/><stop offset=".5" stop-color="#c79a45"/><stop offset="1" stop-color="#8d6526"/></linearGradient>
    <linearGradient id="${id}-wood" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a7713f"/><stop offset="1" stop-color="#5d3a1e"/></linearGradient>
    <linearGradient id="${id}-clay" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9c4f2c"/><stop offset=".4" stop-color="#c8774a"/><stop offset="1" stop-color="#7a3a20"/></linearGradient>
    <linearGradient id="${id}-glaze" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#173a40"/><stop offset=".4" stop-color="#2f6670"/><stop offset="1" stop-color="#112a2f"/></linearGradient>
    <radialGradient id="${id}-glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ffd27a" stop-opacity=".55"/><stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></radialGradient>
    <linearGradient id="${id}-page" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#f3ead3"/><stop offset="1" stop-color="#d9cba7"/></linearGradient>
  </defs>`;
  const horizon = b.s === 'salah' ? 268 : 282;
  let scene = `<rect width="400" height="400" fill="url(#${id}-wall)"/>
    <rect y="${horizon}" width="400" height="${400 - horizon}" fill="url(#${id}-table)"/>
    <rect y="${horizon}" width="400" height="3" fill="#fff" opacity=".12"/>`;

  if (b.s === 'foundations') {
    // branch with leaves and small fruits rising from the main pomegranate
    scene += `<path d="M205 228 C215 180 240 150 262 120 S300 70 318 52" stroke="#5a4127" stroke-width="5" fill="none" stroke-linecap="round"/>
      <path d="M238 160 C262 160 285 172 300 190" stroke="#5a4127" stroke-width="3.5" fill="none" stroke-linecap="round"/>
      <path d="M262 120 C240 108 222 90 214 70" stroke="#5a4127" stroke-width="3" fill="none" stroke-linecap="round"/>`;
    [[230, 172, 52, -150], [244, 150, 56, -30], [270, 112, 50, -160], [284, 98, 54, -20], [300, 70, 46, -60], [214, 72, 44, -110], [226, 96, 46, -175],
     [292, 186, 46, 30], [270, 170, 42, 70], [318, 52, 40, -40], [252, 136, 44, 20]].forEach(([x, y, l, a]) => (scene += leaf(x, y, l, a, id)));
    scene += pomegranate(304, 206, 20, id) + pomegranate(266, 110, 16, id);
    if (v2) {
      // second large fruit for the family volume
      scene += shadow(118, 344, 60, 11) + pomegranate(118, 300, 44, id);
    }
    scene += shadow(205, 352, 92, 16) + pomegranate(198, 280, 72, id);
    scene += shadow(316, 366, 44, 8, .25) + ring(300, 356, 26, 10, id) + ring(330, 352, 24, 9, id);
  }

  if (b.s === 'rabbani') {
    const tall = v2 ? 1.15 : 1;
    // lantern glow + lantern
    scene += `<circle cx="305" cy="245" r="95" fill="url(#${id}-glow)"/>` + shadow(305, 338, 50, 9);
    scene += `<g><path d="M305 150 v12" stroke="url(#${id}-gold)" stroke-width="3"/><circle cx="305" cy="146" r="6" fill="none" stroke="url(#${id}-gold)" stroke-width="3"/>
      <path d="M275 200 Q305 150 335 200Z" fill="url(#${id}-gold)"/><rect x="270" y="198" width="70" height="10" rx="2" fill="#8d6526"/>
      <rect x="276" y="208" width="58" height="104" fill="#ffcc6b"/><rect x="276" y="208" width="58" height="104" fill="url(#${id}-glow)"/>
      <path d="M285 208 v104 M305 208 v104 M325 208 v104" stroke="#8d6526" stroke-width="3"/>
      <path d="M276 240 h58 M276 280 h58" stroke="#8d6526" stroke-width="2" opacity=".7"/>
      <rect x="276" y="208" width="58" height="104" fill="none" stroke="url(#${id}-gold)" stroke-width="4"/>
      <ellipse cx="305" cy="262" rx="9" ry="16" fill="#fff6d8"/>
      <rect x="266" y="312" width="78" height="12" rx="2" fill="url(#${id}-gold)"/><rect x="272" y="324" width="66" height="10" rx="2" fill="#8d6526"/></g>`;
    // olive sapling in a clay pot
    scene += shadow(165, 362, 70, 12);
    const top = 300 - 190 * tall;
    scene += `<path d="M162 300 C160 250 172 210 166 ${f(top + 40)}" stroke="#6b4e33" stroke-width="8" fill="none" stroke-linecap="round"/>
      <path d="M165 230 C140 205 125 190 110 ${f(top + 70)}" stroke="#6b4e33" stroke-width="4.5" fill="none" stroke-linecap="round"/>
      <path d="M167 205 C190 185 205 170 220 ${f(top + 55)}" stroke="#6b4e33" stroke-width="4.5" fill="none" stroke-linecap="round"/>`;
    const L = [[110, top + 70, -120], [104, top + 92, -170], [124, top + 80, -60], [130, 205, -150], [140, 196, -40], [220, top + 55, -60], [230, top + 70, -10], [206, top + 66, -110],
      [190, 180, 20], [196, 168, -100], [166, top + 40, -90], [158, top + 50, -140], [176, top + 52, -40], [150, 225, 170], [178, 228, 10], [118, top + 105, 160], [214, 150, 30]];
    L.forEach(([x, y, a]) => (scene += leaf(x, y, 30 * tall, a, id + '', 0.22).replace(`url(#${id}-leaf)`, `url(#${id}-oleaf)`)));
    if (v2) [[120, top + 95], [212, top + 82], [184, 192], [142, 210]].forEach(([x, y]) => (scene += `<ellipse cx="${x}" cy="${f(y)}" rx="5" ry="7" fill="#3d3446"/>`));
    scene += `<path d="M120 296 L210 296 L196 362 L134 362Z" fill="url(#${id}-clay)"/><rect x="112" y="284" width="106" height="18" rx="4" fill="url(#${id}-clay)"/>
      <path d="M120 320 h86" stroke="#6b3018" stroke-width="2" opacity=".5"/>`;
  }

  if (b.s === 'youAre') {
    // arched window with crescent and star
    scene += `<path d="M48 250 V120 A55 55 0 0 1 158 120 V250Z" fill="#1c2a47"/>
      <path d="M48 250 V120 A55 55 0 0 1 158 120 V250Z" fill="none" stroke="#c9a96a" stroke-width="5"/>
      <path d="M103 66 V250 M48 170 H158" stroke="#c9a96a" stroke-width="3" opacity=".8"/>
      <circle cx="128" cy="112" r="20" fill="#f3dfa0"/><circle cx="138" cy="104" r="18" fill="#1c2a47"/>
      <path d="M74 135 l3 8 8 0 -6 5 2 8 -7 -5 -7 5 2 -8 -6 -5 8 0Z" fill="#f3dfa0"/>
      <rect x="40" y="250" width="126" height="10" fill="#8a7454"/>`;
    // rehal with open book
    scene += shadow(222, 360, 92, 13);
    scene += `<path d="M150 360 L290 250 L302 262 L170 368Z" fill="url(#${id}-wood)"/><path d="M294 360 L154 250 L142 262 L274 368Z" fill="url(#${id}-wood)"/>
      <path d="M142 262 Q222 300 302 262" stroke="#4a2e17" stroke-width="3" fill="none"/>
      <path d="M222 286 Q186 262 140 270 L150 220 Q190 210 222 236Z" fill="url(#${id}-page)"/>
      <path d="M222 286 Q258 262 304 270 L294 220 Q254 210 222 236Z" fill="#efe4c8"/>
      <path d="M222 236 V286" stroke="#a8956c" stroke-width="2"/>`;
    for (let i = 0; i < 6; i++) {
      scene += `<path d="M${156 + i * 1.5} ${232 + i * 8} Q190 ${226 + i * 8} 214 ${244 + i * 7}" stroke="#7a6a4c" stroke-width="1.4" fill="none" opacity=".55"/>`;
      scene += `<path d="M${288 - i * 1.5} ${232 + i * 8} Q254 ${226 + i * 8} 230 ${244 + i * 7}" stroke="#7a6a4c" stroke-width="1.4" fill="none" opacity=".55"/>`;
    }
    if (v2) {
      scene += shadow(340, 352, 46, 8) + `<rect x="300" y="322" width="84" height="22" rx="2" fill="#7b2f40"/><rect x="306" y="300" width="74" height="22" rx="2" fill="#245a7d"/>
        <rect x="296" y="278" width="80" height="22" rx="2" fill="#c9a24a"/><path d="M300 333 h84 M306 311 h74 M296 289 h80" stroke="#fff" stroke-opacity=".35" stroke-width="2"/>`;
    } else {
      scene += shadow(338, 356, 34, 7) + `<path d="M318 312 L358 312 L352 352 L324 352Z" fill="url(#${id}-clay)"/><rect x="314" y="304" width="48" height="10" rx="3" fill="url(#${id}-clay)"/>
        <path d="M338 306 C336 286 340 272 338 258" stroke="#5d7a3a" stroke-width="3" fill="none"/>` + leaf(338, 276, 26, -150, id, .4) + leaf(338, 268, 28, -30, id, .4);
    }
  }

  if (b.s === 'resilience') {
    if (v2) {
      scene += `<circle cx="320" cy="230" r="70" fill="url(#${id}-glow)"/>` + shadow(320, 352, 30, 6)
        + `<rect x="304" y="262" width="32" height="88" rx="3" fill="#efe6d2"/><rect x="304" y="262" width="10" height="88" fill="#fff" opacity=".35"/>
           <path d="M320 262 v-8" stroke="#3a2a1a" stroke-width="2"/><path d="M320 222 C330 236 328 250 320 254 C312 250 310 236 320 222Z" fill="#ffd27a"/>
           <path d="M320 234 C324 242 323 249 320 251 C317 249 316 242 320 234Z" fill="#fff6d8"/>`;
    }
    // kintsugi bowl
    const bx = v2 ? 190 : 205;
    scene += shadow(bx + 6, 352, 108, 15);
    scene += `<path d="M${bx - 100} 252 Q${bx - 98} 346 ${bx} 348 Q${bx + 98} 346 ${bx + 100} 252Z" fill="url(#${id}-glaze)"/>
      <ellipse cx="${bx}" cy="252" rx="100" ry="20" fill="#0d2226"/><ellipse cx="${bx}" cy="252" rx="100" ry="20" fill="none" stroke="#3f7a84" stroke-width="3"/>
      <path d="M${bx - 60} 262 L${bx - 48} 290 L${bx - 62} 312 L${bx - 40} 336" stroke="url(#${id}-gold)" stroke-width="3.2" fill="none" stroke-linejoin="round"/>
      <path d="M${bx + 30} 268 L${bx + 18} 296 L${bx + 40} 318 L${bx + 30} 344" stroke="url(#${id}-gold)" stroke-width="3.2" fill="none" stroke-linejoin="round"/>
      <path d="M${bx - 48} 290 L${bx - 10} 300 L${bx + 18} 296" stroke="url(#${id}-gold)" stroke-width="2.4" fill="none"/>
      <path d="M${bx - 20} 233 L${bx - 4} 252 L${bx + 22} 240" stroke="url(#${id}-gold)" stroke-width="2.4" fill="none"/>
      <ellipse cx="${bx - 62}" cy="292" rx="10" ry="26" fill="#fff" opacity=".12"/>`;
    // olive branch on the table
    scene += `<path d="M60 372 C120 360 170 368 240 378" stroke="#5a4127" stroke-width="3.5" fill="none" stroke-linecap="round"/>`;
    [[80, 368, -150], [100, 364, -30], [125, 362, -160], [150, 364, 20], [175, 366, -20], [200, 370, 160], [225, 375, -15]].forEach(([x, y, a]) =>
      (scene += leaf(x, y, 30, a, id, .24).replace(`url(#${id}-leaf)`, `url(#${id}-oleaf)`)));
    [[112, 376], [162, 378], [212, 384]].forEach(([x, y]) => (scene += `<ellipse cx="${x}" cy="${y}" rx="6" ry="8" fill="#2f2a3a"/>`));
  }

  if (b.s === 'salah') {
    // mihrab niche with hanging lamp
    scene += `<path d="M120 268 V140 Q120 70 200 40 Q280 70 280 140 V268Z" fill="#1b2420"/>
      <path d="M120 268 V140 Q120 70 200 40 Q280 70 280 140 V268" fill="none" stroke="#c9a96a" stroke-width="5"/>
      <path d="M132 268 V144 Q132 84 200 56 Q268 84 268 144 V268" fill="none" stroke="#c9a96a" stroke-width="1.5" opacity=".6"/>
      <circle cx="200" cy="168" r="70" fill="url(#${id}-glow)"/>
      <path d="M200 56 V138" stroke="url(#${id}-gold)" stroke-width="2"/>
      <path d="M184 140 h32 l-6 34 h-20Z" fill="url(#${id}-gold)"/><path d="M188 148 h24 l-4 22 h-16Z" fill="#ffd27a"/>`;
    // prayer rug in perspective
    scene += `<path d="M112 278 L288 278 L360 400 L40 400Z" fill="#8e2f33"/>
      <path d="M124 286 L276 286 L338 392 L62 392Z" fill="none" stroke="url(#${id}-gold)" stroke-width="3"/>
      <path d="M134 294 L266 294 L322 388 L78 388Z" fill="#6f2229"/>
      <path d="M160 388 L176 330 Q200 300 224 330 L240 388" fill="none" stroke="url(#${id}-gold)" stroke-width="2.5"/>
      <path d="M190 388 L196 348 Q200 340 204 348 L210 388" fill="none" stroke="#e8cf92" stroke-width="1.5" opacity=".7"/>`;
    // tasbih beads
    for (let i = 0; i < 33; i++) {
      const a = (i / 33) * Math.PI * 2;
      scene += `<circle cx="${f(290 + 34 * Math.cos(a))}" cy="${f(352 + 12 * Math.sin(a))}" r="3.6" fill="#ead9ad" stroke="#8a6d3e" stroke-width=".6"/>`;
    }
    scene += `<path d="M256 352 L238 372" stroke="#ead9ad" stroke-width="2"/><path d="M238 372 l-6 18 M238 372 l0 19 M238 372 l6 17" stroke="#c9a96a" stroke-width="1.6"/>`;
  }

  return `<svg viewBox="0 0 400 400" class="illus">${defs}<g clip-path="url(#${id}-clip)">${scene}<rect width="400" height="400" fill="url(#${id}-light)"/></g></svg>`;
}

// tone-on-tone motif tiles for the top field
function motif(kind, ink) {
  const icon = {
    pomegranate: (x, y) => `<circle cx="${x}" cy="${y}" r="13"/><path d="M${x - 5} ${y - 11} l-2 -7 4 3 3 -5 3 5 4 -3 -2 7Z"/>`,
    olive: (x, y) => `<path d="M${x - 14} ${y + 8} Q${x} ${y} ${x + 14} ${y - 10}" stroke="${ink}" stroke-width="2" fill="none"/>
      <ellipse cx="${x - 6}" cy="${y - 1}" rx="7" ry="3" transform="rotate(-50 ${x - 6} ${y - 1})"/><ellipse cx="${x + 2}" cy="${y + 4}" rx="7" ry="3" transform="rotate(30 ${x + 2} ${y + 4})"/>
      <ellipse cx="${x + 8}" cy="${y - 9}" rx="7" ry="3" transform="rotate(-70 ${x + 8} ${y - 9})"/><circle cx="${x - 9}" cy="${y + 9}" r="3"/>`,
    star: (x, y) => `<rect x="${x - 10}" y="${y - 10}" width="20" height="20"/><rect x="${x - 10}" y="${y - 10}" width="20" height="20" transform="rotate(45 ${x} ${y})"/>`,
    arch: (x, y) => `<path d="M${x - 11} ${y + 14} V${y - 2} Q${x - 11} ${y - 12} ${x} ${y - 17} Q${x + 11} ${y - 12} ${x + 11} ${y - 2} V${y + 14}Z"/>`,
  }[kind];
  return `<pattern id="motif" width="64" height="64" patternUnits="userSpaceOnUse"><g fill="${ink}">${icon(16, 16)}${icon(48, 48)}</g></pattern>`;
}

function wrapHtml(b, css) {
  const s = SERIES[b.s];
  const pages = PAGES[b.n] || DEFAULT_PAGES;
  const spine = +(pages * PAPER_IN_PER_PAGE).toFixed(3);
  const W = BLEED * 2 + TRIM_W * 2 + spine, H = TRIM_H + BLEED * 2;
  const backX = BLEED, spineX = BLEED + TRIM_W, frontX = spineX + spine;
  const split = 5.0; // in, from top edge of the bleed box
  const bookLine = b.vol ? `Book ${NUM[b.n]} &nbsp;·&nbsp; ${s.title} &nbsp;·&nbsp; Volume ${b.vol}` : 'The Ihsan Series &nbsp;·&nbsp; Companion Manual';
  const bottomLine = b.audience || TAGLINE;
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
${css}
@page { size: ${W}in ${H}in; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { width: ${W}in; height: ${H}in; position: relative; overflow: hidden; background: ${s.bottom}; -webkit-print-color-adjust: exact; }
.top { position: absolute; left: 0; top: 0; width: 100%; height: ${split}in; background: ${s.top}; }
.top svg { position: absolute; inset: 0; width: 100%; height: 100%; opacity: .55; }
.bottom { position: absolute; left: 0; top: ${split}in; width: 100%; bottom: 0;
  background: repeating-linear-gradient(112deg, rgba(255,255,255,.055) 0 .7in, rgba(255,255,255,0) .7in 1.6in), linear-gradient(180deg, ${s.bottom}, ${s.bottom2}); }
.panel { position: absolute; top: ${BLEED}in; height: ${TRIM_H}in; }
.front { left: ${frontX}in; width: ${TRIM_W}in; text-align: center; color: #fff; }
.author { position: absolute; top: .34in; left: 0; right: 0; font-family: Cinzel; font-weight: 600; font-size: 21pt; letter-spacing: .1em; color: #fff; }
.creds { position: absolute; top: .76in; left: 0; right: 0; font-family: Montserrat; font-weight: 500; font-size: 6.6pt; line-height: 1.55; letter-spacing: .04em; color: rgba(255,255,255,.92); }
.title { position: absolute; top: 1.24in; left: .4in; right: .4in; font-family: Montserrat; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; line-height: 1.02; color: ${s.accent}; text-wrap: balance; }
.voltitle { position: absolute; left: .55in; right: .55in; font-family: Montserrat; font-weight: 700; font-size: 8.6pt; letter-spacing: .2em; line-height: 1.5; text-transform: uppercase; color: ${s.accent}; text-wrap: balance; }
.circle { position: absolute; width: 3.55in; height: 3.55in; left: ${(TRIM_W - 3.55) / 2}in; top: ${split - BLEED - 1.6}in; border-radius: 50%;
  box-shadow: 0 .1in .28in rgba(0,0,0,.35), 0 0 0 .045in rgba(255,255,255,.18); overflow: hidden; }
.circle svg { width: 100%; height: 100%; display: block; }
.artbg { position: absolute; inset: -12%; width: 124%; height: 124%; object-fit: cover; filter: blur(16px) brightness(.8); }
.artfg { position: absolute; left: 50%; top: 50%; display: block;
  -webkit-mask-image: linear-gradient(to right, transparent 0, #000 7%, #000 93%, transparent 100%); }
.guide { position: absolute; top: 7.08in; left: .45in; right: .45in; font-family: Montserrat; font-weight: 800; font-size: 12.5pt; letter-spacing: .06em; line-height: 1.25; text-transform: uppercase; text-wrap: balance; }
.tag { position: absolute; top: 7.8in; left: .5in; right: .5in; font-family: Montserrat; font-weight: 400; font-size: 11pt; letter-spacing: .1em; line-height: 1.3; text-transform: uppercase; color: rgba(255,255,255,.88); text-wrap: balance; }
.foot { position: absolute; bottom: .32in; left: 0; right: 0; font-family: Montserrat; font-weight: 600; font-size: 6.4pt; letter-spacing: .24em; text-transform: uppercase; color: rgba(255,255,255,.85); }
.spine { left: ${spineX}in; width: ${spine}in; color: #fff; }
.spine .num { position: absolute; top: .3in; width: 100%; text-align: center; font-family: Cinzel; font-weight: 600; font-size: 11pt; }
.spine .vt { position: absolute; left: 0; width: 100%; display: flex; align-items: center; justify-content: center; writing-mode: vertical-rl; white-space: nowrap; }
.spine .stitle { top: .85in; height: 4.1in; font-family: Montserrat; font-weight: 800; font-size: ${Math.min(14, spine * 30)}pt; letter-spacing: .14em; text-transform: uppercase; }
.spine .sauthor { top: 5.25in; height: 2.6in; font-family: Cinzel; font-weight: 600; font-size: ${Math.min(9, spine * 19)}pt; letter-spacing: .16em; text-transform: uppercase; }
.spine .mark { position: absolute; bottom: .32in; left: 50%; width: .26in; height: .26in; transform: translateX(-50%); }
.back { left: ${backX}in; width: ${TRIM_W}in; }
.card { position: absolute; top: .45in; left: .42in; right: .42in; background: #f7f1e3; border-radius: .06in; padding: .34in .36in .3in; box-shadow: 0 .05in .2in rgba(0,0,0,.25); color: #2b2622; }
.hook { font-family: Montserrat; font-weight: 800; font-size: 10.4pt; letter-spacing: .07em; line-height: 1.32; text-transform: uppercase; color: ${s.accent}; }
.rule { width: .8in; height: 1.6pt; background: ${s.top}; margin: .16in 0 .16in; }
.card p { font-family: 'EB Garamond'; font-size: 10pt; line-height: 1.5; text-align: justify; hyphens: auto; margin-bottom: .09in; }
.say { font-family: Montserrat; font-weight: 700; font-size: 6.2pt; letter-spacing: .2em; text-transform: uppercase; color: ${s.accent}; margin: .14in 0 .08in; opacity: .85; }
.q { border-left: 2.2pt solid ${s.bottom}; padding: .01in 0 .01in .12in; margin-bottom: .08in; font-family: 'EB Garamond'; font-style: italic; font-size: 9pt; line-height: 1.42; color: #4a423b; }
.card p.close { margin-top: .12in; margin-bottom: 0; }
.bio { position: absolute; left: .45in; bottom: .52in; width: 3.2in; color: #fff; font-family: Montserrat; }
.bio .n { font-family: Cinzel; font-weight: 600; font-size: 11pt; letter-spacing: .1em; margin-bottom: .06in; }
.bio .l { font-size: 6.3pt; line-height: 1.6; color: rgba(255,255,255,.88); }
.bio .c { font-size: 6.3pt; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; margin-top: .12in; }
.barcode { position: absolute; right: .3in; bottom: .3in; width: 2in; height: 1.2in; background: #fff; display: flex; align-items: center; justify-content: center; text-align: center;
  font-family: Montserrat; font-size: 6pt; letter-spacing: .1em; color: #9a948b; text-transform: uppercase; }
body.guides .gl { position: absolute; top: 0; bottom: 0; border-left: 1px dashed rgba(255,0,255,.9); }
body.guides .gh { position: absolute; left: 0; right: 0; border-top: 1px dashed rgba(255,0,255,.9); }
</style></head><body>
<div class="top"><svg><defs>${motif(s.motif, s.ink)}</defs><rect width="100%" height="100%" fill="url(#motif)"/></svg></div>
<div class="bottom"></div>

<div class="panel back">
  <div class="card">
    <div class="hook">${b.hook}</div>
    <div class="rule"></div>
    ${b.blurb.map((p) => `<p>${p}</p>`).join('')}
    <div class="say">What clients are saying</div>
    ${QUOTES.map((q) => `<div class="q">“${q}”</div>`).join('')}
    <p class="close">${b.close}</p>
  </div>
  <div class="bio"><div class="n">${AUTHOR}, RP</div>
    <div class="l">Registered Psychotherapist · Founder of Al Iman Family Services<br>Former Clinician, 27 Years at SickKids Hospital</div>
    <div class="c">${s.category}</div><div class="l">${PUBLISHER}</div></div>
  <div class="barcode">ISBN barcode area<br>2 × 1.2 in</div>
</div>

<div class="panel spine">
  ${spine >= 0.25 ? `<div class="num">${b.vol ? b.n : '✦'}</div>
  <div class="vt stitle">${s.title}</div>
  <div class="vt sauthor">${AUTHOR}</div>
  <svg class="mark" viewBox="0 0 40 40"><g fill="#fff"><rect x="10" y="10" width="20" height="20"/><rect x="10" y="10" width="20" height="20" transform="rotate(45 20 20)"/></g></svg>` : ''}
</div>

<div class="panel front">
  <div class="author">${AUTHOR.toUpperCase()}</div>
  <div class="creds">${CREDS.join('<br>')}</div>
  <div class="title">${s.title}</div>
  <div class="voltitle">${b.volTitle.replace(/(\S+-\S+)/g, '<span style="white-space:nowrap">$1</span>')}</div>
  <div class="circle">${artFor(b) ? artTag(b) : illustration(b)}</div>
  <div class="guide">${s.guide}</div>
  <div class="tag">${bottomLine}</div>
  <div class="foot">${bookLine}</div>
</div>

<div class="gl" style="left:${BLEED}in"></div><div class="gl" style="left:${spineX}in"></div><div class="gl" style="left:${frontX}in"></div><div class="gl" style="left:${W - BLEED}in"></div>
<div class="gh" style="top:${BLEED}in"></div><div class="gh" style="top:${H - BLEED}in"></div>
</body></html>`;
  return { html, W, H, spine, pages, frontX };
}

// Painted art overrides the vector scene: drop art/book-<n>.png (or .jpg/.webp), square, and rebuild.
const artFor = (b) => ['png', 'jpg', 'jpeg', 'webp'].map((e) => `art/book-${b.n}.${e}`).find((p) => fs.existsSync(path.join(__dirname, p)));

// Portrait art: w = painting width as a share of the circle, y = point of the painting (0 top, 1 bottom)
// placed at the circle's centre. The sides fill with a blurred copy so no hard edge shows.
const ART_FIT = { 1: { w: 1, y: .5 }, 2: { w: 1, y: .5 }, 3: { w: .75, y: .55 }, 4: { w: .68, y: .52 }, 5: { w: .75, y: .58 },
  6: { w: .72, y: .52 }, 7: { w: .92, y: .55 }, 8: { w: .92, y: .55 }, 9: { w: .92, y: .5 } };
const artTag = (b) => {
  const src = artFor(b), { w, y } = ART_FIT[b.n] || { w: 1, y: .5 };
  const fg = `<img class="artfg" src="${src}" style="width:${w * 100}%;transform:translate(-50%,-${y * 100}%)${w === 1 ? ';-webkit-mask-image:none' : ''}">`;
  return w === 1 ? fg : `<img class="artbg" src="${src}">${fg}`;
};

const nameOf = (b) => b.slug || `book-${b.n}-${SERIES[b.s].title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-vol-${b.vol.toLowerCase()}`;

(async () => {
  const out = __dirname;
  for (const d of ['pdf', 'preview']) fs.mkdirSync(path.join(out, d), { recursive: true });
  const css = fs.readFileSync(path.join(out, 'fonts', 'fonts.css'), 'utf8');
  const browser = await chromium.launch();
  const report = [];
  for (const b of BOOKS) {
    const { html, W, H, spine, pages, frontX } = wrapHtml(b, css);
    const file = path.join(out, `.render-${b.n}.html`);
    fs.writeFileSync(file, html);
    const page = await browser.newPage({ viewport: { width: Math.ceil(W * 96), height: Math.ceil(H * 96) }, deviceScaleFactor: 2 });
    await page.goto('file://' + file, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    // fit the title: largest size up to 46pt that stays within two lines with no overflowing word,
    // then hang the volume title right under it
    await page.evaluate(() => {
      const t = document.querySelector('.title');
      for (let pt = 42; pt >= 24; pt -= 1) {
        t.style.fontSize = pt + 'pt';
        const lh = parseFloat(getComputedStyle(t).lineHeight);
        if (t.scrollWidth <= t.clientWidth + 1 && t.getBoundingClientRect().height <= lh * 2 + 2) break;
      }
      const r = t.getBoundingClientRect();
      const v = document.querySelector('.voltitle');
      v.style.top = (t.offsetTop + r.height + 0.13 * 96) + 'px';
      const circleTop = document.querySelector('.circle').offsetTop;
      if (v.offsetTop + v.offsetHeight > circleTop - 0.12 * 96) {
        // tighten if the stack runs into the illustration
        t.style.fontSize = parseFloat(t.style.fontSize) * 0.88 + 'pt';
        v.style.top = (t.offsetTop + t.getBoundingClientRect().height + 0.1 * 96) + 'px';
      }
    });
    const overflow = await page.evaluate(() => {
      const card = document.querySelector('.card').getBoundingClientRect();
      const bio = document.querySelector('.bio').getBoundingClientRect();
      const v = document.querySelector('.voltitle').getBoundingClientRect();
      const c = document.querySelector('.circle').getBoundingClientRect();
      return { cardHitsBio: card.bottom > bio.top - 8, volHitsCircle: v.bottom > c.top - 6 };
    });
    const name = nameOf(b);
    await page.pdf({ path: path.join(out, 'pdf', `${name}.pdf`), width: `${W}in`, height: `${H}in`, printBackground: true, preferCSSPageSize: true });
    await page.evaluate(() => document.body.classList.add('guides'));
    await page.screenshot({ path: path.join(out, 'preview', `${name}-wrap.png`) });
    await page.evaluate(() => document.body.classList.remove('guides'));
    await page.screenshot({ path: path.join(out, 'preview', `${name}-front.png`), clip: { x: frontX * 96, y: 0, width: (TRIM_W + BLEED) * 96, height: H * 96 } });
    await page.close();
    fs.unlinkSync(file);
    report.push({ book: name, pages, spine_in: spine, size_in: `${W.toFixed(3)} x ${H}`, ...overflow });
  }
  await browser.close();
  console.table(report);
})();
