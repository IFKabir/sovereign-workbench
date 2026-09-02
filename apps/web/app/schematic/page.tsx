'use client';

import SchematicViewer from '@/components/SchematicViewer';
import { Search } from 'lucide-react';

export default function SchematicPage() {
  return (
    <div className="h-full flex flex-col p-6 max-w-[1600px] mx-auto w-full font-mono select-none">
      <div className="mb-4 flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-xl font-bold text-[#e8e8e8] flex items-center uppercase tracking-wider">
            <Search className="mr-3 w-6 h-6 text-[#8fb03e]" /> SCHEMATIC INSPECTION WORKSPACE / आरेख निरीक्षण
          </h1>
          <p className="text-xs text-[#c4c4c4] mt-1">
            Pan & Zoom engineering drawings with real-time YOLOv11s symbol detection & OISD compliance mapping
          </p>
        </div>
      </div>

      <div className="flex-1 min-h-0 relative">
        <SchematicViewer />
      </div>
    </div>
  );
}
