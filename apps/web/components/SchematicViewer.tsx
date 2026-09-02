'use client';

import { useState, useRef, ChangeEvent } from 'react';
import { ZoomIn, ZoomOut, Maximize, Layers, Upload, Scan, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import { getApiHeaders } from '@/lib/session';

export interface DetectionBox {
  class_id: number;
  label: string;
  tag: string;
  confidence: number;
  category: 'VALVE' | 'PUMP' | 'SENSOR' | 'TANK' | 'VESSEL';
  hazard_status: 'NORMAL' | 'WARNING' | 'OISD_VIOLATION';
  description: string;
  bbox_normalized: {
    x_center: number;
    y_center: number;
    width: number;
    height: number;
  };
}

const PRESETS = [
  {
    id: 'CDU_BYPASS',
    title: 'CDU-2 Control Valve Bypass Line',
    description: 'Real technical piping layout for Crude Distillation Unit CV-101 bypass line',
    image: '/schematics/cdu_bypass_line.png',
  },
  {
    id: 'PUMP_ISOLATION',
    title: 'P-201A/B Pump Isolation Manifold',
    description: 'Real technical drawing for centrifugal pump suction & discharge manifold',
    image: '/schematics/pump_manifold_system.png',
  },
];

const hazardBadges = {
  NORMAL: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30',
  WARNING: 'bg-accent-amber/10 text-accent-amber border-accent-amber/30',
  OISD_VIOLATION: 'bg-danger/10 text-danger border-danger/30 animate-pulse',
};

export default function SchematicViewer() {
  const [selectedPresetId, setSelectedPresetId] = useState<string>('CDU_BYPASS');
  const [scale, setScale] = useState(1);
  const [activeBox, setActiveBox] = useState<DetectionBox | null>(null);
  const [customImage, setCustomImage] = useState<string | null>(null);
  const [customFile, setCustomFile] = useState<File | null>(null);
  const [detections, setDetections] = useState<DetectionBox[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const currentPreset = PRESETS.find((p) => p.id === selectedPresetId) || PRESETS[0];
  const activeImageSrc = customImage || currentPreset.image;

  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCustomFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setCustomImage(event.target?.result as string);
        setActiveBox(null);
        setDetections([]);
        setAnalyzed(false);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyzeYOLO = async () => {
    setAnalyzing(true);
    setActiveBox(null);
    try {
      const formData = new FormData();
      if (customFile) {
        formData.append('file', customFile);
      } else {
        formData.append('preset', selectedPresetId);
      }

      const res = await fetch('/api/v1/agent/schematic/detect', {
        method: 'POST',
        headers: getApiHeaders(),
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        const rawBoxes = data.detections || [];
        setDetections(rawBoxes);
        setAnalyzed(true);
      }
    } catch (err) {
      console.error('YOLO analysis failed:', err);
    } finally {
      setAnalyzing(false);
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
              {customImage ? 'Custom Uploaded Engineering Drawing' : currentPreset.title}
            </h3>
            <p className="text-[11px] text-gray-400 font-mono">
              {customImage ? 'User Uploaded P&ID' : currentPreset.description}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Preset Selectors */}
          <div className="flex bg-sovereign-dark rounded-lg p-1 border border-sovereign-border space-x-1">
            {PRESETS.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setSelectedPresetId(p.id);
                  setCustomImage(null);
                  setCustomFile(null);
                  setActiveBox(null);
                  setDetections([]);
                  setAnalyzed(false);
                }}
                className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${
                  selectedPresetId === p.id && !customImage
                    ? 'bg-accent-cyan/20 text-accent-cyan font-bold border border-accent-cyan/40'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {p.id === 'CDU_BYPASS' ? 'CDU Bypass' : 'Pump Manifold'}
              </button>
            ))}
          </div>

          {/* Upload Button */}
          <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept="image/*,.pdf" className="hidden" />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-1.5 bg-sovereign-dark border border-sovereign-border text-gray-300 hover:text-white rounded-lg text-xs font-mono flex items-center transition-all"
            title="Upload P&ID image"
          >
            <Upload className="w-3.5 h-3.5 mr-1.5" /> Upload P&ID
          </button>

          {/* Analyze YOLO Button */}
          <button
            onClick={handleAnalyzeYOLO}
            disabled={analyzing}
            className="px-3 py-1.5 bg-gradient-to-r from-accent-cyan/20 to-accent-emerald/20 text-accent-cyan border border-accent-cyan/40 hover:bg-accent-cyan/30 rounded-lg text-xs font-mono font-bold flex items-center transition-all shadow-[0_0_10px_rgba(6,182,212,0.15)] disabled:opacity-50"
          >
            <Scan className={`w-3.5 h-3.5 mr-1.5 ${analyzing ? 'animate-spin' : ''}`} />
            {analyzing ? 'Analyzing...' : 'Analyze P&ID with YOLOv11s'}
          </button>

          {/* Zoom Controls */}
          <div className="flex items-center space-x-1 bg-sovereign-dark rounded-lg p-1 border border-sovereign-border">
            <button
              onClick={() => setScale((s) => Math.max(0.5, s - 0.2))}
              className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="px-1.5 font-mono text-[11px] text-gray-300 min-w-[40px] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={() => setScale((s) => Math.min(3, s + 0.2))}
              className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setScale(1)} className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded">
              <Maximize className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Pan / Zoom Viewport */}
      <div className="flex-1 overflow-auto bg-[#05070a] relative flex items-center justify-center p-6 industrial-grid">
        <div
          className="relative transition-transform duration-200 shadow-2xl rounded bg-slate-950 border border-slate-800"
          style={{ transform: `scale(${scale})`, width: '100%', maxWidth: '1000px', aspectRatio: '4/3' }}
        >
          {/* Genuine Technical P&ID Image */}
          <img
            src={activeImageSrc}
            alt="P&ID Diagram"
            className="w-full h-full object-contain rounded select-none"
          />

          {/* Dynamic YOLO Overlay Bounding Boxes */}
          {detections.map((box, idx) => {
            const { x_center, y_center, width, height } = box.bbox_normalized;
            const leftPct = (x_center - width / 2) * 100;
            const topPct = (y_center - height / 2) * 100;
            const widthPct = width * 100;
            const heightPct = height * 100;

            const isSelected = activeBox?.tag === box.tag;
            const borderColor =
              box.hazard_status === 'OISD_VIOLATION'
                ? 'border-danger'
                : box.hazard_status === 'WARNING'
                ? 'border-accent-amber'
                : 'border-accent-cyan';
            const bgColor =
              box.hazard_status === 'OISD_VIOLATION'
                ? 'bg-danger/20'
                : box.hazard_status === 'WARNING'
                ? 'bg-accent-amber/15'
                : 'bg-accent-cyan/15';

            return (
              <div
                key={idx}
                onClick={() => setActiveBox(box)}
                className={`absolute border-2 rounded cursor-pointer transition-all duration-200 ${borderColor} ${bgColor} ${
                  isSelected
                    ? 'ring-2 ring-white z-20 scale-105 shadow-[0_0_15px_rgba(6,182,212,0.4)]'
                    : 'hover:scale-102 hover:bg-opacity-30 z-10'
                }`}
                style={{
                  left: `${leftPct}%`,
                  top: `${topPct}%`,
                  width: `${widthPct}%`,
                  height: `${heightPct}%`,
                }}
              >
                <div className="absolute -top-6 left-0 bg-sovereign-dark text-[10px] px-1.5 py-0.5 rounded border border-sovereign-border font-mono text-gray-200 whitespace-nowrap flex items-center shadow-md">
                  <span>{box.tag || box.label}</span>
                  <span className="ml-1 text-[9px] text-gray-400">({Math.round(box.confidence * 100)}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* No Symbols Message */}
      {analyzed && detections.length === 0 && (
        <div className="p-3 bg-sovereign-dark border-t border-sovereign-border text-center text-xs text-gray-400 font-mono">
          No ISA-5.1 symbols detected in this region.
        </div>
      )}

      {/* Interactive Inspection Tooltip / Drawer */}
      {activeBox && (
        <div className="p-4 bg-sovereign-dark border-t border-sovereign-border">
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-3">
              <span className="font-mono text-lg font-bold text-accent-cyan">{activeBox.tag || activeBox.label}</span>
              <span
                className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${
                  hazardBadges[activeBox.hazard_status || 'NORMAL']
                }`}
              >
                {(activeBox.hazard_status || 'NORMAL').replace('_', ' ')}
              </span>
              <span className="text-xs font-mono text-gray-400 bg-sovereign-surface px-2 py-0.5 rounded border border-gray-700">
                YOLOv11s: {Math.round(activeBox.confidence * 100)}% confidence
              </span>
              <span className="text-xs font-mono text-gray-400">Category: {activeBox.category || 'ISA-5.1'}</span>
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

      {/* Footer Status Bar */}
      <div className="p-3 border-t border-sovereign-border bg-sovereign-surface/90 flex justify-between items-center px-6 text-xs text-gray-400 font-mono">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 border border-accent-cyan bg-accent-cyan/20 rounded-sm" />
            <span>NORMAL SYMBOL</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 border border-accent-amber bg-accent-amber/20 rounded-sm" />
            <span>WARNING</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 border border-danger bg-danger/20 rounded-sm" />
            <span>OISD VIOLATION</span>
          </div>
        </div>

        <div className="text-[11px] text-gray-500">
          {analyzed ? `${detections.length} ISA-5.1 symbols detected by YOLOv11s` : 'Click "Analyze P&ID with YOLOv11s" to run inference'}
        </div>
      </div>
    </div>
  );
}
