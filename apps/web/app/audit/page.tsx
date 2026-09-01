'use client';
import { FileCode2, Search, CheckCircle, ShieldAlert, ChevronDown, ChevronRight } from 'lucide-react';
import { useState, Fragment } from 'react';

const mockLogs = [
  { id: 'BLK-0092', time: '2026-08-31 23:40:12', user: 'Op-A', role: 'L1_OPERATOR', action: 'INIT_QUERY', status: 'SUCCESS', hash: '0x8f4...e2a' },
  { id: 'BLK-0093', time: '2026-08-31 23:41:05', user: 'Agent-PID', role: 'SYSTEM', action: 'EXTRACT_ENTITIES', status: 'SUCCESS', hash: '0x1a9...c7b' },
  { id: 'BLK-0094', time: '2026-08-31 23:42:30', user: 'Agent-Compl', role: 'SYSTEM', action: 'EVALUATE_RULES', status: 'WARNING', hash: '0x4f2...99d' },
  { id: 'BLK-0095', time: '2026-08-31 23:45:01', user: 'Sup-B', role: 'L3_SUPERVISOR', action: 'HITL_APPROVE', status: 'SUCCESS', hash: '0x99e...11f' },
];

export default function AuditPage() {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-full flex flex-col">
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 flex items-center">
            <FileCode2 className="mr-3 w-8 h-8 text-accent-emerald" /> Cryptographic Audit Log
          </h1>
          <p className="text-sm text-gray-400 mt-2 font-mono">Immutable ledger of all human and agent actions</p>
        </div>
        
        <button className="flex items-center px-5 py-2.5 bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/30 rounded-xl hover:bg-accent-emerald/20 transition-all shadow-[0_0_10px_rgba(16,185,129,0.1)] font-mono text-sm font-semibold">
          <CheckCircle className="w-4 h-4 mr-2" /> Verify Chain Integrity
        </button>
      </div>

      <div className="glass-panel border border-sovereign-border rounded-2xl flex-1 overflow-hidden flex flex-col shadow-xl">
        <div className="p-5 border-b border-sovereign-border flex space-x-4 bg-sovereign-surface/50">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-gray-500" />
            <input type="text" placeholder="Search by Block ID, User, or Action..." className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 transition-all shadow-inner" />
          </div>
          <select className="bg-sovereign-dark border border-sovereign-border text-gray-300 text-sm font-mono rounded-xl px-4 py-2.5 outline-none focus:border-accent-cyan cursor-pointer shadow-inner">
            <option>All Roles</option>
            <option>SYSTEM</option>
            <option>L1_OPERATOR</option>
            <option>L3_SUPERVISOR</option>
          </select>
        </div>

        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="text-xs text-gray-500 uppercase bg-sovereign-surface/30 border-b border-sovereign-border sticky top-0 backdrop-blur-md">
              <tr>
                <th className="w-10 px-4 py-4"></th>
                <th className="px-6 py-4 font-semibold tracking-wider">Block ID</th>
                <th className="px-6 py-4 font-semibold tracking-wider">Timestamp</th>
                <th className="px-6 py-4 font-semibold tracking-wider">User / Agent</th>
                <th className="px-6 py-4 font-semibold tracking-wider">Role</th>
                <th className="px-6 py-4 font-semibold tracking-wider">Action</th>
                <th className="px-6 py-4 font-semibold tracking-wider">Status</th>
                <th className="px-6 py-4 font-semibold tracking-wider">Tx Hash</th>
              </tr>
            </thead>
            <tbody>
              {mockLogs.map((log) => (
                <Fragment key={log.id}>
                  <tr 
                    onClick={() => setExpanded(expanded === log.id ? null : log.id)}
                    className={`border-b border-sovereign-border/50 transition-colors cursor-pointer ${expanded === log.id ? 'bg-sovereign-surface/60' : 'hover:bg-sovereign-surface/30'}`}
                  >
                    <td className="px-4 py-4 text-gray-500">
                      {expanded === log.id ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-accent-cyan">{log.id}</td>
                    <td className="px-6 py-4 font-mono text-gray-300">{log.time}</td>
                    <td className="px-6 py-4 text-gray-200 font-medium">{log.user}</td>
                    <td className="px-6 py-4">
                      <span className="font-mono text-[10px] px-2 py-1 bg-gray-800 rounded border border-gray-700 text-gray-300">{log.role}</span>
                    </td>
                    <td className="px-6 py-4 text-gray-200 font-medium">{log.action}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-md text-xs font-bold tracking-wider border ${log.status === 'SUCCESS' ? 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/20' : 'bg-accent-amber/10 text-accent-amber border-accent-amber/20'}`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs tracking-wider text-gray-500">{log.hash}</td>
                  </tr>
                  {expanded === log.id && (
                    <tr className="bg-sovereign-dark/50 border-b border-sovereign-border">
                      <td colSpan={8} className="px-10 py-6">
                        <div className="grid grid-cols-2 gap-8">
                          <div>
                            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Transaction Details</h4>
                            <div className="bg-sovereign-surface rounded-lg p-4 font-mono text-xs text-gray-300 border border-sovereign-border space-y-2">
                              <p><span className="text-gray-500">Prev Hash:</span> 0x3d7...f9c</p>
                              <p><span className="text-gray-500">Signature:</span> ed25519:a7b8...</p>
                              <p><span className="text-gray-500">Nonce:</span> 14482</p>
                            </div>
                          </div>
                          <div>
                            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Payload Data</h4>
                            <div className="bg-sovereign-surface rounded-lg p-4 font-mono text-xs text-accent-amber border border-sovereign-border overflow-x-auto">
                              {`{
  "action": "${log.action}",
  "params": {
    "target": "V-101",
    "value": 150
  },
  "auth": "${log.role}"
}`}
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
        </div>
        
        <div className="p-4 border-t border-sovereign-border bg-sovereign-surface/80 text-xs text-center text-gray-500 font-mono tracking-wider">
          Showing 4 of 43,921 validated blocks · Chain Height: <span className="text-accent-emerald font-bold">#43921</span>
        </div>
      </div>
    </div>
  );
}
