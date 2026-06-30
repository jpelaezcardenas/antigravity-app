"use client";

interface StepNavigationProps {
  onBack?: () => void;
  onNext?: () => void;
  nextLabel?: string;
  backLabel?: string;
  canGoNext?: boolean;
  canGoBack?: boolean;
  errorMessage?: string;
  isFinalStep?: boolean;
}

export function StepNavigation({
  onBack,
  onNext,
  nextLabel = "Siguiente",
  backLabel = "Atrás",
  canGoNext = true,
  canGoBack = true,
  errorMessage,
  isFinalStep = false,
}: StepNavigationProps) {
  return (
    <div className="flex flex-col gap-3 pt-4 mt-2">
      {errorMessage && (
        <div className="bg-status-critical/10 border border-status-critical/30 rounded-xl px-4 py-2.5 flex items-center gap-2">
          <span className="material-symbols-outlined text-status-critical text-[18px]">
            error
          </span>
          <span className="text-sm text-status-critical font-medium">
            {errorMessage}
          </span>
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        {canGoBack && onBack ? (
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-2 px-5 py-3 rounded-xl border border-white/10 bg-white/[0.03] text-on-surface hover:bg-white/[0.06] hover:border-white/20 transition-all font-semibold"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            {backLabel}
          </button>
        ) : (
          <div />
        )}

        <button
          type="button"
          onClick={onNext}
          disabled={!canGoNext}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${
            canGoNext
              ? isFinalStep
                ? "bg-gradient-to-r from-[#2DD4BF] to-[#8B5CF6] text-white shadow-[0_0_24px_rgba(45,212,191,0.4)] hover:shadow-[0_0_32px_rgba(45,212,191,0.6)]"
                : "bg-gradient-to-r from-[#2DD4BF] to-[#14B8A6] text-[#020617] shadow-[0_0_20px_rgba(45,212,191,0.3)] hover:shadow-[0_0_28px_rgba(45,212,191,0.5)]"
              : "bg-white/[0.05] text-on-surface-variant/40 cursor-not-allowed"
          }`}
        >
          {nextLabel}
          <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}
