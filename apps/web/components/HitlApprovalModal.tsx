'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle, XCircle, Shield, Flame } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getSession, getRoleInfo, type MRPLSession } from '@/lib/session';

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
  const [session, setSession] = useState<MRPLSession | null>(null);
  const [safetyChecks, setSafetyChecks] = useState({
    dbb: false,
    gasTest: false,
    fireEquip: false,
  });

  useEffect(() => {
    if (isOpen) {
      setSession(getSession());
      setSafetyChecks({ dbb: false, gasTest: false, fireEquip: false });
      setComment('');
    }
  }, [isOpen]);

  if (!isOpen || !session) return null;

  const roleInfo = getRoleInfo(session.role);
  const canApprove = session.role !== 'OPERATOR';
  const allChecked = safetyChecks.dbb && safetyChecks.gasTest && safetyChecks.fireEquip;
  const approveEnabled = canApprove && allChecked;

  const handleDecision = (approved: boolean) => {
    if (onApproveAction) {
      onApproveAction(approved, comment);
    }
    onClose();
  };

  const requestId = threadId ? threadId.slice(0, 8).toUpperCase() : 'N/A';

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-sovereign-dark/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="glass-panel w-full max-w-2xl rounded-2xl overflow-hidden border border-sovereign-border shadow-2xl max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="p-5 border-b border-sovereign-border bg-gradient-to-r from-danger/10 to-accent-amber/10">
            <div className="flex justify-between items-start">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-lg bg-danger/20 border border-danger/30 flex items-center justify-center">
                  <Flame className="w-5 h-5 text-danger" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-100">MRPL Fire & Safety Department</h2>
                  <p className="text-xs text-gray-400">Authorization Gate — Digital Permit Clearance</p>
                </div>
              </div>
              <span className={`px-3 py-1.5 text-xs font-bold tracking-wider rounded border ${riskColors[riskLevel]}`}>
                {riskLevel} RISK
              </span>
            </div>
          </div>

          <div className="p-6 space-y-5">
            {/* Request Info Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-sovereign-surface p-3 rounded-lg border border-sovereign-border">
                <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-1">Request ID</p>
                <p className="font-mono text-sm text-gray-200">PTW-{requestId}</p>
              </div>
              <div className="bg-sovereign-surface p-3 rounded-lg border border-sovereign-border">
                <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-1">Plant Unit</p>
                <p className="text-sm text-gray-200">{session.plantUnit}</p>
              </div>
            </div>

            {/* Requested Action */}
            <div>
              <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-semibold">Requested Action</h3>
              <p className="font-mono text-gray-200 text-sm bg-sovereign-surface inline-block px-3 py-1.5 rounded border border-sovereign-border">
                {actionType}
              </p>
            </div>

            {/* Draft Content */}
            <div>
              <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-semibold">Action Details</h3>
              <div className="bg-sovereign-dark p-4 rounded-xl border border-sovereign-border font-mono text-sm text-gray-300 max-h-32 overflow-y-auto leading-relaxed shadow-inner">
                {draftContent}
              </div>
            </div>

            {/* Compliance Flags */}
            {complianceFlags && complianceFlags.length > 0 && (
              <div>
                <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-semibold">Safety Standard Cross-Reference</h3>
                <ul className="space-y-1.5">
                  {complianceFlags.map((flag, idx) => (
                    <li key={idx} className="text-sm text-accent-amber flex items-start bg-accent-amber/5 p-2 rounded border border-accent-amber/10">
                      <AlertTriangle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>{flag}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Mandatory Safety Checkboxes */}
            <div className="bg-sovereign-surface/50 p-4 rounded-xl border border-sovereign-border">
              <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-3 font-semibold flex items-center">
                <Shield className="w-3.5 h-3.5 mr-1.5" />
                Mandatory Pre-flight Safety Confirmation
              </h3>
              <div className="space-y-3">
                <label className={`flex items-start space-x-3 ${canApprove ? 'cursor-pointer group' : 'cursor-not-allowed opacity-60'}`}>
                  <input
                    type="checkbox"
                    id="chk-dbb"
                    disabled={!canApprove}
                    checked={safetyChecks.dbb}
                    onChange={(e) => setSafetyChecks(prev => ({ ...prev, dbb: e.target.checked }))}
                    className="mt-0.5 w-4 h-4 rounded border-sovereign-border bg-sovereign-dark accent-accent-cyan disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                  <span className="text-sm text-gray-300 group-hover:text-gray-200 transition-colors">Double Block and Bleed (DBB) or physical blinding verified</span>
                </label>
                <label className={`flex items-start space-x-3 ${canApprove ? 'cursor-pointer group' : 'cursor-not-allowed opacity-60'}`}>
                  <input
                    type="checkbox"
                    id="chk-gastest"
                    disabled={!canApprove}
                    checked={safetyChecks.gasTest}
                    onChange={(e) => setSafetyChecks(prev => ({ ...prev, gasTest: e.target.checked }))}
                    className="mt-0.5 w-4 h-4 rounded border-sovereign-border bg-sovereign-dark accent-accent-cyan disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                  <span className="text-sm text-gray-300 group-hover:text-gray-200 transition-colors">Atmospheric Gas Test conducted (LEL {'<'} 0%, H₂S {'<'} 10 ppm)</span>
                </label>
                <label className={`flex items-start space-x-3 ${canApprove ? 'cursor-pointer group' : 'cursor-not-allowed opacity-60'}`}>
                  <input
                    type="checkbox"
                    id="chk-fireequip"
                    disabled={!canApprove}
                    checked={safetyChecks.fireEquip}
                    onChange={(e) => setSafetyChecks(prev => ({ ...prev, fireEquip: e.target.checked }))}
                    className="mt-0.5 w-4 h-4 rounded border-sovereign-border bg-sovereign-dark accent-accent-cyan disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                  <span className="text-sm text-gray-300 group-hover:text-gray-200 transition-colors">Firefighting equipment positioned on standby</span>
                </label>
              </div>
            </div>

            {/* Approver Section */}
            <div>
              <h3 className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-semibold">Authorization Notes</h3>
              <textarea
                className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl p-4 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan resize-none shadow-inner transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                rows={2}
                placeholder={canApprove ? 'Enter approval/rejection rationale and authorization PIN...' : 'You do not have authorization to approve this action.'}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                disabled={!canApprove}
              />
              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">Signed as:</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${roleInfo.bg} ${roleInfo.color} ${roleInfo.border} border`}>
                    {roleInfo.label}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">({session.userId})</span>
                </div>
                {threadId && <p className="text-xs text-gray-500 font-mono">Block: {requestId}</p>}
              </div>
            </div>

            {/* OPERATOR warning & role switcher guidance */}
            {!canApprove && (
              <div className="p-3 rounded-lg border border-amber-900/60 bg-amber-950/20 text-amber-300 text-xs flex items-center justify-between">
                <span>Signed in as <strong>{roleInfo.label}</strong>. Switch to <strong>Safety Officer</strong> or <strong>Process Engineer</strong> in top navigation bar to unlock authorization.</span>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="p-5 border-t border-sovereign-border bg-sovereign-surface/80 flex justify-end space-x-4">
            <button
              onClick={() => handleDecision(false)}
              className="px-5 py-2.5 rounded-lg font-medium border border-sovereign-border hover:bg-sovereign-border/50 hover:text-white transition-colors flex items-center text-gray-400"
            >
              <XCircle className="w-4 h-4 mr-2" /> Reject & Escalate
            </button>
            <button
              onClick={() => handleDecision(true)}
              disabled={!approveEnabled}
              className={`px-5 py-2.5 rounded-lg font-medium transition-all flex items-center ${
                approveEnabled
                  ? 'bg-accent-emerald/20 text-accent-emerald hover:bg-accent-emerald/30 border border-accent-emerald/50 shadow-[0_0_10px_rgba(16,185,129,0.15)] hover:shadow-[0_0_15px_rgba(16,185,129,0.25)]'
                  : 'bg-sovereign-border text-gray-500 border border-sovereign-border cursor-not-allowed'
              }`}
            >
              <CheckCircle className="w-4 h-4 mr-2" /> Authorize & Resume
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
