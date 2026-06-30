import Link from "next/link";
import type { TatyEscalation } from "@/lib/types/contexia";

export function TatyEscalationCard({ data }: { data: TatyEscalation }) {
  const baseClass =
    "w-full bg-surface-elevated rounded-xl p-4 border border-ai-narrative-tint/30 flex items-center justify-between hover:bg-surface-variant/50 transition-colors group";

  const content = (
    <>
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-ai-narrative-tint/20 border border-ai-narrative-tint/40 flex items-center justify-center">
          <span className="material-symbols-outlined text-ai-narrative-tint">
            support_agent
          </span>
        </div>
        <div className="text-left">
          <h4 className="font-body-md text-body-md font-semibold text-on-surface group-hover:text-ai-narrative-tint transition-colors">
            {data.title}
          </h4>
          <p className="font-label-caps text-label-caps text-on-surface-variant">
            {data.subtitle}
          </p>
        </div>
      </div>
      <span className="material-symbols-outlined text-on-surface-variant group-hover:text-ai-narrative-tint group-hover:translate-x-1 transition-all">
        arrow_forward
      </span>
    </>
  );

  if (data.href) {
    return (
      <Link href={data.href} className={baseClass}>
        {content}
      </Link>
    );
  }

  return (
    <button type="button" className={baseClass}>
      {content}
    </button>
  );
}
