'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare, Search, FileText, Shield, Flame } from 'lucide-react';
import { getSession, type MRPLSession } from '@/lib/session';

export default function SidebarNav() {
  const pathname = usePathname();
  const [session, setSession] = useState<MRPLSession | null>(null);

  useEffect(() => {
    setSession(getSession());
  }, [pathname]);

  const isDirector = session?.role === 'PLANT_DIRECTOR';

  return (
    <aside className="w-64 glass-panel border-r border-sovereign-border flex flex-col z-10 h-screen sticky top-0 shrink-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-sovereign-border">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-emerald flex items-center justify-center shadow-lg shadow-accent-cyan/20">
            <Flame className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-gray-100 tracking-wide">MRPL Sovereign</h1>
            <h2 className="text-[10px] text-gray-400 mt-0.5">Intelligence Platform</h2>
          </div>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        <p className="px-3 py-2 text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Operations</p>
        <Link
          href="/"
          className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors text-sm ${
            pathname === '/' || pathname === '/chat'
              ? 'bg-accent-cyan/10 text-accent-cyan font-semibold border border-accent-cyan/20'
              : 'text-gray-300 hover:bg-sovereign-surface hover:text-white'
          }`}
        >
          <MessageSquare className="w-4.5 h-4.5" />
          <span>AI Operational Console</span>
        </Link>

        <p className="px-3 py-2 mt-4 text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Engineering</p>
        <Link
          href="/schematic"
          className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors text-sm ${
            pathname === '/schematic'
              ? 'bg-accent-cyan/10 text-accent-cyan font-semibold border border-accent-cyan/20'
              : 'text-gray-300 hover:bg-sovereign-surface hover:text-white'
          }`}
        >
          <Search className="w-4.5 h-4.5" />
          <span>Schematic Inspection</span>
        </Link>

        {/* Audit Ledger restricted strictly to PLANT_DIRECTOR */}
        {isDirector && (
          <Link
            href="/audit"
            className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors text-sm ${
              pathname === '/audit'
                ? 'bg-accent-cyan/10 text-accent-cyan font-semibold border border-accent-cyan/20'
                : 'text-gray-300 hover:bg-sovereign-surface hover:text-white'
            }`}
          >
            <FileText className="w-4.5 h-4.5" />
            <span>Audit Ledger</span>
          </Link>
        )}
      </nav>

      {/* Footer Air-Gap Badge */}
      <div className="p-4 border-t border-sovereign-border">
        <div className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-accent-emerald/5 border border-accent-emerald/15">
          <Shield className="w-4 h-4 text-accent-emerald" />
          <div>
            <p className="text-[10px] text-accent-emerald font-semibold">Zero WAN Egress</p>
            <p className="text-[9px] text-gray-500">Air-Gapped Intranet Node</p>
          </div>
          <span className="w-2 h-2 rounded-full bg-accent-emerald animate-pulse ml-auto" />
        </div>
      </div>
    </aside>
  );
}
