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

## Cloudflare Pages Configuration

Use the following settings in Cloudflare Pages:

- Build command: `npm run build`
- Build directory: `dist`
- Framework preset: `None` or `Vite`
- Root directory: `/frontend`

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
