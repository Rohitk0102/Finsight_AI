import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../../hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { SuggestionChips } from './SuggestionChips';

interface ChatWindowProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
  user?: any;
}

export function ChatWindow({ messages, loading, onSend, user }: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const hasUserMessages = messages.some(m => m.role === 'user');

  return (
    <div className="flex flex-col flex-1 w-full h-full overflow-y-auto custom-scrollbar p-4 md:p-6 pb-0" ref={scrollRef}>
      {!hasUserMessages && messages.length === 0 && (
        <div className="flex flex-col items-center justify-center flex-1 h-full opacity-80 mt-10">
          <h2 className="text-xl font-bold finsight-accent tracking-wider mb-2">FINSIGHT AI</h2>
          <p className="text-sm finsight-muted mb-8 text-center">
            FINANCIAL INTELLIGENCE<br/>
            TYPE A QUERY TO BEGIN
          </p>
          <SuggestionChips onSelect={onSend} />
        </div>
      )}
      
      <div className="flex flex-col max-w-4xl mx-auto w-full">
        {messages.map((msg, idx) => (
          <MessageBubble key={msg.id || idx} message={msg} user={user} />
        ))}
        
        {loading && <TypingIndicator />}
        
        {/* Invisible element to ensure we can scroll past the last message if needed */}
        <div className="h-4" />
      </div>
    </div>
  );
}
