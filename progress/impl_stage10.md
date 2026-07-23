# Stage 10 — CashTodayCard: no longer masks fetch errors with mock data

## Scope

Single file: `contexia-app/components/pulso/CashTodayCard.tsx`.

## Bug (before)

The `useEffect`'s `.catch()` handler on `fetchFinancials()` failure fell back to the mock,
presented as "ready" (real) data — violating the archived spec requirement that error
states must be honest and never show a misleading mock value.

Old code:

```tsx
const [status, setStatus] = useState<"loading" | "ready" | "empty">("loading");
...
.catch((error) => {
  if (cancelled) return;
  // Spec "degrades gracefully": on any fetch failure fall back to the
  // baked-in placeholder figures — the end user must never see an error
  // banner here (same fail-safe contract as the retired injected script).
  console.warn("[CashTodayCard] financials fetch failed, using fallback", error);
  setCash(pulsoMock.cash);
  setStatus("ready");
});
```

There was no `"error"` status branch in the render — a fetch failure was
indistinguishable from a genuinely successful live fetch.

## Fix (after)

1. Removed the unused `pulsoMock` import (it was only referenced by the
   error-fallback path; no other usage in the file).
2. Widened the status union to `"loading" | "ready" | "empty" | "error"`.
3. `.catch()` now sets `status = "error"` instead of assigning `pulsoMock.cash`
   and marking `"ready"`. `console.warn` is kept for debugging.

```tsx
.catch((error) => {
  if (cancelled) return;
  // Spec "degrades gracefully": on any fetch failure render an
  // unobtrusive error state — never fall back to a mock value
  // presented as if it were real, live data.
  console.warn("[CashTodayCard] financials fetch failed", error);
  setStatus("error");
});
```

4. Added a new `"error"` render branch, styled identically to the existing
   `"empty"` state (same card shell, `@theme` tokens only, no ad-hoc colors,
   no red banner) with quiet copy matching the app's tone:

```tsx
if (status === "error") {
  return (
    <section className="bg-surface-elevated rounded-xl p-6 border border-white/10 relative overflow-hidden">
      <h2 className="font-body-md text-body-md text-white mb-2">
        Caja Real de Hoy
      </h2>
      <p className="font-body-md text-body-md text-on-surface-variant">
        No pudimos actualizar tu Caja Real. Intenta de nuevo en un momento.
      </p>
    </section>
  );
}
```

## `pulsoMock` grep confirmation

```
$ grep -n pulsoMock contexia-app/components/pulso/CashTodayCard.tsx
13:  // whole COP, matching the existing pulsoMock convention (e.g. 42_850_000).
```

Only remaining hit is a code comment (unrelated to the removed fallback usage,
describing the minor-units convention used by `toCashToday`) — no import, no
reference, no fallback-on-error usage of `pulsoMock` remains.

## Manual trace

- `fetchFinancials()` throws `ApiError` (non-2xx) or a network `TypeError` →
  rejected promise → `.catch()` fires → `status = "error"` → the new `"error"`
  render branch is hit. `cash` state is never set from mock data on this path.
- Success path (`snapshot.status !== "empty"`) is unchanged: `setCash(toCashToday(snapshot))`
  + `status = "ready"`.
- `snapshot.status === "empty"` path is unchanged: `status = "empty"`.

## Verification

```
$ cd contexia-app && npx tsc --noEmit
(no output — clean)
```

## Commit

`014b740` — `fix(pwa-tenant-aware-screens): CashTodayCard no longer masks fetch errors with mock data`

Only `contexia-app/components/pulso/CashTodayCard.tsx` staged/committed (verified via
`git status` before `git add`; Stage 8/9 concurrent-agent files left untouched).

## Not done (out of scope, per task instructions)

- `tasks.md` not checked off — leader/reviewer owns that.
