'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { isLoggedIn } from '@/lib/session';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (pathname === '/login') {
      setChecked(true);
      return;
    }

    if (!isLoggedIn()) {
      router.replace('/login');
    } else {
      setChecked(true);
    }
  }, [pathname, router]);

  if (!checked && pathname !== '/login') {
    return (
      <div className="min-h-screen w-full bg-sovereign-dark flex items-center justify-center text-xs font-mono text-gray-500">
        Authenticating MRPL Intranet Session...
      </div>
    );
  }

  return <>{children}</>;
}
