'use client';
import { useState, useRef, ChangeEvent, ReactNode } from 'react';
import { ZoomIn, ZoomOut, Maximize, Layers, Upload, FileText, AlertTriangle, CheckCircle2 } from 'lucide-react';

export interface BBox {
  id: string;
  x: number; // percentage
  y: number; // percentage
  w: number; // percentage
  h: number; // percentage
  tag: string;
  type: 'VALVE' | 'PUMP' | 'SENSOR' | 'TANK' | 'VESSEL';
  confidence: number; // 0-1
  hazardStatus: 'NORMAL' | 'WARNING' | 'OISD_VIOLATION';
  description: string;
}

interface PresetSchematic {
  id: string;
  title: string;
  description: string;
  boxes: BBox[];
  svgContent: ReactNode;
}

const PRESETS: Record<string, PresetSchematic> = {
  CDU_BYPASS: {
    id: 'CDU_BYPASS',
    title: 'CDU-2 Control Valve Bypass Line',
    description: 'Crude Distillation Unit bypass valve CV-101 line layout',
    boxes: [
      { id: '1', x: 28, y: 32, w: 16, h: 18, tag: 'CV-101', type: 'VALVE', confidence: 0.984, hazardStatus: 'OISD_VIOLATION', description: 'Control Valve CV-101 bypass line missing required bleed valve (OISD-118 Section 6.2 violation)' },
      { id: '2', x: 12, y: 35, w: 10, h: 12, tag: 'PT-102', type: 'SENSOR', confidence: 0.952, hazardStatus: 'NORMAL', description: 'Pressure Transmitter PT-102 (0-25 bar range)' },
      { id: '3', x: 58, y: 32, w: 14, h: 16, tag: 'V-101', type: 'VALVE', confidence: 0.971, hazardStatus: 'NORMAL', description: 'Double block gate valve V-101 isolation' },
      { id: '4', x: 76, y: 55, w: 12, h: 14, tag: 'TT-104', type: 'SENSOR', confidence: 0.941, hazardStatus: 'NORMAL', description: 'Temperature Transmitter TT-104' },
    ],
    svgContent: (
      <svg className="w-full h-full" viewBox="0 0 800 600" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Process Flow Line */}
        <path d="M 50 250 L 250 250 L 250 160 L 550 160 L 550 250 L 750 250" stroke="#06b6d4" strokeWidth="4" fill="none" />
        <path d="M 250 250 L 550 250" stroke="#10b981" strokeWidth="4" strokeDasharray="8 4" fill="none" />
        
        {/* Main Control Valve CV-101 */}
        <g transform="translate(360, 135)">
          <polygon points="0,0 30,25 0,50" fill="#f59e0b" opacity="0.3" stroke="#f59e0b" strokeWidth="2" />
          <polygon points="60,0 30,25 60,50" fill="#f59e0b" opacity="0.3" stroke="#f59e0b" strokeWidth="2" />
          <line x1="30" y1="25" x2="30" y2="-15" stroke="#f59e0b" strokeWidth="2" />
          <circle cx="30" cy="-22" r="10" fill="#1e293b" stroke="#f59e0b" strokeWidth="2" />
          <text x="30" y="-38" textAnchor="middle" fill="#f59e0b" fontSize="12" fontFamily="monospace" fontWeight="bold">CV-101</text>
        </g>
        
        {/* Pressure Transmitter PT-102 */}
        <g transform="translate(130, 210)">
          <line x1="15" y1="40" x2="15" y2="15" stroke="#06b6d4" strokeWidth="2" />
          <circle cx="15" cy="0" r="16" fill="#0f172a" stroke="#06b6d4" strokeWidth="2" />
          <text x="15" y="4" textAnchor="middle" fill="#06b6d4" fontSize="11" fontFamily="monospace" fontWeight="bold">PT-102</text>
        </g>

        {/* Gate Valve V-101 */}
        <g transform="translate(500, 225)">
          <polygon points="0,0 20,15 0,30" fill="#10b981" opacity="0.3" stroke="#10b981" strokeWidth="2" />
          <polygon points="40,0 20,15 40,30" fill="#10b981" opacity="0.3" stroke="#10b981" strokeWidth="2" />
          <line x1="20" y1="15" x2="20" y2="-10" stroke="#10b981" strokeWidth="2" />
          <line x1="10" y1="-10" x2="30" y2="-10" stroke="#10b981" strokeWidth="2" />
          <text x="20" y="-18" textAnchor="middle" fill="#10b981" fontSize="11" fontFamily="monospace" fontWeight="bold">V-101</text>
        </g>

        {/* Labels & Annotations */}
        <text x="70" y="235" fill="#94a3b8" fontSize="12" fontFamily="monospace">CRUDE FEED (Line 101-CDU)</text>
        <text x="400" y="280" fill="#10b981" fontSize="11" fontFamily="monospace">BYPASS LINE (2" Sch 80)</text>
        <text x="400" y="110" fill="#ef4444" fontSize="11" fontFamily="monospace" fontWeight="bold">⚠️ MISSING BLEED VALVE (OISD-118)</text>
      </svg>
    ),
  },
  PUMP_ISOLATION: {
    id: 'PUMP_ISOLATION',
    title: 'P-201A/B Pump Isolation Manifold',
    description: 'Centrifugal pump suction & discharge manifold arrangement',
    boxes: [
      { id: '1', x: 22, y: 40, w: 22, h: 25, tag: 'P-201A', type: 'PUMP', confidence: 0.991, hazardStatus: 'WARNING', description: 'Duty Centrifugal Pump P-201A (Abnormal vibration logged in handover)' },
      { id: '2', x: 58, y: 40, w: 22, h: 25, tag: 'P-201B', type: 'PUMP', confidence: 0.988, hazardStatus: 'NORMAL', description: 'Standby Centrifugal Pump P-201B' },
      { id: '3', x: 10, y: 46, w: 10, h: 14, tag: 'HV-201', type: 'VALVE', confidence: 0.963, hazardStatus: 'NORMAL', description: 'Suction Isolation Hand Valve' },
      { id: '4', x: 44, y: 22, w: 14, h: 16, tag: 'FCV-205', type: 'VALVE', confidence: 0.947, hazardStatus: 'NORMAL', description: 'Minimum flow recirculation valve' },
    ],
    svgContent: (
      <svg className="w-full h-full" viewBox="0 0 800 600" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Suction Line */}
        <path d="M 50 300 L 180 300 M 180 300 L 180 220 L 220 220 M 180 300 L 180 380 L 220 380" stroke="#06b6d4" strokeWidth="4" strokeDasharray="none" />
        
        {/* Discharge Line */}
        <path d="M 360 220 L 450 220 L 450 300 L 750 300 M 360 380 L 450 380 L 450 300" stroke="#10b981" strokeWidth="4" />

        {/* Pump A Icon */}
        <g transform="translate(260, 190)">
          <circle cx="35" cy="30" r="30" fill="#0f172a" stroke="#06b6d4" strokeWidth="3" />
          <polygon points="35,0 65,30 35,30" fill="#06b6d4" opacity="0.5" />
          <text x="35" y="68" textAnchor="middle" fill="#06b6d4" fontSize="12" fontFamily="monospace" fontWeight="bold">P-201A</text>
        </g>

        {/* Pump B Icon */}
        <g transform="translate(260, 350)">
          <circle cx="35" cy="30" r="30" fill="#0f172a" stroke="#10b981" strokeWidth="3" />
          <polygon points="35,0 65,30 35,30" fill="#10b981" opacity="0.5" />
          <text x="35" y="68" textAnchor="middle" fill="#10b981" fontSize="12" fontFamily="monospace" fontWeight="bold">P-201B</text>
        </g>

        <text x="60" y="280" fill="#94a3b8" fontSize="12" fontFamily="monospace">SUCTION HEADER</text>
        <text x="600" y="280" fill="#10b981" fontSize="12" fontFamily="monospace">DISCHARGE HEADER</text>
      </svg>
    ),
  },
};

