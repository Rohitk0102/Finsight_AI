import React from 'react';
import { ChatMessage } from '../../hooks/useChat';
import { formatPrice, formatPercent, formatNumber } from './utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageBubbleProps {
  message: ChatMessage;
  user?: any;
}

export function MessageBubble({ message, user }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  
  // Format the time
  const timeStr = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

  // Custom components for Markdown to maintain terminal styling and conditional coloring
  const MarkdownComponents = {
    strong: ({ children }: any) => <strong className="font-bold text-[var(--accent)]">{children}</strong>,
    a: ({ href, children }: any) => <a href={href} target="_blank" rel="noopener noreferrer" className="underline decoration-dashed hover:text-[var(--accent)]">{children}</a>,
    ul: ({ children }: any) => <ul className="list-disc ml-4 mb-3 space-y-1">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal ml-4 mb-3 space-y-1">{children}</ol>,
    table: ({ children }: any) => (
      <div className="overflow-x-auto my-3 border border-[var(--bot-border)] rounded">
        <table className="w-full text-xs text-left border-collapse">{children}</table>
      </div>
    ),
    th: ({ children }: any) => <th className="p-2 border-b border-[var(--bot-border)] bg-black/20 font-bold uppercase">{children}</th>,
    td: ({ children }: any) => <td className="p-2 border-b border-black/10">{children}</td>,
    p: ({ children }: any) => {
      // Logic for inline percentage coloring
      if (typeof children === 'string') {
        const parts = children.split(/(▼[\d.]+%|▲[\d.]+%)/g);
        return (
          <p className="mb-3 last:mb-0 leading-relaxed">
            {parts.map((part, i) => {
              if (part.startsWith('▼')) return <span key={i} className="text-[#ff4d4d] font-bold">{part}</span>;
              if (part.startsWith('▲')) return <span key={i} className="text-[#00d68f] font-bold">{part}</span>;
              return part;
            })}
          </p>
        );
      }
      return <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>;
    }
  };

  return (
    <div className={`flex w-full mb-6 animate-fade-in-up ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex items-center justify-center flex-shrink-0 w-8 h-8 mr-3 font-bold bg-[var(--bot-bubble)] border border-[var(--accent)] text-[var(--accent)] rounded-sm mt-1">
          F
        </div>
      )}
      
      <div className={`flex flex-col max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-md text-[13px] ${
          isUser 
            ? 'bg-[var(--user-bubble)] border border-[var(--user-border)] text-white' 
            : 'bg-[var(--bot-bubble)] border border-[var(--bot-border)] text-[var(--text)]'
        }`}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]} 
            components={MarkdownComponents as any}
          >
            {message.content}
          </ReactMarkdown>
          
          {!isUser && message.marketData && message.marketData.length > 0 && (
            <div className="flex flex-col gap-2 mt-4 pt-3 border-t border-[var(--bot-border)]">
              {message.marketData.map((data, i) => (
                <div key={i} className="flex flex-wrap items-center gap-3 text-xs">
                  <span className="font-bold text-white">[{data.symbol}]</span>
                  <span className="text-[var(--text)]">{formatPrice(data.price)}</span>
                  <span className={data.change_pct >= 0 ? "text-[#00d68f]" : "text-[#ff4d4d]"}>
                    {formatPercent(data.change_pct)}
                  </span>
                  {data.volume && <span className="text-[var(--muted)]">VOL: {formatNumber(data.volume)}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="mt-1 text-[10px] finsight-muted tracking-wider">
          {timeStr}
        </div>
      </div>
      
      {isUser && (
        <div className="flex-shrink-0 ml-3 mt-1">
          {user?.imageUrl ? (
            <img src={user.imageUrl} className="w-8 h-8 rounded-sm border border-[var(--user-border)]" alt="U" />
          ) : (
            <div className="flex items-center justify-center w-8 h-8 font-bold bg-[var(--user-bubble)] border border-[var(--user-border)] text-white rounded-sm">
              {user?.firstName?.charAt(0) || user?.username?.charAt(0) || 'U'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
