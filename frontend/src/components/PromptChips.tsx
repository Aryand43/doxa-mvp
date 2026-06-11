export function PromptChips({
  prompts,
  onSelect,
  disabled,
}: {
  prompts: string[];
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}) {
  if (prompts.length === 0) return null;
  return (
    <div className="chip-row">
      {prompts.map((p) => (
        <button
          key={p}
          type="button"
          className="chip"
          onClick={() => onSelect(p)}
          disabled={disabled}
        >
          {p}
        </button>
      ))}
    </div>
  );
}
