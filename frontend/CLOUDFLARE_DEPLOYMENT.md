# Cloudflare Deployment Guide for Matra Frontend

This guide prepares the Matra frontend for deployment to Cloudflare Pages.

## Build Setup

1. Install dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. Build the static site:

   ```bash
   npm run build
   ```

3. The production output is generated in `frontend/dist`.

## Cloudflare Pages / Workers Configuration

If you're using **Cloudflare Pages** (recommended for static sites) use these settings:

- Build command: `npm run build`
- Build directory: `dist`
- Framework preset: `None` or `Vite`
- Root directory: `/frontend`

If your pipeline uses `wrangler` (Workers or Workers Sites) make sure Wrangler only uploads the production build rather than the entire repo. Two easy options:

- Add a `wrangler.toml` at `frontend/wrangler.toml` with `site.bucket = "./dist"` (this repo already includes one).
- Add a `.wranglerignore` in the frontend directory to exclude `src`, `node_modules`, `public`, and other large folders (this repo already includes one). This prevents Wrangler from attempting to upload tens of thousands of source files and hitting the 20,000 asset limit.

Recommended CI/Deploy command (ensures only `dist` is uploaded):

```bash
# from repository root or inside frontend/
pnpm run build
npx wrangler pages publish ./dist --project-name=matra-frontend
```

Notes:
- Cloudflare's Workers asset upload will fail when the manifest contains more than 20,000 files unless you are on a paid plan. Only upload `dist` to avoid this.
- If you're using Pages, you don't need `wrangler` at all — set the Pages build command to `npm run build` so Pages uploads only the `dist` directory.
- The `npx wrangler versions upload` invocation seen in CI uploads the entire working directory as assets unless configured to target `dist`; use `wrangler pages publish ./dist` (or the Pages UI) to avoid the asset limit.

## Client-Side Routing

This app uses client-side navigation with Navigo.

- Set the Pages project to use `index.html` as the fallback page for unknown routes.
- If you cannot set the fallback in the Cloudflare Pages UI, use the Pages `404` handling option and point it to `index.html`.

## Environment Variables

Cloudflare Pages supports build-time environment variables.

Set these variables in Pages:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`
- `VITE_API_BASE_URL` — backend API origin, e.g. `https://api.example.com`

## Notes on Assets and Paths

- `vite.config.ts` is configured with `base: '/'` and output directory `dist`.
- The logo assets are now referenced using Vite-friendly relative paths so they are included in the production build.
- `favicon.svg` remains served from the root and is compatible with Pages.

## Quick Verification

After deployment, verify:

- `https://<your-pages-site>/` loads the app.
- Client-side routes like `/triage` and `/dashboard` work after refresh.
- API calls use `VITE_API_BASE_URL` and not the local host origin.
