import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col w-full p-4 mt-auto">
      <div className="relative flex items-center w-full finsight-sidebar-bg border finsight-border rounded-lg focus-within:border-[var(--accent)] transition-colors p-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask Finsight AI..."
          className="flex-1 w-full max-h-[120px] bg-transparent resize-none outline-none text-sm placeholder:text-[var(--muted)] p-2"
          rows={1}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="absolute right-2 bottom-2 p-2 ml-2 rounded bg-[var(--user-bubble)] border border-[var(--accent)] text-[var(--accent)] disabled:opacity-50 disabled:border-[var(--muted)] disabled:text-[var(--muted)] hover:bg-[var(--user-border)] transition-colors"
        >
          <ArrowUp className="w-4 h-4" strokeWidth={3} />
        </button>
      </div>
      <div className="flex justify-between items-center w-full px-2 mt-2">
        <span className="text-[10px] uppercase finsight-muted tracking-wider">
          ENTER_TO_SEND · FINSIGHT_AI
        </span>
        <span className="text-[10px] finsight-muted">
          {text.length} CHARS
        </span>
      </div>
    </div>
  );
}
