import { Suspense } from "react";
import { RentaNaturalLandingForm } from "@/components/renta-natural/RentaNaturalLandingForm";

/**
 * Public social-ad landing page (b2c-social-lead-capture, Task 4).
 * URL: `contexia.online/renta-natural` — confirmed by the founder 2026-09-10
 * (design.md "Open Questions"). No auth, no shell (TopBar/BottomNav) — this
 * is the first page a Facebook/Instagram/TikTok ad click lands on, not part
 * of the authenticated PWA.
 */
export default function RentaNaturalPage() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 px-6 py-16">
      <div className="flex flex-col gap-2 text-center">
        <span className="text-xs font-bold uppercase tracking-widest text-teal-300">
          Renta Natural 2026
        </span>
        <h1 className="text-2xl font-extrabold text-white">
          Declara tu renta sin complicaciones
        </h1>
        <p className="text-sm text-white/70">
          Deja tus datos y Taty, la asistente de Contexia, te contacta por WhatsApp para
          ayudarte con tu declaración de Renta Natural 2026.
        </p>
      </div>

      {/* useSearchParams (RentaNaturalLandingForm) requires a Suspense boundary
          under the App Router — this page is otherwise a Server Component. */}
      <Suspense fallback={null}>
        <RentaNaturalLandingForm />
      </Suspense>
    </main>
  );
}
