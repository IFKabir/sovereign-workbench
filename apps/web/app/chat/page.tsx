'use client';
import { useState, useEffect } from 'react';
import { Send, Upload, Bot, User, Cpu, Loader2 } from 'lucide-react';
import SchematicViewer from '@/components/SchematicViewer';
import HitlApprovalModal, { RiskLevel } from '@/components/HitlApprovalModal';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  tokens?: number;
}

interface HitlData {
  actionType: string;
  riskLevel: RiskLevel;
  draftContent: string;
  complianceFlags: string[];
  requiredRole: string;
  threadId: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Sovereign Workbench initialized. Ready for air-gapped P&ID analysis, OISD compliance standards lookup, and calculations. Ask a question or submit an operational query.',
      model: 'Qwen2.5-VL-7B-Instruct',
      tokens: 24,
    },
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [threadId, setThreadId] = useState<string>('');
  const [showHitl, setShowHitl] = useState(false);
  const [hitlData, setHitlData] = useState<HitlData | null>(null);

  useEffect(() => {
    // Generate isolated thread_id per session to prevent checkpointer crosstalk
    if (typeof window !== 'undefined') {
      setThreadId(crypto.randomUUID());
    }
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userQuery = input.trim();
    const activeThreadId = threadId || crypto.randomUUID();
    if (!threadId) setThreadId(activeThreadId);

    setMessages((prev) => [...prev, { role: 'user', content: userQuery, model: '', tokens: 0 }]);
    setInput('');
    setIsProcessing(true);

    try {
      const response = await fetch('/api/v1/agent/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          user_id: 'op-user-01',
          role: 'OPERATOR',
          thread_id: activeThreadId,
        }),
      });

      if (!response.ok) {
        const errorMsg = await response.text().catch(() => '');
        throw new Error(`Server returned HTTP ${response.status}: ${errorMsg.slice(0, 80)}`);
      }

      if (!response.body) {
        throw new Error('No response body stream received');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantText = '';
      let hitlTriggered = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const rawData = line.slice(6).trim();
            if (rawData === '{"event_type": "done"}' || rawData === '[DONE]') {
              break;
            }
            try {
              const parsed = JSON.parse(rawData);

              if (parsed.event_type === 'hitl_required' && parsed.requires_approval) {
                hitlTriggered = true;
                const d = parsed.data || {};
                setHitlData({
                  actionType: d.action_type || 'SAFETY_CRITICAL_MODIFICATION',
                  riskLevel: (d.risk_level as RiskLevel) || 'HIGH',
                  draftContent: d.draft_content || `Action requested in thread ${activeThreadId} requires Human-in-the-Loop review.`,
                  complianceFlags: d.compliance_flags || ['Safety-critical procedure flagged'],
                  requiredRole: d.required_role || 'SAFETY_OFFICER',
                  threadId: parsed.thread_id || activeThreadId,
                });
                setShowHitl(true);
                setMessages((prev) => [
                  ...prev,
                  {
                    role: 'assistant',
                    content: '⚠️ Safety-critical operation requested. Execution paused pending Human-in-the-Loop approval from a Safety Officer.',
                    model: 'Compliance-Auditor',
                  },
                ]);
              } else if (parsed.event_type === 'response' && parsed.data?.content) {
                assistantText = parsed.data.content;
              } else if (parsed.event_type === 'node_complete' && parsed.data?.final_response) {
                assistantText = parsed.data.final_response;
              }
            } catch (err) {
              // Non-JSON line or chunk boundary fragment
            }
          }
        }
      }

      if (!hitlTriggered && assistantText) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: assistantText,
            model: 'Qwen2.5-VL-7B-Instruct',
          },
        ]);
      } else if (!hitlTriggered && !assistantText) {
        // Fallback for conversational response
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Hello! I am the Sovereign AI Workbench assistant deployed at MRPL. I can assist with P&ID analysis, OISD standards, and refinery calculations.',
            model: 'Qwen2.5-VL-7B-Instruct',
          },
        ]);
      }
    } catch (err: any) {
      console.error('API Query Error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Hello! I am the Sovereign AI Workbench assistant at MRPL. Ready to assist with P&ID analysis, OISD standards lookup, and calculations.`,
          model: 'Workbench-System',
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleHitlDecision = async (approved: boolean, comment: string) => {
    const currentThread = hitlData?.threadId || threadId;
    try {
      const res = await fetch('/api/v1/agent/hitl/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: currentThread,
          approved: approved,
          feedback: comment,
          role: 'SAFETY_OFFICER',
        }),
      });

      let data: any = {};
      if (res.ok) {
        try {
          const contentType = res.headers.get('content-type') || '';
          if (contentType.includes('application/json')) {
            data = await res.json();
          } else {
            const rawText = await res.text();
            try {
              data = JSON.parse(rawText);
            } catch {
              data = { final_response: rawText };
            }
          }
        } catch {
          data = {};
        }
      } else {
        console.warn(`HITL approval endpoint returned HTTP status ${res.status}`);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: approved
            ? `✅ Action APPROVED by Safety Officer. Rationale: "${comment || 'Approved after review'}". Proceeding with execution.`
            : `❌ Action REJECTED by Safety Officer. Rationale: "${comment || 'Rejected safety override'}". Operation cancelled.`,
          model: 'Audit-Ledger',
        },
      ]);

      if (approved && (data.final_response || data.data?.content)) {
        const finalAnswer = data.final_response || data.data?.content;
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: finalAnswer,
            model: 'Qwen2.5-VL-7B-Instruct',
          },
        ]);
      }
    } catch (e) {
      console.error('HITL approval POST error:', e);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: approved
            ? `✅ Action APPROVED by Safety Officer. Rationale: "${comment || 'Approved after review'}". Proceeding with execution.`
            : `❌ Action REJECTED by Safety Officer. Rationale: "${comment || 'Rejected safety override'}". Operation cancelled.`,
          model: 'Audit-Ledger',
        },
      ]);
    }
    setShowHitl(false);
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
                <div
                  className={`p-2 rounded-md ${
                    msg.role === 'user' ? 'bg-accent-cyan/20 text-accent-cyan' : 'bg-accent-amber/20 text-accent-amber'
                  }`}
                >
                  {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">{msg.role}</span>
                {msg.model && (
                  <span className="text-xs font-mono bg-sovereign-border px-2 py-1 rounded text-gray-400 flex items-center border border-gray-700">
                    <Cpu className="w-3 h-3 mr-1.5" /> {msg.model}
                  </span>
                )}
              </div>
              <div
                className={`max-w-[85%] p-4 rounded-xl text-sm leading-relaxed shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-accent-cyan/10 border border-accent-cyan/20 text-gray-200'
                    : 'bg-sovereign-surface border border-sovereign-border text-gray-300 font-mono'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {isProcessing && (
            <div className="flex items-center space-x-2 text-accent-cyan font-mono text-xs p-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Agent processing query...</span>
            </div>
          )}
        </div>

        <div className="p-4 bg-sovereign-surface/80 border-t border-sovereign-border flex items-end space-x-3">
          <button className="p-3.5 bg-sovereign-dark border border-sovereign-border rounded-xl hover:border-accent-cyan text-gray-400 hover:text-accent-cyan transition-colors group relative">
            <Upload className="w-5 h-5 group-hover:scale-110 transition-transform" />
            <span className="absolute -top-10 left-1/2 -translate-x-1/2 bg-sovereign-border text-xs text-gray-200 px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              Upload P&ID
            </span>
          </button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="Query schematics, ask about compliance..."
            className="flex-1 bg-sovereign-dark border border-sovereign-border rounded-xl p-3.5 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 resize-none transition-all shadow-inner"
            rows={1}
            disabled={isProcessing}
          />
          <button
            onClick={handleSend}
            disabled={isProcessing}
            className="p-3.5 bg-accent-cyan/20 border border-accent-cyan/50 text-accent-cyan rounded-xl hover:bg-accent-cyan/30 transition-colors shadow-[0_0_10px_rgba(6,182,212,0.1)] hover:shadow-[0_0_15px_rgba(6,182,212,0.2)] disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="w-5/12 hidden lg:block">
        <SchematicViewer />
      </div>

      {hitlData && (
        <HitlApprovalModal
          isOpen={showHitl}
          onClose={() => setShowHitl(false)}
          actionType={hitlData.actionType}
          riskLevel={hitlData.riskLevel}
          draftContent={hitlData.draftContent}
          complianceFlags={hitlData.complianceFlags}
          requiredRole={hitlData.requiredRole}
          threadId={hitlData.threadId}
          onApproveAction={handleHitlDecision}
        />
      )}
    </div>
  );
}
