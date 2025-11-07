/**
 * WebSocket hook for AI Tutor application.
 * 
 * Manages WebSocket connection for live updates.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { apiConfig } from '../lib/api';

/**
 * WebSocket message type.
 */
export interface WebSocketMessage {
  type: string;
  data?: unknown;
}

/**
 * WebSocket hook.
 */
export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connectRef = useRef<(() => void) | null>(null);
  const isConnectingRef = useRef(false);

  const connect = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (isConnectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    isConnectingRef.current = true;
    
    // Get WebSocket URL from API base URL
    const wsUrl = apiConfig.baseUrl.replace('/api', '').replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        isConnectingRef.current = false;
        setIsConnected(true);
        console.log('WebSocket connected');
        
        // Send ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          } else {
            clearInterval(pingInterval);
          }
        }, 30000); // Ping every 30 seconds
        
        // Store interval ID for cleanup
        (ws as unknown as { _pingInterval?: number })._pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setMessages((prev) => [...prev, message]);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        isConnectingRef.current = false;
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        isConnectingRef.current = false;
        setIsConnected(false);
        console.log('WebSocket disconnected');
        
        // Clean up ping interval
        const pingInterval = (ws as unknown as { _pingInterval?: number })._pingInterval;
        if (pingInterval) {
          clearInterval(pingInterval);
        }
        
        // Attempt to reconnect after 3 seconds (only if not manually disconnected)
        if (wsRef.current === ws) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            if (connectRef.current) {
              connectRef.current();
            }
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      isConnectingRef.current = false;
      console.error('Failed to create WebSocket connection:', error);
    }
  }, []);

  // Store connect function in ref to avoid dependency issues
  connectRef.current = connect;

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    isConnectingRef.current = false;
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - only run on mount/unmount

  return {
    isConnected,
    messages,
    sendMessage,
    connect,
    disconnect,
  };
}

