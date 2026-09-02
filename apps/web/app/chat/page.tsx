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
  FileText,
  Search,
  X,
  BookOpen,
  Image as ImageIcon,
} from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import SchematicViewer from '@/components/SchematicViewer';
import HitlApprovalModal, { RiskLevel } from '@/components/HitlApprovalModal';
import { CitationList, type Citation } from '@/components/CitationList';
import { getSession, getApiHeaders, type MRPLSession } from '@/lib/session';
import {
  getChatSession,
  saveChatSession,
  createNewChatSession,
  getActiveThreadId,
  type ChatMessage as Message,
} from '@/lib/chatStore';

interface HitlData {
  actionType: string;
  riskLevel: RiskLevel;
  draftContent: string;
  complianceFlags: string[];
  requiredRole: string;
  threadId: string;
}

const roleStyles: Record<string, { bg: string; color: string; border: string; icon: any }> = {
  'Sovereign AI': { bg: 'bg-[#57692c]/20', color: 'text-[#8fb03e]', border: 'border-[#8fb03e]', icon: Bot },
  'Compliance Auditor': { bg: 'bg-red-950/40', color: 'text-red-400', border: 'border-red-500', icon: Shield },
  'Engineering Sandbox': { bg: 'bg-[#57692c]/30', color: 'text-[#8fb03e]', border: 'border-[#8fb03e]', icon: Beaker },
  'P&ID Inspector': { bg: 'bg-amber-950/40', color: 'text-amber-400', border: 'border-amber-500', icon: Search },
};

