/**
 * Console page for AI Tutor application.
 * 
 * Implements the Command Console interface with form-based UI
 * for all CLI commands.
 */

import { useState } from 'react';
import { apiClient } from '../lib/api';
import type { CommandResult } from '../lib/api';
import { useLocalStorage } from '../hooks/useLocalStorage';
import toast from 'react-hot-toast';

/**
 * Console log entry type.
 */
interface ConsoleLog {
  id: string;
  timestamp: string;
  command: string;
  result: CommandResult;
}

/**
 * Console page component.
 */
export function Console() {
  const [activeTab, setActiveTab] = useState<'db' | 'index' | 'ai' | 'chat'>('db');
  const [logs, setLogs] = useLocalStorage<ConsoleLog[]>('console_logs', []);
  const [isLoading, setIsLoading] = useState(false);

  // Database form state
  const [dbPath, setDbPath] = useState('');

  // Index form state
  const [indexEventId, setIndexEventId] = useState('');
  const [indexUseStub, setIndexUseStub] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchTopk, setSearchTopk] = useState(5);
  const [searchUseStub, setSearchUseStub] = useState(true);

  // AI form state
  const [aiTask, setAiTask] = useState('summarize');
  const [aiInput, setAiInput] = useState('');

  // Chat form state
  const [chatTitle, setChatTitle] = useState('');
  const [chatSessionId, setChatSessionId] = useState('');

  const addLog = (command: string, result: CommandResult) => {
    const log: ConsoleLog = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      command,
      result,
    };
    setLogs((prev) => [...prev, log].slice(-100)); // Keep last 100 logs
  };

  // Database commands
  const handleDbCheck = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.dbCheck();
      addLog('db check', response);
      if (response.success) {
        toast.success('Database check completed');
      } else {
        toast.error(response.error?.message || 'Database check failed');
      }
    } catch (error) {
      toast.error('Failed to check database');
      console.error('Failed to check database:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDbInit = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.dbInit();
      addLog('db init', response);
      if (response.success) {
        toast.success('Database initialized');
      } else {
        toast.error(response.error?.message || 'Database initialization failed');
      }
    } catch (error) {
      toast.error('Failed to initialize database');
      console.error('Failed to initialize database:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Index commands
  const handleIndexBuild = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.indexBuild(indexEventId || undefined, indexUseStub);
      addLog('index build', response);
      if (response.success) {
        toast.success('Index build completed');
      } else {
        toast.error(response.error?.message || 'Index build failed');
      }
    } catch (error) {
      toast.error('Failed to build index');
      console.error('Failed to build index:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleIndexStatus = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.indexStatus();
      addLog('index status', response);
      if (response.success) {
        toast.success('Index status retrieved');
      } else {
        toast.error(response.error?.message || 'Failed to get index status');
      }
    } catch (error) {
      toast.error('Failed to get index status');
      console.error('Failed to get index status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleIndexSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiClient.indexSearch(searchQuery, searchTopk, searchUseStub);
      addLog('index search', response);
      if (response.success) {
        toast.success('Search completed');
      } else {
        toast.error(response.error?.message || 'Search failed');
      }
    } catch (error) {
      toast.error('Failed to search index');
      console.error('Failed to search index:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // AI commands
  const handleAiRoutes = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.aiRoutes();
      addLog('ai routes', response);
      if (response.success) {
        toast.success('AI routes retrieved');
      } else {
        toast.error(response.error?.message || 'Failed to get AI routes');
      }
    } catch (error) {
      toast.error('Failed to get AI routes');
      console.error('Failed to get AI routes:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAiTest = async () => {
    if (!aiInput.trim()) {
      toast.error('Please enter test input');
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiClient.aiTest(aiTask, aiInput);
      addLog('ai test', response);
      if (response.success) {
        toast.success('AI test completed');
      } else {
        toast.error(response.error?.message || 'AI test failed');
      }
    } catch (error) {
      toast.error('Failed to test AI');
      console.error('Failed to test AI:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Chat commands
  const handleChatStart = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.chatStart(chatTitle || undefined);
      addLog('chat start', response);
      if (response.success) {
        toast.success('Chat session started');
        setChatTitle('');
      } else {
        toast.error(response.error?.message || 'Failed to start chat session');
      }
    } catch (error) {
      toast.error('Failed to start chat session');
      console.error('Failed to start chat session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatResume = async () => {
    if (!chatSessionId.trim()) {
      toast.error('Please enter a session ID');
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiClient.chatResume(chatSessionId);
      addLog('chat resume', response);
      if (response.success) {
        toast.success('Chat session resumed');
        setChatSessionId('');
      } else {
        toast.error(response.error?.message || 'Failed to resume chat session');
      }
    } catch (error) {
      toast.error('Failed to resume chat session');
      console.error('Failed to resume chat session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatList = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.chatList();
      addLog('chat list', response);
      if (response.success) {
        toast.success('Chat sessions retrieved');
      } else {
        toast.error(response.error?.message || 'Failed to list chat sessions');
      }
    } catch (error) {
      toast.error('Failed to list chat sessions');
      console.error('Failed to list chat sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearLogs = () => {
    if (confirm('Are you sure you want to clear all logs?')) {
      setLogs([]);
      toast.success('Logs cleared');
    }
  };

  return (
    <div className="flex h-full">
      {/* Command Forms */}
      <div className="flex-1 p-6 overflow-y-auto bg-parchment-50">
        <h1 className="text-3xl font-headline font-semibold mb-6 text-ink-900">Command Console</h1>

        {/* Tabs */}
        <div className="mb-6 border-b border-brass-600">
          <div className="flex space-x-4">
            {(['db', 'index', 'ai', 'chat'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 font-semibold transition-all duration-120 ${
                  activeTab === tab
                    ? 'border-b-2 border-brass-600 text-ink-900'
                    : 'text-ink-900 opacity-70 hover:opacity-100 hover:text-verdigris-500'
                }`}
              >
                {tab.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Database Commands */}
        {activeTab === 'db' && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">Database Check</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Database Path (optional)</label>
                  <input
                    type="text"
                    value={dbPath}
                    onChange={(e) => setDbPath(e.target.value)}
                    placeholder="Leave empty for default"
                    className="input w-full"
                  />
                </div>
                <button
                  onClick={handleDbCheck}
                  disabled={isLoading}
                  className="button button--primary disabled:opacity-50"
                >
                  Check Database
                </button>
              </div>
            </div>

            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">Database Init</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Database Path (optional)</label>
                  <input
                    type="text"
                    value={dbPath}
                    onChange={(e) => setDbPath(e.target.value)}
                    placeholder="Leave empty for default"
                    className="input w-full"
                  />
                </div>
                <button
                  onClick={handleDbInit}
                  disabled={isLoading}
                  className="button button--primary disabled:opacity-50"
                >
                  Initialize Database
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Index Commands */}
        {activeTab === 'index' && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">Index Build</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Event ID (optional)</label>
                  <input
                    type="text"
                    value={indexEventId}
                    onChange={(e) => setIndexEventId(e.target.value)}
                    placeholder="Leave empty for all events"
                    className="input w-full"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={indexUseStub}
                    onChange={(e) => setIndexUseStub(e.target.checked)}
                    className="mr-2"
                  />
                  <label className="text-sm text-ink-900">Use stub embeddings</label>
                </div>
                <button
                  onClick={handleIndexBuild}
                  disabled={isLoading}
                  className="button button--primary disabled:opacity-50"
                >
                  Build Index
                </button>
              </div>
            </div>

            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">Index Status</h2>
              <button
                onClick={handleIndexStatus}
                disabled={isLoading}
                className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                Get Status
              </button>
            </div>

            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">Index Search</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Query</label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Enter search query"
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Top K</label>
                  <input
                    type="number"
                    value={searchTopk}
                    onChange={(e) => setSearchTopk(parseInt(e.target.value) || 5)}
                    min={1}
                    max={100}
                    className="input w-full"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={searchUseStub}
                    onChange={(e) => setSearchUseStub(e.target.checked)}
                    className="mr-2"
                  />
                  <label className="text-sm text-ink-900">Use stub embeddings</label>
                </div>
                <button
                  onClick={handleIndexSearch}
                  disabled={isLoading}
                  className="button button--primary disabled:opacity-50"
                >
                  Search
                </button>
              </div>
            </div>
          </div>
        )}

        {/* AI Commands */}
        {activeTab === 'ai' && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">AI Routes</h2>
              <button
                onClick={handleAiRoutes}
                disabled={isLoading}
                className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                Get Routes
              </button>
            </div>

            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">AI Test</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Task</label>
                  <select
                    value={aiTask}
                    onChange={(e) => setAiTask(e.target.value)}
                    className="input w-full"
                  >
                    <option value="summarize">Summarize</option>
                    <option value="classify">Classify</option>
                    <option value="chat">Chat</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Input</label>
                  <textarea
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                    placeholder="Enter test input"
                    rows={5}
                    className="input w-full"
                  />
                </div>
                <button
                  onClick={handleAiTest}
                  disabled={isLoading}
                  className="button button--primary disabled:opacity-50"
                >
                  Test
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Chat Commands */}
        {activeTab === 'chat' && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">Chat Start</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Title (optional)</label>
                  <input
                    type="text"
                    value={chatTitle}
                    onChange={(e) => setChatTitle(e.target.value)}
                    placeholder="Enter session title"
                    className="input w-full"
                  />
                </div>
                <button
                  onClick={handleChatStart}
                  disabled={isLoading}
                  className="button button--primary disabled:opacity-50"
                >
                  Start Session
                </button>
              </div>
            </div>

            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">Chat Resume</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-ink-900">Session ID</label>
                  <input
                    type="text"
                    value={chatSessionId}
                    onChange={(e) => setChatSessionId(e.target.value)}
                    placeholder="Enter session ID"
                    className="input w-full"
                  />
                </div>
                <button
                  onClick={handleChatResume}
                  disabled={isLoading}
                  className="button button--primary disabled:opacity-50"
                >
                  Resume Session
                </button>
              </div>
            </div>

            <div className="card">
              <h2 className="text-xl font-headline font-semibold mb-4 text-ink-900">Chat List</h2>
              <button
                onClick={handleChatList}
                disabled={isLoading}
                className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                List Sessions
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Logs Panel */}
      <div className="w-96 bg-parchment-100 border-l border-brass-600 p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-headline font-semibold text-ink-900">Logs</h2>
          <button
            onClick={clearLogs}
            className="button button--danger px-3 py-1 text-sm"
          >
            Clear
          </button>
        </div>
        <div className="space-y-2">
          {logs.length === 0 && (
            <div className="text-ink-900 opacity-60 text-sm">No logs yet</div>
          )}
          {logs.map((log) => (
            <div
              key={log.id}
              className={`card text-sm ${
                log.result.success ? 'border-verdigris-500' : 'border-garnet-600'
              }`}
            >
              <div className="font-semibold text-ink-900">{log.command}</div>
              <div className="text-xs text-ink-900 opacity-70">
                {new Date(log.timestamp).toLocaleString()}
              </div>
              <div className="mt-2 text-xs">
                {log.result.success ? (
                  <pre className="whitespace-pre-wrap text-xs font-mono text-ink-900 opacity-80">
                    {JSON.stringify(log.result.result, null, 2)}
                  </pre>
                ) : (
                  <div className="text-garnet-600">
                    {log.result.error?.message || 'Unknown error'}
                  </div>
                )}
              </div>
              <div className="text-xs text-ink-900 opacity-60 mt-1">
                Duration: {log.result.duration_seconds.toFixed(2)}s
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
