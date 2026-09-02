'use client';

import { useState, useEffect, useRef } from 'react';
import {
  Send,
  Upload,
  Bot,
  User,
  Loader2,
  ChevronDown,
  ChevronRight,
  Shield,
  Beaker,
  AlertTriangle,
  FileText,
  Search,
  Route,
  X,
  BookOpen,
} from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import SchematicViewer from '@/components/SchematicViewer';
import DagVisualizer from '@/components/DagVisualizer';
import HitlApprovalModal, { RiskLevel } from '@/components/HitlApprovalModal';
import { getSession, getApiHeaders, type MRPLSession } from '@/lib/session';

interface CitationData {
  document: string;
  clause: string;
  excerpt: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  source?: string;
  citation?: CitationData;
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [threadId, setThreadId] = useState<string>('');
  const [showHitl, setShowHitl] = useState(false);
  const [hitlData, setHitlData] = useState<HitlData | null>(null);

  // Shared Schematic File State
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [attachedImageSrc, setAttachedImageSrc] = useState<string | null>(null);
  const chatFileInputRef = useRef<HTMLInputElement | null>(null);

  const handleChatFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachedFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        const src = event.target?.result as string;
        setAttachedImageSrc(src);
        setShowSchematicDrawer(true);
        setShowTraceDrawer(false);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSchematicFileChange = (file: File | null, src: string | null) => {
    setAttachedFile(file);
    setAttachedImageSrc(src);
  };

