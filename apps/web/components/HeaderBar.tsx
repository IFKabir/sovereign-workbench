'use client';
import { useState, useEffect } from 'react';
import { Clock, MapPin, User, ChevronDown, Shield } from 'lucide-react';
import {
  getSession,
  updateSession,
  getCurrentShift,
  getRoleInfo,
  PLANT_UNITS,
  ROLES,
  type MRPLSession,
  type RoleId,
  type PlantUnitId,
} from '@/lib/session';

export default function HeaderBar() {
  const [session, setSession] = useState<MRPLSession | null>(null);
  const [shift, setShift] = useState(getCurrentShift());
  const [showUnitDropdown, setShowUnitDropdown] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState('');

  useEffect(() => {
    setSession(getSession());
    const interval = setInterval(() => setShift(getCurrentShift()), 60000);
    return () => clearInterval(interval);
  }, []);

  if (!session) return null;

  const roleInfo = getRoleInfo(session.role);

  const handleUnitChange = (unitId: PlantUnitId) => {
    const updated = updateSession({ plantUnit: unitId });
    setSession(updated);
    setShowUnitDropdown(false);
  };

  const handleRoleChange = (roleId: RoleId) => {
    const updated = updateSession({ role: roleId });
    setSession(updated);
  };

  const handleNameSave = () => {
    if (nameInput.trim()) {
      const updated = updateSession({ userName: nameInput.trim() });
      setSession(updated);
    }
    setEditingName(false);
  };

  return (
    <div className="h-14 border-b border-sovereign-border bg-sovereign-surface/60 backdrop-blur-sm flex items-center justify-between px-6 shrink-0">
      {/* Left: Plant Unit */}
      <div className="flex items-center space-x-6">
        <div className="relative">
          <button
            onClick={() => { setShowUnitDropdown(!showUnitDropdown); setShowProfileDropdown(false); }}
            className="flex items-center space-x-2 text-sm text-gray-300 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-sovereign-surface border border-transparent hover:border-sovereign-border"
          >
            <MapPin className="w-4 h-4 text-accent-cyan" />
            <span className="font-medium">{session.plantUnit}</span>
            <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
          </button>
          {showUnitDropdown && (
            <div className="absolute top-full left-0 mt-1 w-72 glass-panel border border-sovereign-border rounded-lg shadow-xl z-50 py-1">
              <p className="px-3 py-2 text-xs text-gray-500 uppercase tracking-wider font-semibold border-b border-sovereign-border">Active Plant Unit</p>
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

        {/* Air-Gap Badge */}
        <div className="hidden xl:flex items-center space-x-2 px-3 py-1 rounded-full border border-accent-emerald/20 bg-accent-emerald/5">
          <span className="w-2 h-2 rounded-full bg-accent-emerald animate-pulse" />
          <span className="text-xs text-accent-emerald font-medium">Air-Gapped</span>
        </div>
      </div>

      {/* Right: User Profile */}
      <div className="relative">
        <button
          onClick={() => { setShowProfileDropdown(!showProfileDropdown); setShowUnitDropdown(false); }}
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
          <span className={`text-[10px] font-bold tracking-wider px-2 py-0.5 rounded ${roleInfo.bg} ${roleInfo.color} ${roleInfo.border} border`}>
            {roleInfo.label}
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
        </button>

        {showProfileDropdown && (
          <div className="absolute top-full right-0 mt-1 w-72 glass-panel border border-sovereign-border rounded-lg shadow-xl z-50">
            <div className="p-4 border-b border-sovereign-border">
              <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-3">User Profile</p>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Employee ID</span>
                  <span className="text-xs font-mono text-gray-200">{session.userId}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Name</span>
                  {editingName ? (
                    <input
                      autoFocus
                      value={nameInput}
                      onChange={(e) => setNameInput(e.target.value)}
                      onBlur={handleNameSave}
                      onKeyDown={(e) => e.key === 'Enter' && handleNameSave()}
                      className="text-xs text-gray-200 bg-sovereign-dark border border-sovereign-border rounded px-2 py-1 w-32 focus:outline-none focus:border-accent-cyan"
                    />
                  ) : (
                    <button
                      onClick={() => { setEditingName(true); setNameInput(session.userName); }}
                      className="text-xs text-gray-200 hover:text-accent-cyan transition-colors"
                    >
                      {session.userName} ✎
                    </button>
                  )}
                </div>
              </div>
            </div>
            <div className="p-3">
              <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-2">Switch Role</p>
              <div className="space-y-1">
                {ROLES.map((role) => (
                  <button
                    key={role.id}
                    onClick={() => handleRoleChange(role.id)}
                    className={`w-full text-left px-3 py-2 text-xs rounded transition-colors flex items-center justify-between ${
                      session.role === role.id
                        ? `${role.bg} ${role.color}`
                        : 'text-gray-300 hover:bg-sovereign-surface'
                    }`}
                  >
                    <span>{role.label}</span>
                    {session.role === role.id && <Shield className="w-3 h-3" />}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
