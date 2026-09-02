'use client';
import { useState, useEffect, useRef } from 'react';
import { Send, Upload, Bot, User, Loader2, ChevronDown, ChevronRight, Shield, Beaker, AlertTriangle } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import SchematicViewer from '@/components/SchematicViewer';
import HitlApprovalModal, { RiskLevel } from '@/components/HitlApprovalModal';
import { initSession, getSession, getApiHeaders, type MRPLSession } from '@/lib/session';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  source?: string;
  codeData?: {
    script?: string;
    stdout?: string;
    stderr?: string;
    exitCode?: number;
    sandboxMode?: string;
  };
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
  const searchParams = useSearchParams();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [session, setSession] = useState<MRPLSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'MRPL Sovereign Intelligence Platform ready. I can assist with P&ID schematic analysis, OISD compliance standards lookup, engineering calculations, and shift handover digests. How can I help?',
      source: 'Sovereign AI',
    },
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [threadId, setThreadId] = useState<string>('');
  const [showHitl, setShowHitl] = useState(false);
  const [hitlData, setHitlData] = useState<HitlData | null>(null);
  const [showSchematic, setShowSchematic] = useState(false);
  const [expandedCode, setExpandedCode] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const s = initSession();
    setSession(s);
    setThreadId(s.sessionId);

    // Pre-fill from dashboard launchers
    const q = searchParams.get('q');
    if (q) {
      setInput(decodeURIComponent(q));
    }
    const mode = searchParams.get('mode');
    if (mode === 'schematic') {
      setShowSchematic(true);
    }
  }, [searchParams]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userQuery = input.trim();
    const currentSession = getSession();
    const activeThreadId = threadId || crypto.randomUUID();
    if (!threadId) setThreadId(activeThreadId);

    setMessages((prev) => [...prev, { role: 'user', content: userQuery }]);
    setInput('');
    setIsProcessing(true);

    try {
      const response = await fetch('/api/v1/agent/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getApiHeaders(),
        },
        body: JSON.stringify({
          query: userQuery,
          user_id: currentSession.userId,
          role: currentSession.role,
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
                  draftContent: d.draft_content || `Action requested requires Human-in-the-Loop review.`,
                  complianceFlags: d.compliance_flags || ['Safety-critical procedure flagged'],
                  requiredRole: d.required_role || 'SAFETY_OFFICER',
                  threadId: parsed.thread_id || activeThreadId,
                });
                setShowHitl(true);
                setMessages((prev) => [
                  ...prev,
                  {
                    role: 'assistant',
                    content: '⚠️ **Safety-Critical Operation Detected** — Execution paused pending authorization from Fire & Safety Department.',
                    source: 'Compliance Auditor',
                  },
                ]);
              } else if (parsed.event_type === 'code_result' && parsed.data) {
                const cd = parsed.data;
                setMessages((prev) => [
                  ...prev,
                  {
                    role: 'assistant',
                    content: cd.stdout || 'Calculation completed.',
                    source: 'Engineering Sandbox',
                    codeData: {
                      script: cd.script,
                      stdout: cd.stdout,
                      stderr: cd.stderr,
                      exitCode: cd.exit_code ?? 0,
                      sandboxMode: cd.sandbox_mode,
                    },
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
            source: 'Sovereign AI',
          },
        ]);
      } else if (!hitlTriggered && !assistantText) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'MRPL Sovereign Intelligence Platform ready. I can assist with P&ID analysis, OISD standards, and refinery calculations.',
            source: 'Sovereign AI',
          },
        ]);
      }
    } catch (err: any) {
      console.error('API Query Error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'MRPL Sovereign Intelligence Platform ready. I can assist with P&ID analysis, OISD standards lookup, and engineering calculations.',
          source: 'Sovereign AI',
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleHitlDecision = async (approved: boolean, comment: string) => {
    const currentThread = hitlData?.threadId || threadId;
    const currentSession = getSession();
    try {
      const res = await fetch('/api/v1/agent/hitl/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getApiHeaders(),
        },
        body: JSON.stringify({
          thread_id: currentThread,
          approved: approved,
          feedback: comment,
          role: currentSession.role,
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
            try { data = JSON.parse(rawText); } catch { data = { final_response: rawText }; }
          }
        } catch { data = {}; }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: approved
            ? `✅ **Action AUTHORIZED** by ${currentSession.userName} (${currentSession.userId}). Rationale: "${comment || 'Approved after safety review'}"."`
            : `❌ **Action REJECTED** by ${currentSession.userName} (${currentSession.userId}). Rationale: "${comment || 'Safety override rejected'}". Operation cancelled.`,
          source: 'Audit Ledger',
        },
      ]);

      if (approved && (data.final_response || data.data?.content)) {
        const finalAnswer = data.final_response || data.data?.content;
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: finalAnswer, source: 'Sovereign AI' },
        ]);
      }
    } catch (e) {
      console.error('HITL approval POST error:', e);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: approved
            ? `✅ **Action AUTHORIZED**. Proceeding with execution.`
            : `❌ **Action REJECTED**. Operation cancelled.`,
          source: 'Audit Ledger',
        },
      ]);
    }
    setShowHitl(false);
  };

  const toggleCodeExpand = (idx: number) => {
    setExpandedCode((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getSourceStyle = (source?: string) => {
    switch (source) {
      case 'Compliance Auditor': return { icon: AlertTriangle, color: 'text-accent-amber', bg: 'bg-accent-amber/10', border: 'border-accent-amber/20' };
      case 'Engineering Sandbox': return { icon: Beaker, color: 'text-accent-emerald', bg: 'bg-accent-emerald/10', border: 'border-accent-emerald/20' };
      case 'Audit Ledger': return { icon: Shield, color: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/20' };
      default: return { icon: Bot, color: 'text-accent-cyan', bg: 'bg-accent-cyan/10', border: 'border-accent-cyan/20' };
    }
  };

  return (
    <div className="h-full flex gap-6 p-6">
      <div className="flex-1 flex flex-col glass-panel rounded-xl border border-sovereign-border overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-sovereign-border bg-sovereign-surface/50 flex justify-between items-center">
          <h2 className="font-semibold text-gray-200 text-sm">MRPL AI Operational Console</h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowSchematic(!showSchematic)}
              className="text-xs text-gray-400 hover:text-accent-cyan transition-colors px-2 py-1 rounded border border-sovereign-border hover:border-accent-cyan/30"
            >
              {showSchematic ? 'Hide' : 'Show'} Schematic
            </button>
            <span className="flex items-center text-xs text-accent-emerald bg-accent-emerald/10 px-2 py-1 rounded border border-accent-emerald/20">
              <span className="w-2 h-2 rounded-full bg-accent-emerald mr-2 animate-pulse" />
              Online
            </span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 p-6 overflow-y-auto space-y-5">
          {messages.map((msg, i) => {
            const style = msg.role === 'assistant' ? getSourceStyle(msg.source) : null;
            return (
              <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                {/* Source Label */}
                <div className={`flex items-center space-x-2 mb-1.5 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  {msg.role === 'user' ? (
                    <>
                      <div className="p-1.5 rounded-md bg-accent-cyan/15">
                        <User className="w-3.5 h-3.5 text-accent-cyan" />
                      </div>
                      <span className="text-xs text-gray-400">{session?.userName || 'You'}</span>
                    </>
                  ) : (
                    <>
                      <div className={`p-1.5 rounded-md ${style?.bg}`}>
                        {style && <style.icon className={`w-3.5 h-3.5 ${style.color}`} />}
                      </div>
                      <span className={`text-xs font-medium ${style?.color}`}>{msg.source || 'Sovereign AI'}</span>
                    </>
                  )}
                </div>

                {/* Message Content */}
                <div className={`max-w-[85%] rounded-xl text-sm leading-relaxed shadow-sm ${
                  msg.role === 'user'
                    ? 'p-4 bg-accent-cyan/10 border border-accent-cyan/20 text-gray-200'
                    : `p-4 bg-sovereign-surface border ${style?.border || 'border-sovereign-border'} text-gray-300`
                }`}>
                  {msg.role === 'assistant' ? (
                    <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-li:my-0.5 prose-code:text-accent-cyan prose-code:bg-accent-cyan/10 prose-code:px-1 prose-code:rounded prose-pre:bg-sovereign-dark prose-pre:border prose-pre:border-sovereign-border">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}

                  {/* Code Sandbox Result */}
                  {msg.codeData && (
                    <div className="mt-3 space-y-2">
                      {/* Sandbox Badge */}
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] text-accent-emerald bg-accent-emerald/10 px-2 py-0.5 rounded border border-accent-emerald/20 flex items-center">
                          <Shield className="w-3 h-3 mr-1" />
                          Verified in Isolated Ephemeral Sandbox (Zero Network)
                        </span>
                        {msg.codeData.exitCode === 0 && (
                          <span className="text-[10px] text-accent-emerald">Exit: 0 ✓</span>
                        )}
                      </div>

                      {/* Collapsible Script */}
                      <button
                        onClick={() => toggleCodeExpand(i)}
                        className="flex items-center space-x-1.5 text-xs text-gray-400 hover:text-accent-cyan transition-colors"
                      >
                        {expandedCode[i] ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                        <span>Inspect Calculation Logic & Formula</span>
                      </button>
                      {expandedCode[i] && msg.codeData.script && (
                        <pre className="bg-sovereign-dark p-3 rounded-lg border border-sovereign-border text-xs text-gray-300 overflow-x-auto font-mono">
                          {msg.codeData.script}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {isProcessing && (
            <div className="flex items-center space-x-2 text-accent-cyan text-xs p-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing operational query...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 bg-sovereign-surface/80 border-t border-sovereign-border flex items-end space-x-3">
          <button className="p-3 bg-sovereign-dark border border-sovereign-border rounded-xl hover:border-accent-cyan text-gray-400 hover:text-accent-cyan transition-colors group relative">
            <Upload className="w-5 h-5 group-hover:scale-110 transition-transform" />
            <span className="absolute -top-10 left-1/2 -translate-x-1/2 bg-sovereign-border text-xs text-gray-200 px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              Upload P&ID
            </span>
          </button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="Query schematics, lookup compliance standards, run calculations..."
            className="flex-1 bg-sovereign-dark border border-sovereign-border rounded-xl p-3 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 resize-none transition-all shadow-inner"
            rows={1}
            disabled={isProcessing}
          />
          <button
            onClick={handleSend}
            disabled={isProcessing}
            className="p-3 bg-accent-cyan/20 border border-accent-cyan/50 text-accent-cyan rounded-xl hover:bg-accent-cyan/30 transition-colors shadow-[0_0_10px_rgba(6,182,212,0.1)] hover:shadow-[0_0_15px_rgba(6,182,212,0.2)] disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Schematic Panel */}
      {showSchematic && (
        <div className="w-5/12 hidden lg:block">
          <SchematicViewer />
        </div>
      )}

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