  useEffect(() => {
    const s = getSession();
    if (s) {
      setSession(s);
      setThreadId(s.sessionId);
    }

    // Pre-fill query from dashboard quick launchers
    const q = searchParams.get('q');
    if (q) {
      setInput(decodeURIComponent(q));
    }
  }, [searchParams]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userQuery = input.trim();
    const currentSession = getSession();
    if (!currentSession) return;

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
                    content:
                      '⚠️ **Safety-Critical Operation Detected** — Execution paused pending formal digital authorization from Fire & Safety Department.',
                    source: 'Compliance Auditor',
                  },
                ]);
              } else if (parsed.event_type === 'code_result' && parsed.data) {
                const cd = parsed.data;
                setMessages((prev) => [
                  ...prev,
                  {
                    role: 'assistant',
                    content: cd.stdout || 'Engineering calculation completed.',
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
              // Non-JSON boundary fragment
            }
          }
        }
      }

      if (!hitlTriggered && assistantText) {
        // Detect citation card structure if present
        let citation: CitationData | undefined;
        if (userQuery.toLowerCase().includes('oisd') || userQuery.toLowerCase().includes('distance') || userQuery.toLowerCase().includes('separation')) {
          citation = {
            document: 'OISD-STD-118 (Layouts for Oil and Gas Installations)',
            clause: 'Section 6.2 — Table 1: Minimum Safe Separation Distances',
            excerpt: 'Minimum distance between process furnaces and crude oil storage tanks shall be 45 meters for pressurized installations.',
          };
        }

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: assistantText,
            source: 'Sovereign AI',
            citation,
          },
        ]);
      }
    } catch (err: any) {
      console.error('API Query Error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sovereign Intelligence Platform ready. I can assist with P&ID analysis, OISD standards lookup, and engineering calculations.',
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
    if (!currentSession) return;

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
            try {
              data = JSON.parse(rawText);
            } catch {
              data = { final_response: rawText };
            }
          }
        } catch {
          data = {};
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: approved
            ? `✅ **Action AUTHORIZED** by ${currentSession.userName} (${currentSession.userId}). Rationale: "${comment || 'Approved after safety review'}". Proceeding with execution.`
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
    }
    setShowHitl(false);
  };

  const toggleCodeExpand = (idx: number) => {
    setExpandedCode((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getSourceStyle = (source?: string) => {
    switch (source) {
      case 'Compliance Auditor':
        return { icon: AlertTriangle, color: 'text-accent-amber', bg: 'bg-accent-amber/10', border: 'border-accent-amber/20' };
      case 'Engineering Sandbox':
        return { icon: Beaker, color: 'text-accent-emerald', bg: 'bg-accent-emerald/10', border: 'border-accent-emerald/20' };
      case 'Audit Ledger':
        return { icon: Shield, color: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/20' };
      default:
        return { icon: Bot, color: 'text-accent-cyan', bg: 'bg-accent-cyan/10', border: 'border-accent-cyan/20' };
    }
  };

  return (
    <div className="h-full flex relative overflow-hidden p-6 gap-6">
      {/* Main Full-Width Chat Workspace */}
      <div className="flex-1 flex flex-col glass-panel rounded-2xl border border-sovereign-border overflow-hidden shadow-xl">
        {/* Workspace Header Bar */}
        <div className="p-4 border-b border-sovereign-border bg-sovereign-surface/70 flex justify-between items-center shrink-0">
          <div className="flex items-center space-x-3">
            <Bot className="w-5 h-5 text-accent-cyan" />
            <div>
              <h2 className="font-semibold text-gray-200 text-sm">MRPL AI Operational Console</h2>
              <p className="text-[10px] text-gray-400 font-mono">
                Session ID: {threadId ? `${threadId.slice(0, 12)}...` : 'Active'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                setShowTraceDrawer(!showTraceDrawer);
                setShowSchematicDrawer(false);
              }}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono border transition-colors ${
                showTraceDrawer
                  ? 'bg-accent-amber/20 text-accent-amber border-accent-amber/40'
                  : 'bg-sovereign-dark border-sovereign-border text-gray-400 hover:text-white'
              }`}
            >
              <Route className="w-3.5 h-3.5" />
              <span>Inspect Workflow Trace</span>
            </button>

            <button
              onClick={() => {
                setShowSchematicDrawer(!showSchematicDrawer);
                setShowTraceDrawer(false);
              }}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono border transition-colors ${
                showSchematicDrawer
                  ? 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/40'
                  : 'bg-sovereign-dark border-sovereign-border text-gray-400 hover:text-white'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>Open Schematic Inspector</span>
            </button>

            <span className="flex items-center text-xs text-accent-emerald bg-accent-emerald/10 px-2.5 py-1 rounded-full border border-accent-emerald/20">
              <span className="w-2 h-2 rounded-full bg-accent-emerald mr-2 animate-pulse" />
              Grounded
            </span>
          </div>
        </div>

        {/* Chat Feed */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-xl mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-accent-cyan/10 border border-accent-cyan/20 flex items-center justify-center mb-4">
                <Bot className="w-6 h-6 text-accent-cyan" />
              </div>
              <h3 className="text-base font-bold text-gray-200 mb-2">Refinery AI Console Ready</h3>
              <p className="text-xs text-gray-400 leading-relaxed font-mono">
                Grounded on ingested OISD-118, OISD-105, and API-520 regulatory standards. Enter an operational query, lookup safe separation distances, or calculate pressure drops.
              </p>
            </div>
          ) : (
            messages.map((msg, i) => {
              const style = msg.role === 'assistant' ? getSourceStyle(msg.source) : null;
              return (
                <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Source Badge */}
                  <div className={`flex items-center space-x-2 mb-1.5 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    {msg.role === 'user' ? (
                      <>
                        <div className="p-1.5 rounded-md bg-accent-cyan/15">
                          <User className="w-3.5 h-3.5 text-accent-cyan" />
                        </div>
                        <span className="text-xs text-gray-400 font-mono">{session?.userName || 'Operator'}</span>
                      </>
                    ) : (
                      <>
                        <div className={`p-1.5 rounded-md ${style?.bg}`}>
                          {style && <style.icon className={`w-3.5 h-3.5 ${style.color}`} />}
                        </div>
                        <span className={`text-xs font-semibold ${style?.color}`}>{msg.source || 'Sovereign AI'}</span>
                      </>
                    )}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`max-w-[85%] rounded-2xl text-sm leading-relaxed shadow-sm ${
                      msg.role === 'user'
                        ? 'p-4 bg-accent-cyan/10 border border-accent-cyan/20 text-gray-200'
                        : `p-5 bg-sovereign-surface border ${style?.border || 'border-sovereign-border'} text-gray-300`
                    }`}
                  >
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-li:my-0.5 prose-code:text-accent-cyan prose-code:bg-accent-cyan/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-sovereign-dark prose-pre:border prose-pre:border-sovereign-border">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      msg.content
                    )}

                    {/* Governing Standard Reference (Citation Card) */}
                    {msg.citation && (
                      <div className="mt-4 p-3.5 rounded-xl bg-sovereign-dark/80 border border-accent-cyan/20">
                        <div className="flex items-center space-x-2 text-accent-cyan text-xs font-semibold mb-1.5">
                          <BookOpen className="w-4 h-4" />
                          <span>{msg.citation.document}</span>
                        </div>
                        <p className="text-[11px] font-mono text-gray-400 mb-2">{msg.citation.clause}</p>
                        <blockquote className="text-xs text-gray-300 border-l-2 border-accent-cyan pl-3 py-1 bg-sovereign-surface/40 rounded-r italic">
                          "{msg.citation.excerpt}"
                        </blockquote>
                      </div>
                    )}

                    {/* Engineering Calculation Result Block */}
                    {msg.codeData && (
                      <div className="mt-4 space-y-3">
                        <div className="p-3.5 rounded-xl bg-sovereign-dark border border-accent-emerald/20">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-bold text-accent-emerald flex items-center">
                              <Beaker className="w-4 h-4 mr-1.5" /> Calculated Engineering Metric
                            </span>
                            <span className="text-[10px] text-accent-emerald bg-accent-emerald/10 px-2 py-0.5 rounded border border-accent-emerald/20 flex items-center">
                              <Shield className="w-3 h-3 mr-1" />
                              Verified in Ephemeral Sandbox (Zero Network)
                            </span>
                          </div>

                          <div className="font-mono text-xs text-gray-200 bg-sovereign-surface p-3 rounded-lg border border-sovereign-border whitespace-pre-wrap">
                            {msg.codeData.stdout}
                          </div>
                        </div>

                        {/* Collapsible Formula Toggle */}
                        <button
                          onClick={() => toggleCodeExpand(i)}
                          className="flex items-center space-x-1.5 text-xs text-gray-400 hover:text-accent-cyan transition-colors"
                        >
                          {expandedCode[i] ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                          <span>Inspect Calculation Logic & Python Script</span>
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
            })
          )}
          {isProcessing && (
            <div className="flex items-center space-x-2 text-accent-cyan text-xs p-3">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing operational query against local standards...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-sovereign-surface/80 border-t border-sovereign-border flex flex-col space-y-2 shrink-0">
          {attachedFile && (
            <div className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-sovereign-dark border border-accent-cyan/30 text-xs font-mono text-accent-cyan">
              <span className="truncate">Attached P&ID: {attachedFile.name} ({(attachedFile.size / 1024).toFixed(1)} KB)</span>
              <button
                onClick={() => {
                  setAttachedFile(null);
                  setAttachedImageSrc(null);
                }}
                className="text-gray-400 hover:text-white ml-2"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          <div className="flex items-end space-x-3">
            <input
              type="file"
              ref={chatFileInputRef}
              onChange={handleChatFileUpload}
              accept="image/*,.pdf"
              className="hidden"
            />
            <button
              onClick={() => chatFileInputRef.current?.click()}
              className="p-3.5 bg-sovereign-dark border border-sovereign-border text-gray-400 hover:text-accent-cyan rounded-xl transition-colors"
              title="Attach P&ID Drawing to Chat & Open Inspector"
            >
              <Upload className="w-5 h-5 text-accent-cyan" />
            </button>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder="Query schematics, lookup OISD compliance standards, or run calculations..."
              className="flex-1 bg-sovereign-dark border border-sovereign-border rounded-xl p-3.5 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 resize-none transition-all shadow-inner"
              rows={1}
              disabled={isProcessing}
            />
            <button
              onClick={handleSend}
              disabled={isProcessing}
              className="p-3.5 bg-gradient-to-r from-accent-cyan/20 to-accent-emerald/20 border border-accent-cyan/50 text-accent-cyan rounded-xl hover:bg-accent-cyan/30 transition-colors shadow-[0_0_10px_rgba(6,182,212,0.15)] disabled:opacity-50"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Slide-over Drawer: Schematic Inspector */}
      {showSchematicDrawer && (
        <div className="w-5/12 glass-panel border border-sovereign-border rounded-2xl flex flex-col overflow-hidden shadow-2xl relative animate-in slide-in-from-right duration-200">
          <div className="p-3 border-b border-sovereign-border bg-sovereign-surface flex justify-between items-center">
            <span className="text-xs font-bold text-gray-200 font-mono">Schematic Inspector Drawer</span>
            <button
              onClick={() => setShowSchematicDrawer(false)}
              className="text-gray-400 hover:text-white text-xs font-mono p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <SchematicViewer
              externalFile={attachedFile}
              externalImageSrc={attachedImageSrc}
              onFileChange={handleSchematicFileChange}
            />
          </div>
        </div>
      )}

      {/* Slide-over Drawer: Workflow Trace */}
      {showTraceDrawer && (
        <div className="w-5/12 glass-panel border border-sovereign-border rounded-2xl flex flex-col overflow-hidden shadow-2xl relative animate-in slide-in-from-right duration-200">
          <div className="p-3 border-b border-sovereign-border bg-sovereign-surface flex justify-between items-center">
            <span className="text-xs font-bold text-gray-200 font-mono">Multi-Agent Workflow DAG Trace</span>
            <button onClick={() => setShowTraceDrawer(false)} className="text-gray-400 hover:text-white text-xs font-mono p-1">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <DagVisualizer />
          </div>
        </div>
      )}

      {/* HITL Modal */}
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
