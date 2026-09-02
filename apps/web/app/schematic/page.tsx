'use client';

import SchematicViewer from '@/components/SchematicViewer';
import { Search } from 'lucide-react';

export default function SchematicPage() {
  return (
    <div className="h-full flex flex-col p-6 max-w-[1600px] mx-auto w-full">
      <div className="mb-4 flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center">
            <Search className="mr-3 w-6 h-6 text-accent-cyan" /> Schematic Inspection Workspace
          </h1>
          <p className="text-xs text-gray-400 mt-1 font-mono">
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