const hazardBadges = {
  NORMAL: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30',
  WARNING: 'bg-accent-amber/10 text-accent-amber border-accent-amber/30',
  OISD_VIOLATION: 'bg-danger/10 text-danger border-danger/30 animate-pulse',
};

export default function SchematicViewer() {
  const [selectedPresetKey, setSelectedPresetKey] = useState<string>('CDU_BYPASS');
  const [scale, setScale] = useState(1);
  const [activeBox, setActiveBox] = useState<BBox | null>(null);
  const [customImage, setCustomImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const currentPreset = PRESETS[selectedPresetKey];
  const boxesToRender = customImage ? [] : currentPreset.boxes;

  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setCustomImage(event.target?.result as string);
        setActiveBox(null);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="glass-panel flex flex-col h-full rounded-xl overflow-hidden border border-sovereign-border shadow-lg relative">
      {/* Header Bar */}
      <div className="p-4 border-b border-sovereign-border flex justify-between items-center bg-sovereign-surface/80 flex-wrap gap-2">
        <div className="flex items-center space-x-3">
          <Layers className="w-5 h-5 text-accent-cyan" />
          <div>
            <h3 className="font-mono text-sm font-bold text-gray-200">
              {customImage ? 'Uploaded P&ID Schematic' : currentPreset.title}
            </h3>
            <p className="text-[11px] text-gray-400 font-mono">
              {customImage ? 'YOLOv11s Custom Schematic Analysis' : currentPreset.description}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Preset Selectors */}
          <div className="flex bg-sovereign-dark rounded-lg p-1 border border-sovereign-border space-x-1">
            <button
              onClick={() => { setSelectedPresetKey('CDU_BYPASS'); setCustomImage(null); setActiveBox(null); }}
              className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${selectedPresetKey === 'CDU_BYPASS' && !customImage ? 'bg-accent-cyan/20 text-accent-cyan font-bold border border-accent-cyan/40' : 'text-gray-400 hover:text-gray-200'}`}
            >
              CDU Bypass
            </button>
            <button
              onClick={() => { setSelectedPresetKey('PUMP_ISOLATION'); setCustomImage(null); setActiveBox(null); }}
              className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${selectedPresetKey === 'PUMP_ISOLATION' && !customImage ? 'bg-accent-cyan/20 text-accent-cyan font-bold border border-accent-cyan/40' : 'text-gray-400 hover:text-gray-200'}`}
            >
              Pump Manifold
            </button>
          </div>

          {/* Upload Button */}
          <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept="image/*" className="hidden" />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-1.5 bg-accent-emerald/10 border border-accent-emerald/30 text-accent-emerald hover:bg-accent-emerald/20 rounded-lg text-xs font-mono flex items-center transition-all shadow-[0_0_8px_rgba(16,185,129,0.1)]"
            title="Upload P&ID image"
          >
            <Upload className="w-3.5 h-3.5 mr-1.5" /> Upload
          </button>

          {/* Zoom Controls */}
          <div className="flex items-center space-x-1 bg-sovereign-dark rounded-lg p-1 border border-sovereign-border">
            <button onClick={() => setScale((s) => Math.max(0.5, s - 0.2))} className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded">
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="px-1.5 font-mono text-[11px] text-gray-300 min-w-[40px] text-center">{Math.round(scale * 100)}%</span>
            <button onClick={() => setScale((s) => Math.min(3, s + 0.2))} className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded">
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setScale(1)} className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded">
              <Maximize className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div className="flex-1 overflow-auto bg-[#05070a] relative flex items-center justify-center p-6 industrial-grid" style={{ backgroundImage: 'linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px)' }}>
        <div
          className="relative transition-transform duration-200 shadow-2xl rounded bg-slate-950 border border-slate-800"
          style={{ transform: `scale(${scale})`, width: '100%', maxWidth: '800px', aspectRatio: '4/3' }}
        >
          {customImage ? (
            <img src={customImage} alt="Uploaded P&ID" className="w-full h-full object-contain rounded" />
          ) : (
            currentPreset.svgContent
          )}

          {/* Render Bounding Box Overlays */}
          {boxesToRender.map((box) => {
            const isSelected = activeBox?.id === box.id;
            const borderColor = box.hazardStatus === 'OISD_VIOLATION' ? 'border-danger' : box.hazardStatus === 'WARNING' ? 'border-accent-amber' : 'border-accent-cyan';
            const bgColor = box.hazardStatus === 'OISD_VIOLATION' ? 'bg-danger/20' : box.hazardStatus === 'WARNING' ? 'bg-accent-amber/15' : 'bg-accent-cyan/15';

            return (
              <div
                key={box.id}
                onClick={() => setActiveBox(box)}
                className={`absolute border-2 rounded cursor-pointer transition-all duration-200 ${borderColor} ${bgColor} ${isSelected ? 'ring-2 ring-white z-20 scale-105 shadow-[0_0_15px_rgba(6,182,212,0.4)]' : 'hover:scale-102 hover:bg-opacity-30 z-10'}`}
                style={{ left: `${box.x}%`, top: `${box.y}%`, width: `${box.w}%`, height: `${box.h}%` }}
              >
                <div className="absolute -top-6 left-0 bg-sovereign-dark text-[10px] px-1.5 py-0.5 rounded border border-sovereign-border font-mono text-gray-200 whitespace-nowrap flex items-center shadow-md">
                  <span>{box.tag}</span>
                  <span className="ml-1 text-[9px] text-gray-400">({Math.round(box.confidence * 100)}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Inspector Details Tooltip / Drawer */}
      {activeBox && (
        <div className="p-4 bg-sovereign-dark border-t border-sovereign-border animate-in slide-in-from-bottom-2">
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-3">
              <span className="font-mono text-lg font-bold text-accent-cyan">{activeBox.tag}</span>
              <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${hazardBadges[activeBox.hazardStatus]}`}>
                {activeBox.hazardStatus.replace('_', ' ')}
              </span>
              <span className="text-xs font-mono text-gray-400 bg-sovereign-surface px-2 py-0.5 rounded border border-gray-700">
                YOLOv11s: {Math.round(activeBox.confidence * 100)}%
              </span>
            </div>
            <button onClick={() => setActiveBox(null)} className="text-xs text-gray-500 hover:text-gray-300 font-mono">
              Close ✕
            </button>
          </div>
          <p className="text-xs font-mono text-gray-300 mt-2 leading-relaxed bg-sovereign-surface p-2.5 rounded border border-sovereign-border">
            {activeBox.description}
          </p>
        </div>
      )}

      {/* Footer Legend */}
      <div className="p-3 border-t border-sovereign-border bg-sovereign-surface/90 flex justify-center space-x-6 text-xs text-gray-300 font-mono">
        <div className="flex items-center space-x-2"><div className="w-3 h-3 border border-accent-cyan bg-accent-cyan/20 rounded-sm"></div><span>VALVE / PUMP</span></div>
        <div className="flex items-center space-x-2"><div className="w-3 h-3 border border-accent-amber bg-accent-amber/20 rounded-sm"></div><span>WARNING (CHECK)</span></div>
        <div className="flex items-center space-x-2"><div className="w-3 h-3 border border-danger bg-danger/20 rounded-sm"></div><span>OISD VIOLATION</span></div>
      </div>
    </div>
  );
}
