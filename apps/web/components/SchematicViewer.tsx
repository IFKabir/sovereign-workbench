'use client';

import { useState, useRef, useEffect, ChangeEvent, DragEvent } from 'react';
import { ZoomIn, ZoomOut, Maximize, Layers, Upload, Scan, FileImage, AlertTriangle, ShieldCheck, X } from 'lucide-react';
import { getApiHeaders } from '@/lib/session';

export interface DetectionBox {
  class_id: number;
  label: string;
  tag: string;
  confidence: number;
  category: 'VALVE' | 'PUMP' | 'SENSOR' | 'TANK' | 'VESSEL' | string;
  hazard_status: 'NORMAL' | 'WARNING' | 'OISD_VIOLATION' | string;
  description: string;
  bbox_normalized: {
    x_center: number;
    y_center: number;
    width: number;
    height: number;
  };
}

interface SchematicViewerProps {
  externalFile?: File | null;
  externalImageSrc?: string | null;
  onFileChange?: (file: File | null, src: string | null) => void;
}

const hazardBadges: Record<string, string> = {
  NORMAL: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30',
  WARNING: 'bg-accent-amber/10 text-accent-amber border-accent-amber/30',
  OISD_VIOLATION: 'bg-danger/10 text-danger border-danger/30 animate-pulse',
};

