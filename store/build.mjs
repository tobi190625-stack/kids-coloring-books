#!/usr/bin/env node
// Builds the Little Crayon Tales online store into site/ (plain HTML, CSS and JS).
//
//   node store/build.mjs
//
// Edit store/content/ (books + settings), store/src/ (styles + script) and store/public/
// (files copied as they are). Everything in site/ is generated and wiped on every build.
// No dependencies, Node 18 or newer. On Netlify the site URL comes from the URL variable.
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const STORE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(STORE);
const OUT = path.join(ROOT, 'site');
const PUBLIC = path.join(STORE, 'public');

const warnings = [];
const warn = (msg) => warnings.push(msg);
const fail = (msg) => {
  console.error(`\nBuild stopped: ${msg}\n`);
  process.exit(1);
};
const readJSON = (file) => {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (err) {
    fail(`${path.relative(ROOT, file)} is not valid JSON (${err.message})`);
  }
};

// ---------- content ----------

const settings = readJSON(path.join(STORE, 'content', 'settings.json'));
const BOOK_DIR = path.join(STORE, 'content', 'books');
const allBooks = fs
  .readdirSync(BOOK_DIR)
  .filter((f) => f.endsWith('.json'))
  .map((f) => ({ ...readJSON(path.join(BOOK_DIR, f)), _file: f }));

for (const b of allBooks) {
  for (const key of ['id', 'slug', 'title', 'status', 'cover']) {
    if (!b[key]) fail(`store/content/books/${b._file} needs "${key}"`);
  }
  if (!/^[a-z0-9-]+$/.test(b.slug)) fail(`${b._file}: slug may only use a-z, 0-9 and dashes`);
  if (!['live', 'soon', 'hidden'].includes(b.status)) fail(`${b._file}: status must be live, soon or hidden`);
  if (b.status === 'live' && !b.asin) {
    warn(`${b._file}: status is "live" but there is no Amazon ASIN, showing it as coming soon`);
    b.status = 'soon';
  }
  b.inside ??= [];
  b.colored ??= [];
  b.highlights ??= [];
  b.gift_for ??= [];
  b.reviews ??= [];
  b.name = b.short_name || b.title.split(' ')[0];
}
for (const key of ['id', 'slug']) {
  const seen = new Set();
  for (const b of allBooks) {
    if (seen.has(b[key])) fail(`two books use the ${key} "${b[key]}"`);
    seen.add(b[key]);
  }
}
const books = allBooks.filter((b) => b.status !== 'hidden').sort((a, b) => (a.order ?? 99) - (b.order ?? 99));
const liveBooks = books.filter((b) => b.status === 'live');

const SITE_URL = (settings.url || process.env.URL || '').replace(/\/+$/, '');
const YEAR = new Date().getFullYear();
const amazon = settings.amazon || {};
// Associates tags per store; keys use _ for dots (co_uk = amazon.co.uk) so the admin can edit them
const TAGS = Object.fromEntries(
  Object.entries(amazon.tags || {})
    .filter(([, v]) => v)
    .map(([k, v]) => [k.replace(/_/g, '.'), v]),
);
const DEFAULT_STORE = amazon.default_store || 'com';

// Amazon stores that sell KDP paperbacks (same ASIN everywhere)
const STORES = [
  ['com', 'US'], ['co.uk', 'UK'], ['ca', 'Canada'], ['com.au', 'Australia'],
  ['de', 'Germany'], ['fr', 'France'], ['es', 'Spain'], ['it', 'Italy'], ['nl', 'Netherlands'],
  ['pl', 'Poland'], ['se', 'Sweden'], ['co.jp', 'Japan'],
];
// visitor country (Netlify GeoIP) -> Amazon store, for the /go/<book> short links
const COUNTRY_STORE = {
  'co.uk': ['gb', 'ie', 'gg', 'je', 'im'], ca: ['ca'], 'com.au': ['au', 'nz'],
  de: ['de', 'at', 'ch', 'lu', 'li'], fr: ['fr', 'be', 'mc'], es: ['es', 'pt'], it: ['it', 'sm', 'va'],
  nl: ['nl'], pl: ['pl'], se: ['se', 'no', 'dk', 'fi'], 'co.jp': ['jp'],
};

const amazonUrl = (asin, tld = DEFAULT_STORE) =>
  `https://www.amazon.${tld}/dp/${asin}${TAGS[tld] ? `?tag=${encodeURIComponent(TAGS[tld])}` : ''}`;

// ---------- tiny HTML helpers (values are escaped unless wrapped in raw) ----------

class Raw {
  constructor(s) {
    this.s = s;
  }
}
const raw = (s) => new Raw(String(s));
const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ESC[c]);
const show = (v) => (v == null || v === false ? '' : v instanceof Raw ? v.s : Array.isArray(v) ? v.map(show).join('') : esc(v));
const html = (strings, ...values) => raw(strings.reduce((out, s, i) => out + s + (i < values.length ? show(values[i]) : ''), ''));
const attrs = (obj) =>
  raw(
    Object.entries(obj)
      .filter(([, v]) => v !== undefined && v !== null && v !== false && v !== '')
      .map(([k, v]) => (v === true ? ` ${k}` : ` ${k}="${esc(v)}"`))
      .join(''),
  );
// FAQ answers and notes may use [links](books/) and **bold**
const inline = (ctx, text) =>
  raw(
    esc(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, label, href) => `<a href="${/^(https?:|mailto:|#)/.test(href) ? href : ctx.root + href}">${label}</a>`),
  );

// Keep short phrases on one line ("ages 3 to 6", "8.5 x 8.5 in"); only touches visible text, not tags or scripts
const glue = (text) =>
  text
    .replace(/(\d) to (\d)/g, '$1\u00a0to\u00a0$2')
    .replace(/(\d) x (\d)/g, '$1\u00a0x\u00a0$2')
    .replace(/(\d) (in|pages|pictures)\b/g, '$1\u00a0$2');
const typeset = (page) =>
  page
    .split(/(<script[\s\S]*?<\/script>|<[^>]+>)/)
    .map((part) => (part.startsWith('<') ? part : glue(part)))
    .join('');

