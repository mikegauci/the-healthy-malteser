# The Healthy Malteser

A static Astro migration of [thehealthymalteser.com](https://thehealthymalteser.com/).
No WordPress, CMS, database, PHP, forms, Mailjet, or runtime API is required.

## Develop and build

Use Node 24 and the existing checkout; a cloud task is already isolated, so do
not create a worktree unless requested.

```sh
export ASTRO_TELEMETRY_DISABLED=1
npm ci --cache /workspace/.npm-cache --no-audit --no-fund
npm run dev -- --port 4321
```

`npm run build` generates `dist/`. Vercel runs the same build from `main`.
Telemetry is disabled in this cloud environment because its home directory is
read-only. No application secrets are needed by the deployed static website.
Deployment tokens remain in secure cloud environment settings; a gitignored
`.env` with credential names is available for local use. Never expose deployment
tokens as `PUBLIC_` variables or configure them in the site's Vercel environment.

## Content and presentation

- `src/content/routes.json`: page metadata, canonical paths, structured data,
  stylesheet references, and publication IDs.
- `src/content/pages/*.html`: editable content for all 28 published posts,
  four published pages, category/tag archives, pagination, and 27 print pages.
- `src/content/recipes.json`: original recipe data, including ingredients,
  instructions, measurements, timings, and nutrition where provided.
- `src/content/header.html` and `footer.html`: shared navigation and branding.
- `public/media`: local WebP versions of the original photographs and logos.
  Responsive image candidates and intrinsic dimensions are preserved.
- `public/styles`: original static presentation rules and small accessibility,
  responsive menu, print, and click-to-load media adaptations. Original CSS class
  names remain styling hooks; they do not load a CMS or plugin.
- `public/site.js`: a small script for mobile navigation, on-demand video/social
  embeds, printing, and returning to the top. No frontend framework is shipped.
- `docs/content-inventory.json`: publication IDs and the complete migrated URL list.

The source declares Lato and Great Vibes in places without loading those webfonts.
The migration preserves the observed fallback typography and mirrors its loaded
PT Sans font locally as WOFF2. The original subscription/comment submission forms
are omitted at the owner's request; existing published comments remain read-only.
YouTube and Instagram contact third parties only after a visitor chooses to load
an embed; external social links remain available without JavaScript.

## URLs and SEO

Existing post, page, category, tag, pagination, and print paths are retained.
`vercel.json` provides permanent redirects for legacy WordPress publication IDs,
legacy image URLs, `/home/`, old sitemap URLs, and the obsolete author archive.
That author URL previously canonicalised to the homepage; it now leads to the
canonical author biography at `/mystory/`.

Each content page has its own title, description, canonical, social metadata,
and original appropriate structured data, including Recipe data. Paginated
archives have distinct titles and canonical URLs. `sitemap.xml` lists the 55
canonical content/archive routes; print copies and the HTTP 404 page are excluded
and marked `noindex`. `robots.txt` and `llms.txt` are static repository files.

## One-time import

Normal development/builds do not contact the old website. `scripts/import-content.py`
converts the archived source HTML, public API exports, and downloaded asset map
from `MIGRATION_SOURCE_DIR` into the repository's editable content. It requires
`scripts/requirements-import.txt`. The original acquisition archive is retained
outside this checkout at `/workspace/migration-source`; it contains operational
account/DNS snapshots too and must not be committed or published.

## Release checks

Keep verification focused: one final production build; check route membership,
local links/assets, SEO files, and JSON-LD; compare representative desktop/mobile
layouts and navigation; verify the deployed homepage, article, print page,
permanent redirect, SEO endpoints, caching, and real HTTP 404 response. This is
not a PageSpeed score or email-delivery claim. No email integration is used.

Before a domain switch, snapshot Cloudflare DNS and obtain Vercel's recommended
web records. Change only apex/www web records. Preserve all email, MX, TXT, CAA,
verification, and unrelated hosts. Validate production routing/TLS and compare
all unaffected DNS records afterwards.
