import type { NoteOfDay } from "@/lib/types/contexia";

export function NoteOfDayCard({ note }: { note: NoteOfDay }) {
  return (
    <section className="relative bg-surface-elevated/50 backdrop-blur-md rounded-xl p-6 border border-ai-narrative-tint/30 shadow-[0_0_30px_rgba(139,92,246,0.1)]">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-full bg-ai-narrative-tint/20 flex items-center justify-center shrink-0 border border-ai-narrative-tint/50">
          <span className="material-symbols-outlined icon-fill text-secondary-fixed-dim">
            auto_awesome
          </span>
        </div>
        <div>
          <h2 className="font-title-md text-title-md text-primary-container mb-1">
            {note.title}
          </h2>
          <p className="font-body-lg text-body-lg text-on-surface leading-relaxed">
            {note.body}
          </p>
        </div>
      </div>
    </section>
  );
}
