export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state state-error" role="alert">
      <strong>Something went wrong.</strong>
      <span>{message}</span>
    </div>
  );
}
