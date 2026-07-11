import { AlertTriangle, X } from "lucide-react";

export default function ErrorToast({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-sm animate-[fade-in_0.2s_ease-out]">
      <div className="flex items-start gap-3 rounded-xl bg-rose-500/10 backdrop-blur-md border border-rose-500/30 px-4 py-3 shadow-2xl shadow-rose-900/40">
        <AlertTriangle className="w-4.5 h-4.5 text-rose-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-semibold text-rose-300">Backtest failed</p>
          <p className="text-xs text-rose-300/80 mt-0.5 leading-relaxed">{message}</p>
        </div>
        <button
          onClick={onDismiss}
          className="text-rose-400/70 hover:text-rose-300 transition-colors"
          aria-label="Dismiss error"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
