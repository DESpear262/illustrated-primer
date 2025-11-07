/**
 * Chat page for AI Tutor application.
 * 
 * Implements the Tutor Chat interface with streaming AI responses,
 * session management, and context awareness.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient, ChatSession, ChatMessage, CommandResult } from '../lib/api';
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
  const [showSessions, setShowSessions] = useState(true);
  const [hoveredMessage, setHoveredMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [logs, setLogs] = useLocalStorage<Record<string, ChatMessage[]>>('chat_logs', {});

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load messages for current session
  useEffect(() => {
    if (currentSession) {
      loadSessionMessages(currentSession.session_id);
    }
  }, [currentSession]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Save messages to localStorage
  useEffect(() => {
    if (currentSession) {
      setLogs((prev) => ({
        ...prev,
        [currentSession.session_id]: messages,
      }));
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
      if (process.env.NODE_ENV !== 'test') {
        toast.error('Failed to load sessions');
      }
      console.error('Failed to load sessions:', error);
    }
  };

  const loadSessionMessages = async (sessionId: string) => {
    try {
      // Load from localStorage first
      const savedMessages = logs[sessionId] || [];
      setMessages(savedMessages);

      // Optionally reload from backend if needed
      // For now, we'll rely on localStorage and add messages as they come in
    } catch (error) {
      console.error('Failed to load session messages:', error);
    }
  };

  const startNewSession = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.chatStart();
      if (response.success && response.result) {
        const session = response.result as ChatSession;
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
        setCurrentSession(session);
        await loadSessionMessages(session.session_id);
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
    <div className="flex h-full">
      {/* Session List Sidebar */}
      {showSessions && (
        <div className="w-64 bg-gray-100 border-r border-gray-300 p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">Sessions</h2>
            <button
              onClick={() => setShowSessions(false)}
              className="text-gray-600 hover:text-gray-800"
            >
              ✕
            </button>
          </div>
          <button
            onClick={startNewSession}
            disabled={isLoading}
            className="w-full mb-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            New Session
          </button>
          <div className="space-y-2">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                onClick={() => resumeSession(session)}
                className={`p-3 rounded cursor-pointer ${
                  currentSession?.session_id === session.session_id
                    ? 'bg-blue-200'
                    : 'bg-white hover:bg-gray-200'
                }`}
              >
                <div className="font-semibold">{session.title || 'Untitled Session'}</div>
                <div className="text-sm text-gray-600">
                  {session.last_at ? new Date(session.last_at).toLocaleDateString() : 'No messages'}
                </div>
                <div className="text-xs text-gray-500">{session.cnt || 0} messages</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-gray-200 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {!showSessions && (
              <button
                onClick={() => setShowSessions(true)}
                className="text-gray-600 hover:text-gray-800"
              >
                ☰
              </button>
            )}
            <h1 className="text-xl font-bold">
              {currentSession?.title || 'Tutor Chat'}
            </h1>
          </div>
          {currentSession && (
            <div className="flex items-center space-x-2">
              <button
                onClick={exportSession}
                className="px-3 py-1 bg-gray-300 rounded hover:bg-gray-400"
              >
                Export
              </button>
              <button
                onClick={deleteSession}
                className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              {currentSession ? 'Start a conversation...' : 'Start a new session to begin chatting'}
            </div>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'student' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl rounded-lg p-3 ${
                  message.role === 'student'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-800'
                }`}
                onMouseEnter={() => message.context_chunks && setHoveredMessage(message.session_id + index)}
                onMouseLeave={() => setHoveredMessage(null)}
              >
                <div className="text-sm font-semibold mb-1">
                  {message.role === 'student' ? 'You' : 'Tutor'}
                </div>
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.context_chunks && hoveredMessage === message.session_id + index && (
                  <div className="mt-2 text-xs opacity-75">
                    Used {message.context_chunks} context chunks
                  </div>
                )}
                <div className="text-xs mt-1 opacity-75">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-200 rounded-lg p-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-300 p-4">
          <div className="flex space-x-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={!currentSession || isLoading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              rows={3}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || !currentSession || isLoading}
              className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
