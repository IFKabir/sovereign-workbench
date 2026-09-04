'use client';

import { useState, useRef, useEffect, ChangeEvent, DragEvent } from 'react';
import { ZoomIn, ZoomOut, Maximize, Layers, Upload, Scan, FileImage, X } from 'lucide-react';
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
  onDetectionsComplete?: (detections: DetectionBox[]) => void;
}

const hazardBadges: Record<string, string> = {
  NORMAL: 'bg-[#57692c] text-white border-[#8fb03e]',
  WARNING: 'bg-amber-900/60 text-amber-300 border-amber-500',
  OISD_VIOLATION: 'bg-red-950 text-red-300 border-red-500 animate-pulse',
};

export default function SchematicViewer({
  externalFile,
  externalImageSrc,
  onFileChange,
  onDetectionsComplete,
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
        formData.append('preset', 'CDU_BYPASS');
      }

      const res = await fetch('/api/v1/agent/schematic/detect', {
        method: 'POST',
        headers: getApiHeaders(),
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        const detList = data.detections || [];
        setDetections(detList);
        setAnalyzed(true);
        if (onDetectionsComplete) {
          onDetectionsComplete(detList);
        }
      }
    } catch (err) {
      console.error('YOLO analysis failed:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  // Pan / Drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
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
    <div className="bg-[#1a1a1a] flex flex-col h-full border-2 border-[#8fb03e] shadow-none relative select-none font-mono">
      {/* Top Header Bar */}
      <div className="p-3 bg-[#242424] border-b border-[#8fb03e] flex justify-between items-center flex-wrap gap-2 z-10">
        <div className="flex items-center space-x-3">
          <Layers className="w-5 h-5 text-[#8fb03e]" />
          <div>
            <h3 className="text-xs font-bold text-[#e8e8e8] tracking-wider uppercase">
              {file ? file.name : 'P&ID INSPECTOR WORKSPACE / पीएंडआईडी निरीक्षक'}
            </h3>
            <p className="text-[10px] text-[#c4c4c4]">
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
            className="px-3 py-1.5 bg-[#57692c] text-white border border-[#8fb03e] text-xs font-bold hover:bg-[#8fb03e] hover:text-[#1a1a1a] transition-all cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5 mr-1.5 inline text-white" /> SELECT P&ID / फ़ाइल चुनें
          </button>

          {imageSrc && (
            <button
              onClick={handleAnalyzeYOLO}
              disabled={analyzing}
              className="px-3 py-1.5 bg-[#57692c] text-white border border-[#8fb03e] text-xs font-bold hover:bg-[#8fb03e] hover:text-[#1a1a1a] transition-all disabled:opacity-50 cursor-pointer"
            >
              <Scan className={`w-3.5 h-3.5 mr-1.5 inline ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'ANALYZING...' : 'ANALYZE WITH YOLOv11s'}
            </button>
          )}

          {/* Pan / Zoom Controls */}
          {imageSrc && (
            <div className="flex items-center space-x-1 bg-[#1a1a1a] p-1 border border-[#8fb03e]">
              <button
                onClick={() => setScale((s) => Math.max(0.4, s - 0.2))}
                className="p-1 hover:bg-[#57692c] text-[#c4c4c4] hover:text-white"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="px-1.5 text-[11px] text-[#e8e8e8] min-w-[40px] text-center font-bold">
                {Math.round(scale * 100)}%
              </span>
              <button
                onClick={() => setScale((s) => Math.min(4, s + 0.2))}
                className="p-1 hover:bg-[#57692c] text-[#c4c4c4] hover:text-white"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button onClick={resetView} className="p-1 hover:bg-[#57692c] text-[#c4c4c4] hover:text-white" title="Reset View">
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
        className={`flex-1 overflow-hidden bg-[#121212] relative flex items-center justify-center p-6 industrial-grid ${
          isDragging ? 'cursor-grabbing' : imageSrc ? 'cursor-grab' : 'cursor-default'
        } ${isDragOver ? 'border-2 border-dashed border-[#8fb03e] bg-[#57692c]/10' : ''}`}
      >
        {imageSrc ? (
          <div
            className="relative transition-transform duration-75 border-2 border-[#8fb03e] bg-[#1a1a1a]"
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
              className="w-full h-full object-contain pointer-events-none"
            />

            {/* GIGW Specification: Solid Green Label Band along Bottom Edge */}
            <div className="absolute bottom-0 left-0 right-0 bg-[#57692c] border-t border-[#8fb03e] text-white px-3 py-1 text-[11px] font-bold uppercase tracking-wider flex justify-between items-center z-10">
              <span>{file ? file.name : 'SCHEMATIC DIAGRAM DRAWING'}</span>
              <span>ISA-5.1 COMPLIANCE CANVAS</span>
            </div>

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
                  ? 'border-red-500'
                  : box.hazard_status === 'WARNING'
                  ? 'border-amber-500'
                  : 'border-[#8fb03e]';
              const bgColor =
                box.hazard_status === 'OISD_VIOLATION'
                  ? 'bg-red-950/40'
                  : box.hazard_status === 'WARNING'
                  ? 'bg-amber-950/40'
                  : 'bg-[#57692c]/30';

              return (
                <div
                  key={idx}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveBox(box);
                  }}
                  className={`absolute border-2 cursor-pointer transition-all duration-150 ${borderColor} ${bgColor} ${
                    isSelected ? 'ring-2 ring-white z-20 scale-105' : 'hover:scale-102 z-10'
                  }`}
                  style={{
                    left: `${leftPct}%`,
                    top: `${topPct}%`,
                    width: `${widthPct}%`,
                    height: `${heightPct}%`,
                  }}
                >
                  <div className="absolute -top-6 left-0 bg-[#1a1a1a] text-[10px] px-1.5 py-0.5 border border-[#8fb03e] text-[#e8e8e8] font-bold whitespace-nowrap flex items-center shadow-none pointer-events-none">
                    <span>{box.tag || box.label}</span>
                    <span className="ml-1 text-[9px] text-[#8fb03e]">({Math.round(box.confidence * 100)}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Clean Industrial Empty State */
          <div className="text-center max-w-md p-8 bg-[#202020] border-2 border-[#8fb03e]">
            <div className="w-16 h-16 bg-[#57692c] border border-[#8fb03e] flex items-center justify-center mx-auto mb-4">
              <FileImage className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-sm font-bold text-[#e8e8e8] uppercase mb-2">
              Piping & Instrumentation Diagram (P&ID) Inspector
            </h3>
            <p className="text-xs text-[#c4c4c4] leading-relaxed mb-6">
              No active engineering schematic loaded. Upload a scanned or exported drawing (.png, .jpg, .webp, .svg, .pdf) to initiate ISA-5.1 symbol detection and safety compliance checks.
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-5 py-2.5 bg-[#57692c] text-white border-2 border-[#8fb03e] hover:bg-[#8fb03e] hover:text-[#1a1a1a] text-xs font-bold inline-flex items-center transition-all cursor-pointer"
            >
              <Upload className="w-4 h-4 mr-2" /> SELECT P&ID DRAWING / फ़ाइल का चयन करें
            </button>
          </div>
        )}
      </div>

      {/* Inference Status / 0 Detections Bar */}
      {analyzing && (
        <div className="p-2.5 bg-[#1a1a1a] border-t border-[#8fb03e] text-center text-xs text-[#8fb03e] font-bold flex items-center justify-center space-x-2">
          <Scan className="w-4 h-4 animate-spin" />
          <span>RUNNING YOLOv11s INFERENCE ON LOCAL GPU/CPU...</span>
        </div>
      )}

      {analyzed && !analyzing && detections.length === 0 && (
        <div className="p-2.5 bg-[#1a1a1a] border-t border-[#8fb03e] text-center text-xs text-[#c4c4c4]">
          0 ISA-5.1 symbols detected in this drawing.
        </div>
      )}

      {/* Component Inspection Drawer */}
      {activeBox && (
        <div className="p-4 bg-[#242424] border-t-2 border-[#8fb03e]">
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-3 flex-wrap gap-2">
              <span className="text-sm font-bold text-[#8fb03e]">{activeBox.tag || activeBox.label}</span>
              <span
                className={`px-2 py-0.5 text-[10px] font-bold border ${
                  hazardBadges[activeBox.hazard_status || 'NORMAL'] || hazardBadges.NORMAL
                }`}
              >
                {(activeBox.hazard_status || 'NORMAL').replace('_', ' ')}
              </span>
              <span className="text-xs text-[#c4c4c4] bg-[#1a1a1a] px-2 py-0.5 border border-neutral-700">
                Confidence: {Math.round(activeBox.confidence * 100)}%
              </span>
              <span className="text-xs text-[#c4c4c4]">Category: {activeBox.category || 'EQUIPMENT'}</span>
              <span className="text-xs text-neutral-500">
                Bounds: [{activeBox.bbox_normalized.y_center.toFixed(2)}, {activeBox.bbox_normalized.x_center.toFixed(2)}]
              </span>
            </div>
            <button onClick={() => setActiveBox(null)} className="text-xs text-neutral-400 hover:text-white font-bold">
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-[#e8e8e8] mt-2 leading-relaxed bg-[#1a1a1a] p-2.5 border border-[#8fb03e]">
            {activeBox.description}
          </p>
        </div>
      )}

      {/* Footer Status */}
      <div className="p-2 bg-[#242424] border-t border-[#8fb03e] flex justify-between items-center px-4 text-xs text-[#c4c4c4]">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 border border-[#8fb03e] bg-[#57692c]" />
            <span>NORMAL EQUIPMENT</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 border border-amber-500 bg-amber-900/60" />
            <span>WARNING</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 border border-red-500 bg-red-950" />
            <span>OISD VIOLATION</span>
          </div>
        </div>

        <div className="text-[11px] text-[#8fb03e] font-bold">
          {analyzed ? `${detections.length} ISA-5.1 SYMBOLS DETECTED BY YOLOv11s` : 'CLICK "ANALYZE WITH YOLOv11s" TO RUN INFERENCE'}
        </div>
      </div>
    </div>
  );
}
