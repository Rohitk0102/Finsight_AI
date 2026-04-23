"use client";

import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { ChatWindow } from './ChatWindow';
import { ChatInput } from './ChatInput';
import { MarketTicker } from './MarketTicker';
import { useChat } from '../../hooks/useChat';
import { Menu, X } from 'lucide-react';
import { useUser } from '@clerk/nextjs';

interface FinsightChatProps {
  apiEndpoint?: string;
  userId?: string;
  onClose?: () => void;
  isOverlay?: boolean;
}

export default function FinsightChat({ apiEndpoint, userId = 'rohit', onClose, isOverlay = false }: FinsightChatProps) {
  const { user } = useUser();
  const { messages, loading, sendMessage, clearSession, loadSession, sessionId, lastMessageAt } = useChat({
    wsEndpoint: apiEndpoint,
    userId
  });
  
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className={`flex flex-col h-full finsight-theme finsight-drawer ${
      isOverlay 
        ? 'fixed right-0 top-0 bottom-0 w-full max-w-4xl z-[100] shadow-2xl border-l finsight-border' 
        : 'w-full flex-1'
    }`}>
      {/* Top Header / Ticker Area */}
      <div className="flex items-center justify-between finsight-bg border-b finsight-border relative z-10 h-10 flex-shrink-0">
        <div className="flex items-center lg:hidden h-full px-2">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 finsight-accent hover:bg-[var(--sidebar-border)] rounded"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          <MarketTicker />
        </div>
        {onClose && (
          <button 
            onClick={onClose}
            className="flex items-center justify-center w-10 h-10 finsight-muted hover:finsight-accent hover:bg-[var(--sidebar-border)] transition-colors border-l finsight-border"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Main Layout Area */}
      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar 
          onNewChat={() => {
            clearSession();
            setSidebarOpen(false);
          }} 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)}
          userId={userId}
          user={user}
          currentSessionId={sessionId}
          lastMessageAt={lastMessageAt}
          onSelectSession={(id) => {
            loadSession(id);
            setSidebarOpen(false);
          }}
          isOverlay={isOverlay}
        />
        
        <div className={`flex flex-col flex-1 h-full mx-auto border-l finsight-border bg-black/20 relative w-full ${isOverlay ? 'max-w-4xl' : ''}`}>
          <ChatWindow 
            messages={messages} 
            loading={loading} 
            user={user}
            onSend={(text) => {
              sendMessage(text);
              setSidebarOpen(false);
            }} 
          />
          <ChatInput 
            onSend={sendMessage} 
            disabled={loading} 
          />
        </div>
      </div>
    </div>
  );
}