const ICONS = Object.fromEntries(
  fs
    .readdirSync(path.join(STORE, 'icons'))
    .filter((f) => f.endsWith('.svg'))
    .map((f) => [f.slice(0, -4), fs.readFileSync(path.join(STORE, 'icons', f), 'utf8').trim()]),
);
const icon = (name, cls = '') => {
  if (!ICONS[name]) fail(`missing icon store/icons/${name}.svg`);
  return raw(ICONS[name].replace('<svg ', `<svg class="icon${cls ? ` ${cls}` : ''}" aria-hidden="true" focusable="false" `));
};

// ---------- images ----------

function imageSize(file) {
  const b = fs.readFileSync(file);
  if (b.toString('ascii', 0, 4) === 'RIFF' && b.toString('ascii', 8, 12) === 'WEBP') {
    const chunk = b.toString('ascii', 12, 16);
    if (chunk === 'VP8X') return { w: 1 + b.readUIntLE(24, 3), h: 1 + b.readUIntLE(27, 3) };
    if (chunk === 'VP8L') {
      const bits = b.readUInt32LE(21);
      return { w: 1 + (bits & 0x3fff), h: 1 + ((bits >> 14) & 0x3fff) };
    }
    if (chunk === 'VP8 ') return { w: b.readUInt16LE(26) & 0x3fff, h: b.readUInt16LE(28) & 0x3fff };
  }
  if (b.length > 24 && b.readUInt32BE(0) === 0x89504e47) return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  if (b[0] === 0xff && b[1] === 0xd8) {
    for (let i = 2; i + 9 < b.length; ) {
      if (b[i] !== 0xff) {
        i++;
        continue;
      }
      const marker = b[i + 1];
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return { w: b.readUInt16BE(i + 7), h: b.readUInt16BE(i + 5) };
      }
      i += 2 + b.readUInt16BE(i + 2);
    }
  }
  return { w: 0, h: 0 };
}

const sizeCache = new Map();
function variant(src) {
  if (!sizeCache.has(src)) {
    const file = path.join(PUBLIC, src);
    sizeCache.set(src, fs.existsSync(file) ? imageSize(file) : null);
  }
  return sizeCache.get(src);
}
const sibling = (src, w) => src.replace(/(\.\w+)$/, `-${w}$1`);
const smallOf = (src) => (variant(sibling(src, 480)) ? sibling(src, 480) : src);

// <img> with width/height, and a srcset from the -480 / -720 copies next to the picture
function img(ctx, src, { alt = '', sizes = '100vw', cls, eager = false, small = false } = {}) {
  src = String(src).replace(/^\/+/, '');
  const big = variant(src);
  if (!big) warn(`missing picture store/public/${src}`);
  const useSrc = small ? smallOf(src) : src;
  const size = variant(useSrc) || { w: 0, h: 0 };
  const set = small || !big ? [] : [480, 720].map((w) => sibling(src, w)).filter(variant).concat(src);
  const srcset = set.length > 1 ? set.map((f) => `${ctx.root}${f} ${variant(f).w}w`).join(', ') : undefined;
  return html`<img alt="${alt}"${attrs({
    src: ctx.root + useSrc,
    srcset,
    sizes: srcset ? sizes : undefined,
    width: size.w || undefined,
    height: size.h || undefined,
    class: cls,
    loading: eager ? undefined : 'lazy',
    decoding: eager ? undefined : 'async',
    fetchpriority: eager ? 'high' : undefined,
  })}>`;
}

// ---------- shared pieces ----------

const storeOptions = (selected = DEFAULT_STORE) =>
  STORES.map(([tld, country]) => html`<option value="${tld}"${selected === tld ? raw(' selected') : ''}>Amazon.${tld} (${country})</option>`);

const storeData = () =>
  JSON.stringify({
    defaultStore: DEFAULT_STORE,
    detect: amazon.detect_store !== false,
    bagCheckout: amazon.bag_checkout !== false,
    tags: TAGS,
    stores: STORES.map(([tld]) => tld),
    icons: { plus: icon('plus').s, minus: icon('minus').s, amazon: icon('amazon-logo').s, bag: icon('tote-simple').s },
    books: Object.fromEntries(
      liveBooks.map((b) => [b.id, { title: b.title, asin: b.asin, url: `books/${b.slug}/`, cover: smallOf(b.cover) }]),
    ),
  }).replace(/</g, '\\u003c');

function header(ctx, active) {
  const link = (href, label, key, cls) =>
    html`<a href="${ctx.root + href}"${attrs({ class: cls, 'aria-current': active === key ? 'page' : undefined })}>${label}</a>`;
  return html`
<header class="site-header">
  <div class="container header-row">
    <a class="brand" href="${ctx.root || './'}">
      <img src="${ctx.root}img/brand/logo-96.webp" width="44" height="44" alt="">
      <span class="brand-name">${settings.name}</span>
    </a>
    <nav class="main-nav" aria-label="Main">
      ${link('books/', 'Books', 'books')}
      ${link('free-coloring-pages/', 'Free pages', 'free')}
      ${link('about/', 'About', 'about', 'nav-about')}
    </nav>
    <button class="bag-button js-only" type="button" data-open-bag aria-haspopup="dialog" aria-controls="bag">
      ${icon('tote-simple')}<span class="visually-hidden">Your bag</span><span class="bag-count" data-bag-count hidden>0</span>
    </button>
  </div>
</header>`;
}

function footer(ctx) {
  const s = settings.social || {};
  const socials = [
    ['tiktok', 'TikTok'], ['instagram', 'Instagram'], ['youtube', 'YouTube'], ['pinterest', 'Pinterest'], ['facebook', 'Facebook'],
  ].filter(([k]) => s[k]);
  return html`
<footer class="site-footer">
  <div class="container footer-grid">
    <div class="footer-brand">
      <a class="brand" href="${ctx.root || './'}">
        <img src="${ctx.root}img/brand/logo-192.webp" width="56" height="56" alt="" loading="lazy">
        <span class="brand-name">${settings.name}</span>
      </a>
      <p>${settings.tagline}, for ages 3 to 6.</p>
      <ul class="social" role="list">
        ${socials.map(([k, label]) => html`<li><a href="${s[k]}" target="_blank" rel="noopener" aria-label="${settings.name} on ${label}">${icon(`${k}-logo`)}</a></li>`)}
      </ul>
    </div>
    <nav class="footer-nav" aria-labelledby="footer-books">
      <h2 class="footer-title" id="footer-books">Books</h2>
      <ul role="list">${books.map((b) => html`<li><a href="${ctx.root}books/${b.slug}/">${b.title}</a></li>`)}</ul>
    </nav>
    <nav class="footer-nav" aria-labelledby="footer-more">
      <h2 class="footer-title" id="footer-more">More</h2>
      <ul role="list">
        <li><a href="${ctx.root}free-coloring-pages/">Free coloring pages</a></li>
        <li><a href="${ctx.root}about/">About and questions</a></li>
        <li><a href="${ctx.root}privacy/">Privacy</a></li>
        ${settings.legal_notice ? html`<li><a href="${ctx.root}legal/">Legal notice</a></li>` : ''}
      </ul>
    </nav>
  </div>
  <div class="container">
    <div class="footer-fine">
      <div class="footer-store js-only">
        <label for="store-select">Your Amazon store</label>
        <select id="store-select" data-store-select>${storeOptions()}</select>
      </div>
      <div>
        <p>© ${YEAR} ${settings.name}. The pictures are real pages from our books.</p>
        ${Object.keys(TAGS).length ? html`<p>As an Amazon Associate we earn from qualifying purchases.</p>` : ''}
      </div>
    </div>
  </div>
</footer>`;
}

