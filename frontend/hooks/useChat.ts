import { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { finsightApi } from '../lib/api/client';

export type MessageRole = 'user' | 'assistant';

export interface MarketData {
  symbol: string;
  price: number;
  change_pct: number;
  volume?: number;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  marketData?: MarketData[];
}

interface UseChatProps {
  wsEndpoint?: string;
  userId?: string;
}

function resolveWsUrl(sessionId: string, userId: string, customEndpoint?: string): string {
  if (customEndpoint) return customEndpoint;
  
  const configured = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  
  let base = configured;
  if (!base.endsWith("/finsight")) {
    base = base + "/finsight";
  }

  if (base.startsWith("https://")) {
    base = base.replace("https://", "wss://");
  } else if (base.startsWith("http://")) {
    base = base.replace("http://", "ws://");
  }
  
  return `${base}/ws/${sessionId}?user_id=${userId}`;
}

export function useChat({ wsEndpoint, userId = 'anonymous' }: UseChatProps = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [lastMessageAt, setLastMessageAt] = useState<number>(0);
  const wsRef = useRef<WebSocket | null>(null);

  // Load history when sessionId changes
  useEffect(() => {
    if (!sessionId || !userId) return;

    const fetchHistory = async () => {
      setLoading(true);
      try {
        const res = await finsightApi.history(sessionId, userId);
        if (res.status === 200) {
          const history = res.data.map((m: any) => ({
            id: uuidv4() + '-hist',
            role: m.role,
            content: m.content,
            timestamp: m.timestamp
          }));
          setMessages(history);
        }
      } catch (e) {
        console.error('Failed to fetch chat history:', e);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [sessionId, userId]);

  // Initialize session ID
  useEffect(() => {
    const storedSession = localStorage.getItem('finsight_session');
    if (storedSession) {
      setSessionId(storedSession);
    } else {
      const newSession = uuidv4();
      localStorage.setItem('finsight_session', newSession);
      setSessionId(newSession);
    }
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    if (!sessionId) return;
    
    const endpoint = resolveWsUrl(sessionId, userId, wsEndpoint);

    const ws = new WebSocket(endpoint);
    
    ws.onopen = () => {
      console.log('Finsight WS Connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token') {
          setLoading(false);
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            
            if (lastMessage && lastMessage.role === 'assistant' && !lastMessage.id.includes('done')) {
              // Immutable update: create a new array and a new object for the last message
              return [
                ...prev.slice(0, -1),
                { ...lastMessage, content: lastMessage.content + data.token }
              ];
            } else {
              // Start a new assistant message
              return [
                ...prev,
                {
                  id: uuidv4(),
                  role: 'assistant',
                  content: data.token,
                  timestamp: new Date().toISOString()
                }
              ];
            }
          });
        } else if (data.type === 'done') {
          setLastMessageAt(Date.now()); // Trigger sidebar refresh
          // Finalize message and add metadata (market data)
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              return [
                ...prev.slice(0, -1),
                { 
                  ...lastMessage, 
                  id: lastMessage.id + '-done', // Mark as complete
                  marketData: data.metadata?.market_data 
                }
              ];
            }
            return prev;
          });
        }
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };

    ws.onclose = () => {
      console.log('Finsight WS Disconnected');
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [sessionId, wsEndpoint, userId]);

  const sendMessage = useCallback((text: string) => {
    if (!text.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    wsRef.current.send(JSON.stringify({ message: text }));
  }, []);

  const clearSession = useCallback(() => {
    const newSession = uuidv4();
    localStorage.setItem('finsight_session', newSession);
    setSessionId(newSession);
    setMessages([]);
  }, []);

  const loadSession = useCallback((id: string) => {
    localStorage.setItem('finsight_session', id);
    setSessionId(id);
    // History will be loaded by the useEffect hook
  }, []);

  return {
    messages,
    loading,
    sendMessage,
    clearSession,
    loadSession,
    sessionId,
    lastMessageAt
  };
}
