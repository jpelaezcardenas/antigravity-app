# Contexia Auth Routing

This is the source of truth for the production login flow.

## Canonical login

- The only production login UI is `/login.html`.
- The source file is `login.html` at the repository root.
- Do not route app access to `/wizard/login`, `/wizard/login/`, `contexia-app/app/login`, or `contexia-wizard/app/login`.

## Public entry points

- Landing `Acceso App` goes to `/login.html`.
- `/login`, `/app/login`, `/app/login.html`, `/wizard/login`, and `/wizard/login/` redirect to `/login.html`.
- `Shadow Audit` is separate and goes to `https://contexia-wizard.vercel.app/wizard`.

## Post-login destinations

- `Cliente` goes to `/app/overview`.
- `Admin` goes to `/app/bunker`.
- The only admin email is `contexia.marketing@gmail.com`.
- `contexia.marketing@gmail.com` can also enter as `Cliente` when the user chooses the `Cliente` role.

## Logout

- App logout goes to `/logout`.
- `/logout` redirects to `/logout.html`.
- `logout.html` clears local session storage/cookies and returns to `/login.html`.

## Deployment note

Vercel production has served `main` during this incident. Keep `main` and `deploy-prod` aligned for login/routing fixes unless the Vercel project source branch is changed intentionally.