function bagDialog(ctx) {
  return html`
<dialog class="bag" id="bag" aria-labelledby="bag-title" data-bag>
  <div class="bag-head">
    <h2 id="bag-title">Your bag</h2>
    <button class="icon-button" type="button" data-close-bag aria-label="Close bag">${icon('x')}</button>
  </div>
  <div class="bag-items" data-bag-items aria-live="polite"></div>
  <div class="bag-foot" data-bag-foot>
    <label class="store-row" for="bag-store"><span>Amazon store</span>
      <select id="bag-store" data-store-select>${storeOptions()}</select>
    </label>
    <a class="btn btn-primary btn-block" href="${ctx.root}books/" target="_blank" rel="noopener" data-checkout>${icon('amazon-logo')} Check out on Amazon</a>
    <p class="fine">Amazon asks you to confirm, then shows the price and delivery before you pay.</p>
  </div>
</dialog>`;
}

const buyLink = (b, cls) =>
  html`<a class="btn btn-primary ${cls}" data-asin="${b.asin}" href="${amazonUrl(b.asin)}" target="_blank" rel="noopener">${icon('amazon-logo')} Buy on Amazon</a>`;
const bagButton = (b, cls) =>
  html`<button class="btn btn-secondary js-only ${cls}" type="button" data-add="${b.id}">${icon('plus')} Add to bag</button>`;

function bookCard(ctx, b, level = 3) {
  const url = `${ctx.root}books/${b.slug}/`;
  const title = html`<a href="${url}">${b.title}</a>`;
  return html`
<article class="book-card" style="--tint: ${b.tint || '#FFF0C9'}">
  <a class="book-card-media" href="${url}" tabindex="-1" aria-hidden="true">
    ${img(ctx, b.cover, { sizes: '(min-width: 1100px) 340px, (min-width: 700px) 45vw, 92vw' })}
  </a>
  <div class="book-card-body">
    <p class="badge${b.status === 'soon' ? ' badge-soon' : ''}">${b.status === 'soon' ? 'Coming soon' : b.badge}</p>
    ${level === 2 ? html`<h2 class="book-card-title">${title}</h2>` : html`<h3 class="book-card-title">${title}</h3>`}
    <p class="book-card-text">${b.summary}</p>
    <p class="meta">Ages ${b.ages} · ${b.pictures} pictures to color</p>
    <div class="card-actions">
      ${b.status === 'live'
        ? [buyLink(b, 'btn-sm'), bagButton(b, 'btn-sm')]
        : html`<a class="btn btn-secondary btn-sm" href="${url}#notify">${icon('bell-ringing')} Get notified</a>`}
    </div>
  </div>
</article>`;
}

let formCount = 0;
function emailForm(ctx, { name, action, button, hidden = {}, note }) {
  const id = `email-${++formCount}`;
  return html`
<form class="email-form" name="${name}" method="POST" action="${ctx.root + action}" data-netlify="true" netlify-honeypot="company" data-form>
  <input type="hidden" name="form-name" value="${name}">
  ${Object.entries(hidden).map(([k, v]) => html`<input type="hidden" name="${k}" value="${v}">`)}
  <p class="hp" aria-hidden="true"><label>Company <input name="company" tabindex="-1" autocomplete="off"></label></p>
  <div class="field">
    <label for="${id}">Your email</label>
    <div class="field-row">
      <input id="${id}" name="email" type="email" autocomplete="email" required placeholder="you@example.com" aria-describedby="${id}-error">
      <button class="btn btn-primary" type="submit">${button}</button>
    </div>
    <p class="field-error" id="${id}-error" hidden></p>
  </div>
  <p class="fine">${note || 'We only email about new books and freebies. Unsubscribe anytime.'} <a href="${ctx.root}privacy/">Privacy</a></p>
</form>`;
}

function freeBand(ctx, headingLevel = 2) {
  const fp = settings.free_pages;
  const heading = headingLevel === 1 ? html`<h1>${fp.title}</h1>` : html`<h2>${fp.title}</h2>`;
  return html`
<div class="free-grid">
  <div class="free-art" aria-hidden="true">
    ${fp.preview.map((src, i) => html`<span class="free-sheet free-sheet-${i + 1}">${img(ctx, src, { small: true })}</span>`)}
  </div>
  <div class="free-copy">
    ${heading}
    <p class="lead">${fp.text}</p>
    ${emailForm(ctx, { name: 'free-pages', action: 'thank-you/', button: 'Get the free pages' })}
  </div>
</div>`;
}

function faqList(ctx) {
  return html`<div class="faq-list">
    ${settings.faq.map((f) => html`<details><summary>${f.q}</summary><p>${inline(ctx, f.a)}</p></details>`)}
  </div>`;
}

function moreComing(ctx) {
  const names = settings.more_coming || [];
  if (!names.length) return '';
  const list = names.length > 1 ? `${names.slice(0, -1).join(', ')} and ${names.at(-1)}` : names[0];
  return html`<p class="more-coming">${icon('sparkle')} More friends on the way: ${list}. <a href="${ctx.root}books/#notify">Get notified</a></p>`;
}

// ---------- page frame ----------

