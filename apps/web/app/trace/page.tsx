'use client';
import DagVisualizer from '@/components/DagVisualizer';
import { Route } from 'lucide-react';

export default function TracePage() {
  return (
    <div className="h-full flex flex-col p-8 max-w-[1600px] mx-auto w-full">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 flex items-center">
            <Route className="mr-3 w-8 h-8 text-accent-cyan" /> Execution Trace
          </h1>
          <p className="text-sm text-gray-400 mt-2 font-mono">Real-time inspection of multi-agent reasoning paths</p>
        </div>
        <select className="bg-sovereign-surface border border-sovereign-border text-gray-200 text-sm font-mono rounded-xl px-4 py-3 focus:ring-1 focus:ring-accent-cyan focus:border-accent-cyan block outline-none min-w-[250px] shadow-sm cursor-pointer">
          <option>Task: PID-Extraction-994</option>
          <option>Task: Compliance-Check-993</option>
          <option>Task: RAG-Query-992</option>
        </select>
      </div>
      
      <div className="flex-1 min-h-0 relative">
        <DagVisualizer />
      </div>
    </div>
  );
}
