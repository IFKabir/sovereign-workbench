'use client';
import { useState } from 'react';
import { Send, Upload, Bot, User, Cpu } from 'lucide-react';
import SchematicViewer from '@/components/SchematicViewer';
import HitlApprovalModal from '@/components/HitlApprovalModal';

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Sovereign Workbench initialized. Ready for air-gapped P&ID analysis and compliance checks. Please upload a schematic or ask a question.', model: 'Llama-3-70B-Instruct', tokens: 24 }
  ]);
  const [input, setInput] = useState('');
  const [showHitl, setShowHitl] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, { role: 'user', content: input, model: '', tokens: 0 }]);
    setInput('');
    
    // Simulate processing that triggers HITL
    setTimeout(() => {
       setShowHitl(true);
    }, 1500);
  };

  return (
    <div className="h-full flex gap-6 p-6">
      <div className="flex-1 flex flex-col glass-panel rounded-xl border border-sovereign-border overflow-hidden">
        <div className="p-4 border-b border-sovereign-border bg-sovereign-surface/50 flex justify-between items-center">
          <h2 className="font-mono font-bold text-gray-200 text-sm">Terminal // Chat Interaction</h2>
          <span className="flex items-center text-xs font-mono text-accent-emerald bg-accent-emerald/10 px-2 py-1 rounded border border-accent-emerald/20">
            <span className="w-2 h-2 rounded-full bg-accent-emerald mr-2 animate-pulse"></span>
            Agent Ready
          </span>
        </div>
        
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`flex items-center space-x-3 mb-2 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                <div className={`p-2 rounded-md ${msg.role === 'user' ? 'bg-accent-cyan/20 text-accent-cyan' : 'bg-accent-amber/20 text-accent-amber'}`}>
                  {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">{msg.role}</span>
                {msg.model && <span className="text-xs font-mono bg-sovereign-border px-2 py-1 rounded text-gray-400 flex items-center border border-gray-700"><Cpu className="w-3 h-3 mr-1.5"/> {msg.model}</span>}
              </div>
              <div className={`max-w-[85%] p-4 rounded-xl text-sm leading-relaxed shadow-sm ${msg.role === 'user' ? 'bg-accent-cyan/10 border border-accent-cyan/20 text-gray-200' : 'bg-sovereign-surface border border-sovereign-border text-gray-300 font-mono'}`}>
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 bg-sovereign-surface/80 border-t border-sovereign-border flex items-end space-x-3">
          <button className="p-3.5 bg-sovereign-dark border border-sovereign-border rounded-xl hover:border-accent-cyan text-gray-400 hover:text-accent-cyan transition-colors group relative">
            <Upload className="w-5 h-5 group-hover:scale-110 transition-transform" />
            <span className="absolute -top-10 left-1/2 -translate-x-1/2 bg-sovereign-border text-xs text-gray-200 px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">Upload P&ID</span>
          </button>
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="Query schematics, ask about compliance..."
            className="flex-1 bg-sovereign-dark border border-sovereign-border rounded-xl p-3.5 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 resize-none transition-all shadow-inner"
            rows={1}
          />
          <button onClick={handleSend} className="p-3.5 bg-accent-cyan/20 border border-accent-cyan/50 text-accent-cyan rounded-xl hover:bg-accent-cyan/30 transition-colors shadow-[0_0_10px_rgba(6,182,212,0.1)] hover:shadow-[0_0_15px_rgba(6,182,212,0.2)]">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="w-5/12 hidden lg:block">
        <SchematicViewer />
      </div>

      <HitlApprovalModal 
        isOpen={showHitl} 
        onClose={() => setShowHitl(false)}
        actionType="MODIFY_VALVE_PARAMETER"
        riskLevel="HIGH"
        draftContent="Execute configuration change on V-101. Set target pressure threshold to 150 PSI."
        complianceFlags={["Exceeds standard operating threshold (120 PSI)", "Requires L3 Supervisor Approval"]}
        requiredRole="L3_SUPERVISOR"
      />
    </div>
  );
}
