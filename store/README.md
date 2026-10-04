# Little Crayon Tales online store

A fast, free-to-host shop for the books. Amazon still prints, sells and ships every copy;
the store's job is to turn TikTok / Instagram / Pinterest visitors into Amazon orders and
email subscribers.

| What it does | How |
|---|---|
| Book pages with a cover, back cover and real inside pages (tap to zoom) | `books/<slug>/` |
| **Bag**: pick several books, check out on Amazon in one go | Amazon's add-to-cart link (`gp/aws/cart/add.html`) |
| Sends each visitor to **their own Amazon** (US, UK, CA, AU, DE, FR, ES, IT, NL, PL, SE, JP), changeable in the footer | time zone + browser language |
| **Free coloring pages** for an email (grows your mailing list) | Netlify Forms, PDF in `public/downloads/` |
| "Tell me when Dex is out" signup on coming-soon books, plus a contact form | Netlify Forms |
| Short links for bios and captions: `yoursite/nico` (book page), `yoursite/go/nico` (straight to the visitor's local Amazon) | `site/_redirects` |
| Google and AI search: Book schema, FAQ schema, sitemap, `llms.txt`, link-preview images per book | made by the build |
| Phone first, dark ("bedtime") mode, works with keyboard and screen readers, no cookies or trackers | |
| **Admin panel** at `/admin/` to edit books and texts without code | Decap CMS (free, open source) |

Everything is plain HTML/CSS/JS with no monthly fee. The fonts are self-hosted (no Google
requests, which matters for privacy rules in Europe).

## Put it online (Netlify, free)

1. Merge this branch into `main` on GitHub.
2. Go to [app.netlify.com](https://app.netlify.com), **Add new project > Import an existing project > GitHub**,
   pick `kids-coloring-books`. Netlify reads `netlify.toml` (build: `node store/build.mjs`,
   publish: `site`), so just click **Deploy**.
3. In the project, open **Forms** and click **Enable form detection**, then redeploy once
   (Deploys > Trigger deploy). Under Forms > Notifications you can get an email for every signup.
4. Optional: **Domain management > Add a domain** (e.g. `littlecrayontales.com`).
5. Test once on your phone: add both books to the bag and tap **Check out on Amazon**. Amazon
   should ask "add to cart?" with both books. If it ever shows an error instead, set
   `amazon.bag_checkout` to `false` in `content/settings.json` (or in the admin), and the bag
   keeps a "View on Amazon" link per book.

From then on, every push to `main` (or every save in the admin) updates the site in about a minute.

No GitHub? Drag the `site/` folder onto [app.netlify.com/drop](https://app.netlify.com/drop).
Everything works except the admin panel. It also runs on Cloudflare Pages or GitHub Pages (point
them at `site/`), but the forms only work on Netlify.

## Admin panel (`/admin/`), one-time setup

1. Netlify project > **Project configuration > Identity > Enable Identity**.
2. Identity > **Registration > Invite only** (important: otherwise anyone could sign up and edit the shop).
3. Identity > **Services > Git Gateway > Enable**.
4. Identity > **Invite users**, enter your email, open the invite link and choose a password.
5. Open `yoursite/admin/`. "Books" and "Store settings" are editable; every save becomes a
   commit on GitHub and the site rebuilds itself.

## Everyday tasks

- **Dex goes live:** in the admin (or `content/books/dex.json`) set Status to *On sale* and paste
  the ASIN, the code after `/dp/` in the Amazon link. Everything else (buttons, bag, short links,
  search data) follows.
- **New book:** make its pictures with `python3 tools/make_store_assets.py <id>` after adding it to
  `store/assets.json`, copy `content/books/nico.json` to `content/books/<id>.json` and edit it,
  then `node store/build.mjs`. Or ask Claude: "add Rocco to the store".
  (Colored-in example pages need `pip install numpy scipy` and a `marketing/paint` map.)
- **Prices:** left empty on purpose (Amazon changes them). Fill `price` (e.g. `8.99`) to show a
  US list price.
- **Amazon Associates:** paste your tracking IDs under `amazon.tags`. The required disclosure
  then appears in the footer automatically.
- **Germany / EU:** if you need an Impressum, fill `legal_notice`; a Legal notice page appears.
- **Reviews:** only real ones with permission, under `reviews` in a book.

## Files

| Path | What it is |
|---|---|
| `content/settings.json`, `content/books/*.json` | All text and settings (what the admin edits) |
| `src/styles.css`, `src/app.js` | Look and behavior (bag, Amazon store, gallery, slider, forms) |
| `public/` | Copied as-is: pictures, fonts, free PDF, admin panel |
| `icons/` | Phosphor icons (MIT) used by the build |
| `build.mjs` | Builds `site/` (no dependencies, Node 18+) |
| `assets.json` + `../tools/make_store_assets.py` | Which book pages become web pictures, link previews and the free PDF |
| `../site/` | The built website. Generated: don't edit by hand, it is replaced on every build |
