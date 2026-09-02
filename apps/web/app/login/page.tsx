'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, Lock, User, Building2, Key, ArrowRight } from 'lucide-react';
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
    <div className="min-h-screen w-full flex items-center justify-center p-6 bg-[#1a1a1a] industrial-grid relative select-none font-mono">
      <div className="bg-[#202020] w-full max-w-md border-2 border-[#8fb03e] shadow-2xl p-8 relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-[#57692c] border-2 border-[#8fb03e] p-1 overflow-hidden flex items-center justify-center mx-auto mb-4">
            <img src="/mrpl_logo.jpg" alt="MRPL Logo" className="w-full h-full object-contain" />
          </div>
          <h1 className="text-lg font-bold text-[#e8e8e8] tracking-wider uppercase">
            Mangalore Refinery and Petrochemicals Limited
          </h1>
          <h2 className="text-xs text-[#8fb03e] mt-1 font-semibold">
            MRPL Sovereign Operational Copilot Node
          </h2>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-[#2b2b2b] border border-[#8fb03e] mt-3 text-[10px] text-[#8fb03e] font-bold">
            <Shield className="w-3.5 h-3.5 text-[#8fb03e]" />
            <span>Air-Gapped Intranet Node // On-Premise Auth</span>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-3 bg-red-950/40 border border-red-500 text-red-400 text-xs flex items-center space-x-2">
            <Lock className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-[#8fb03e] uppercase tracking-wider mb-1">
              Employee ID / कर्मचारी आईडी
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3 top-3 text-neutral-500" />
              <input
                type="text"
                required
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="e.g. EMP-10492"
                className="w-full bg-[#1a1a1a] border border-[#8fb03e] pl-10 pr-4 py-2.5 text-sm text-[#e8e8e8] focus:outline-none focus:bg-[#282828] transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#8fb03e] uppercase tracking-wider mb-1">
              Full Name / पूरा नाम
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3 top-3 text-neutral-500" />
              <input
                type="text"
                required
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="e.g. Rajesh Kumar"
                className="w-full bg-[#1a1a1a] border border-[#8fb03e] pl-10 pr-4 py-2.5 text-sm text-[#e8e8e8] focus:outline-none focus:bg-[#282828] transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#8fb03e] uppercase tracking-wider mb-1">
              Assigned Plant Unit / संयंत्र इकाई
            </label>
            <div className="relative">
              <Building2 className="w-4 h-4 absolute left-3 top-3 text-neutral-500" />
              <select
                value={plantUnit}
                onChange={(e) => setPlantUnit(e.target.value as PlantUnitId)}
                className="w-full bg-[#1a1a1a] border border-[#8fb03e] pl-10 pr-4 py-2.5 text-sm text-[#e8e8e8] focus:outline-none focus:bg-[#282828] cursor-pointer"
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
            <label className="block text-xs font-bold text-[#8fb03e] uppercase tracking-wider mb-1">
              Operational Role Tier / भूमिका श्रेणी
            </label>
            <div className="relative">
              <Shield className="w-4 h-4 absolute left-3 top-3 text-neutral-500" />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as RoleId)}
                className="w-full bg-[#1a1a1a] border border-[#8fb03e] pl-10 pr-4 py-2.5 text-sm text-[#e8e8e8] focus:outline-none focus:bg-[#282828] cursor-pointer"
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
            <label className="block text-xs font-bold text-[#8fb03e] uppercase tracking-wider mb-1">
              Security Passcode / Badge PIN
            </label>
            <div className="relative">
              <Key className="w-4 h-4 absolute left-3 top-3 text-neutral-500" />
              <input
                type="password"
                required
                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#1a1a1a] border border-[#8fb03e] pl-10 pr-4 py-2.5 text-sm text-[#e8e8e8] focus:outline-none focus:bg-[#282828] transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-6 py-3 px-4 bg-[#57692c] hover:bg-[#8fb03e] hover:text-[#1a1a1a] text-white font-bold border-2 border-[#8fb03e] transition-all flex items-center justify-center space-x-2 text-sm disabled:opacity-50 cursor-pointer"
          >
            <span>AUTHENTICATE SESSION / प्रवेश करें</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-neutral-700 text-center">
          <p className="text-[10px] text-neutral-500 font-mono">
            MRPL IT Infrastructure Security Policy // Confidential Data Access
          </p>
        </div>
      </div>
    </div>
  );
}
