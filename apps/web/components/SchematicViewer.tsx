'use client';
import { useState } from 'react';
import { ZoomIn, ZoomOut, Maximize, Layers } from 'lucide-react';

interface BBox {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  type: 'VALVE' | 'PUMP' | 'SENSOR' | 'TANK';
}

const mockBBoxes: BBox[] = [
  { id: '1', x: 20, y: 30, w: 12, h: 12, label: 'V-101 (Gate Valve)', type: 'VALVE' },
  { id: '2', x: 60, y: 40, w: 18, h: 18, label: 'P-202A (Centrifugal)', type: 'PUMP' },
  { id: '3', x: 45, y: 70, w: 9, h: 9, label: 'PT-303 (Pressure)', type: 'SENSOR' },
];

const typeColors = {
  VALVE: 'border-accent-amber bg-accent-amber/10',
  PUMP: 'border-accent-cyan bg-accent-cyan/10',
  SENSOR: 'border-accent-emerald bg-accent-emerald/10',
  TANK: 'border-purple-500 bg-purple-500/10',
};

export default function SchematicViewer() {
  const [scale, setScale] = useState(1);
  const [activeBox, setActiveBox] = useState<BBox | null>(null);

  return (
    <div className="glass-panel flex flex-col h-full rounded-xl overflow-hidden border border-sovereign-border shadow-lg relative">
      <div className="p-4 border-b border-sovereign-border flex justify-between items-center bg-sovereign-surface/80">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-accent-cyan" />
          <h3 className="font-mono text-sm font-bold text-gray-200">P&ID Analysis Viewer</h3>
        </div>
        <div className="flex items-center space-x-1 bg-sovereign-dark rounded-lg p-1 border border-sovereign-border">
          <button onClick={() => setScale(s => Math.max(0.5, s - 0.2))} className="p-1.5 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded transition-colors"><ZoomOut className="w-3.5 h-3.5" /></button>
          <span className="px-2 font-mono text-xs text-gray-300 min-w-[50px] text-center">{Math.round(scale * 100)}%</span>
          <button onClick={() => setScale(s => Math.min(3, s + 0.2))} className="p-1.5 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded transition-colors"><ZoomIn className="w-3.5 h-3.5" /></button>
          <div className="w-px h-4 bg-sovereign-border mx-1"></div>
          <button onClick={() => setScale(1)} className="p-1.5 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded transition-colors"><Maximize className="w-3.5 h-3.5" /></button>
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-[#05070a] relative flex items-center justify-center p-8 industrial-grid" style={{ backgroundImage: 'linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px)' }}>
        <div
          className="relative transition-transform duration-200 shadow-2xl rounded bg-white/5 border border-white/10"
          style={{ transform: `scale(${scale})`, width: '100%', maxWidth: '800px', aspectRatio: '4/3' }}
        >
          <div className="absolute inset-0 flex items-center justify-center text-gray-700 font-mono text-sm border-2 border-dashed border-gray-800 rounded">
            [ Schematic Placeholder ]
          </div>
          {mockBBoxes.map((box) => (
            <div
              key={box.id}
              onClick={() => setActiveBox(box)}
              className={`absolute border-2 cursor-pointer transition-all duration-200 ${typeColors[box.type]} ${activeBox?.id === box.id ? 'ring-2 ring-white z-10 bg-opacity-30' : 'hover:bg-opacity-20'}`}
              style={{ left: `${box.x}%`, top: `${box.y}%`, width: `${box.w}%`, height: `${box.h}%` }}
            >
              <div className={`absolute -top-7 left-1/2 -translate-x-1/2 bg-sovereign-dark text-[10px] px-2 py-1 rounded border font-mono whitespace-nowrap transition-opacity ${activeBox?.id === box.id ? 'opacity-100 text-white border-gray-500' : 'opacity-0 border-sovereign-border text-gray-400'} pointer-events-none shadow-lg z-20`}>
                {box.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-4 border-t border-sovereign-border bg-sovereign-surface/90 flex justify-center space-x-6">
        <div className="flex items-center space-x-2 text-xs text-gray-300 font-mono"><div className="w-3 h-3 border border-accent-amber bg-accent-amber/20 rounded-sm"></div><span>VALVE</span></div>
        <div className="flex items-center space-x-2 text-xs text-gray-300 font-mono"><div className="w-3 h-3 border border-accent-cyan bg-accent-cyan/20 rounded-sm"></div><span>PUMP</span></div>
        <div className="flex items-center space-x-2 text-xs text-gray-300 font-mono"><div className="w-3 h-3 border border-accent-emerald bg-accent-emerald/20 rounded-sm"></div><span>SENSOR</span></div>
      </div>
    </div>
  );
}
