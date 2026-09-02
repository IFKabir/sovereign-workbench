'use client';

import { useState } from 'react';
import { Pause, Play } from 'lucide-react';

export default function GIGWHeader() {
  const [isTickerPaused, setIsTickerPaused] = useState(false);

  return (
    <header className="w-full shrink-0 z-40 select-none font-sans border-b border-[#8fb03e]">
      {/* Scrolling Notice Ticker Bar (#1a1a1a with #4a9eff links) */}
      <div className="bg-[#1a1a1a] border-b border-[#8fb03e] px-4 py-1.5 flex items-center space-x-3 text-xs font-mono">
        <div className="bg-[#57692c] text-white px-2.5 py-0.5 font-bold uppercase text-[10px] tracking-wider border border-[#8fb03e] shrink-0 flex items-center">
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
          className="bg-[#2b2b2b] text-[#c4c4c4] hover:text-white px-2 py-0.5 border border-neutral-600 text-[10px] flex items-center shrink-0 cursor-pointer"
          title={isTickerPaused ? 'Play Ticker' : 'Pause Ticker'}
        >
          {isTickerPaused ? <Play className="w-3 h-3 mr-1 text-[#8fb03e]" /> : <Pause className="w-3 h-3 mr-1 text-[#8fb03e]" />}
          <span>{isTickerPaused ? 'PLAY' : 'PAUSE'}</span>
        </button>
      </div>
    </header>
  );
}
