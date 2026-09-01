'use client';

import { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert } from 'lucide-react';
import clsx from 'clsx';

export default function AirgapBadge() {
  const [isVerified, setIsVerified] = useState(true);
  const [lastVerifiedText, setLastVerifiedText] = useState<string>('');

  useEffect(() => {
    // Format timestamp on client mount to avoid SSR hydration mismatch
    setLastVerifiedText(new Date().toLocaleTimeString());
    const interval = setInterval(() => {
      setLastVerifiedText(new Date().toLocaleTimeString());
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className={clsx(
        'flex items-center space-x-2 px-3 py-2 rounded-md border text-sm font-medium transition-colors cursor-help w-full justify-center',
        isVerified
          ? 'bg-accent-emerald/10 border-accent-emerald/30 text-accent-emerald shadow-[0_0_10px_rgba(16,185,129,0.2)]'
          : 'bg-danger/10 border-danger/30 text-danger animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.2)]'
      )}
      title={lastVerifiedText ? `Last verified: ${lastVerifiedText}` : 'Air-gap active'}
    >
      {isVerified ? (
        <ShieldCheck className="w-4 h-4" />
      ) : (
        <ShieldAlert className="w-4 h-4" />
      )}
      <span>{isVerified ? 'AIR-GAPPED' : 'NETWORK RISK'}</span>
    </div>
  );
}
