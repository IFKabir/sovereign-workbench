'use client';

import { Citation } from '@/components/CitationList';

export interface CodeData {
  script?: string;
  stdout?: string;
  stderr?: string;
  exitCode?: number;
  sandboxMode?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  source?: string;
  imageSrc?: string;
  citations?: Citation[];
  codeData?: CodeData;
  timestamp?: string;
}

export interface ChatSession {
  threadId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

const STORAGE_KEY = 'mrpl_sovereign_chat_sessions_v1';
const ACTIVE_THREAD_KEY = 'mrpl_sovereign_active_thread_id';

const DEFAULT_GREETING: ChatMessage = {
  role: 'assistant',
  content:
    'MRPL Sovereign Intelligence Platform ready. I can assist with P&ID schematic analysis, OISD compliance standards lookup, engineering calculations, and shift handover digests. How can I help?',
  source: 'Sovereign AI',
};

/**
 * Get all saved chat sessions sorted by updatedAt descending.
 */
export function getChatSessions(): ChatSession[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const sessions: ChatSession[] = JSON.parse(raw);
    return sessions.sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  } catch (err) {
    console.error('Failed to parse chat sessions from localStorage:', err);
    return [];
  }
}

/**
 * Get a specific chat session by threadId.
 */
export function getChatSession(threadId: string): ChatSession | null {
  const sessions = getChatSessions();
  return sessions.find((s) => s.threadId === threadId) || null;
}

/**
 * Save or update a chat session.
 */
export function saveChatSession(threadId: string, messages: ChatMessage[], customTitle?: string): ChatSession {
  if (typeof window === 'undefined') {
    return {
      threadId,
      title: customTitle || 'Operational Query',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages,
    };
  }

  const sessions = getChatSessions();
  const existingIdx = sessions.findIndex((s) => s.threadId === threadId);
  const now = new Date().toISOString();

  // Derive title from first user message if available
  let title = customTitle;
  if (!title) {
    const firstUserMsg = messages.find((m) => m.role === 'user');
    if (firstUserMsg) {
      title = firstUserMsg.content.slice(0, 36).trim() + (firstUserMsg.content.length > 36 ? '...' : '');
    } else {
      title = 'AI Operational Query';
    }
  }

  let session: ChatSession;

  if (existingIdx >= 0) {
    session = {
      ...sessions[existingIdx],
      title: title || sessions[existingIdx].title,
      updatedAt: now,
      messages,
    };
    sessions[existingIdx] = session;
  } else {
    session = {
      threadId,
      title,
      createdAt: now,
      updatedAt: now,
      messages,
    };
    sessions.unshift(session);
  }

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    localStorage.setItem(ACTIVE_THREAD_KEY, threadId);
    // Dispatch custom event to notify SidebarNav of store changes
    window.dispatchEvent(new Event('mrpl_chat_sessions_updated'));
  } catch (err) {
    console.error('Failed to save chat session to localStorage:', err);
  }

  return session;
}

/**
 * Create a new clean chat session.
 */
export function createNewChatSession(): ChatSession {
  const newThreadId = 'THREAD-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 6);
  const initialMessages: ChatMessage[] = [DEFAULT_GREETING];
  return saveChatSession(newThreadId, initialMessages, 'New Operational Chat');
}

/**
 * Delete a specific chat session by threadId.
 */
export function deleteChatSession(threadId: string): void {
  if (typeof window === 'undefined') return;
  const sessions = getChatSessions().filter((s) => s.threadId !== threadId);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    const active = localStorage.getItem(ACTIVE_THREAD_KEY);
    if (active === threadId) {
      localStorage.removeItem(ACTIVE_THREAD_KEY);
    }
    window.dispatchEvent(new Event('mrpl_chat_sessions_updated'));
  } catch (err) {
    console.error('Failed to delete chat session from localStorage:', err);
  }
}

/**
 * Get current active thread ID from localStorage.
 */
export function getActiveThreadId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACTIVE_THREAD_KEY);
}

/**
 * Clear all chat history.
 */
export function clearAllChatSessions(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(ACTIVE_THREAD_KEY);
  window.dispatchEvent(new Event('mrpl_chat_sessions_updated'));
}
