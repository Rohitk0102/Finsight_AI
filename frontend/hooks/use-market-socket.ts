"use client";

import { useEffect, useMemo, useRef } from "react";
import { useMarketPulseStore } from "@/lib/markets/store";
import type { MarketSocketMessage } from "@/lib/markets/types";

function resolveSocketUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  if (configured.startsWith("https://")) {
    return configured.replace("https://", "wss://") + "/markets/ws";
  }
  if (configured.startsWith("http://")) {
    return configured.replace("http://", "ws://") + "/markets/ws";
  }
  return "ws://localhost:8000/api/v1/markets/ws";
}

export function useMarketSocket(symbols: string[]) {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);
  const mountedRef = useRef(true);
  const latestSymbolsRef = useRef<string[]>([]);
  const subscribedRef = useRef<string[]>([]);
  const setSocketStatus = useMarketPulseStore((state) => state.setSocketStatus);
  const setSubscribedSymbols = useMarketPulseStore((state) => state.setSubscribedSymbols);
  const upsertLiveQuotes = useMarketPulseStore((state) => state.upsertLiveQuotes);
  const socketUrl = useMemo(() => resolveSocketUrl(), []);
  const normalizedSymbols = useMemo(() => Array.from(new Set(symbols.filter(Boolean))), [symbols]);

  useEffect(() => {
    latestSymbolsRef.current = normalizedSymbols;
    setSubscribedSymbols(normalizedSymbols);

    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }

    const current = new Set(subscribedRef.current);
    const next = new Set(normalizedSymbols);
    const added = normalizedSymbols.filter((symbol) => !current.has(symbol));
    const removed = subscribedRef.current.filter((symbol) => !next.has(symbol));

    if (added.length) {
      socket.send(JSON.stringify({ action: "subscribe", symbols: added }));
    }
    if (removed.length) {
      socket.send(JSON.stringify({ action: "unsubscribe", symbols: removed }));
    }
    subscribedRef.current = normalizedSymbols;
  }, [normalizedSymbols, setSubscribedSymbols]);

  useEffect(() => {
    mountedRef.current = true;
    let reconnectDelay = 1500;

    const connect = () => {
      setSocketStatus(socketRef.current ? "reconnecting" : "connecting");
      const socket = new WebSocket(socketUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        if (!mountedRef.current) return;
        reconnectDelay = 1500;
        setSocketStatus("connected");
        const symbolsToSubscribe = latestSymbolsRef.current;
        subscribedRef.current = symbolsToSubscribe;
        setSubscribedSymbols(symbolsToSubscribe);
        if (symbolsToSubscribe.length) {
          socket.send(JSON.stringify({ action: "subscribe", symbols: symbolsToSubscribe }));
        }
      };

      socket.onmessage = (event) => {
        if (!mountedRef.current) return;
        const payload = JSON.parse(event.data) as MarketSocketMessage;
        if (payload.type === "quote_update" && payload.quotes?.length) {
          upsertLiveQuotes(payload.quotes);
        }
      };

      socket.onerror = () => {
        if (!mountedRef.current) return;
        setSocketStatus("error");
      };

      socket.onclose = () => {
        if (!mountedRef.current) return;
        setSocketStatus("disconnected");
        reconnectRef.current = window.setTimeout(() => {
          connect();
          reconnectDelay = Math.min(reconnectDelay * 1.4, 8000);
        }, reconnectDelay);
      };
    };

    connect();

    return () => {
      mountedRef.current = false;
      subscribedRef.current = [];
      setSubscribedSymbols([]);
      if (reconnectRef.current) {
        window.clearTimeout(reconnectRef.current);
      }
      socketRef.current?.close();
      socketRef.current = null;
      setSocketStatus("idle");
    };
  }, [setSocketStatus, setSubscribedSymbols, socketUrl, upsertLiveQuotes]);
}
