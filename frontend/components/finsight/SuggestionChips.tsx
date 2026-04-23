import React from 'react';

interface SuggestionChipsProps {
  onSelect: (text: string) => void;
}

const SUGGESTIONS = [
  "Analyze my portfolio",
  "Top movers today",
  "Explain RSI",
  "NVDA earnings breakdown",
  "Fed rate impact"
];

export function SuggestionChips({ onSelect }: SuggestionChipsProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3 p-6 mt-10">
      {SUGGESTIONS.map((text, i) => (
        <button
          key={i}
          onClick={() => onSelect(text)}
          className="px-4 py-2 text-sm transition-all bg-transparent rounded-full finsight-accent-border border border-dashed hover:bg-[var(--user-border)] finsight-accent focus:outline-none"
        >
          {text}
        </button>
      ))}
    </div>
  );
}
