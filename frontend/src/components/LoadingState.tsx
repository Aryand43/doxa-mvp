export function LoadingState({ label = "Working…" }: { label?: string }) {
  return (
    <div className="state state-loading">
      <span className="spinner" aria-hidden />
      <span>{label}</span>
    </div>
  );
}
