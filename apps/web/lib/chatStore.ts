'use client';

import { Citation } from '@/components/CitationList';
import { getSession } from '@/lib/session';

export interface CodeData {
  script?: string;
  stdout?: string;
  stderr?: string;
  exitCode?: number;
  sandboxMode?: string;
  metrics?: Array<{ name: string; value: string }>;
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

const DEFAULT_GREETING: ChatMessage = {
  role: 'assistant',
  content:
    'MRPL Sovereign Intelligence Platform ready. I can assist with P&ID schematic analysis, OISD compliance standards lookup, engineering calculations, and shift handover digests. How can I help?',
  source: 'Sovereign AI',
};

/**
  * Derive storage keys strictly scoped by user_id to prevent multi-user chat data leakage.
  */
function getStorageKey(customUserId?: string): string {
  if (typeof window === 'undefined') return 'mrpl_sovereign_chat_sessions_anon';
  const session = getSession();
  const userId = customUserId || session?.userId || 'anonymous';
  return `mrpl_sovereign_chat_sessions_${userId}`;
}

function getActiveThreadKey(customUserId?: string): string {
  if (typeof window === 'undefined') return 'mrpl_sovereign_active_thread_id_anon';
  const session = getSession();
  const userId = customUserId || session?.userId || 'anonymous';
  return `mrpl_sovereign_active_thread_id_${userId}`;
}

/**
 * Get all saved chat sessions for the active user sorted by updatedAt descending.
 */
export function getChatSessions(userId?: string): ChatSession[] {
  if (typeof window === 'undefined') return [];
  try {
    const key = getStorageKey(userId);
    const raw = localStorage.getItem(key);
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
 * Get a specific chat session by threadId for the active user.
 */
export function getChatSession(threadId: string, userId?: string): ChatSession | null {
  const sessions = getChatSessions(userId);
  return sessions.find((s) => s.threadId === threadId) || null;
}

/**
 * Save or update a chat session for the specified user ID.
 */
export function saveChatSession(
  threadId: string,
  messages: ChatMessage[],
  customTitle?: string,
  userId?: string
): ChatSession {
  if (typeof window === 'undefined') {
    return {
      threadId,
      title: customTitle || 'Operational Query',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages,
    };
  }

  const storageKey = getStorageKey(userId);
  const activeThreadKey = getActiveThreadKey(userId);
  const sessions = getChatSessions(userId);
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
    localStorage.setItem(storageKey, JSON.stringify(sessions));
    localStorage.setItem(activeThreadKey, threadId);
    window.dispatchEvent(new Event('mrpl_chat_sessions_updated'));
  } catch (err) {
    console.error('Failed to save chat session to localStorage:', err);
  }

  return session;
}

/**
 * Create a new clean chat session for the active user.
 */
export function createNewChatSession(userId?: string): ChatSession {
  const newThreadId = 'THREAD-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 6);
  const initialMessages: ChatMessage[] = [DEFAULT_GREETING];
  return saveChatSession(newThreadId, initialMessages, 'New Operational Chat', userId);
}

/**
 * Delete a specific chat session by threadId for the active user.
 */
export function deleteChatSession(threadId: string, userId?: string): void {
  if (typeof window === 'undefined') return;
  const storageKey = getStorageKey(userId);
  const activeThreadKey = getActiveThreadKey(userId);
  const sessions = getChatSessions(userId).filter((s) => s.threadId !== threadId);
  try {
    localStorage.setItem(storageKey, JSON.stringify(sessions));
    const active = localStorage.getItem(activeThreadKey);
    if (active === threadId) {
      localStorage.removeItem(activeThreadKey);
    }
    window.dispatchEvent(new Event('mrpl_chat_sessions_updated'));
  } catch (err) {
    console.error('Failed to delete chat session from localStorage:', err);
  }
}

/**
 * Get current active thread ID from localStorage for the active user.
 */
export function getActiveThreadId(userId?: string): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(getActiveThreadKey(userId));
}

/**
 * Clear all chat history for the active user.
 */
export function clearAllChatSessions(userId?: string): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(getStorageKey(userId));
  localStorage.removeItem(getActiveThreadKey(userId));
  window.dispatchEvent(new Event('mrpl_chat_sessions_updated'));
}
