'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { MessageSquare, LayoutDashboard, Activity, FileText, Shield, User, LogOut, Plus, Trash2, Clock, MessageCircle } from 'lucide-react';
import { getSession, logoutSession, getRoleInfo, type MRPLSession } from '@/lib/session';
import { getChatSessions, createNewChatSession, deleteChatSession, type ChatSession } from '@/lib/chatStore';

export default function SidebarNav() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [session, setSession] = useState<MRPLSession | null>(null);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const currentThreadId = searchParams.get('threadId');

  const refreshSessions = () => {
    const s = getSession();
    if (s?.userId) {
      setChatSessions(getChatSessions(s.userId));
    } else {
      setChatSessions([]);
    }
  };

  useEffect(() => {
    const s = getSession();
    setSession(s);
    refreshSessions();

    const handleUpdate = () => refreshSessions();
    window.addEventListener('mrpl_chat_sessions_updated', handleUpdate);
    return () => window.removeEventListener('mrpl_chat_sessions_updated', handleUpdate);
  }, [pathname, currentThreadId]);

  const isDirector = session?.role === 'PLANT_DIRECTOR';
  const roleInfo = session ? getRoleInfo(session.role) : null;

  const handleNewChat = () => {
    const newSession = createNewChatSession();
    router.push(`/chat?threadId=${newSession.threadId}`);
  };

  const handleDeleteChat = (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation();
    deleteChatSession(threadId);
    if (currentThreadId === threadId) {
      router.push('/chat');
    }
  };

  const handleSignOut = () => {
    logoutSession();
    router.replace('/login');
  };

  return (
    <aside className="w-64 bg-[#1a1a1a] border-r border-[#8fb03e] flex flex-col z-10 h-screen sticky top-0 shrink-0 select-none font-mono">
      {/* Brand Header with MRPL Logo */}
      <div className="p-4 border-b border-[#8fb03e] bg-[#242424]">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-[#57692c] border border-[#8fb03e] p-0.5 overflow-hidden flex items-center justify-center shrink-0">
            <img src="/mrpl_logo.jpg" alt="MRPL Logo" className="w-full h-full object-contain" />
          </div>
          <div>
            <h1 className="font-bold text-xs text-[#e8e8e8] tracking-wider uppercase">MRPL SOVEREIGN</h1>
            <h2 className="text-[9px] text-[#8fb03e] font-semibold">ONGC Subsidiary</h2>
          </div>
        </div>

        {/* NEW CHAT Button */}
        <button
          onClick={handleNewChat}
          className="w-full mt-3 py-2 px-3 bg-[#57692c] hover:bg-[#8fb03e] hover:text-[#1a1a1a] text-white font-bold text-xs border border-[#8fb03e] transition-all flex items-center justify-center space-x-2 uppercase cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>[+] NEW CHAT / नया संवाद</span>
        </button>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
        <p className="px-2 py-1 text-[10px] text-[#8fb03e] uppercase tracking-widest font-bold bg-[#2b2b2b] border-l-2 border-[#8fb03e]">
          OPERATIONS / परिचालन
        </p>
        <Link
          href="/"
          className={`flex items-center space-x-2.5 px-3 py-2 text-xs font-bold transition-colors border ${
            pathname === '/'
              ? 'bg-[#57692c] text-white border-[#8fb03e]'
              : 'text-[#c4c4c4] border-transparent hover:bg-[#2b2b2b] hover:text-white'
          }`}
        >
          <LayoutDashboard className="w-4 h-4 text-[#8fb03e]" />
          <span>[+] Dashboard</span>
        </Link>
        <Link
          href="/chat"
          className={`flex items-center space-x-2.5 px-3 py-2 text-xs font-bold transition-colors border ${
            pathname === '/chat'
              ? 'bg-[#57692c] text-white border-[#8fb03e]'
              : 'text-[#c4c4c4] border-transparent hover:bg-[#2b2b2b] hover:text-white'
          }`}
        >
          <MessageSquare className="w-4 h-4 text-[#8fb03e]" />
          <span>[+] AI Console</span>
        </Link>

        <p className="px-2 py-1 mt-4 text-[10px] text-[#8fb03e] uppercase tracking-widest font-bold bg-[#2b2b2b] border-l-2 border-[#8fb03e]">
          ENGINEERING / इंजीनियरिंग
        </p>
        <Link
          href="/trace"
          className={`flex items-center space-x-2.5 px-3 py-2 text-xs font-bold transition-colors border ${
            pathname === '/trace'
              ? 'bg-[#57692c] text-white border-[#8fb03e]'
              : 'text-[#c4c4c4] border-transparent hover:bg-[#2b2b2b] hover:text-white'
          }`}
        >
          <Activity className="w-4 h-4 text-[#8fb03e]" />
          <span>[+] DAG Agent Trace</span>
        </Link>

        {/* Audit Ledger restricted strictly to PLANT_DIRECTOR */}
        {isDirector && (
          <Link
            href="/audit"
            className={`flex items-center space-x-2.5 px-3 py-2 text-xs font-bold transition-colors border ${
              pathname === '/audit'
                ? 'bg-[#57692c] text-white border-[#8fb03e]'
                : 'text-[#c4c4c4] border-transparent hover:bg-[#2b2b2b] hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4 text-[#8fb03e]" />
            <span>[+] Audit Ledger</span>
          </Link>
        )}

        {/* Previous Chat History - POSITIONED BELOW ENGINEERING */}
        {chatSessions.length > 0 && (
          <div className="mt-4 pt-2 border-t border-[#8fb03e]/30">
            <p className="px-2 py-1 text-[10px] text-[#8fb03e] uppercase tracking-widest font-bold bg-[#2b2b2b] border-l-2 border-[#8fb03e] flex items-center justify-between">
              <span>PREVIOUS CHATS / पूर्व संवाद</span>
              <span className="text-[9px] text-[#c4c4c4]">({chatSessions.length})</span>
            </p>
            <div className="mt-1.5 space-y-1 max-h-56 overflow-y-auto pr-0.5">
              {chatSessions.map((s) => {
                const isActive = currentThreadId === s.threadId;
                const formattedTime = new Date(s.updatedAt).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                });
                return (
                  <div
                    key={s.threadId}
                    onClick={() => router.push(`/chat?threadId=${s.threadId}`)}
                    className={`group relative flex items-center justify-between px-2.5 py-1.5 text-xs transition-colors cursor-pointer border ${
                      isActive
                        ? 'bg-[#57692c]/40 text-white border-[#8fb03e]'
                        : 'text-[#c4c4c4] border-transparent hover:bg-[#242424] hover:text-white'
                    }`}
                  >
                    <div className="flex items-center space-x-2 min-w-0 pr-6">
                      <MessageCircle className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-[#8fb03e]' : 'text-neutral-500'}`} />
                      <div className="truncate">
                        <p className="text-[11px] font-bold truncate leading-tight">{s.title}</p>
                        <p className="text-[9px] text-neutral-500 font-mono flex items-center mt-0.5">
                          <Clock className="w-2.5 h-2.5 mr-1 text-neutral-600" />
                          {formattedTime}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={(e) => handleDeleteChat(e, s.threadId)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-neutral-400 hover:text-red-400 hover:bg-red-950/40 border border-transparent hover:border-red-500/40 transition-all shrink-0 cursor-pointer"
                      title="Delete chat session"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </nav>

      {/* User Session Profile & Sign Out Footer */}
      {session && roleInfo && (
        <div className="p-3 border-t border-[#8fb03e] bg-[#242424] space-y-2">
          <div className="flex items-center justify-between bg-[#1a1a1a] p-2 border border-[#8fb03e]">
            <div className="flex items-center space-x-2 overflow-hidden">
              <div className="w-6 h-6 bg-[#57692c] border border-[#8fb03e] flex items-center justify-center shrink-0">
                <User className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="truncate">
                <p className="text-[11px] font-bold text-[#e8e8e8] truncate">{session.userName}</p>
                <p className="text-[9px] text-[#8fb03e]">{roleInfo.label}</p>
              </div>
            </div>
            <button
              onClick={handleSignOut}
              className="p-1 text-red-400 hover:text-red-300 hover:bg-red-950/50 border border-red-500/30 transition-colors shrink-0 cursor-pointer"
              title="Sign Out Session"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Air-Gap Badge */}
          <div className="flex items-center space-x-2 px-2 py-1 bg-[#1a1a1a] border border-[#8fb03e]">
            <Shield className="w-3.5 h-3.5 text-[#8fb03e]" />
            <span className="text-[9px] text-[#c4c4c4] font-bold">AIR-GAPPED INTRANET NODE</span>
          </div>
        </div>
      )}
    </aside>
  );
}
