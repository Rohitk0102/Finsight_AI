export function TypingIndicator() {
  return (
    <div className="flex flex-col gap-2 p-4 mt-2">
      <div className="text-[11px] finsight-muted tracking-widest">
        ANALYZING MARKET DATA...
      </div>
      <div className="flex gap-1.5">
        <div className="w-2 h-2 rounded-full finsight-bg finsight-accent border border-[var(--accent)] animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2 h-2 rounded-full finsight-bg finsight-accent border border-[var(--accent)] animate-bounce" style={{ animationDelay: '200ms' }}></div>
        <div className="w-2 h-2 rounded-full finsight-bg finsight-accent border border-[var(--accent)] animate-bounce" style={{ animationDelay: '400ms' }}></div>
      </div>
    </div>
  );
}