function preprocessLatex(content: string): string {
  if (!content) return '';
  let text = content;

  // 1. Standard LaTeX display math delimiters \[ ... \] -> $$ ... $$
  text = text.replace(/\\\[\s*([\s\S]*?)\s*\\\]/g, '\n$$\n$1\n$$\n');

  // 2. Standard LaTeX inline math delimiters \( ... \) -> $ ... $
  text = text.replace(/\\\(\s*([\s\S]*?)\s*\\\)/g, ' $$1$ ');

  // 3. Convert bare bracketed LaTeX math expressions like [ \text{Re} = ... ] or [ Re = \frac{...} ]
  text = text.replace(/(?:^|\n)\[\s*(\\text\{[\s\S]*?)\s*\](?:\n|$)/g, '\n$$\n$1\n$$\n');
  text = text.replace(/(?:^|\n)\[\s*([A-Za-z0-9_\s\\\{\}\(\)\+\-\*\/\=\.\,\:\^\;\%\$\|\&\<\>]+?\\(?:frac|sqrt|rho|mu|delta|sigma|eta|pi|cdot|times|text)[\s\S]*?)\s*\](?:\n|$)/g, '\n$$\n$1\n$$\n');

  // 4. Sanitize quadruple dollar signs $$$$ -> $$
  text = text.replace(/\$\$\$\$/g, '$$');

  return text;
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

  // Drawer Toggles & Shared Schematic File State
  const [showSchematicDrawer, setShowSchematicDrawer] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [attachedImageSrc, setAttachedImageSrc] = useState<string | null>(null);
  const [expandedCode, setExpandedCode] = useState<Record<number, boolean>>({});

  const chatFileInputRef = useRef<HTMLInputElement | null>(null);

  const handleChatFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachedFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        const src = event.target?.result as string;
        setAttachedImageSrc(src);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSchematicFileChange = (file: File | null, src: string | null) => {
    setAttachedFile(file);
    setAttachedImageSrc(src);
  };

  // Load chat session based on threadId parameter or active stored thread
  useEffect(() => {
    const s = getSession();
    if (s) {
      setSession(s);
    }

    const paramThreadId = searchParams.get('threadId');
    if (paramThreadId) {
      const existingSession = getChatSession(paramThreadId);
      if (existingSession) {
        setThreadId(existingSession.threadId);
        setMessages(existingSession.messages);
      } else {
        setThreadId(paramThreadId);
        const newSession = saveChatSession(paramThreadId, [
          {
            role: 'assistant',
            content:
              'MRPL Sovereign Intelligence Platform ready. I can assist with P&ID schematic analysis, OISD compliance standards lookup, engineering calculations, and shift handover digests. How can I help?',
            source: 'Sovereign AI',
          },
        ]);
        setMessages(newSession.messages);
      }
    } else {
      const activeId = getActiveThreadId();
      if (activeId) {
        const existingSession = getChatSession(activeId);
        if (existingSession) {
          setThreadId(existingSession.threadId);
          setMessages(existingSession.messages);
        } else {
          const fresh = createNewChatSession();
          setThreadId(fresh.threadId);
          setMessages(fresh.messages);
        }
      } else {
        const fresh = createNewChatSession();
        setThreadId(fresh.threadId);
        setMessages(fresh.messages);
      }
    }

    // Pre-fill query from dashboard quick launchers
    const q = searchParams.get('q');
    if (q) {
      setInput(decodeURIComponent(q));
    }
    const mode = searchParams.get('mode');
    if (mode === 'schematic') {
      setShowSchematicDrawer(true);
    }
  }, [searchParams]);

  // Automatically persist messages whenever updated
  useEffect(() => {
    if (threadId && messages.length > 0) {
      saveChatSession(threadId, messages);
    }
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, threadId]);

  const handleSend = async () => {
    if ((!input.trim() && !attachedImageSrc) || isProcessing) return;

    const userQuery = input.trim() || 'Inspect attached P&ID diagram.';
    const currentSession = getSession();
    if (!currentSession) return;

    const activeThreadId = threadId || crypto.randomUUID();
    if (!threadId) setThreadId(activeThreadId);

    const userMsg: Message = {
      role: 'user',
      content: userQuery,
      imageSrc: attachedImageSrc || undefined,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    const currentAttachedSrc = attachedImageSrc;
    setAttachedImageSrc(null);
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
          image_data: currentAttachedSrc || undefined,
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
      let responseCitations: Citation[] = [];
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
                if (parsed.data.citations && Array.isArray(parsed.data.citations)) {
                  responseCitations = parsed.data.citations;
                }
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
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: assistantText,
            source: 'Sovereign AI',
            citations: responseCitations.length > 0 ? responseCitations : undefined,
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

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: `[HITL Authorization Signal] Decision: ${approved ? 'APPROVED' : 'REJECTED'}. Note: "${comment || 'No comment provided'}"`,
      },
    ]);

    setIsProcessing(true);

    try {
      const res = await fetch('/api/v1/agent/hitl/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getApiHeaders(),
        },
        body: JSON.stringify({
          thread_id: currentThread,
          approved,
          user_id: currentSession.userId,
          role: currentSession.role,
          comment,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            data.final_response ||
            (approved
              ? '✅ Action authorized and executed into process control stream.'
              : '❌ Action rejected by Digital Permit sign-off.'),
          source: 'Compliance Auditor',
        },
      ]);
    } catch (err) {
      console.error('HITL Decision Error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Error communicating decision to sovereign engine checkpointer.',
          source: 'Compliance Auditor',
        },
      ]);
    } finally {
      setIsProcessing(false);
      setShowHitl(false);
    }
  };

  const toggleCodeExpand = (idx: number) => {
    setExpandedCode((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="h-full flex relative overflow-hidden p-6 gap-6 font-mono select-none">
      {/* Main Full-Width Chat Workspace */}
      <div className="flex-1 flex flex-col bg-[#202020] border-2 border-[#8fb03e] overflow-hidden shadow-none">
        {/* Workspace Header Bar */}
        <div className="p-4 border-b border-[#8fb03e] bg-[#242424] flex justify-between items-center shrink-0">
          <div className="flex items-center space-x-3">
            <Bot className="w-5 h-5 text-[#8fb03e]" />
            <div>
              <h2 className="font-bold text-[#e8e8e8] text-sm tracking-wider uppercase">MRPL AI OPERATIONAL CONSOLE</h2>
              <p className="text-[10px] text-[#c4c4c4]">
                SESSION ID: {threadId ? threadId : 'ACTIVE'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowSchematicDrawer(!showSchematicDrawer)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold border transition-colors cursor-pointer ${
                showSchematicDrawer
                  ? 'bg-[#8fb03e] text-black border-[#8fb03e]'
                  : 'bg-[#57692c] text-white border-[#8fb03e] hover:bg-[#8fb03e] hover:text-black'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>[+] SCHEMATIC INSPECTOR DRAWER</span>
            </button>

            <span className="flex items-center text-xs text-white bg-[#57692c] px-2.5 py-1 font-bold border border-[#8fb03e]">
              <span className="w-2 h-2 rounded-full bg-[#8fb03e] mr-2 animate-pulse" />
              GROUNDED
            </span>
          </div>
        </div>

        {/* Chat Feed */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.map((msg, i) => {
            const style = msg.source ? roleStyles[msg.source] || roleStyles['Sovereign AI'] : roleStyles['Sovereign AI'];
            return (
              <div
                key={i}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                {/* Message Meta Badge */}
                <div className="flex items-center space-x-2 mb-1.5 px-1">
                  {msg.role === 'user' ? (
                    <>
                      <div className="p-1 rounded bg-[#57692c] border border-[#8fb03e]">
                        <User className="w-3.5 h-3.5 text-white" />
                      </div>
                      <span className="text-xs text-[#c4c4c4] font-bold">{session?.userName || 'Operator'}</span>
                    </>
                  ) : (
                    <>
                      <div className={`p-1 border ${style?.border} ${style?.bg}`}>
                        {style && <style.icon className={`w-3.5 h-3.5 ${style.color}`} />}
                      </div>
                      <span className={`text-xs font-bold ${style?.color}`}>{msg.source || 'Sovereign AI'}</span>
                    </>
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  className={`max-w-[85%] text-xs leading-relaxed border ${
                    msg.role === 'user'
                      ? 'p-4 bg-[#57692c]/30 border-[#8fb03e] text-[#e8e8e8]'
                      : `p-5 bg-[#1a1a1a] border-[#8fb03e] text-[#e8e8e8]`
                  }`}
                >
                  {/* Render Image Attachment if Present */}
                  {msg.imageSrc && (
                    <div className="mb-3 border border-[#8fb03e] bg-[#121212] p-1.5">
                      <img
                        src={msg.imageSrc}
                        alt="Attached P&ID Image"
                        className="max-h-64 w-auto object-contain border border-[#8fb03e]"
                      />
                      <div className="bg-[#57692c] text-white px-2 py-0.5 text-[9px] font-bold mt-1 uppercase tracking-wider">
                        ATTACHED P&ID DRAWING ATTACHMENT
                      </div>
                    </div>
                  )}

                  {msg.role === 'assistant' ? (
                    <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-li:my-0.5 prose-code:text-[#8fb03e] prose-code:bg-[#57692c]/20 prose-code:px-1.5 prose-code:py-0.5 prose-pre:bg-[#121212] prose-pre:border prose-pre:border-[#8fb03e]">
                      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
                        {preprocessLatex(msg.content)}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}

                  {/* Dynamic Governing Standard References (Collapsible Accordion) */}
                  {msg.citations && msg.citations.length > 0 && (
                    <CitationList citations={msg.citations} />
                  )}

                  {/* Engineering Calculation Result Block */}
                  {msg.codeData && (
                    <div className="mt-4 space-y-3 font-mono">
                      <div className="p-3 bg-[#121212] border border-[#8fb03e]">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold text-[#8fb03e] flex items-center">
                            <Beaker className="w-4 h-4 mr-1.5" /> CALCULATED METRIC
                          </span>
                          <span className="text-[9px] text-white bg-[#57692c] px-2 py-0.5 border border-[#8fb03e] flex items-center font-bold">
                            <Shield className="w-3 h-3 mr-1" />
                            AIR-GAPPED EPHEMERAL SANDBOX
                          </span>
                        </div>

                        <div className="text-xs text-[#e8e8e8] bg-[#1a1a1a] p-3 border border-[#8fb03e] whitespace-pre-wrap">
                          {msg.codeData.stdout}
                        </div>
                      </div>

                      {/* Collapsible Formula Toggle */}
                      <button
                        onClick={() => toggleCodeExpand(i)}
                        className="flex items-center space-x-1.5 text-xs text-[#c4c4c4] hover:text-white transition-colors cursor-pointer"
                      >
                        {expandedCode[i] ? <ChevronDown className="w-3.5 h-3.5 text-[#8fb03e]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#8fb03e]" />}
                        <span>INSPECT CALCULATION LOGIC & PYTHON SCRIPT</span>
                      </button>
                      {expandedCode[i] && msg.codeData.script && (
                        <pre className="bg-[#121212] p-3 border border-[#8fb03e] text-xs text-[#e8e8e8] overflow-x-auto">
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
            <div className="flex items-center space-x-2 text-[#8fb03e] text-xs p-3 font-bold">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>PROCESSING OPERATIONAL QUERY AGAINST LOCAL STANDARDS & GROUNDED KNOWLEDGE...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-[#8fb03e] bg-[#242424]">
          {/* Preview Attached Image if Present */}
          {attachedImageSrc && (
            <div className="mb-3 p-2 bg-[#1a1a1a] border border-[#8fb03e] flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <img src={attachedImageSrc} alt="Preview" className="w-10 h-10 object-cover border border-[#8fb03e]" />
                <div>
                  <p className="text-xs font-bold text-[#e8e8e8] truncate">
                    {attachedFile ? attachedFile.name : 'Attached Image Diagram'}
                  </p>
                  <p className="text-[9px] text-[#8fb03e]">Ready to send with operational query</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setAttachedFile(null);
                  setAttachedImageSrc(null);
                }}
                className="text-neutral-400 hover:text-red-400 p-1"
                title="Remove attachment"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          <div className="flex items-center space-x-3">
            <input
              type="file"
              ref={chatFileInputRef}
              onChange={handleChatFileUpload}
              accept="image/*,.pdf"
              className="hidden"
            />
            <button
              onClick={() => chatFileInputRef.current?.click()}
              className="p-2.5 bg-[#1a1a1a] border border-[#8fb03e] text-[#8fb03e] hover:bg-[#57692c] hover:text-white transition-colors cursor-pointer"
              title="Attach P&ID Schematic / Diagram Image"
            >
              <Upload className="w-4 h-4" />
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask an operational query, OISD standard, or calculate pipe metrics..."
              className="flex-1 bg-[#1a1a1a] border border-[#8fb03e] px-4 py-2.5 text-xs text-[#e8e8e8] focus:outline-none focus:bg-[#282828] transition-all"
            />

            <button
              onClick={handleSend}
              disabled={isProcessing || (!input.trim() && !attachedImageSrc)}
              className="px-5 py-2.5 bg-[#57692c] text-white font-bold border-2 border-[#8fb03e] hover:bg-[#8fb03e] hover:text-[#1a1a1a] text-xs transition-all disabled:opacity-50 flex items-center space-x-1.5 cursor-pointer uppercase"
            >
              <span>SEND / भेजें</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Slide-out Schematic Inspector Drawer */}
      {showSchematicDrawer && (
        <div className="w-[600px] flex flex-col bg-[#202020] border-2 border-[#8fb03e] overflow-hidden">
          <div className="p-3 bg-[#242424] border-b border-[#8fb03e] flex justify-between items-center">
            <h3 className="font-bold text-xs text-[#e8e8e8] tracking-wider uppercase">
              P&ID SCHEMATIC INSPECTION CANVAS
            </h3>
            <button
              onClick={() => setShowSchematicDrawer(false)}
              className="text-xs text-[#c4c4c4] hover:text-white font-bold"
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

      {/* Human-In-The-Loop Approval Modal */}
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
