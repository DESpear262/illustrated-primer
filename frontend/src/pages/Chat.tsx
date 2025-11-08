/**
 * Chat page for AI Tutor application.
 * 
 * Implements the Tutor Chat interface with streaming AI responses,
 * session management, and context awareness.
 */

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../lib/api';
import type { ChatSession, ChatMessage } from '../lib/api';
import { useLocalStorage } from '../hooks/useLocalStorage';
import toast from 'react-hot-toast';

/**
 * Chat page component.
 */
export function Chat() {
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hoveredMessage, setHoveredMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [, setLogs] = useLocalStorage<Record<string, ChatMessage[]>>('chat_logs', {});

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load messages for current session (only when session changes)
  const prevSessionIdRef = useRef<string | null>(null);
  const isInitialLoadRef = useRef(false);
  
  useEffect(() => {
    if (currentSession) {
      // Only load if session actually changed
      if (prevSessionIdRef.current !== currentSession.session_id) {
        // Mark as initial load to prevent immediate save
        isInitialLoadRef.current = true;
        
        // Read directly from localStorage to avoid dependency on logs state
        try {
          const storedLogs = window.localStorage.getItem('chat_logs');
          const logsData = storedLogs ? JSON.parse(storedLogs) : {};
          const savedMessages = logsData[currentSession.session_id] || [];
          
          console.log('Loading messages for session:', currentSession.session_id, 'Found', savedMessages.length, 'messages');
          setMessages(savedMessages);
          prevSessionIdRef.current = currentSession.session_id;
          
          // Reset initial load flag after a short delay to allow state to settle
          setTimeout(() => {
            isInitialLoadRef.current = false;
          }, 100);
        } catch (error) {
          console.error('Failed to load messages from localStorage:', error);
          setMessages([]);
          prevSessionIdRef.current = currentSession.session_id;
          isInitialLoadRef.current = false;
        }
      }
    } else {
      setMessages([]);
      prevSessionIdRef.current = null;
      isInitialLoadRef.current = false;
    }
  }, [currentSession?.session_id]); // Only depend on session ID, not logs

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Save messages to localStorage (only when they actually change, not on initial load)
  const prevMessagesRef = useRef<ChatMessage[]>([]);
  
  useEffect(() => {
    if (currentSession && !isInitialLoadRef.current) {
      // Skip save on initial load (when we just loaded from localStorage)
      
      // Only save if messages actually changed
      const messagesChanged = 
        prevMessagesRef.current.length !== messages.length ||
        JSON.stringify(prevMessagesRef.current) !== JSON.stringify(messages);
      
      if (messagesChanged) {
        console.log('Saving messages for session:', currentSession.session_id, 'Count:', messages.length);
        setLogs((prev) => ({
          ...prev,
          [currentSession.session_id]: messages,
        }));
        prevMessagesRef.current = messages;
      }
    } else if (isInitialLoadRef.current) {
      // Update prevMessagesRef even on initial load so we don't save immediately after
      prevMessagesRef.current = messages;
    }
  }, [messages, currentSession, setLogs]);

  const loadSessions = async () => {
    try {
      const response = await apiClient.chatList();
      if (response && response.success && response.result) {
        const sessionList = (response.result.sessions as ChatSession[]) || [];
        setSessions(sessionList);
      }
    } catch (error) {
      // Silently fail in test environment
      if (import.meta.env.MODE !== 'test') {
        toast.error('Failed to load sessions');
      }
      console.error('Failed to load sessions:', error);
    }
  };

  const startNewSession = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.chatStart();
      if (response.success && response.result) {
        const session = response.result as unknown as ChatSession;
        setCurrentSession(session);
        setMessages([]);
        toast.success('New session started');
        await loadSessions();
      } else {
        toast.error(response.error?.message || 'Failed to start session');
      }
    } catch (error) {
      toast.error('Failed to start session');
      console.error('Failed to start session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const resumeSession = async (session: ChatSession) => {
    try {
      setIsLoading(true);
      const response = await apiClient.chatResume(session.session_id);
      if (response.success && response.result) {
        const result = response.result as {
          session_id: string;
          title?: string;
          messages?: Array<{
            event_id?: string;
            actor: string;
            content: string;
            created_at: string;
          }>;
          message_count?: number;
        };
        
        // Update session with title from backend if available
        const updatedSession: ChatSession = {
          ...session,
          title: result.title || session.title,
        };
        
        // Set current session first
        setCurrentSession(updatedSession);
        
        // Convert backend messages to ChatMessage format and set them
        if (result.messages && result.messages.length > 0) {
          const chatMessages: ChatMessage[] = result.messages.map((msg) => ({
            role: msg.actor === 'student' ? 'student' : msg.actor === 'tutor' ? 'tutor' : 'system',
            content: msg.content,
            timestamp: msg.created_at,
            session_id: result.session_id,
            event_id: msg.event_id,
          }));
          
          // Mark that we've loaded from API so the load effect doesn't overwrite
          prevSessionIdRef.current = result.session_id;
          
          // Set messages from backend (this will trigger save to localStorage via useEffect)
          setMessages(chatMessages);
        } else {
          // No messages from backend, let the load effect try localStorage
          setMessages([]);
        }
        toast.success('Session resumed');
      } else {
        toast.error(response.error?.message || 'Failed to resume session');
      }
    } catch (error) {
      toast.error('Failed to resume session');
      console.error('Failed to resume session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !currentSession || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'student',
      content: input.trim(),
      timestamp: new Date().toISOString(),
      session_id: currentSession.session_id,
    };

    // Add user message immediately
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiClient.chatTurn(currentSession.session_id, userMessage.content);
      if (response.success && response.result) {
        const result = response.result as {
          tutor_reply: string;
          context_chunks?: number;
          turn_index?: number;
        };

        const tutorMessage: ChatMessage = {
          role: 'tutor',
          content: result.tutor_reply,
          timestamp: new Date().toISOString(),
          session_id: currentSession.session_id,
          context_chunks: result.context_chunks,
        };

        setMessages((prev) => [...prev, tutorMessage]);
        toast.success('Message sent');
      } else {
        toast.error(response.error?.message || 'Failed to send message');
        // Remove user message on error
        setMessages((prev) => prev.filter((msg) => msg !== userMessage));
      }
    } catch (error) {
      toast.error('Failed to send message');
      console.error('Failed to send message:', error);
      // Remove user message on error
      setMessages((prev) => prev.filter((msg) => msg !== userMessage));
    } finally {
      setIsLoading(false);
    }
  };

  const exportSession = () => {
    if (!currentSession) return;

    const sessionData = {
      session: currentSession,
      messages: messages,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(sessionData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-session-${currentSession.session_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Session exported');
  };

  const deleteSession = async () => {
    if (!currentSession) return;

    if (!confirm('Are you sure you want to delete this session?')) return;

    try {
      // For now, just remove from localStorage
      // Backend delete endpoint can be added later
      setLogs((prev) => {
        const newLogs = { ...prev };
        delete newLogs[currentSession.session_id];
        return newLogs;
      });
      setCurrentSession(null);
      setMessages([]);
      await loadSessions();
      toast.success('Session deleted');
    } catch (error) {
      toast.error('Failed to delete session');
      console.error('Failed to delete session:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-row h-full w-full overflow-hidden">
      {/* Main Chat Area - Center column (main focus) - THIS SHOULD BE FLEX */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <div className="bg-parchment-100 border-b border-brass-600 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <h1 className="text-xl font-headline font-semibold text-ink-900">
            {currentSession?.title || 'Tutor Chat'}
          </h1>
          {currentSession && (
            <div className="flex items-center space-x-2">
              <button
                onClick={exportSession}
                className="button px-3 py-1"
              >
                Export
              </button>
              <button
                onClick={deleteSession}
                className="button button--danger px-3 py-1"
              >
                Delete
              </button>
            </div>
          )}
        </div>

        {/* Messages - Main content area */}
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6 bg-parchment-50">
          {messages.length === 0 && (
            <div className="text-center text-ink-900 opacity-60 mt-16">
              {currentSession ? 'Start a conversation...' : 'Start a new session to begin chatting'}
            </div>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'student' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl ${
                  message.role === 'student'
                    ? 'chat-user'
                    : 'chat-ai'
                }`}
                onMouseEnter={() => message.context_chunks && setHoveredMessage(message.session_id + index)}
                onMouseLeave={() => setHoveredMessage(null)}
              >
                <div className={`text-sm font-semibold mb-2 ${
                  message.role === 'student' ? 'text-white opacity-92' : 'text-ink-900'
                }`}>
                  {message.role === 'student' ? 'You' : 'Tutor'}
                </div>
                <div className={`whitespace-pre-wrap leading-relaxed ${
                  message.role === 'student' ? 'text-white opacity-92' : 'text-ink-900'
                }`}>{message.content}</div>
                {message.context_chunks && hoveredMessage === message.session_id + index && (
                  <div className={`mt-2 text-xs ${
                    message.role === 'student' ? 'text-white opacity-75' : 'text-ink-900 opacity-70'
                  }`}>
                    Used {message.context_chunks} context chunks
                  </div>
                )}
                <div className={`text-xs mt-2 ${
                  message.role === 'student' ? 'text-white opacity-75' : 'text-ink-900 opacity-70'
                }`}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="card">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-brass-600 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-brass-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-brass-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-brass-600 px-8 py-4 bg-parchment-100 flex-shrink-0">
          <div className="flex space-x-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={!currentSession || isLoading}
              className="input flex-1 resize-none disabled:opacity-50"
              rows={3}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || !currentSession || isLoading}
              className="button button--primary px-8 py-3 disabled:opacity-50 self-end"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      {/* Session List Sidebar - Right side, very narrow - THIS SHOULD BE FIXED WIDTH */}
      <div 
        className="bg-parchment-100 border-l border-brass-600 p-2 overflow-hidden flex flex-col" 
        style={{ 
          width: '192px',
          maxWidth: '192px',
          minWidth: '192px',
          flexBasis: '192px',
          flexGrow: 0,
          flexShrink: 0
        }}
      >
        <div className="mb-1 flex-shrink-0 w-full overflow-hidden">
          <h2 className="text-xs font-headline font-semibold text-ink-900 mb-1 text-center truncate w-full">Sessions</h2>
          <button
            onClick={startNewSession}
            disabled={isLoading}
            className="button button--primary text-xs disabled:opacity-50"
            style={{ width: '100%', maxWidth: '100%', minWidth: 0, padding: '4px 2px' }}
          >
            New
          </button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-0.5 min-w-0 w-full">
          {sessions.length === 0 && (
            <div className="text-xs text-ink-900 opacity-60 text-center py-1 leading-tight px-0.5 truncate w-full">
              None
            </div>
          )}
          {sessions.map((session) => (
            <div
              key={session.session_id}
              onClick={() => resumeSession(session)}
              className={`p-1 rounded cursor-pointer transition-all duration-120 min-w-0 w-full overflow-hidden ${
                currentSession?.session_id === session.session_id
                  ? 'bg-verdigris-500 text-white'
                  : 'bg-parchment-50 hover:bg-parchment-100 border border-brass-600'
              }`}
            >
              <div className="font-semibold text-xs truncate leading-tight w-full">{session.title || 'Untitled'}</div>
              <div className={`text-xs mt-0.5 leading-tight truncate w-full ${
                currentSession?.session_id === session.session_id ? 'text-white opacity-90' : 'text-ink-900 opacity-70'
              }`}>
                {session.last_at ? new Date(session.last_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