const ASSETS = {};
function layout(ctx, { title, description, body, active, ogImage, jsonld = [], noindex = false, bodyClass = '' }) {
  const canonical = SITE_URL && ctx.path ? SITE_URL + ctx.path : '';
  const og = ogImage || 'img/brand/og.jpg';
  const ogUrl = SITE_URL ? `${SITE_URL}/${og}` : ctx.root + og;
  const announcement = settings.announcement
    ? html`<div class="announce"><div class="container">${inline(ctx, settings.announcement)}</div></div>`
    : '';
  return `<!doctype html>
${html`<html lang="en" data-root="${ctx.root}">
<head>
<meta charset="utf-8">
<script>document.documentElement.classList.add('js')</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<meta name="description" content="${description}">
${canonical ? html`<link rel="canonical" href="${canonical}">` : ''}
${noindex ? raw('<meta name="robots" content="noindex">') : ''}
<meta property="og:type" content="${ctx.ogType || 'website'}">
<meta property="og:site_name" content="${settings.name}">
<meta property="og:title" content="${title}">
<meta property="og:description" content="${description}">
<meta property="og:image" content="${ogUrl}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
${canonical ? html`<meta property="og:url" content="${canonical}">` : ''}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FFF8EC" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#161D2B" media="(prefers-color-scheme: dark)">
<link rel="icon" href="${ctx.root}favicon.ico" sizes="any">
<link rel="icon" href="${ctx.root}img/brand/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="${ctx.root}img/brand/apple-touch-icon.png">
<link rel="manifest" href="${ctx.root}site.webmanifest">
<link rel="preload" href="${ctx.root}fonts/grandstander.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="${ctx.root}fonts/nunito.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="${ctx.root + ASSETS.css}">
<script src="${ctx.root + ASSETS.js}" defer></script>
${jsonld.map((data) => raw(`<script type="application/ld+json">${JSON.stringify(data).replace(/</g, '\\u003c')}</script>`))}
<script type="application/json" id="store-data">${raw(storeData())}</script>
</head>
<body class="${bodyClass}">
<a class="skip-link" href="#main">Skip to content</a>
${announcement}
${header(ctx, active)}
<main id="main">
${body}
</main>
${footer(ctx)}
${bagDialog(ctx)}
</body>
</html>`.s.replace(/\n\s*\n/g, '\n')}
`;
}

// ---------- pages ----------

const pages = [];
const page = (file, urlPath, render) => {
  const depth = file === '404.html' ? -1 : file.split('/').length - 1;
  const ctx = { root: depth < 0 ? '/' : '../'.repeat(depth), path: urlPath };
  pages.push({ file, urlPath, render: () => render(ctx) });
};

const abs = (p) => (SITE_URL ? `${SITE_URL}${p}` : p);
const orgLd = {
  '@type': 'Organization',
  '@id': abs('/#org'),
  name: settings.name,
  url: abs('/'),
  logo: abs('/img/brand/icon-512.png'),
  description: settings.description,
  sameAs: Object.values(settings.social || {}).filter(Boolean),
};

function homePage(ctx) {
  const hero = [books[1], books[0], books[2]].filter(Boolean);
  const peek = [];
  const rows = books.map((b) => [...b.inside.map((p) => ({ ...p, kind: 'inside' })), ...b.colored.map((p) => ({ ...p, kind: 'colored' }))]);
  for (let i = 0; peek.length < 12 && rows.some((r) => r[i]); i++) {
    rows.forEach((r, j) => r[i] && peek.length < 12 && peek.push({ ...r[i], book: books[j] }));
  }
  const cmp = settings.compare;
  const cmpBook = cmp && books.find((b) => b.id === cmp.book);
  return layout(ctx, {
    title: `${settings.name}: ${settings.tagline} (ages 3-6)`,
    description: settings.description,
    bodyClass: 'page-home',
    jsonld: [
      { '@context': 'https://schema.org', '@graph': [orgLd, { '@type': 'WebSite', '@id': abs('/#site'), name: settings.name, url: abs('/'), publisher: { '@id': abs('/#org') } }] },
      {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: settings.faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*/g, '') } })),
      },
    ],
    body: html`
<section class="hero">
  <div class="container hero-grid">
    <div class="hero-copy">
      <h1>${heroTitle(settings.hero_title)}</h1>
      <p class="lead">${settings.hero_text}</p>
      <div class="cta-row">
        <a class="btn btn-primary btn-lg" href="#books">Shop the books</a>
        <a class="btn btn-secondary btn-lg" href="${ctx.root}free-coloring-pages/">${icon('download-simple')} Get the free pages</a>
      </div>
    </div>
    <div class="hero-art">
      ${hero.map((b, i) => html`<a class="hero-book hero-book-${i + 1}" href="${ctx.root}books/${b.slug}/" style="--tint: ${b.tint}">
        ${img(ctx, b.cover, { alt: b.title, eager: i === 1, sizes: '(min-width: 960px) 300px, 45vw' })}</a>`)}
    </div>
  </div>
</section>

<section class="section" id="books" aria-labelledby="books-title">
  <div class="container">
    <h2 id="books-title">Meet the books</h2>
    <p class="section-lead">Every book is one sweet story with a friendly animal, from good morning to goodnight.</p>
    <div class="book-grid">${books.map((b) => bookCard(ctx, b))}</div>
    ${moreComing(ctx)}
  </div>
</section>

${cmp && cmpBook ? html`
<section class="section section-tint" aria-labelledby="how-title">
  <div class="container split">
    <figure class="compare" data-compare style="--pos: 50%">
      <div class="compare-frame">
        ${img(ctx, cmp.before, { alt: `A page from ${cmpBook.title} before coloring`, sizes: '(min-width: 960px) 520px, 92vw', cls: 'compare-before' })}
        ${img(ctx, cmp.after, { alt: '', sizes: '(min-width: 960px) 520px, 92vw', cls: 'compare-after' })}
        <span class="compare-handle" aria-hidden="true">${icon('palette')}</span>
        <input class="compare-range js-only" type="range" min="0" max="100" value="50" aria-label="Color the page: drag to show more color">
      </div>
      <figcaption>${cmp.caption}</figcaption>
    </figure>
    <div class="split-copy">
      <h2 id="how-title">Color the story, then read it</h2>
      <ul class="points" role="list">
        <li>${icon('palette')}<div><h3>One big picture</h3><p>Bold, thick lines and big shapes that are easy for little hands.</p></div></li>
        <li>${icon('book-open-text')}<div><h3>One short sentence</h3><p>Big, clear letters, so early readers can read each page with you.</p></div></li>
        <li>${icon('gift')}<div><h3>One sweet story</h3><p>From good morning to goodnight, with a “This book belongs to” page.</p></div></li>
      </ul>
    </div>
  </div>
