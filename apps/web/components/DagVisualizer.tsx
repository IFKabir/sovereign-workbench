'use client';
import { useCallback, useState } from 'react';
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState, Handle, Position } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Server, ShieldCheck, FileText, Database, UserCheck, Zap, Activity } from 'lucide-react';

const AgentNode = ({ data, isConnectable }: any) => {
  const Icon = data.icon;
  return (
    <div className={`glass-panel p-4 rounded-xl border-2 w-56 bg-sovereign-surface/90 backdrop-blur-xl transition-all ${data.active ? 'border-accent-cyan shadow-[0_0_20px_rgba(6,182,212,0.3)] scale-105' : 'border-sovereign-border'}`}>
      <Handle type="target" position={Position.Top} isConnectable={isConnectable} className="!w-3 !h-3 !bg-gray-600 !border-2 !border-sovereign-dark" />
      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 rounded-lg ${data.active ? 'bg-accent-cyan/20 text-accent-cyan shadow-inner' : 'bg-gray-800/50 text-gray-400'}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className={`text-[9px] px-2 py-1 rounded-md uppercase font-bold tracking-widest ${data.status === 'completed' ? 'bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20' : data.status === 'active' ? 'bg-accent-amber/10 text-accent-amber border border-accent-amber/20 animate-pulse' : 'bg-gray-800 text-gray-500 border border-gray-700'}`}>
          {data.status}
        </span>
      </div>
      <h4 className="font-mono text-sm font-bold text-gray-100 mb-1">{data.label}</h4>
      <div className="mt-3 pt-3 border-t border-sovereign-border flex justify-between items-center text-[10px] font-mono">
        <span className="text-gray-400 flex items-center"><Database className="w-3 h-3 mr-1"/> {data.tokens} tkns</span>
        <span className="text-gray-400 flex items-center"><Activity className="w-3 h-3 mr-1"/> {data.time}ms</span>
      </div>
      <Handle type="source" position={Position.Bottom} isConnectable={isConnectable} className="!w-3 !h-3 !bg-gray-600 !border-2 !border-sovereign-dark" />
    </div>
  );
};

const nodeTypes = { agentNode: AgentNode };

const initialNodes = [
  { id: '1', type: 'agentNode', position: { x: 300, y: 50 }, data: { label: 'InputClassifier', icon: Zap, status: 'completed', active: false, tokens: 124, time: 45 } },
  { id: '2', type: 'agentNode', position: { x: 100, y: 220 }, data: { label: 'PIDAnalyzer', icon: Activity, status: 'completed', active: false, tokens: 856, time: 1205 } },
  { id: '3', type: 'agentNode', position: { x: 500, y: 220 }, data: { label: 'RAGRetriever', icon: Database, status: 'completed', active: false, tokens: 412, time: 310 } },
  { id: '4', type: 'agentNode', position: { x: 300, y: 390 }, data: { label: 'ComplianceAuditor', icon: FileText, status: 'active', active: true, tokens: 1024, time: 800 } },
  { id: '5', type: 'agentNode', position: { x: 300, y: 560 }, data: { label: 'HITLGate', icon: UserCheck, status: 'idle', active: false, tokens: 0, time: 0 } },
  { id: '6', type: 'agentNode', position: { x: 300, y: 730 }, data: { label: 'ResponseGenerator', icon: Server, status: 'idle', active: false, tokens: 0, time: 0 } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: false, style: { stroke: '#10b981', strokeWidth: 2 } },
  { id: 'e1-3', source: '1', target: '3', animated: false, style: { stroke: '#10b981', strokeWidth: 2 } },
  { id: 'e2-4', source: '2', target: '4', animated: true, style: { stroke: '#06b6d4', strokeWidth: 3 } },
  { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: '#06b6d4', strokeWidth: 3 } },
  { id: 'e4-5', source: '4', target: '5', animated: false, style: { stroke: '#374151', strokeWidth: 2 } },
  { id: 'e5-6', source: '5', target: '6', animated: false, style: { stroke: '#374151', strokeWidth: 2 } },
];

export default function DagVisualizer() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="w-full h-full min-h-[700px] glass-panel rounded-2xl overflow-hidden border border-sovereign-border relative shadow-xl">
      <div className="absolute top-6 left-6 z-10 glass-panel px-4 py-2.5 rounded-lg border border-accent-emerald/30 bg-accent-emerald/5 flex items-center space-x-3 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
        <ShieldCheck className="w-5 h-5 text-accent-emerald" />
        <span className="font-mono text-sm font-semibold text-gray-200">Chain Verification: <span className="text-accent-emerald tracking-wide">SECURE</span></span>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        className="bg-[#05070a]"
      >
        <Background color="#1f2937" gap={20} size={1} />
        <Controls className="!bg-sovereign-surface !border-sovereign-border !fill-white !rounded-lg !overflow-hidden shadow-lg" />
        <MiniMap 
          nodeColor="#374151" 
          maskColor="rgba(5, 7, 10, 0.7)" 
          className="!bg-sovereign-surface !border !border-sovereign-border !rounded-xl" 
        />
      </ReactFlow>
    </div>
  );
}
