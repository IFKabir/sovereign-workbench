'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { useState } from 'react';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

interface HitlModalProps {
  isOpen: boolean;
  onClose: () => void;
  actionType: string;
  riskLevel: RiskLevel;
  draftContent: string;
  complianceFlags: string[];
  requiredRole: string;
  threadId?: string;
  onApproveAction?: (approved: boolean, comment: string) => void;
}

const riskColors = {
  LOW: 'text-accent-emerald border-accent-emerald bg-accent-emerald/10',
  MEDIUM: 'text-accent-amber border-accent-amber bg-accent-amber/10',
  HIGH: 'text-orange-500 border-orange-500 bg-orange-500/10',
  CRITICAL: 'text-danger border-danger bg-danger/10',
};

export default function HitlApprovalModal({
  isOpen,
  onClose,
  actionType,
  riskLevel,
  draftContent,
  complianceFlags,
  requiredRole,
  threadId,
  onApproveAction,
}: HitlModalProps) {
  const [comment, setComment] = useState('');

  if (!isOpen) return null;

  const handleDecision = (approved: boolean) => {
    if (onApproveAction) {
      onApproveAction(approved, comment);
    }
    onClose();
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-sovereign-dark/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="glass-panel w-full max-w-2xl rounded-2xl overflow-hidden border border-sovereign-border shadow-2xl"
        >
          <div
            className={`p-5 border-b flex justify-between items-center ${riskColors[riskLevel]
              .replace('text-', 'bg-')
              .replace('/10', '/20')} border-b-2`}
            style={{ borderBottomColor: 'currentcolor' }}
          >
            <div className="flex items-center space-x-3">
              <AlertTriangle className={`w-7 h-7 ${riskColors[riskLevel].split(' ')[0]}`} />
              <h2 className="text-xl font-bold text-gray-100">Human-in-the-Loop Required</h2>
            </div>
            <span className={`px-3 py-1.5 text-xs font-bold tracking-wider rounded border ${riskColors[riskLevel]}`}>
              {riskLevel} RISK
            </span>
          </div>

          <div className="p-8 space-y-8">
            <div>
              <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-semibold">Action Type</h3>
              <p className="font-mono text-gray-200 text-sm bg-sovereign-surface inline-block px-3 py-1.5 rounded border border-sovereign-border">
                {actionType}
              </p>
            </div>

            <div>
              <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-semibold">Draft Response / Plan</h3>
              <div className="bg-sovereign-dark p-4 rounded-xl border border-sovereign-border font-mono text-sm text-gray-300 max-h-48 overflow-y-auto leading-relaxed shadow-inner">
                {draftContent}
              </div>
            </div>

            {complianceFlags && complianceFlags.length > 0 && (
              <div>
                <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-3 font-semibold">Compliance Flags</h3>
                <ul className="space-y-2">
                  {complianceFlags.map((flag, idx) => (
                    <li key={idx} className="text-sm text-accent-amber flex items-start bg-accent-amber/5 p-2 rounded border border-accent-amber/10">
                      <AlertTriangle className="w-4 h-4 mr-2.5 mt-0.5 flex-shrink-0" />
                      <span>{flag}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-semibold">Approver Comments</h3>
              <textarea
                className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl p-4 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan resize-none shadow-inner transition-colors"
                rows={3}
                placeholder="Enter approval/rejection rationale..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
              <div className="flex items-center justify-between mt-2">
                <p className="text-xs text-gray-500">
                  Required Role: <span className="font-mono text-accent-cyan px-1.5 py-0.5 rounded bg-accent-cyan/10">{requiredRole}</span>
                </p>
                {threadId && <p className="text-xs text-gray-500 font-mono">Thread: {threadId.slice(0, 8)}...</p>}
              </div>
            </div>
          </div>

          <div className="p-5 border-t border-sovereign-border bg-sovereign-surface/80 flex justify-end space-x-4">
            <button
              onClick={() => handleDecision(false)}
              className="px-5 py-2.5 rounded-lg font-medium border border-sovereign-border hover:bg-sovereign-border/50 hover:text-white transition-colors flex items-center text-gray-400"
            >
              <XCircle className="w-4 h-4 mr-2" /> Reject
            </button>
            <button
              onClick={() => handleDecision(true)}
              className="px-5 py-2.5 rounded-lg font-medium bg-accent-cyan/20 text-accent-cyan hover:bg-accent-cyan/30 border border-accent-cyan/50 transition-all flex items-center shadow-[0_0_10px_rgba(6,182,212,0.15)] hover:shadow-[0_0_15px_rgba(6,182,212,0.25)]"
            >
              <CheckCircle className="w-4 h-4 mr-2" /> Approve Action
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