</section>` : ''}

<section class="section peek" aria-labelledby="peek-title">
  <div class="container">
    <h2 id="peek-title">Peek inside</h2>
    <p class="section-lead">Real pages from our books, in black and white and colored in.</p>
  </div>
  <div class="peek-track" tabindex="0" role="region" aria-label="Pages from our books">
    <ul role="list">
      ${peek.map((p) => html`<li><a class="peek-item" href="${ctx.root}books/${p.book.slug}/">
        ${img(ctx, p.image, { small: true, alt: `${p.kind === 'colored' ? 'Colored-in page' : 'Coloring page'} from ${p.book.title}: ${p.text}` })}
        <span class="peek-caption">${p.kind === 'colored' ? 'Colored in, from ' : 'From '}${p.book.name}</span></a></li>`)}
    </ul>
  </div>
</section>

<section class="section section-free" id="free" aria-label="${settings.free_pages.title}">
  <div class="container">${freeBand(ctx)}</div>
</section>

<section class="section" aria-labelledby="faq-title">
  <div class="container narrow">
    <h2 id="faq-title">Questions parents ask</h2>
    ${faqList(ctx)}
  </div>
</section>`,
  });
}

// "Story books kids color and read" -> crayon marks under "color" and "read"
function heroTitle(text) {
  return raw(esc(text).replace(/\b(color|read)\b/gi, '<span class="crayon">$1</span>'));
}

function shopPage(ctx) {
  return layout(ctx, {
    title: `All books | ${settings.name}`,
    description: `Every ${settings.name} Color & Read story book for ages 3-6, with big pictures to color and short sentences in big letters.`,
    active: 'books',
    bodyClass: 'page-shop',
    body: html`
<section class="page-head">
  <div class="container">
    <h1>All books</h1>
    <p class="lead">Color & Read story books for ages 3 to 6. Each one is a whole story, one big picture and one short sentence at a time.</p>
  </div>
</section>
<section class="section section-top-0">
  <div class="container">
    <div class="book-grid">${books.map((b) => bookCard(ctx, b, 2))}</div>
    ${moreComing(ctx)}
  </div>
</section>
<section class="section section-tint" id="notify" aria-labelledby="notify-title">
  <div class="container narrow center">
    <h2 id="notify-title">Hear about new books first</h2>
    <p class="lead">One short email when a new story comes out. That’s it.</p>
    ${emailForm(ctx, { name: 'notify', action: 'youre-on-the-list/', button: 'Notify me', hidden: { book: 'all' } })}
  </div>
</section>`,
  });
}

