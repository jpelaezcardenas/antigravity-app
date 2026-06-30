export function FAB() {
  return (
    <button
      type="button"
      aria-label="Chat con Taty"
      className="fixed bottom-28 right-container-margin-mobile w-14 h-14 bg-primary-container rounded-full shadow-[0_0_20px_rgba(45,212,191,0.4)] flex items-center justify-center z-40 hover:opacity-90 active:scale-95 transition-all md:hidden"
    >
      <span className="material-symbols-outlined icon-fill text-bg-obsidian">
        forum
      </span>
    </button>
  );
}
