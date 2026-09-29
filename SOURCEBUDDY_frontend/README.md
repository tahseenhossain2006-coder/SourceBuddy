# SourceBuddy — Frontend

React + TypeScript + Vite frontend for SourceBuddy, an AI-assisted supplier
sourcing console.

## Requirements

- Node.js 18+ (20+ recommended)
- npm 9+

## Installation

    npm install

## Development

    npm run dev

The dev server runs on `http://localhost:3000` because the backend CORS policy
allows only that origin. See `vite.config.ts`.

## Type checking

    npm run typecheck

## Production build

    npm run build

Output goes to `dist/`.

## Environment configuration

Copy `.env.example` to `.env.local` and set:

    VITE_API_BASE_URL=http://localhost:8000

`VITE_API_BASE_URL` must be set for production builds. The client will throw at
startup if it is missing in a production bundle; the localhost fallback applies
to development only.

No secrets belong in `VITE_*` variables — they are inlined into the browser
bundle.

## Backend requirement

This frontend expects the SourceBuddy FastAPI backend to be running at the URL
in `VITE_API_BASE_URL`. Without it, `/app/*` routes will fail with network
errors and auth flows will not work.

The backend contract is documented in `SOURCEBUDDY_BACKEND_CONTRACT.md` in the
project root.

## Main routes

Public:

- `/` — landing page
- `/login` — sign in
- `/signup` — register

Protected (all require authentication):

- `/app` — console home
- `/app/search` — new search
- `/app/search/:searchId` — search detail (reduced supplier schema)
- `/app/suppliers/:id` — supplier detail (reads from router state; no
  supplier-by-id endpoint exists)
- `/app/compare` — client-side comparison of loaded suppliers
- `/app/rfq` — create RFQ
- `/app/rfq/:id` — RFQ detail with status transitions
- `/app/watchlists` — watchlists
- `/app/alerts` — unread alerts