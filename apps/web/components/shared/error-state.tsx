type ErrorStateProps = {
  message?: string;
  onRetry?: () => void;
};

export function ErrorState({ message = "请求失败，请确认后端服务是否已启动。", onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border px-6 py-12 text-center" style={{ borderColor: "var(--error-bg)", background: "var(--error-bg)" }}>
      <div className="text-2xl mb-2">⚠</div>
      <p className="text-sm font-medium" style={{ color: "var(--error)" }}>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-4 rounded-lg px-4 py-2 text-sm font-medium text-white" style={{ background: "var(--accent)" }}>
          重试
        </button>
      )}
    </div>
  );
}
