'use client';
import { FileCode2, Search, CheckCircle, ShieldAlert, ChevronDown, ChevronRight, RefreshCw, AlertTriangle } from 'lucide-react';
import { useState, useEffect, Fragment } from 'react';
import { getApiHeaders } from '@/lib/session';

interface AuditBlock {
  block_id: number;
  timestamp: string;
  prev_hash: string;
  user_id: string;
  role: string;
  action: string;
  query: string;
  models_called: string[];
  token_count?: number;
  status: string;
  payload_hash: string;
  combined_sha256: string;
}

export default function AuditPage() {
  const [blocks, setBlocks] = useState<AuditBlock[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verifyResult, setVerifyResult] = useState<{ status: string; message: string; tampered: boolean } | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/audit/blocks?limit=50', {
        headers: getApiHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setBlocks(data.blocks || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('Failed to fetch audit blocks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await fetch('/api/v1/audit/verify', {
        headers: getApiHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setVerifyResult({
          status: data.status,
          message: data.message,
          tampered: data.tampered,
        });
      }
    } catch (err) {
      console.error('Chain verification failed:', err);
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  const filteredBlocks = blocks.filter((b) => {
    const matchesSearch =
      !searchTerm ||
      b.block_id.toString().includes(searchTerm) ||
      b.user_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.query.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === 'ALL' || b.role.toUpperCase() === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-full flex flex-col">
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 flex items-center">
            <FileCode2 className="mr-3 w-8 h-8 text-accent-emerald" /> Cryptographic Audit Ledger
          </h1>
          <p className="text-sm text-gray-400 mt-2 font-mono">
            SHA-256 hash-chained SQLite ledger of all human & agent operations
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={verifying}
          className="flex items-center px-5 py-2.5 bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/30 rounded-xl hover:bg-accent-emerald/20 transition-all shadow-[0_0_10px_rgba(16,185,129,0.1)] font-mono text-sm font-semibold disabled:opacity-50"
        >
          {verifying ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
          Verify Chain Integrity
        </button>
      </div>

      {/* Verification Result Banner */}
      {verifyResult && (
        <div
          className={`mb-6 p-4 rounded-xl border flex items-center justify-between ${
            verifyResult.tampered
              ? 'bg-danger/10 border-danger/30 text-danger'
              : 'bg-accent-emerald/10 border-accent-emerald/30 text-accent-emerald'
          }`}
        >
          <div className="flex items-center space-x-3">
            {verifyResult.tampered ? <ShieldAlert className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
            <div>
              <p className="font-bold text-sm">
                {verifyResult.tampered ? 'Warning: Hash Chain Discrepancy Detected' : 'Cryptographic Ledger Validated'}
              </p>
              <p className="text-xs font-mono opacity-90 mt-0.5">{verifyResult.message}</p>
            </div>
          </div>
          <button onClick={() => setVerifyResult(null)} className="text-xs opacity-60 hover:opacity-100 font-mono">
            Dismiss ✕
          </button>
        </div>
      )}

      <div className="glass-panel border border-sovereign-border rounded-2xl flex-1 overflow-hidden flex flex-col shadow-xl">
        <div className="p-5 border-b border-sovereign-border flex space-x-4 bg-sovereign-surface/50">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-gray-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by Block ID, User, or Action..."
              className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 transition-all shadow-inner"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="bg-sovereign-dark border border-sovereign-border text-gray-300 text-sm font-mono rounded-xl px-4 py-2.5 outline-none focus:border-accent-cyan cursor-pointer shadow-inner"
          >
            <option value="ALL">All Roles</option>
            <option value="OPERATOR">OPERATOR</option>
            <option value="SAFETY_OFFICER">SAFETY_OFFICER</option>
            <option value="PROCESS_ENGINEER">PROCESS_ENGINEER</option>
            <option value="PLANT_DIRECTOR">PLANT_DIRECTOR</option>
          </select>
          <button
            onClick={fetchAuditLogs}
            className="p-2.5 bg-sovereign-dark border border-sovereign-border rounded-xl text-gray-400 hover:text-accent-cyan transition-colors"
            title="Refresh logs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="overflow-x-auto flex-1">
          {loading ? (
            <div className="p-12 text-center text-gray-400 font-mono text-sm">
              Fetching ledger blocks from SQLite audit database...
            </div>
          ) : filteredBlocks.length === 0 ? (
            <div className="p-12 text-center text-gray-400 font-mono text-sm">
              No audit events logged for this session.
            </div>
          ) : (
            <table className="w-full text-left text-sm text-gray-400">
              <thead className="text-xs text-gray-500 uppercase bg-sovereign-surface/30 border-b border-sovereign-border sticky top-0 backdrop-blur-md">
                <tr>
                  <th className="w-10 px-4 py-4"></th>
                  <th className="px-6 py-4 font-semibold tracking-wider">Block ID</th>
                  <th className="px-6 py-4 font-semibold tracking-wider">Timestamp</th>
                  <th className="px-6 py-4 font-semibold tracking-wider">User ID</th>
                  <th className="px-6 py-4 font-semibold tracking-wider">Role</th>
                  <th className="px-6 py-4 font-semibold tracking-wider">Action</th>
                  <th className="px-6 py-4 font-semibold tracking-wider">Status</th>
                  <th className="px-6 py-4 font-semibold tracking-wider">Combined SHA-256</th>
                </tr>
              </thead>
              <tbody>
                {filteredBlocks.map((log) => (
                  <Fragment key={log.block_id}>
                    <tr
                      onClick={() => setExpanded(expanded === log.block_id ? null : log.block_id)}
                      className={`border-b border-sovereign-border/50 transition-colors cursor-pointer ${
                        expanded === log.block_id ? 'bg-sovereign-surface/60' : 'hover:bg-sovereign-surface/30'
                      }`}
                    >
                      <td className="px-4 py-4 text-gray-500">
                        {expanded === log.block_id ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </td>
                      <td className="px-6 py-4 font-mono font-bold text-accent-cyan">#{log.block_id}</td>
                      <td className="px-6 py-4 font-mono text-xs text-gray-300">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-gray-200 font-medium font-mono text-xs">{log.user_id}</td>
                      <td className="px-6 py-4">
                        <span className="font-mono text-[10px] px-2 py-1 bg-gray-800 rounded border border-gray-700 text-gray-300">
                          {log.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-200 font-medium font-mono text-xs">{log.action}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2.5 py-1 rounded-md text-xs font-bold tracking-wider border ${
                            log.status === 'success' || log.status === 'SUCCESS'
                              ? 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/20'
                              : 'bg-accent-amber/10 text-accent-amber border-accent-amber/20'
                          }`}
                        >
                          {log.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs tracking-wider text-gray-500">
                        {log.combined_sha256 ? `${log.combined_sha256.slice(0, 12)}...` : 'N/A'}
                      </td>
                    </tr>
                    {expanded === log.block_id && (
                      <tr className="bg-sovereign-dark/50 border-b border-sovereign-border">
                        <td colSpan={8} className="px-10 py-6">
                          <div className="grid grid-cols-2 gap-8">
                            <div>
                              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                                Cryptographic Linking
                              </h4>
                              <div className="bg-sovereign-surface rounded-lg p-4 font-mono text-xs text-gray-300 border border-sovereign-border space-y-2">
                                <p>
                                  <span className="text-gray-500">Prev Hash:</span>{' '}
                                  <span className="text-accent-cyan">{log.prev_hash}</span>
                                </p>
                                <p>
                                  <span className="text-gray-500">Payload Hash:</span> {log.payload_hash}
                                </p>
                                <p>
                                  <span className="text-gray-500">Combined SHA-256:</span>{' '}
                                  <span className="text-accent-emerald">{log.combined_sha256}</span>
                                </p>
                              </div>
                            </div>
                            <div>
                              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                                Action Payload & Query
                              </h4>
                              <div className="bg-sovereign-surface rounded-lg p-4 font-mono text-xs text-accent-amber border border-sovereign-border overflow-x-auto">
                                <p className="text-gray-300 mb-1">
                                  <span className="text-gray-500">Query:</span> "{log.query}"
                                </p>
                                <p className="text-gray-300">
                                  <span className="text-gray-500">Models:</span> {JSON.stringify(log.models_called)}
                                </p>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="p-4 border-t border-sovereign-border bg-sovereign-surface/80 text-xs text-center text-gray-500 font-mono tracking-wider">
          Showing {filteredBlocks.length} of {total} validated blocks · Chain Height:{' '}
          <span className="text-accent-emerald font-bold">#{total}</span>
        </div>
      </div>
    </div>
  );
}

