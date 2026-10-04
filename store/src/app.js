// Little Crayon Tales store: the bag (checks out on Amazon), the visitor's local Amazon store,
// the book gallery, the color-in slider and friendly form checks. No dependencies.
(() => {
  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
  const root = document.documentElement.dataset.root || '';
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Netlify Identity sends invite and password links to the home page: hand them to the admin
  if (/(invite|recovery|confirmation|email_change)_token=/.test(location.hash) && !location.pathname.includes('/admin')) {
    location.replace(`${root}admin/${location.hash}`);
    return;
  }

  let data = { books: {}, stores: ['com'], tags: {}, defaultStore: 'com', icons: {} };
  try {
    data = { ...data, ...JSON.parse($('#store-data').textContent) };
  } catch {}

  const saved = {
    get(key, fallback) {
      try {
        const v = localStorage.getItem(key);
        return v === null ? fallback : JSON.parse(v);
      } catch {
        return fallback;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch {}
    },
  };

  function toast(text) {
    $('.toast')?.remove();
    const el = document.createElement('div');
    el.className = 'toast';
    el.setAttribute('role', 'status');
    el.textContent = text;
    document.body.append(el);
    setTimeout(() => el.remove(), 2400);
  }

  // ---------- which Amazon store ----------

  const TIMEZONES = {
    'Europe/London': 'co.uk', 'Europe/Dublin': 'co.uk', 'Europe/Berlin': 'de', 'Europe/Vienna': 'de',
    'Europe/Zurich': 'de', 'Europe/Luxembourg': 'de', 'Europe/Paris': 'fr', 'Europe/Brussels': 'fr',
    'Europe/Madrid': 'es', 'Europe/Lisbon': 'es', 'Europe/Rome': 'it', 'Europe/Amsterdam': 'nl',
    'Europe/Warsaw': 'pl', 'Europe/Stockholm': 'se', 'Europe/Oslo': 'se', 'Europe/Copenhagen': 'se',
    'Europe/Helsinki': 'se', 'Asia/Tokyo': 'co.jp', 'Pacific/Auckland': 'com.au',
  };
  const CANADA = /^America\/(Toronto|Vancouver|Edmonton|Winnipeg|Halifax|St_Johns|Regina|Montreal|Moncton|Whitehorse|Yellowknife|Iqaluit|Glace_Bay|Goose_Bay|Swift_Current|Dawson_Creek)$/;
  const REGIONS = {
    GB: 'co.uk', IE: 'co.uk', CA: 'ca', AU: 'com.au', NZ: 'com.au', DE: 'de', AT: 'de', CH: 'de',
    FR: 'fr', BE: 'fr', ES: 'es', PT: 'es', IT: 'it', NL: 'nl', PL: 'pl', SE: 'se', JP: 'co.jp',
  };

  function detectStore() {
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
      if (TIMEZONES[tz]) return TIMEZONES[tz];
      if (tz.startsWith('Australia/')) return 'com.au';
      if (CANADA.test(tz)) return 'ca';
      if (tz.startsWith('America/') || tz.startsWith('US/')) return 'com';
    } catch {}
    for (const lang of navigator.languages || [navigator.language || '']) {
      const region = (lang.split('-')[1] || '').toUpperCase();
      if (REGIONS[region]) return REGIONS[region];
    }
    return null;
  }

  const known = (tld) => data.stores.includes(tld);
  let current = saved.get('lct-store', null);
  if (!known(current)) current = (data.detect && detectStore()) || data.defaultStore;
  if (!known(current)) current = 'com';

  const tag = (tld) => data.tags[tld] || '';
  const productUrl = (asin) => `https://www.amazon.${current}/dp/${asin}${tag(current) ? `?tag=${encodeURIComponent(tag(current))}` : ''}`;
  const cartUrl = (items) =>
    `https://www.amazon.${current}/gp/aws/cart/add.html?` +
    items.map(([id, qty], i) => `ASIN.${i + 1}=${encodeURIComponent(data.books[id].asin)}&Quantity.${i + 1}=${qty}`).join('&') +
    (tag(current) ? `&AssociateTag=${encodeURIComponent(tag(current))}` : '');

  function applyStore() {
    $$('a[data-asin]').forEach((a) => (a.href = productUrl(a.dataset.asin)));
    $$('[data-store-name]').forEach((el) => (el.textContent = `Amazon.${current}`));
    $$('[data-store-select]').forEach((sel) => (sel.value = current));
    $$('[data-us-only]').forEach((el) => (el.hidden = current !== 'com'));
    renderBag();
  }

  document.addEventListener('change', (e) => {
    if (!e.target.matches('[data-store-select]')) return;
    current = e.target.value;
    saved.set('lct-store', current);
    applyStore();
    toast(`Buy buttons now open Amazon.${current}`);
  });

  // ---------- the bag ----------

  const dialog = $('[data-bag]');
  let bag = saved.get('lct-bag', {});
  const items = () => Object.entries(bag).filter(([id, qty]) => data.books[id] && qty > 0);

  function setBag(next, { bump = false } = {}) {
    bag = next;
    saved.set('lct-bag', bag);
    renderBag();
    if (bump) {
      const count = $('[data-bag-count]');
      count?.classList.remove('bump');
      void count?.offsetWidth;
      count?.classList.add('bump');
    }
  }

  function bagItem([id, qty]) {
    const b = data.books[id];
    return `<div class="bag-item">
      <img src="${esc(root + b.cover)}" alt="" width="76" height="76">
      <div>
        <p class="bag-item-title"><a href="${esc(root + b.url)}">${esc(b.title)}</a></p>
        <div class="bag-item-row">
          <div class="qty" role="group" aria-label="How many copies of ${esc(b.title)}">
            <button type="button" data-qty="-1" data-id="${esc(id)}" aria-label="One copy less"${qty <= 1 ? ' disabled' : ''}>${data.icons.minus || '-'}</button>
            <output>${qty}</output>
            <button type="button" data-qty="1" data-id="${esc(id)}" aria-label="One copy more"${qty >= 10 ? ' disabled' : ''}>${data.icons.plus || '+'}</button>
          </div>
          <button type="button" class="link-button" data-remove="${esc(id)}">Remove</button>
        </div>
        <a class="bag-item-amazon" href="${esc(productUrl(b.asin))}" target="_blank" rel="noopener">View on Amazon.${esc(current)}</a>
      </div>
    </div>`;
  }

  function suggestion() {
    const missing = Object.keys(data.books).find((id) => !bag[id]);
    if (!missing) return '';
    const b = data.books[missing];
    return `<div class="bag-suggest">
      <img src="${esc(root + b.cover)}" alt="" width="52" height="52">
      <p><strong>Complete the set</strong>${esc(b.title)}</p>
      <button class="btn btn-secondary btn-sm" type="button" data-add="${esc(missing)}" data-stay>Add</button>
    </div>`;
  }

  function renderBag() {
    const list = items();
    const count = list.reduce((n, [, qty]) => n + qty, 0);
    $$('[data-bag-count]').forEach((el) => {
      el.textContent = count;
      el.hidden = count === 0;
    });
    $('[data-open-bag]')?.setAttribute('aria-label', count ? `Your bag, ${count} book${count === 1 ? '' : 's'}` : 'Your bag is empty');
    if (!dialog) return;

    // keep keyboard focus on the same control after re-rendering
    const active = dialog.contains(document.activeElement) ? document.activeElement : null;
    const focusKey = active?.dataset.qty ? `[data-qty="${active.dataset.qty}"][data-id="${active.dataset.id}"]` : null;

    const box = $('[data-bag-items]', dialog);
    const foot = $('[data-bag-foot]', dialog);
    if (!list.length) {
      box.innerHTML = `<div class="bag-empty">${data.icons.bag || ''}
        <p class="bag-empty-title">Your bag is empty</p>
        <p>Add a few books, then check out on Amazon in one go.</p>
        <a class="btn btn-secondary" href="${esc(root)}books/">See all books</a></div>`;
      foot.hidden = true;
    } else {
      box.innerHTML = list.map(bagItem).join('') + suggestion();
      foot.hidden = false;
      const checkout = $('[data-checkout]', dialog);
      checkout.hidden = !data.bagCheckout;
      checkout.href = cartUrl(list);
      checkout.innerHTML = `${data.icons.amazon || ''} Check out on Amazon.${esc(current)}`;
    }
    if (focusKey) ($(focusKey, dialog) || $('[data-close-bag]', dialog))?.focus();
  }

  function openBag() {
    if (!dialog) return;
    renderBag();
    if (!dialog.open) dialog.showModal();
  }

  document.addEventListener('click', (e) => {
    const t = e.target instanceof Element ? e.target : null;
    if (!t) return;
    const add = t.closest('[data-add]');
    if (add && data.books[add.dataset.add]) {
      const id = add.dataset.add;
      setBag({ ...bag, [id]: Math.min((bag[id] || 0) + 1, 10) }, { bump: true });
      if (add.hasAttribute('data-stay')) $('[data-close-bag]', dialog)?.focus();
      openBag();
      return;
    }
    const step = t.closest('[data-qty]');
    if (step) {
      const id = step.dataset.id;
      setBag({ ...bag, [id]: Math.max(1, Math.min(10, (bag[id] || 1) + Number(step.dataset.qty))) });
      return;
    }
    const remove = t.closest('[data-remove]');
    if (remove) {
      const next = { ...bag };
      delete next[remove.dataset.remove];
      setBag(next);
      $('[data-close-bag]', dialog)?.focus();
      return;
    }
    if (t.closest('[data-open-bag]')) openBag();
    else if (t.closest('[data-close-bag]')) dialog?.close();
  });
  // a click on the dimmed backdrop closes the bag
  dialog?.addEventListener('click', (e) => {
    if (e.target === dialog) dialog.close();
  });
  window.addEventListener('storage', (e) => {
    if (e.key === 'lct-bag') {
      bag = saved.get('lct-bag', {});
      renderBag();
    }
  });

  // ---------- product gallery + lightbox ----------

  const gallery = $('[data-gallery]');
  const lightbox = $('[data-lightbox]');
  if (gallery) {
    const thumbs = $$('[data-slide]', gallery);
    const main = $('[data-gallery-main]', gallery);
    const mainImg = $('img', main);
    const slides = thumbs.map((t) => ({ full: t.dataset.full, caption: t.dataset.caption, alt: $('img', t).alt, img: $('img', t) }));
    let index = 0;

    const show = (i) => {
      index = (i + slides.length) % slides.length;
      const s = slides[index];
      mainImg.removeAttribute('srcset');
      mainImg.removeAttribute('sizes');
      mainImg.width = s.img.width;
      mainImg.height = s.img.height;
      mainImg.src = s.full;
      mainImg.alt = s.alt;
      main.href = s.full;
      thumbs.forEach((t, k) => (k === index ? t.setAttribute('aria-current', 'true') : t.removeAttribute('aria-current')));
    };
    thumbs.forEach((t, k) =>
      t.addEventListener('click', (e) => {
        e.preventDefault();
        show(k);
      }),
    );

    if (lightbox) {
      const lbImg = $('[data-lightbox-img]', lightbox);
      const lbCaption = $('[data-lightbox-caption]', lightbox);
      const setSlide = (i) => {
        show(i);
        const s = slides[index];
        lbImg.src = s.full;
        lbImg.alt = s.alt;
        lbCaption.textContent = s.caption;
      };
      const open = (i) => {
        setSlide(i);
        lightbox.showModal();
      };
      main.addEventListener('click', (e) => {
        e.preventDefault();
        open(index);
      });
      $$('[data-open-slide]').forEach((a) =>
        a.addEventListener('click', (e) => {
          e.preventDefault();
          open(Number(a.dataset.openSlide));
        }),
      );
      $('[data-lightbox-prev]', lightbox).addEventListener('click', () => setSlide(index - 1));
      $('[data-lightbox-next]', lightbox).addEventListener('click', () => setSlide(index + 1));
      $('[data-lightbox-close]', lightbox).addEventListener('click', () => lightbox.close());
      lightbox.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') setSlide(index - 1);
        if (e.key === 'ArrowRight') setSlide(index + 1);
      });
      lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox || e.target.tagName === 'FIGURE') lightbox.close();
      });
      let startX = null;
      lightbox.addEventListener('pointerdown', (e) => (startX = e.clientX));
      lightbox.addEventListener('pointerup', (e) => {
        if (startX === null) return;
        const dx = e.clientX - startX;
        startX = null;
        if (Math.abs(dx) > 50) setSlide(index + (dx < 0 ? 1 : -1));
      });
    }
  }

  // ---------- "color the page" slider ----------

  $$('[data-compare]').forEach((fig) => {
    const range = $('.compare-range', fig);
    if (!range) return;
    let touched = false;
    const set = (v) => fig.style.setProperty('--pos', `${v}%`);
    range.addEventListener('input', () => {
      touched = true;
      set(range.value);
    });
    set(range.value);
    if (reduceMotion || !('IntersectionObserver' in window)) return;
    // one gentle sweep the first time it scrolls into view, so people see it can be dragged
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        io.disconnect();
        const start = performance.now();
        const frame = (now) => {
          if (touched) return;
          const t = Math.min((now - start) / 1800, 1);
          const v = 50 + Math.sin(t * Math.PI * 2) * 24 * (1 - t);
          set(v);
          range.value = v;
          if (t < 1) requestAnimationFrame(frame);
        };
        setTimeout(() => requestAnimationFrame(frame), 300);
      },
      { threshold: 0.6 },
    );
    io.observe(fig);
  });

  // ---------- sticky buy bar on phones ----------

  const bar = $('[data-buy-bar]');
  const buyBox = $('[data-buy-box]');
  if (bar && buyBox && 'IntersectionObserver' in window) {
    const wide = window.matchMedia('(min-width: 960px)');
    let pastBuy = false;
    let atFooter = false;
    const update = () => (bar.hidden = !pastBuy || atFooter || wide.matches);
    // the viewport is stretched far downwards, so "intersecting" means "not yet scrolled past"
    // (a plain observer misses a jump from below the buttons straight back to the top)
    new IntersectionObserver(
      ([e]) => {
        pastBuy = !e.isIntersecting;
        update();
      },
      { rootMargin: '0px 0px 100000px 0px' },
    ).observe(buyBox);
    new IntersectionObserver(([e]) => {
      atFooter = e.isIntersecting;
      update();
    }).observe($('.site-footer'));
    wide.addEventListener?.('change', update);
  }

  // ---------- share ----------

  const pageUrl = $('link[rel="canonical"]')?.href || location.href.split('#')[0];
  $$('[data-share-pin]').forEach((a) => {
    const media = new URL(a.dataset.media, location.href).href;
    a.href = `https://www.pinterest.com/pin/create/button/?url=${encodeURIComponent(pageUrl)}&media=${encodeURIComponent(media)}&description=${encodeURIComponent(document.title)}`;
  });
  $$('[data-share-fb]').forEach((a) => (a.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(pageUrl)}`));
  $$('[data-share]').forEach((btn) =>
    btn.addEventListener('click', async () => {
      if (navigator.share) {
        try {
          await navigator.share({ title: document.title, url: pageUrl });
        } catch {}
        return;
      }
      try {
        await navigator.clipboard.writeText(pageUrl);
        toast('Link copied');
      } catch {
        toast('Copy the link from the address bar');
      }
    }),
  );

  // ---------- forms: check on leaving a field, clear as soon as it is fixed ----------

  function problem(input) {
    const v = input.value.trim();
    if (!v) return input.type === 'email' ? 'Please add your email address.' : 'Please write a short message.';
    if (input.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) {
      return 'This email address looks incomplete. It should look like name@example.com.';
    }
    return '';
  }
  function mark(input, message) {
    const el = document.getElementById((input.getAttribute('aria-describedby') || '').split(' ')[0]);
    if (message) input.setAttribute('aria-invalid', 'true');
    else input.removeAttribute('aria-invalid');
    if (el) {
      el.textContent = message;
      el.hidden = !message;
    }
  }
  $$('form[data-form]').forEach((form) => {
    form.noValidate = true;
    const fields = $$('input[required], textarea[required]', form);
    form.addEventListener('submit', (e) => {
      let first = null;
      fields.forEach((input) => {
        const message = problem(input);
        mark(input, message);
        if (message && !first) first = input;
      });
      if (first) {
        e.preventDefault();
        first.focus();
        return;
      }
      const button = $('button[type="submit"]', form);
      if (button) {
        button.disabled = true;
        button.dataset.label = button.innerHTML;
        button.textContent = 'Sending...';
      }
    });
    fields.forEach((input) => {
      input.addEventListener('blur', () => input.value && mark(input, problem(input)));
      input.addEventListener('input', () => input.hasAttribute('aria-invalid') && mark(input, problem(input)));
    });
  });
  // coming back with the browser's back button: buttons work again, bag is fresh
  window.addEventListener('pageshow', (e) => {
    if (!e.persisted) return;
    $$('button[data-label]').forEach((b) => {
      b.disabled = false;
      b.innerHTML = b.dataset.label;
    });
    bag = saved.get('lct-bag', {});
    renderBag();
  });

  applyStore();
})();
