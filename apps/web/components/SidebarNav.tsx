'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare, Search, FileText, Shield } from 'lucide-react';
import { getSession, type MRPLSession } from '@/lib/session';

export default function SidebarNav() {
  const pathname = usePathname();
  const [session, setSession] = useState<MRPLSession | null>(null);

  useEffect(() => {
    setSession(getSession());
  }, [pathname]);

  const isDirector = session?.role === 'PLANT_DIRECTOR';

  return (
    <aside className="w-64 bg-[#1a1a1a] border-r border-[#8fb03e] flex flex-col z-10 h-screen sticky top-0 shrink-0 select-none font-mono">
      {/* Brand Header */}
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
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 py-3 px-2 space-y-1">
        <p className="px-2 py-1 text-[10px] text-[#8fb03e] uppercase tracking-widest font-bold bg-[#2b2b2b] border-l-2 border-[#8fb03e]">
          OPERATIONS / परिचालन
        </p>
        <Link
          href="/"
          className={`flex items-center space-x-2.5 px-3 py-2 text-xs font-bold transition-colors border ${
            pathname === '/' || pathname === '/chat'
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
          href="/schematic"
          className={`flex items-center space-x-2.5 px-3 py-2 text-xs font-bold transition-colors border ${
            pathname === '/schematic'
              ? 'bg-[#57692c] text-white border-[#8fb03e]'
              : 'text-[#c4c4c4] border-transparent hover:bg-[#2b2b2b] hover:text-white'
          }`}
        >
          <Search className="w-4 h-4 text-[#8fb03e]" />
          <span>[+] P&ID Inspection</span>
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
      </nav>

      {/* Footer Air-Gap Badge */}
      <div className="p-3 border-t border-[#8fb03e] bg-[#242424]">
        <div className="flex items-center space-x-2 px-2.5 py-1.5 bg-[#1a1a1a] border border-[#8fb03e]">
          <Shield className="w-4 h-4 text-[#8fb03e]" />
          <div>
            <p className="text-[10px] text-[#8fb03e] font-bold">Zero WAN Egress</p>
            <p className="text-[9px] text-[#c4c4c4]">Air-Gapped Intranet Node</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
