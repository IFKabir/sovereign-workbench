'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { User, LogOut, ChevronDown, Shield, Pause, Play, Eye, Accessibility } from 'lucide-react';
import { getSession, logoutSession, getRoleInfo, type MRPLSession } from '@/lib/session';

export default function GIGWHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState<MRPLSession | null>(null);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [textSize, setTextSize] = useState<'normal' | 'large' | 'xlarge'>('normal');
  const [lang, setLang] = useState<'EN' | 'HI'>('EN');
  const [isTickerPaused, setIsTickerPaused] = useState(false);

  useEffect(() => {
    setSession(getSession());
  }, [pathname]);

  const roleInfo = session ? getRoleInfo(session.role) : null;
  const isDirector = session?.role === 'PLANT_DIRECTOR';

  const handleSignOut = () => {
    logoutSession();
    router.replace('/login');
  };

  const handleTextSizeChange = (size: 'normal' | 'large' | 'xlarge') => {
    setTextSize(size);
    if (typeof document !== 'undefined') {
      if (size === 'normal') document.documentElement.style.fontSize = '100%';
      if (size === 'large') document.documentElement.style.fontSize = '110%';
      if (size === 'xlarge') document.documentElement.style.fontSize = '120%';
    }
  };

  if (!session) return null;

  return (
    <header className="w-full shrink-0 z-40 select-none font-sans border-b border-accent-green">
      {/* 1. Accessibility Toolbar Strip (#2b2b2b) */}
      <div className="bg-[#2b2b2b] text-[#c4c4c4] px-6 py-1 text-[11px] flex justify-between items-center border-b border-neutral-700">
        <div className="flex items-center space-x-4">
          <a href="#main-content" className="hover:text-white underline font-mono flex items-center">
            <Accessibility className="w-3 h-3 mr-1 text-accent-green" /> Skip to Main Content
          </a>
          <span className="text-neutral-600">|</span>
          <a href="#accessibility" className="hover:text-white underline font-mono">
            Screen Reader Access
          </a>
        </div>

        <div className="flex items-center space-x-4">
          {/* Text Size Stepper */}
          <div className="flex items-center space-x-1 font-mono font-bold bg-[#1a1a1a] px-2 py-0.5 border border-neutral-600">
            <span className="text-[10px] text-neutral-400 mr-1">Text Size:</span>
            <button
              onClick={() => handleTextSizeChange('normal')}
              className={`px-1 hover:text-white ${textSize === 'normal' ? 'text-accent-green font-black underline' : 'text-neutral-400'}`}
              title="Normal Text Size"
            >
              A-
            </button>
            <button
              onClick={() => handleTextSizeChange('large')}
              className={`px-1 hover:text-white ${textSize === 'large' ? 'text-accent-green font-black underline' : 'text-neutral-400'}`}
              title="Large Text Size"
            >
              A
            </button>
            <button
              onClick={() => handleTextSizeChange('xlarge')}
              className={`px-1 hover:text-white ${textSize === 'xlarge' ? 'text-accent-green font-black underline' : 'text-neutral-400'}`}
              title="Extra Large Text Size"
            >
              A+
            </button>
          </div>

          <span className="text-neutral-600">|</span>

          {/* Language Toggle Pill */}
          <button
            onClick={() => setLang(lang === 'EN' ? 'HI' : 'EN')}
            className="px-2 py-0.5 bg-[#57692c] text-white font-bold border border-accent-green text-[11px] hover:bg-accent-green hover:text-black transition-colors"
          >
            {lang === 'EN' ? 'हिन्दी' : 'English'}
          </button>
        </div>
      </div>

      {/* 2. Main Portal Header (#1a1a1a) with Official MRPL Logo */}
      <div className="bg-[#1a1a1a] px-6 py-3 flex justify-between items-center border-b border-[#2b2b2b]">
        <div className="flex items-center space-x-4">
          {/* Official MRPL Logo Tile */}
          <div className="w-14 h-14 bg-[#57692c] border border-accent-green p-0.5 overflow-hidden flex items-center justify-center shrink-0">
            <img
              src="/mrpl_logo.jpg"
              alt="MRPL Logo"
              className="w-full h-full object-contain"
            />
          </div>

          <div>
            <h1 className="text-base md:text-lg font-bold text-[#e8e8e8] tracking-wide uppercase font-mono">
              Mangalore Refinery and Petrochemicals Limited
            </h1>
            <h2 className="text-xs text-accent-green font-semibold tracking-normal mt-0.5">
              एमआरपीएल · A Subsidiary of Oil and Natural Gas Corporation (ONGC) | A Govt. of India Enterprise
            </h2>
            <p className="text-[10px] text-[#c4c4c4] font-mono mt-0.5">
              Sovereign Operational Copilot Node — Air-Gapped Intranet System
            </p>
          </div>
        </div>

        {/* User Profile & Sign Out */}
        <div className="relative">
          {roleInfo && (
            <button
              onClick={() => setShowProfileDropdown(!showProfileDropdown)}
              className="flex items-center space-x-3 bg-[#222222] border border-accent-green px-3 py-1.5 hover:bg-[#2b2b2b] transition-colors"
            >
              <div className="w-7 h-7 bg-[#57692c] border border-accent-green flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="text-left hidden md:block">
                <p className="text-xs font-bold text-[#e8e8e8]">{session.userName}</p>
                <p className="text-[10px] text-[#c4c4c4] font-mono">{session.userId}</p>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-[#57692c] text-white border border-accent-green">
                {roleInfo.label}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-accent-green" />
            </button>
          )}

          {showProfileDropdown && (
            <div className="absolute top-full right-0 mt-1 w-64 bg-[#1a1a1a] border-2 border-accent-green shadow-2xl z-50 p-4 font-mono text-xs">
              <p className="text-[10px] text-accent-green uppercase font-bold tracking-wider mb-2 border-b border-neutral-700 pb-1">
                Authenticated Session Info
              </p>
              <div className="space-y-1.5 text-[#c4c4c4]">
                <div className="flex justify-between">
                  <span>Employee ID:</span>
                  <span className="text-white font-bold">{session.userId}</span>
                </div>
                <div className="flex justify-between">
                  <span>Full Name:</span>
                  <span className="text-white">{session.userName}</span>
                </div>
                <div className="flex justify-between">
                  <span>Role Tier:</span>
                  <span className="text-accent-green font-bold">{roleInfo?.label}</span>
                </div>
                <div className="flex justify-between">
                  <span>Assigned Unit:</span>
                  <span className="text-white">{session.plantUnit}</span>
                </div>
              </div>
              <button
                onClick={handleSignOut}
                className="w-full mt-4 pt-2.5 border-t border-neutral-700 text-xs text-red-400 hover:text-red-300 font-bold flex items-center justify-center space-x-1.5 bg-[#2b2b2b] border border-red-500/30 py-1.5 hover:bg-red-900/30"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out Session</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 3. Horizontal Military Olive Green Nav Bar (#57692c) with [+] markers */}
      <nav className="bg-[#57692c] border-b border-accent-green px-6 py-0 flex items-center justify-between overflow-x-auto">
        <div className="flex items-center space-x-1 font-mono text-xs text-white">
          <Link
            href="/"
            className={`px-4 py-2.5 border-r border-[#8fb03e]/40 font-bold flex items-center space-x-1.5 transition-colors ${
              pathname === '/' || pathname === '/chat'
                ? 'bg-[#8fb03e] text-black font-black'
                : 'hover:bg-[#8fb03e]/30 text-white'
            }`}
          >
            <span>[+] AI OPERATIONAL CONSOLE</span>
          </Link>

          <Link
            href="/schematic"
            className={`px-4 py-2.5 border-r border-[#8fb03e]/40 font-bold flex items-center space-x-1.5 transition-colors ${
              pathname === '/schematic'
                ? 'bg-[#8fb03e] text-black font-black'
                : 'hover:bg-[#8fb03e]/30 text-white'
            }`}
          >
            <span>[+] SCHEMATIC INSPECTION</span>
          </Link>

          {isDirector && (
            <Link
              href="/audit"
              className={`px-4 py-2.5 border-r border-[#8fb03e]/40 font-bold flex items-center space-x-1.5 transition-colors ${
                pathname === '/audit'
                  ? 'bg-[#8fb03e] text-black font-black'
                  : 'hover:bg-[#8fb03e]/30 text-white'
              }`}
            >
              <span>[+] SECURITY AUDIT LEDGER</span>
            </Link>
          )}
        </div>

        <div className="hidden lg:flex items-center space-x-2 text-[10px] font-mono text-white px-3 py-1 bg-[#1a1a1a] border border-accent-green">
          <Shield className="w-3 h-3 text-accent-green" />
          <span>ZERO WAN EGRESS | AIR-GAPPED ON-PREMISE NODE</span>
        </div>
      </nav>

      {/* 4. Scrolling Notice Ticker Bar (#1a1a1a with #4a9eff links) */}
      <div className="bg-[#1a1a1a] border-b border-accent-green px-4 py-1.5 flex items-center space-x-3 text-xs font-mono">
        <div className="bg-[#57692c] text-white px-2.5 py-0.5 font-bold uppercase text-[10px] tracking-wider border border-accent-green shrink-0 flex items-center">
          <span>NOTICES / सूचनाएं</span>
        </div>

        <div className="flex-1 overflow-hidden relative">
          <div className={`whitespace-nowrap inline-block ${isTickerPaused ? '' : 'animate-[marquee_25s_linear_infinite]'}`}>
            <span className="mr-8">
              • OISD-118 Section 6.2 Double Block and Bleed Isolation Verification Engine Active
            </span>
            <span className="mr-8">
              • <a href="/schematic" className="gigw-link">Inspect CDU-II Bypass Line Schematic with YOLOv11s Symbol Detection</a>
            </span>
            <span className="mr-8">
              • SHA-256 Hash-Chained Audit Ledger Active on Local SQLite Node (data/audit_ledger.db)
            </span>
            <span className="mr-8">
              • <a href="/chat?q=Calculate+pressure+drop+across+pipeline" className="gigw-link">Run Darcy-Weisbach / API-520 Engineering Calculations in Isolated Sandbox</a>
            </span>
          </div>
        </div>

        <button
          onClick={() => setIsTickerPaused(!isTickerPaused)}
          className="bg-[#2b2b2b] text-[#c4c4c4] hover:text-white px-2 py-0.5 border border-neutral-600 text-[10px] flex items-center shrink-0"
          title={isTickerPaused ? 'Play Ticker' : 'Pause Ticker'}
        >
          {isTickerPaused ? <Play className="w-3 h-3 mr-1 text-accent-green" /> : <Pause className="w-3 h-3 mr-1 text-accent-green" />}
          <span>{isTickerPaused ? 'PLAY' : 'PAUSE'}</span>
        </button>
      </div>
    </header>
  );
}
