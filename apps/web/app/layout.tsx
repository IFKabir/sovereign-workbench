import './globals.css';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import { LayoutDashboard, MessageSquare, Route, FileCode2, Shield } from 'lucide-react';
import AirgapBadge from '@/components/AirgapBadge';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Sovereign Workbench',
  description: 'Air-Gapped Industrial AI',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-sovereign-dark text-gray-100 min-h-screen flex`}>
        {/* Sidebar */}
        <aside className="w-64 glass-panel border-r border-sovereign-border flex flex-col z-10 h-screen sticky top-0">
          <div className="p-6 border-b border-sovereign-border flex items-center space-x-3">
            <Shield className="w-8 h-8 text-accent-cyan animate-pulse-glow rounded-full" />
            <div>
              <h1 className="font-bold text-sm text-gray-100 tracking-wide uppercase">Sovereign</h1>
              <h2 className="text-xs text-accent-amber font-mono mt-0.5">Workbench v0.1</h2>
            </div>
          </div>

          <nav className="flex-1 py-6 px-4 space-y-2">
            <Link href="/" className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-sovereign-surface hover:text-white transition-colors">
              <LayoutDashboard className="w-5 h-5" />
              <span>Dashboard</span>
            </Link>
            <Link href="/chat" className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-sovereign-surface hover:text-white transition-colors">
              <MessageSquare className="w-5 h-5" />
              <span>Chat</span>
            </Link>
            <Link href="/trace" className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-sovereign-surface hover:text-white transition-colors">
              <Route className="w-5 h-5" />
              <span>Agent Trace</span>
            </Link>
            <Link href="/audit" className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-sovereign-surface hover:text-white transition-colors">
              <FileCode2 className="w-5 h-5" />
              <span>Audit Log</span>
            </Link>
          </nav>

          <div className="p-6 border-t border-sovereign-border">
            <AirgapBadge />
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 industrial-grid relative h-screen overflow-y-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