export default function SchematicViewer({
  externalFile,
  externalImageSrc,
  onFileChange,
}: SchematicViewerProps) {
  const [file, setFile] = useState<File | null>(externalFile || null);
  const [imageSrc, setImageSrc] = useState<string | null>(externalImageSrc || null);
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const [activeBox, setActiveBox] = useState<DetectionBox | null>(null);
  const [detections, setDetections] = useState<DetectionBox[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Sync external file/src if passed from Chat component
  useEffect(() => {
    if (externalFile || externalImageSrc) {
      setFile(externalFile || null);
      setImageSrc(externalImageSrc || null);
      setActiveBox(null);
      setDetections([]);
      setAnalyzed(false);
      setScale(1);
      setPan({ x: 0, y: 0 });
    }
  }, [externalFile, externalImageSrc]);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    const reader = new FileReader();
    reader.onload = (event) => {
      const src = event.target?.result as string;
      setImageSrc(src);
      setActiveBox(null);
      setDetections([]);
      setAnalyzed(false);
      setScale(1);
      setPan({ x: 0, y: 0 });
      if (onFileChange) {
        onFileChange(selectedFile, src);
      }
    };
    reader.readAsDataURL(selectedFile);
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      handleFileSelect(selected);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      handleFileSelect(dropped);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleAnalyzeYOLO = async () => {
    if (!file && !imageSrc) return;
    setAnalyzing(true);
    setActiveBox(null);

    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      } else {
        // Preset sample image fallback
        formData.append('preset', 'CDU_BYPASS');
      }

      const res = await fetch('/api/v1/agent/schematic/detect', {
        method: 'POST',
        headers: getApiHeaders(),
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setDetections(data.detections || []);
        setAnalyzed(true);
      }
    } catch (err) {
      console.error('YOLO analysis failed:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  // Pan / Drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Left mouse button only
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetView = () => {
    setScale(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="glass-panel flex flex-col h-full rounded-xl overflow-hidden border border-sovereign-border shadow-lg relative select-none">
      {/* Top Header Bar */}
      <div className="p-3.5 border-b border-sovereign-border flex justify-between items-center bg-sovereign-surface/80 flex-wrap gap-2 z-10">
        <div className="flex items-center space-x-3">
          <Layers className="w-5 h-5 text-accent-cyan" />
          <div>
            <h3 className="font-mono text-sm font-bold text-gray-200">
              {file ? file.name : 'P&ID Inspector Workspace'}
            </h3>
            <p className="text-[11px] text-gray-400 font-mono">
              {file
                ? `Size: ${(file.size / 1024).toFixed(1)} KB — Scanned Raster/Vector Drawing`
                : 'ISA-5.1 Symbol Detection & Safety Compliance Canvas'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileInputChange}
            accept="image/*,.pdf"
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1.5 bg-sovereign-dark border border-sovereign-border text-gray-300 hover:text-white rounded-lg text-xs font-mono flex items-center transition-all"
          >
            <Upload className="w-3.5 h-3.5 mr-1.5 text-accent-cyan" /> Select P&ID
          </button>

          {imageSrc && (
            <button
              onClick={handleAnalyzeYOLO}
              disabled={analyzing}
              className="px-3 py-1.5 bg-gradient-to-r from-accent-cyan/20 to-accent-emerald/20 text-accent-cyan border border-accent-cyan/40 hover:bg-accent-cyan/30 rounded-lg text-xs font-mono font-bold flex items-center transition-all shadow-[0_0_10px_rgba(6,182,212,0.15)] disabled:opacity-50"
            >
              <Scan className={`w-3.5 h-3.5 mr-1.5 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'Analyzing...' : 'Analyze P&ID with YOLOv11s'}
            </button>
          )}

          {/* Pan / Zoom Controls */}
          {imageSrc && (
            <div className="flex items-center space-x-1 bg-sovereign-dark rounded-lg p-1 border border-sovereign-border">
              <button
                onClick={() => setScale((s) => Math.max(0.4, s - 0.2))}
                className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="px-1.5 font-mono text-[11px] text-gray-300 min-w-[40px] text-center">
                {Math.round(scale * 100)}%
              </span>
              <button
                onClick={() => setScale((s) => Math.min(4, s + 0.2))}
                className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button onClick={resetView} className="p-1 hover:bg-sovereign-surface text-gray-400 hover:text-white rounded" title="Reset View">
                <Maximize className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Viewport Container */}
      <div
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`flex-1 overflow-hidden bg-[#05070a] relative flex items-center justify-center p-6 industrial-grid ${
          isDragging ? 'cursor-grabbing' : imageSrc ? 'cursor-grab' : 'cursor-default'
        } ${isDragOver ? 'border-2 border-dashed border-accent-cyan bg-accent-cyan/5' : ''}`}
      >
        {imageSrc ? (
          <div
            className="relative transition-transform duration-75 shadow-2xl rounded bg-slate-950 border border-slate-800"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
              maxWidth: '100%',
              maxHeight: '100%',
              aspectRatio: '4/3',
            }}
          >
            {/* Real Graphic Image Render */}
            <img
              src={imageSrc}
              alt="P&ID Diagram"
              className="w-full h-full object-contain rounded pointer-events-none"
            />

            {/* Dynamic YOLO Overlay Bounding Boxes */}
            {detections.map((box, idx) => {
              const { x_center, y_center, width, height } = box.bbox_normalized;
              const leftPct = (x_center - width / 2) * 100;
              const topPct = (y_center - height / 2) * 100;
              const widthPct = width * 100;
              const heightPct = height * 100;

              const isSelected = activeBox?.tag === box.tag && activeBox?.label === box.label;
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
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveBox(box);
                  }}
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
                  <div className="absolute -top-6 left-0 bg-sovereign-dark text-[10px] px-1.5 py-0.5 rounded border border-sovereign-border font-mono text-gray-200 whitespace-nowrap flex items-center shadow-md pointer-events-none">
                    <span>{box.tag || box.label}</span>
                    <span className="ml-1 text-[9px] text-gray-400">({Math.round(box.confidence * 100)}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Clean Industrial Empty State */
          <div className="text-center max-w-md p-8 rounded-2xl glass-panel border border-sovereign-border shadow-xl">
            <div className="w-16 h-16 rounded-2xl bg-accent-cyan/10 border border-accent-cyan/20 flex items-center justify-center mx-auto mb-4">
              <FileImage className="w-8 h-8 text-accent-cyan" />
            </div>
            <h3 className="text-base font-bold text-gray-100 mb-2">
              Piping & Instrumentation Diagram (P&ID) Inspector
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed font-mono mb-6">
              No active engineering schematic loaded. Upload a scanned or exported drawing (.png, .jpg, .webp, .svg, .pdf) to initiate ISA-5.1 symbol detection and safety compliance checks.
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-5 py-2.5 bg-gradient-to-r from-accent-cyan/20 to-accent-emerald/20 text-accent-cyan border border-accent-cyan/40 hover:bg-accent-cyan/30 rounded-xl text-xs font-mono font-bold inline-flex items-center transition-all shadow-[0_0_15px_rgba(6,182,212,0.15)]"
            >
              <Upload className="w-4 h-4 mr-2" /> Select P&ID Drawing
            </button>
          </div>
        )}
      </div>

      {/* Inference Status / 0 Detections Bar */}
      {analyzing && (
        <div className="p-3 bg-sovereign-dark border-t border-sovereign-border text-center text-xs text-accent-cyan font-mono flex items-center justify-center space-x-2">
          <Scan className="w-4 h-4 animate-spin" />
          <span>Running YOLOv11s inference on local GPU/CPU...</span>
        </div>
      )}

      {analyzed && !analyzing && detections.length === 0 && (
        <div className="p-3 bg-sovereign-dark border-t border-sovereign-border text-center text-xs text-gray-400 font-mono">
          0 ISA-5.1 symbols detected in this drawing.
        </div>
      )}

      {/* Component Inspection Drawer */}
      {activeBox && (
        <div className="p-4 bg-sovereign-dark border-t border-sovereign-border">
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-3 flex-wrap gap-2">
              <span className="font-mono text-base font-bold text-accent-cyan">{activeBox.tag || activeBox.label}</span>
              <span
                className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${
                  hazardBadges[activeBox.hazard_status || 'NORMAL'] || hazardBadges.NORMAL
                }`}
              >
                {(activeBox.hazard_status || 'NORMAL').replace('_', ' ')}
              </span>
              <span className="text-xs font-mono text-gray-400 bg-sovereign-surface px-2 py-0.5 rounded border border-gray-700">
                Confidence: {Math.round(activeBox.confidence * 100)}%
              </span>
              <span className="text-xs font-mono text-gray-400">ISA-5.1 Category: {activeBox.category || 'EQUIPMENT'}</span>
              <span className="text-xs font-mono text-gray-500">
                Bounds: [{activeBox.bbox_normalized.y_center.toFixed(2)}, {activeBox.bbox_normalized.x_center.toFixed(2)}]
              </span>
            </div>
            <button onClick={() => setActiveBox(null)} className="text-xs text-gray-500 hover:text-gray-300 font-mono">
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs font-mono text-gray-300 mt-2 leading-relaxed bg-sovereign-surface p-2.5 rounded border border-sovereign-border">
            {activeBox.description}
          </p>
        </div>
      )}

      {/* Footer Status */}
      <div className="p-2.5 border-t border-sovereign-border bg-sovereign-surface/90 flex justify-between items-center px-6 text-xs text-gray-400 font-mono">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 border border-accent-cyan bg-accent-cyan/20 rounded-sm" />
            <span>NORMAL EQUIPMENT</span>
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
