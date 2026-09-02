'use client';

import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react';

export interface Citation {
  document: string;
  section?: string;
  excerpt: string;
  score?: number;
}

interface CitationListProps {
  citations: Citation[];
}

export const CitationList: React.FC<CitationListProps> = ({ citations }) => {
  if (!citations || citations.length === 0) return null;

  const [expandedIndices, setExpandedIndices] = useState<number[]>([]);

  const toggleIndex = (index: number) => {
    setExpandedIndices((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const toggleAll = () => {
    if (expandedIndices.length === citations.length) {
      setExpandedIndices([]);
    } else {
      setExpandedIndices(citations.map((_, i) => i));
    }
  };

  const allExpanded = expandedIndices.length === citations.length;

  return (
    <div className="mt-3 pt-3 border-t border-[#8fb03e]/40 font-mono select-none">
      {/* Header Bar */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-1.5 text-xs text-[#8fb03e] font-bold uppercase tracking-wider">
          <BookOpen className="w-3.5 h-3.5 text-[#8fb03e]" />
          <span>VERIFIED STANDARDS REFERENCES ({citations.length})</span>
        </div>
        {citations.length > 1 && (
          <button
            type="button"
            onClick={toggleAll}
            className="text-[11px] text-[#c4c4c4] hover:text-white transition-colors cursor-pointer underline font-bold"
          >
            {allExpanded ? '[ COLLAPSE ALL ]' : '[ EXPAND ALL ]'}
          </button>
        )}
      </div>

      {/* Accordion List */}
      <div className="flex flex-col gap-1.5">
        {citations.map((citation, idx) => {
          const isExpanded = expandedIndices.includes(idx);
          const matchPercent = citation.score !== undefined && citation.score !== null
            ? `${(citation.score * 100).toFixed(1)}%`
            : null;

          return (
            <div
              key={idx}
              className="border border-[#8fb03e] bg-[#1a1a1a] hover:bg-[#222222] transition-colors overflow-hidden"
            >
              {/* Clickable Summary Bar */}
              <button
                type="button"
                onClick={() => toggleIndex(idx)}
                className="w-full px-3 py-2 flex items-center justify-between text-left gap-2 cursor-pointer select-none"
              >
                <div className="flex items-center space-x-2 min-w-0">
                  <span className="text-xs font-bold text-[#e8e8e8] truncate">
                    {citation.document}
                  </span>
                  {citation.section && (
                    <span className="text-[11px] text-[#c4c4c4] truncate hidden sm:inline">
                      • {citation.section}
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  {matchPercent && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 bg-[#57692c] text-white border border-[#8fb03e]">
                      MATCH: {matchPercent}
                    </span>
                  )}
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-[#8fb03e]" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#8fb03e]" />
                  )}
                </div>
              </button>

              {/* Collapsible Content */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-2 border-t border-[#8fb03e]/40 text-xs text-[#e8e8e8] bg-[#121212]">
                  <blockquote className="border-l-2 border-[#8fb03e] pl-3 py-1.5 my-1 bg-[#1a1a1a] text-[11px] leading-relaxed text-[#e8e8e8] italic whitespace-pre-wrap">
                    "{citation.excerpt}"
                  </blockquote>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
