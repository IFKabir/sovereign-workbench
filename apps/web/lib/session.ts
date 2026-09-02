/**
 * MRPL Session Management Utility
 * 
 * Client-side session isolation for multi-user intranet access.
 * Stores user identity, plant unit, role, and session ID in localStorage.
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

export const PLANT_UNITS = [
  { id: 'CDU-1', label: 'CDU-1 (Crude Distillation Unit 1)' },
  { id: 'CDU-2', label: 'CDU-2 (Crude Distillation Unit 2)' },
  { id: 'HCU', label: 'HCU (Hydrocracker Unit)' },
  { id: 'VGO-HDT', label: 'VGO-HDT (Vacuum Gas Oil Hydrotreater)' },
  { id: 'AROMATICS', label: 'Aromatics Complex' },
  { id: 'CPP', label: 'Captive Power Plant' },
] as const;

export const ROLES = [
  { id: 'OPERATOR', label: 'Operator', color: 'text-accent-cyan', bg: 'bg-accent-cyan/10', border: 'border-accent-cyan/30' },
  { id: 'SAFETY_OFFICER', label: 'Safety Officer', color: 'text-accent-amber', bg: 'bg-accent-amber/10', border: 'border-accent-amber/30' },
  { id: 'PROCESS_ENGINEER', label: 'Process Engineer', color: 'text-accent-emerald', bg: 'bg-accent-emerald/10', border: 'border-accent-emerald/30' },
  { id: 'PLANT_DIRECTOR', label: 'Plant Director', color: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/30' },
] as const;

export type RoleId = typeof ROLES[number]['id'];
export type PlantUnitId = typeof PLANT_UNITS[number]['id'];

export const SHIFTS = [
  { id: 'A', label: 'Shift A', start: 6, end: 14 },
  { id: 'B', label: 'Shift B', start: 14, end: 22 },
  { id: 'C', label: 'Shift C', start: 22, end: 6 },
] as const;

// ---------------------------------------------------------------------------
// Session Interface
// ---------------------------------------------------------------------------

export interface MRPLSession {
  userId: string;
  userName: string;
  plantUnit: PlantUnitId;
  role: RoleId;
  sessionId: string;
}

// ---------------------------------------------------------------------------
// Storage Keys
// ---------------------------------------------------------------------------

const KEYS = {
  userId: 'mrpl_user_id',
  userName: 'mrpl_user_name',
  plantUnit: 'mrpl_plant_unit',
  role: 'mrpl_role',
  sessionId: 'mrpl_session_id',
} as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function generateEmployeeId(): string {
  const num = Math.floor(10000 + Math.random() * 90000);
  return `EMP-${num}`;
}

// ---------------------------------------------------------------------------
// Session API
// ---------------------------------------------------------------------------

export function isLoggedIn(): boolean {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem(KEYS.userId);
}

export function loginSession(params: {
  userId: string;
  userName: string;
  plantUnit: PlantUnitId;
  role: RoleId;
}): MRPLSession {
  if (typeof window === 'undefined') {
    throw new Error('loginSession can only be called in browser environment');
  }

  const session: MRPLSession = {
    userId: params.userId,
    userName: params.userName,
    plantUnit: params.plantUnit,
    role: params.role,
    sessionId: crypto.randomUUID(),
  };

  localStorage.setItem(KEYS.userId, session.userId);
  localStorage.setItem(KEYS.userName, session.userName);
  localStorage.setItem(KEYS.plantUnit, session.plantUnit);
  localStorage.setItem(KEYS.role, session.role);
  localStorage.setItem(KEYS.sessionId, session.sessionId);
  localStorage.setItem('mrpl_logged_in_at', new Date().toISOString());

  return session;
}

export function logoutSession(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(KEYS.userId);
  localStorage.removeItem(KEYS.userName);
  localStorage.removeItem(KEYS.plantUnit);
  localStorage.removeItem(KEYS.role);
  localStorage.removeItem(KEYS.sessionId);
  localStorage.removeItem('mrpl_logged_in_at');
}

export function getSession(): MRPLSession | null {
  if (typeof window === 'undefined') return null;
  const userId = localStorage.getItem(KEYS.userId);
  if (!userId) return null;

  return {
    userId,
    userName: localStorage.getItem(KEYS.userName) || 'Operator',
    plantUnit: (localStorage.getItem(KEYS.plantUnit) as PlantUnitId) || 'CDU-2',
    role: (localStorage.getItem(KEYS.role) as RoleId) || 'OPERATOR',
    sessionId: localStorage.getItem(KEYS.sessionId) || crypto.randomUUID(),
  };
}

export function updateSession(updates: Partial<MRPLSession>): MRPLSession | null {
  const current = getSession();
  if (!current) return null;
  const updated = { ...current, ...updates };

  if (updates.userId) localStorage.setItem(KEYS.userId, updated.userId);
  if (updates.userName) localStorage.setItem(KEYS.userName, updated.userName);
  if (updates.plantUnit) localStorage.setItem(KEYS.plantUnit, updated.plantUnit);
  if (updates.role) localStorage.setItem(KEYS.role, updated.role);
  if (updates.sessionId) localStorage.setItem(KEYS.sessionId, updated.sessionId);

  return updated;
}

export function getApiHeaders(): Record<string, string> {
  const s = getSession();
  if (!s) return {};
  return {
    'X-User-Id': s.userId,
    'X-User-Role': s.role,
    'X-User-Unit': s.plantUnit,
    'X-Session-Id': s.sessionId,
  };
}

// ---------------------------------------------------------------------------
// Shift Utility
// ---------------------------------------------------------------------------

export function getCurrentShift(): { id: string; label: string; timeRange: string } {
  const hour = new Date().getHours();

  if (hour >= 6 && hour < 14) {
    return { id: 'A', label: 'Shift A', timeRange: '06:00 – 14:00' };
  } else if (hour >= 14 && hour < 22) {
    return { id: 'B', label: 'Shift B', timeRange: '14:00 – 22:00' };
  } else {
    return { id: 'C', label: 'Shift C', timeRange: '22:00 – 06:00' };
  }
}

export function getRoleInfo(roleId: string) {
  return ROLES.find((r) => r.id === roleId) || ROLES[0];
}

export function getPlantUnitLabel(unitId: string) {
  return PLANT_UNITS.find((u) => u.id === unitId)?.label || unitId;
}