function productPage(ctx, b) {
  const slides = [
    { src: b.cover, alt: b.cover_alt || `Cover of ${b.title}`, caption: 'Front cover' },
    ...(b.back ? [{ src: b.back, alt: `Back cover of ${b.title}`, caption: 'Back cover' }] : []),
    ...b.inside.map((p) => ({ src: p.image, alt: `Coloring page: ${p.text}`, caption: p.text })),
    ...b.colored.map((p) => ({ src: p.image, alt: `Colored-in page: ${p.text}`, caption: `Colored in: ${p.text}`, colored: true })),
  ];
  const others = books.filter((o) => o.id !== b.id);
  const url = abs(ctx.path);
  const pinMedia = abs(`/${b.pin || b.cover}`);
  const share = SITE_URL
    ? {
        pin: `https://www.pinterest.com/pin/create/button/?url=${encodeURIComponent(url)}&media=${encodeURIComponent(pinMedia)}&description=${encodeURIComponent(`${b.title}: a color and read story book for ages ${b.ages}`)}`,
        fb: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
      }
    : { pin: 'https://www.pinterest.com/pin/create/button/', fb: 'https://www.facebook.com/sharer/sharer.php' };
  const bookLd = {
    '@context': 'https://schema.org',
    '@type': b.price && b.status === 'live' ? ['Book', 'Product'] : 'Book',
    '@id': `${url}#book`,
    name: b.title,
    alternativeHeadline: b.subtitle,
    description: b.story,
    url,
    image: [abs(`/${b.cover}`), ...(b.back ? [abs(`/${b.back}`)] : [])],
    bookFormat: 'https://schema.org/Paperback',
    numberOfPages: b.pages,
    inLanguage: 'en',
    typicalAgeRange: b.ages,
    genre: "Children's coloring and story book",
    author: { '@type': 'Organization', name: settings.name, url: abs('/') },
    publisher: { '@type': 'Organization', name: settings.name, url: abs('/') },
    ...(b.status === 'live' ? { sameAs: amazonUrl(b.asin) } : {}),
    ...(b.price && b.status === 'live'
      ? {
          brand: { '@type': 'Brand', name: settings.name },
          offers: {
            '@type': 'Offer',
            price: b.price,
            priceCurrency: 'USD',
            availability: 'https://schema.org/InStock',
            url: amazonUrl(b.asin),
            seller: { '@type': 'Organization', name: 'Amazon' },
          },
        }
      : {}),
  };
  const crumbsLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: abs('/') },
      { '@type': 'ListItem', position: 2, name: 'Books', item: abs('/books/') },
      { '@type': 'ListItem', position: 3, name: b.title, item: url },
    ],
  };
  const live = b.status === 'live';
  return layout(
    { ...ctx, ogType: 'book' },
    {
      title: `${b.title} | ${settings.name}`,
      description: `${b.hook} ${b.summary} A color and read story book for ages ${b.ages}${live ? ', on Amazon' : ', coming soon'}.`,
      active: 'books',
      ogImage: b.og_image,
      bodyClass: 'page-product',
      jsonld: [bookLd, crumbsLd],
      body: html`
<nav class="crumbs container" aria-label="Breadcrumb">
  <ol role="list">
    <li><a href="${ctx.root}">Home</a></li>
    <li><a href="${ctx.root}books/">Books</a></li>
    <li><span aria-current="page">${b.title}</span></li>
  </ol>
</nav>

<section class="product container" style="--tint: ${b.tint || '#FFF0C9'}">
  <div class="gallery" data-gallery>
    <a class="gallery-main" href="${ctx.root + b.cover}" data-gallery-main aria-label="View the pictures larger">
      ${img(ctx, b.cover, { alt: slides[0].alt, eager: true, sizes: '(min-width: 1000px) 540px, 92vw' })}
      <span class="gallery-zoom" aria-hidden="true">${icon('magnifying-glass-plus')}</span>
    </a>
    <ul class="gallery-thumbs" role="list">
      ${slides.map((s, i) => html`<li><a class="thumb" href="${ctx.root + s.src}" data-slide="${i}" data-full="${ctx.root + s.src}" data-caption="${s.caption}"${i === 0 ? raw(' aria-current="true"') : ''}>
        ${img(ctx, s.src, { small: true, alt: s.alt })}</a></li>`)}
    </ul>
  </div>

  <div class="product-info">
    <p class="badge${live ? '' : ' badge-soon'}">${live ? b.badge : 'Coming soon'}</p>
    <h1 class="product-title">${b.title}</h1>
    <p class="product-sub">${b.subtitle}</p>
    <p class="product-hook">${b.hook} ${b.summary}</p>
    <ul class="specs" role="list">
      <li>${icon('smiley')}Ages ${b.ages}</li>
      <li>${icon('palette')}${b.pictures} pictures to color</li>
      <li>${icon('book-open-text')}${b.pages} pages</li>
      <li>${icon('printer')}${b.trim} ${String(b.format || 'paperback').toLowerCase()}</li>
    </ul>
    ${live && b.price ? html`<p class="price" data-us-only>$${b.price} <span>list price on Amazon.com</span></p>` : ''}
    ${live
      ? html`
    <div class="buy-box" id="buy" data-buy-box>
      <div class="buy-actions">${buyLink(b, 'btn-lg')}${bagButton(b, 'btn-lg')}</div>
      <p class="buy-note">${icon('truck')}<span>Printed and shipped by <span data-store-name>Amazon.${DEFAULT_STORE}</span></span></p>
    </div>`
      : html`
    <div class="notify-box" id="notify" data-buy-box>
      <h2>Coming soon to Amazon</h2>
      <p>Leave your email and we’ll tell you the day ${b.name} is out.</p>
      ${emailForm(ctx, { name: 'notify', action: 'youre-on-the-list/', button: 'Notify me', hidden: { book: b.id } })}
    </div>`}
    <div class="share">
      <span>Share</span>
      <a class="icon-button" href="${share.pin}" target="_blank" rel="noopener" data-share-pin data-media="${ctx.root + (b.pin || b.cover)}" aria-label="Save to Pinterest">${icon('pinterest-logo')}</a>
      <a class="icon-button" href="${share.fb}" target="_blank" rel="noopener" data-share-fb aria-label="Share on Facebook">${icon('facebook-logo')}</a>
      <button class="icon-button js-only" type="button" data-share aria-label="Share or copy the link">${icon('share-network')}</button>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="story-title">
  <div class="container story-grid">
    <div class="story">
      <h2 id="story-title">The story</h2>
      <p class="story-text">${b.story}</p>
      ${b.gift_for.length ? html`<h3>A sweet gift for</h3><ul class="pills" role="list">${b.gift_for.map((g) => html`<li>${g}</li>`)}</ul>` : ''}
    </div>
    <div class="inside-box">
      <h2>What’s inside</h2>
      <ul class="checks" role="list">${b.highlights.map((h) => html`<li>${icon('check')}<span>${h}</span></li>`)}</ul>
      <p class="fine">Best with crayons and colored pencils. The pictures are printed on both sides of the paper.</p>
    </div>
  </div>
</section>

${b.inside.length || b.colored.length ? html`
<section class="section section-tint" aria-labelledby="pages-title">
  <div class="container">
    <h2 id="pages-title">Peek inside</h2>
    <p class="section-lead">Real pages from the book. Tap a page to see it bigger.</p>
    <ul class="page-grid" role="list">
      ${slides.map((s, i) => (i < (b.back ? 2 : 1) ? '' : html`<li><a class="page-tile" href="${ctx.root + s.src}" data-open-slide="${i}">
        ${img(ctx, s.src, { small: true, alt: s.alt })}${s.colored ? html`<span>Colored-in example</span>` : ''}</a></li>`))}
    </ul>
  </div>
</section>` : ''}

${b.reviews.length ? html`
<section class="section" aria-labelledby="reviews-title">
  <div class="container narrow">
    <h2 id="reviews-title">What parents say</h2>
    <ul class="reviews" role="list">${b.reviews.map((r) => html`<li><blockquote><p>“${r.quote}”</p></blockquote><p class="review-name">${r.name}</p></li>`)}</ul>
  </div>
</section>` : ''}

${others.length ? html`
<section class="section" aria-labelledby="more-title">
  <div class="container">
    <h2 id="more-title">More Color & Read books</h2>
    <div class="book-grid${others.length < 3 ? ' book-grid-center' : ''}">${others.map((o) => bookCard(ctx, o))}</div>
  </div>
</section>` : ''}

<div class="buy-bar" data-buy-bar hidden>
  <div class="container buy-bar-row">
    ${img(ctx, b.cover, { small: true, alt: '', cls: 'buy-bar-cover' })}
    <p class="buy-bar-title">${b.title}</p>
    ${live ? buyLink(b, 'btn-sm') : html`<a class="btn btn-primary btn-sm" href="#notify">${icon('bell-ringing')} Notify me</a>`}
  </div>
</div>

<dialog class="lightbox" data-lightbox aria-label="Pictures from ${b.title}">
  <button class="icon-button lightbox-close" type="button" data-lightbox-close aria-label="Close">${icon('x')}</button>
  <figure>
    <img data-lightbox-img src="${ctx.root + b.cover}" alt="">
    <figcaption data-lightbox-caption></figcaption>
  </figure>
  <button class="icon-button lightbox-prev" type="button" data-lightbox-prev aria-label="Previous picture">${icon('caret-left')}</button>
  <button class="icon-button lightbox-next" type="button" data-lightbox-next aria-label="Next picture">${icon('caret-right')}</button>
</dialog>`,
    },
  );
}

function freePage(ctx) {
  return layout(ctx, {
    title: `Free coloring pages for kids 3-6 | ${settings.name}`,
    description: `${settings.free_pages.text} Big, bold pictures with short sentences in big letters, from ${settings.name}.`,
    active: 'free',
    bodyClass: 'page-free',
    body: html`
<section class="section free-hero">
  <div class="container">${freeBand(ctx, 1)}</div>
</section>
<section class="section section-tint" aria-labelledby="get-title">
  <div class="container narrow">
    <h2 id="get-title">What you get</h2>
    <ul class="checks checks-lg" role="list">
      <li>${icon('check')}<span>${settings.free_pages.preview.length} real pages, one from each of our books</span></li>
      <li>${icon('check')}<span>Bold, thick lines and one short sentence in big letters on every page</span></li>
      <li>${icon('check')}<span>A printable PDF for Letter or A4 paper, yours to print again and again</span></li>
    </ul>
  </div>
</section>`,
  });
}

