"use client";

import { useEffect, useRef, useState } from "react";

import { AlertItem } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8024/api/v1";
const RECONNECT_DELAY_MS = 4_000;
const CONNECT_TIMEOUT_MS = 5_000;

function buildWsUrl(clientId?: number): string | null {
  const token = getStoredToken();
  if (!token || typeof window === "undefined") return null;

  let base: string;
  if (API_BASE.startsWith("http")) {
    base = API_BASE.replace(/^http/, "ws");
  } else {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    base = `${protocol}://${window.location.host}${API_BASE}`;
  }

  const qs = new URLSearchParams({ token });
  if (clientId) qs.set("client_id", String(clientId));
  return `${base}/alerts/ws?${qs.toString()}`;
}

/**
 * 02-P-05: push de alertas críticas por WebSocket en vez de esperar el
 * polling de 60s. Si la conexión no abre a tiempo, se cae o el navegador
 * no la soporta, `connected` queda en false y quien llama debe seguir
 * confiando en su propio polling (refetchInterval) -- este hook nunca
 * bloquea ni rompe la UI, solo intenta sumar push cuando puede.
 */
export function useAlertsSocket(enabled: boolean, clientId?: number) {
  const [pushedAlerts, setPushedAlerts] = useState<AlertItem[] | null>(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUsRef = useRef(false);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    closedByUsRef.current = false;

    function connect() {
      const url = buildWsUrl(clientId);
      if (!url) return;

      let ws: WebSocket;
      try {
        ws = new WebSocket(url);
      } catch {
        return;
      }
      socketRef.current = ws;

      timeoutRef.current = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) ws.close();
      }, CONNECT_TIMEOUT_MS);

      ws.onopen = () => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (parsed?.type === "alerts" && Array.isArray(parsed.data)) {
            setPushedAlerts(parsed.data);
          }
        } catch {
          // Mensaje no reconocido -- se ignora, no rompe la conexión.
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (closedByUsRef.current) return;
        reconnectRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      closedByUsRef.current = true;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [enabled, clientId]);

  return { pushedAlerts: enabled ? pushedAlerts : null, connected: enabled && connected };
}
