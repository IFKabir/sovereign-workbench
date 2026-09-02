'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Flame, Shield, Lock, User, Building2, Key, CheckCircle, ArrowRight } from 'lucide-react';
import { loginSession, PLANT_UNITS, ROLES, type PlantUnitId, type RoleId } from '@/lib/session';

export default function LoginPage() {
  const router = useRouter();
  const [userId, setUserId] = useState('EMP-10492');
  const [userName, setUserName] = useState('Rajesh Kumar');
  const [plantUnit, setPlantUnit] = useState<PlantUnitId>('CDU-2');
  const [role, setRole] = useState<RoleId>('PROCESS_ENGINEER');
  const [passcode, setPasscode] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!userId.trim()) {
      setError('Employee ID is required.');
      return;
    }
    if (!userName.trim()) {
      setError('Full Name is required.');
      return;
    }
    if (!passcode.trim()) {
      setError('Security Passcode / Badge PIN is required.');
      return;
    }

    setSubmitting(true);
    try {
      loginSession({
        userId: userId.trim().toUpperCase(),
        userName: userName.trim(),
        plantUnit,
        role,
      });

      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-6 bg-sovereign-dark industrial-grid relative overflow-hidden">
      {/* Ambient background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent-cyan/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-emerald/10 rounded-full blur-3xl pointer-events-none" />

      <div className="glass-panel w-full max-w-md rounded-2xl border border-sovereign-border shadow-2xl p-8 relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent-cyan via-accent-emerald to-accent-amber flex items-center justify-center mx-auto mb-4 shadow-xl shadow-accent-cyan/20">
            <Flame className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-xl font-bold text-gray-100 tracking-tight">
            MRPL Sovereign Terminal
          </h1>
          <p className="text-xs text-gray-400 mt-1 font-mono">
            Mangalore Refinery and Petrochemicals Limited
          </p>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-accent-emerald/10 border border-accent-emerald/20 mt-3 text-[10px] text-accent-emerald font-semibold">
            <Shield className="w-3 h-3" />
            <span>Air-Gapped Intranet Node // On-Premise Auth</span>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-3 rounded-xl bg-danger/10 border border-danger/30 text-danger text-xs flex items-center space-x-2">
            <Lock className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
              Employee ID
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3.5 top-3 text-gray-500" />
              <input
                type="text"
                required
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="e.g. EMP-10492"
                className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-200 font-mono focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 transition-all shadow-inner"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3.5 top-3 text-gray-500" />
              <input
                type="text"
                required
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="e.g. Rajesh Kumar"
                className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 transition-all shadow-inner"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
              Assigned Plant Unit
            </label>
            <div className="relative">
              <Building2 className="w-4 h-4 absolute left-3.5 top-3 text-gray-500" />
              <select
                value={plantUnit}
                onChange={(e) => setPlantUnit(e.target.value as PlantUnitId)}
                className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 transition-all shadow-inner cursor-pointer"
              >
                {PLANT_UNITS.map((unit) => (
                  <option key={unit.id} value={unit.id}>
                    {unit.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
              Operational Role Tier
            </label>
            <div className="relative">
              <Shield className="w-4 h-4 absolute left-3.5 top-3 text-gray-500" />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as RoleId)}
                className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 transition-all shadow-inner cursor-pointer"
              >
                {ROLES.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label} ({r.id === 'OPERATOR' ? 'Tier 10' : r.id === 'SAFETY_OFFICER' ? 'Tier 20' : r.id === 'PROCESS_ENGINEER' ? 'Tier 30' : 'Tier 40'})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
              Security Passcode / Badge PIN
            </label>
            <div className="relative">
              <Key className="w-4 h-4 absolute left-3.5 top-3 text-gray-500" />
              <input
                type="password"
                required
                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-sovereign-dark border border-sovereign-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-200 font-mono focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 transition-all shadow-inner"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-6 py-3 px-4 bg-gradient-to-r from-accent-cyan to-accent-emerald hover:from-accent-cyan/90 hover:to-accent-emerald/90 text-slate-950 font-bold rounded-xl transition-all shadow-lg shadow-accent-cyan/20 flex items-center justify-center space-x-2 text-sm disabled:opacity-50"
          >
            <span>Authenticate Session</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-sovereign-border text-center">
          <p className="text-[11px] text-gray-500 font-mono">
            MRPL IT Infrastructure Security Policy // Confidential Data Access
          </p>
        </div>
      </div>
    </div>
  );
}