function messagePage(ctx, { title, lead, iconName, extra }) {
  return layout(ctx, {
    title: `${title} | ${settings.name}`,
    description: lead,
    noindex: true,
    bodyClass: 'page-message',
    body: html`
<section class="section message">
  <div class="container narrow center">
    <span class="message-icon">${icon(iconName)}</span>
    <h1>${title}</h1>
    <p class="lead">${lead}</p>
    ${extra}
  </div>
</section>
${liveBooks.length ? html`
<section class="section section-top-0" aria-labelledby="love-title">
  <div class="container">
    <h2 id="love-title" class="center">Get the whole story</h2>
    <div class="book-grid${liveBooks.length < 3 ? ' book-grid-center' : ''}">${liveBooks.map((b) => bookCard(ctx, b))}</div>
  </div>
</section>` : ''}`,
  });
}

function aboutPage(ctx) {
  return layout(ctx, {
    title: `About us and questions | ${settings.name}`,
    description: `${settings.name} makes story books kids color and read, for ages 3-6. Answers to common questions and how to reach us.`,
    active: 'about',
    bodyClass: 'page-about',
    body: html`
<section class="page-head">
  <div class="container narrow">
    <h1>About ${settings.name}</h1>
  </div>
</section>
<section class="section section-top-0">
  <div class="container narrow about">
    <img class="about-logo" src="${ctx.root}img/brand/logo-320.webp" width="160" height="160" alt="The ${settings.name} friends: a bear, a little dinosaur and a reindeer">
    <div class="prose">
      <p>${settings.name} makes story books that kids color <em>and</em> read.</p>
      <p>Every page has one big, bold picture and one short sentence in big, easy letters. Kids color the story, then read it with you. Page by page, a coloring book becomes a first reading book.</p>
      <p>We’re a small independent publisher. Amazon prints and ships our paperbacks, so you get Amazon’s delivery options and returns.</p>
    </div>
  </div>
</section>
<section class="section section-tint" aria-labelledby="faq-title">
  <div class="container narrow">
    <h2 id="faq-title">Questions parents ask</h2>
    ${faqList(ctx)}
  </div>
</section>
<section class="section" id="contact" aria-labelledby="contact-title">
  <div class="container narrow">
    <h2 id="contact-title">Say hello</h2>
    <p class="lead">A question about a book, or an idea for the next one? Write to us.</p>
    <form class="contact-form" name="contact" method="POST" action="${ctx.root}message-sent/" data-netlify="true" netlify-honeypot="company" data-form>
      <input type="hidden" name="form-name" value="contact">
      <p class="hp" aria-hidden="true"><label>Company <input name="company" tabindex="-1" autocomplete="off"></label></p>
      <div class="field">
        <label for="contact-name">Your name <span class="optional">(optional)</span></label>
        <input id="contact-name" name="name" autocomplete="name">
      </div>
      <div class="field">
        <label for="contact-email">Your email</label>
        <input id="contact-email" name="email" type="email" autocomplete="email" required aria-describedby="contact-email-error">
        <p class="field-error" id="contact-email-error" hidden></p>
      </div>
      <div class="field">
        <label for="contact-message">Message</label>
        <textarea id="contact-message" name="message" rows="5" required aria-describedby="contact-message-error"></textarea>
        <p class="field-error" id="contact-message-error" hidden></p>
      </div>
      <button class="btn btn-primary" type="submit">${icon('envelope-simple')} Send message</button>
    </form>
  </div>
</section>`,
  });
}

function textPage(ctx, { title, description, body, noindex = false }) {
  return layout(ctx, {
    title: `${title} | ${settings.name}`,
    description,
    noindex,
    bodyClass: 'page-text',
    body: html`
<section class="page-head"><div class="container narrow"><h1>${title}</h1></div></section>
<section class="section section-top-0"><div class="container narrow prose">${body}</div></section>`,
  });
}

function privacyPage(ctx) {
  const hasTags = Object.keys(TAGS).length > 0;
  return textPage(ctx, {
    title: 'Privacy',
    description: `How ${settings.name} handles your information.`,
    body: html`
<p>We keep this simple and collect as little as we can.</p>
<h2>Emails you give us</h2>
<p>When you ask for the free coloring pages, sign up to hear about a new book or send us a message, we receive what you type in the form (your email address, and your name and message if you write them). Our web host, Netlify, stores these form entries for us. We use them only to send you what you asked for and the occasional note about new books. We never sell or share them. To be removed, write to us through the form on the <a href="${ctx.root}about/#contact">About page</a>.</p>
<h2>Your bag and Amazon store</h2>
<p>The books in your bag and the Amazon store you picked are saved in your own browser (local storage), so they are still there next time. They never reach us. This site sets no cookies and has no ads or tracking scripts.</p>
<h2>Amazon</h2>
<p>Our buy buttons take you to Amazon, which prints, sells and ships our books. Amazon’s own privacy notice applies there.${hasTags ? ' As an Amazon Associate we earn from qualifying purchases made through these links.' : ''}</p>
<h2>Children</h2>
<p>Our books are for children, but this website is for the grown-ups who buy them. Please don’t let children send us their information.</p>`,
  });
}

function notFoundPage(ctx) {
  return layout(ctx, {
    title: `Page not found | ${settings.name}`,
    description: 'This page wandered off.',
    noindex: true,
    bodyClass: 'page-message',
    body: html`
<section class="section message">
  <div class="container narrow center">
    <span class="message-icon">${icon('binoculars')}</span>
    <h1>This page wandered off</h1>
    <p class="lead">Maybe it went sledding with Nico. Let’s get you back to the books.</p>
    <div class="cta-row center">
      <a class="btn btn-primary btn-lg" href="${ctx.root}books/">See all books</a>
      <a class="btn btn-secondary btn-lg" href="${ctx.root}">Go to the home page</a>
    </div>
  </div>
</section>`,
  });
}

// ---------- extra files ----------

