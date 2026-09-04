'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SchematicPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/chat?mode=schematic');
  }, [router]);

  return null;
}
