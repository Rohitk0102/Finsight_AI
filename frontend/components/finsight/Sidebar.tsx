import React, { useEffect, useState } from 'react';
import { Plus, MessageSquare, Terminal } from 'lucide-react';
import { finsightApi } from '../../lib/api/client';
import { formatDistanceToNow } from 'date-fns';

interface SidebarProps {
  onNewChat: () => void;
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  user?: any;
  currentSessionId: string;
  lastMessageAt?: number;
  onSelectSession: (id: string) => void;
  isOverlay?: boolean;
}

interface ChatSession {
  id: string;
  last_message: string;
  timestamp: string;
}

export function Sidebar({ onNewChat, isOpen, onClose, userId, user, currentSessionId, lastMessageAt = 0, onSelectSession, isOverlay = false }: SidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchSessions = async () => {
      if (!userId) return;
      setLoading(true);
      try {
        const res = await finsightApi.sessions(userId);
        if (res.status === 200) {
          setSessions(res.data);
        }
      } catch (error) {
        console.error("Failed to fetch sessions:", error);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen || !isOverlay) {
      fetchSessions();
    }
  }, [isOpen, userId, isOverlay, lastMessageAt]);

  return (
    <>
      {/* Mobile/Overlay Backdrop */}
      {(isOpen || (isOverlay && isOpen)) && (
        <div 
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Content */}
      <div className={`
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        ${isOverlay && !isOpen ? '-translate-x-full' : ''}
        ${isOverlay ? 'fixed' : 'fixed lg:static'}
        inset-y-0 left-0 z-50 w-[260px] h-full
        flex flex-col finsight-sidebar-bg border-r finsight-border
        transition-transform duration-300 ease-in-out
      `}>
        <div className="flex flex-col p-4 border-b finsight-border">
          <div className="flex items-center gap-2 mb-1">
            <Terminal className="w-5 h-5 finsight-accent" />
            <h1 className="text-lg font-bold finsight-accent uppercase tracking-widest">
              FINSIGHT_AI
            </h1>
          </div>
          <div className="text-[10px] finsight-muted uppercase tracking-widest">
            MARKET INTELLIGENCE v2.4
          </div>
        </div>

        <div className="p-4">
          <button
            onClick={onNewChat}
            className="flex items-center justify-center w-full gap-2 p-2 text-sm font-bold border border-dashed rounded finsight-accent-border finsight-accent hover:bg-[var(--user-bubble)] transition-colors"
          >
            <Plus className="w-4 h-4" strokeWidth={3} />
            NEW CONVERSATION
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2 custom-scrollbar">
          <div className="text-[10px] finsight-muted uppercase tracking-widest mb-2 px-2">
            RECENT SESSIONS
          </div>
          
          {loading && <div className="p-2 text-[10px] finsight-muted animate-pulse">SYNCING_SESSIONS...</div>}
          
          {!loading && sessions.length === 0 && (
            <div className="p-2 text-xs finsight-muted italic px-2">
              No recent sessions found.
            </div>
          )}

          {sessions.map((session) => (
            <div 
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`flex items-center gap-3 p-2 mb-1 rounded cursor-pointer transition-colors ${
                currentSessionId === session.id 
                  ? 'bg-[var(--user-bubble)] finsight-accent border finsight-accent-border' 
                  : 'hover:bg-[var(--sidebar-border)] text-[var(--text)]'
              }`}
            >
              <MessageSquare className={`w-4 h-4 flex-shrink-0 ${currentSessionId === session.id ? 'opacity-100' : 'opacity-50'}`} />
              <div className="flex-1 overflow-hidden">
                <div className="text-xs font-bold truncate">{session.last_message}</div>
                <div className="text-[10px] opacity-70">
                  {formatDistanceToNow(new Date(session.timestamp), { addSuffix: true })}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 mt-auto border-t finsight-border bg-black/20">
          <div className="flex items-center gap-3">
            {user?.imageUrl ? (
              <img src={user.imageUrl} className="w-8 h-8 rounded-full border border-[var(--accent)]" alt="Avatar" />
            ) : (
              <div className="flex items-center justify-center w-8 h-8 font-bold text-black rounded-full finsight-bg finsight-accent bg-[var(--accent)]">
                {user?.firstName?.charAt(0) || user?.username?.charAt(0) || 'U'}
              </div>
            )}
            <div className="flex-1 overflow-hidden">
              <div className="text-xs font-bold text-white truncate">
                {user?.fullName || user?.username || 'User'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