function sitemap() {
  if (!SITE_URL) return null;
  const urls = pages.filter((p) => p.urlPath).map((p) => `  <url><loc>${esc(SITE_URL + p.urlPath)}</loc></url>`);
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>\n`;
}

function llmsTxt() {
  const lines = [
    `# ${settings.name}`,
    '',
    `> ${settings.description}`,
    '',
    'Each book is a paperback printed and sold by Amazon. Every page has one full-page coloring picture with bold, thick lines and one short sentence in big letters; together the pages tell one story. Best with crayons and colored pencils.',
    '',
    '## Books',
    '',
    ...books.map(
      (b) =>
        `- [${b.title}](${abs(`/books/${b.slug}/`)}): ${b.summary} Ages ${b.ages}, ${b.pictures} pictures, ${b.trim} ${String(b.format || 'paperback').toLowerCase()}. ${b.status === 'live' ? `Buy on Amazon: ${amazonUrl(b.asin)}` : 'Coming soon.'}`,
    ),
    '',
    '## More',
    '',
    `- [Free coloring pages](${abs('/free-coloring-pages/')}): ${settings.free_pages.text}`,
    `- [About and questions](${abs('/about/')})`,
    '',
  ];
  return lines.join('\n');
}

function redirects() {
  const lines = ['# Short links for bios and captions (generated by store/build.mjs)'];
  for (const b of books) {
    const product = `/books/${b.slug}/`;
    lines.push(`/${b.id}  ${product}  301`);
    if (b.status === 'live') {
      for (const [tld, countries] of Object.entries(COUNTRY_STORE)) {
        lines.push(`/go/${b.id}  ${amazonUrl(b.asin, tld)}  302  Country=${countries.join(',')}`);
      }
      lines.push(`/go/${b.id}  ${amazonUrl(b.asin, 'com')}  302`);
    } else {
      lines.push(`/go/${b.id}  ${product}  302`);
    }
  }
  lines.push('/free  /free-coloring-pages/  301');
  lines.push(`/amazon  ${amazon.author_page || '/books/'}  302`);
  return `${lines.join('\n')}\n`;
}

const HEADERS = `/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: SAMEORIGIN

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/fonts/*
  Cache-Control: public, max-age=31536000, immutable

/downloads/*
  X-Robots-Tag: noindex
`;

const manifest = () =>
  JSON.stringify(
    {
      name: settings.name,
      short_name: settings.name,
      description: settings.description,
      start_url: './',
      display: 'browser',
      background_color: '#FFF8EC',
      theme_color: '#FFF8EC',
      icons: [
        { src: 'img/brand/icon-192.png', sizes: '192x192', type: 'image/png' },
        { src: 'img/brand/icon-512.png', sizes: '512x512', type: 'image/png' },
        { src: 'img/brand/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
      ],
    },
    null,
    2,
  );

// ---------- build ----------

function hashed(src, name, ext) {
  const text = fs.readFileSync(path.join(STORE, 'src', src), 'utf8');
  const file = `assets/${name}.${createHash('sha256').update(text).digest('hex').slice(0, 10)}.${ext}`;
  fs.mkdirSync(path.join(OUT, 'assets'), { recursive: true });
  fs.writeFileSync(path.join(OUT, file), text);
  return file;
}

function write(file, text) {
  const target = path.join(OUT, file);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, text);
}

fs.rmSync(OUT, { recursive: true, force: true });
fs.cpSync(PUBLIC, OUT, { recursive: true });
ASSETS.css = hashed('styles.css', 'styles', 'css');
ASSETS.js = hashed('app.js', 'app', 'js');

page('index.html', '/', homePage);
page('books/index.html', '/books/', shopPage);
for (const b of books) page(`books/${b.slug}/index.html`, `/books/${b.slug}/`, (ctx) => productPage(ctx, b));
page('free-coloring-pages/index.html', '/free-coloring-pages/', freePage);
page('about/index.html', '/about/', aboutPage);
page('privacy/index.html', '/privacy/', privacyPage);
if (settings.legal_notice) {
  page('legal/index.html', '/legal/', (ctx) =>
    textPage(ctx, {
      title: 'Legal notice',
      description: `Legal notice for ${settings.name}.`,
      body: settings.legal_notice.split(/\n{2,}/).map((para) => html`<p>${raw(esc(para).replace(/\n/g, '<br>'))}</p>`),
    }),
  );
}
page('thank-you/index.html', '', (ctx) =>
  messagePage(ctx, {
    title: 'Your free pages are ready',
    lead: 'Download the PDF, then print as many copies as you like.',
    iconName: 'download-simple',
    extra: html`<a class="btn btn-primary btn-lg" href="${ctx.root + settings.free_pages.file}" download="${path.basename(settings.free_pages.file)}">${icon('download-simple')} Download the free pages</a>
      <p class="fine">Printing tip: choose “Fit to page” so the pictures fit on Letter or A4 paper.</p>`,
  }),
);
page('youre-on-the-list/index.html', '', (ctx) =>
  messagePage(ctx, {
    title: 'You’re on the list',
    lead: 'We’ll send you one short email when the next story is out.',
    iconName: 'bell-ringing',
    extra: html`<a class="btn btn-secondary btn-lg" href="${ctx.root}free-coloring-pages/">${icon('download-simple')} Get the free pages</a>`,
  }),
);
page('message-sent/index.html', '', (ctx) =>
  messagePage(ctx, {
    title: 'Thanks for your message',
    lead: 'We read every message and will write back soon.',
    iconName: 'envelope-simple',
    extra: '',
  }),
);
page('404.html', '', notFoundPage);

for (const p of pages) write(p.file, typeset(p.render()));
const sm = sitemap();
if (sm) write('sitemap.xml', sm);
write('robots.txt', `User-agent: *\nAllow: /\nDisallow: /admin/\n${SITE_URL ? `\nSitemap: ${SITE_URL}/sitemap.xml\n` : ''}`);
write('llms.txt', llmsTxt());
write('_redirects', redirects());
write('_headers', HEADERS);
write('site.webmanifest', manifest());

console.log(`Built ${pages.length} pages into site/ (${liveBooks.length} books on sale, ${books.length - liveBooks.length} coming soon)`);
console.log(SITE_URL ? `Site URL: ${SITE_URL}` : 'No site URL yet (set "url" in settings.json; Netlify fills it in): skipped sitemap.xml and absolute links');
for (const w of warnings) console.warn(`Warning: ${w}`);
