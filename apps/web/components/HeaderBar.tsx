'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Clock, MapPin, User, ChevronDown, Shield, LogOut } from 'lucide-react';
import {
  getSession,
  updateSession,
  logoutSession,
  getCurrentShift,
  getRoleInfo,
  PLANT_UNITS,
  type MRPLSession,
  type PlantUnitId,
} from '@/lib/session';

export default function HeaderBar() {
  const router = useRouter();
  const [session, setSession] = useState<MRPLSession | null>(null);
  const [shift, setShift] = useState(getCurrentShift());
  const [showUnitDropdown, setShowUnitDropdown] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  useEffect(() => {
    setSession(getSession());
    const interval = setInterval(() => setShift(getCurrentShift()), 60000);
    return () => clearInterval(interval);
  }, []);

  if (!session) return null;

  const roleInfo = getRoleInfo(session.role);

  const handleUnitChange = (unitId: PlantUnitId) => {
    const updated = updateSession({ plantUnit: unitId });
    if (updated) setSession(updated);
    setShowUnitDropdown(false);
  };

  const handleSignOut = () => {
    logoutSession();
    router.replace('/login');
  };

  return (
    <div className="h-14 border-b border-sovereign-border bg-sovereign-surface/60 backdrop-blur-sm flex items-center justify-between px-6 shrink-0 z-30">
      {/* Left: Plant Unit */}
      <div className="flex items-center space-x-6">
        <div className="relative">
          <button
            onClick={() => {
              setShowUnitDropdown(!showUnitDropdown);
              setShowProfileDropdown(false);
            }}
            className="flex items-center space-x-2 text-sm text-gray-300 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-sovereign-surface border border-transparent hover:border-sovereign-border"
          >
            <MapPin className="w-4 h-4 text-accent-cyan" />
            <span className="font-medium">{session.plantUnit}</span>
            <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
          </button>
          {showUnitDropdown && (
            <div className="absolute top-full left-0 mt-1 w-72 glass-panel border border-sovereign-border rounded-lg shadow-xl z-50 py-1">
              <p className="px-3 py-2 text-xs text-gray-500 uppercase tracking-wider font-semibold border-b border-sovereign-border">
                Active Plant Unit
              </p>
              {PLANT_UNITS.map((unit) => (
                <button
                  key={unit.id}
                  onClick={() => handleUnitChange(unit.id)}
                  className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                    session.plantUnit === unit.id
                      ? 'bg-accent-cyan/10 text-accent-cyan'
                      : 'text-gray-300 hover:bg-sovereign-surface hover:text-white'
                  }`}
                >
                  {unit.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Shift Indicator */}
        <div className="flex items-center space-x-2 text-sm">
          <Clock className="w-4 h-4 text-accent-amber" />
          <span className="text-gray-400">{shift.label}:</span>
          <span className="text-gray-200 font-mono text-xs">{shift.timeRange}</span>
        </div>

        {/* Air-Gap Security Badge */}
        <div className="hidden xl:flex items-center space-x-2 px-3 py-1 rounded-full border border-accent-emerald/20 bg-accent-emerald/5">
          <span className="w-2 h-2 rounded-full bg-accent-emerald animate-pulse" />
          <span className="text-xs text-accent-emerald font-medium">Zero WAN Egress | Air-Gapped Intranet Node</span>
        </div>
      </div>

      {/* Right: Authenticated User Profile */}
      <div className="relative flex items-center space-x-3">
        <button
          onClick={() => {
            setShowProfileDropdown(!showProfileDropdown);
            setShowUnitDropdown(false);
          }}
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
