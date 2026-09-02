'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { User, ChevronDown, Shield, LogOut } from 'lucide-react';
import {
  getSession,
  logoutSession,
  getRoleInfo,
  type MRPLSession,
} from '@/lib/session';

export default function HeaderBar() {
  const router = useRouter();
  const [session, setSession] = useState<MRPLSession | null>(null);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  useEffect(() => {
    setSession(getSession());
  }, []);

  if (!session) return null;

  const roleInfo = getRoleInfo(session.role);

  const handleSignOut = () => {
    logoutSession();
    router.replace('/login');
  };

  return (
    <div className="h-14 border-b border-sovereign-border bg-sovereign-surface/60 backdrop-blur-sm flex items-center justify-between px-6 shrink-0 z-30">
      {/* Left: Air-Gap Security Badge */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 px-3 py-1 rounded-full border border-accent-emerald/20 bg-accent-emerald/5">
          <span className="w-2 h-2 rounded-full bg-accent-emerald animate-pulse" />
          <span className="text-xs text-accent-emerald font-medium">Zero WAN Egress | Air-Gapped Intranet Node</span>
        </div>
      </div>

      {/* Right: Authenticated User Profile */}
      <div className="relative flex items-center space-x-3">
        <button
          onClick={() => setShowProfileDropdown(!showProfileDropdown)}
          className="flex items-center space-x-3 text-sm text-gray-300 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-sovereign-surface border border-transparent hover:border-sovereign-border"
        >
          <div className="flex items-center space-x-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center ${roleInfo.bg} ${roleInfo.border} border`}>
              <User className={`w-3.5 h-3.5 ${roleInfo.color}`} />
            </div>
            <div className="text-left hidden sm:block">
              <p className="text-xs font-medium text-gray-200">{session.userName}</p>
              <p className="text-[10px] text-gray-500 font-mono">{session.userId}</p>
            </div>
          </div>
          <span
            className={`text-[10px] font-bold tracking-wider px-2 py-0.5 rounded ${roleInfo.bg} ${roleInfo.color} ${roleInfo.border} border`}
          >
            {roleInfo.label}
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
        </button>

        {showProfileDropdown && (
          <div className="absolute top-full right-0 mt-1 w-64 glass-panel border border-sovereign-border rounded-lg shadow-xl z-50 p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-3">
              Authenticated Session
            </p>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Employee ID</span>
                <span className="font-mono text-gray-200">{session.userId}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Full Name</span>
                <span className="text-gray-200 font-medium">{session.userName}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Role Tier</span>
                <span className={`font-bold ${roleInfo.color}`}>{roleInfo.label}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Assigned Unit</span>
                <span className="text-gray-200">{session.plantUnit}</span>
              </div>
            </div>

            <button
              onClick={handleSignOut}
              className="w-full mt-4 pt-3 border-t border-sovereign-border text-xs text-danger hover:text-red-400 font-medium flex items-center justify-center space-x-1.5 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out Session</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
