import './globals.css';
import { Inter } from 'next/font/google';
import GIGWHeader from '@/components/GIGWHeader';
import SidebarNav from '@/components/SidebarNav';
import ScrollToTop from '@/components/ScrollToTop';
import AuthGuard from '@/components/AuthGuard';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'MRPL Sovereign Intelligence Platform — Govt. of India Enterprise',
  description: 'Mangalore Refinery and Petrochemicals Limited — On-Premise Operational Copilot',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[#1a1a1a] text-[#e8e8e8] min-h-screen flex flex-col`}>
        <AuthGuard>
          {/* Top Accessibility Bar + Official MRPL Header + Olive Green Nav + Notice Ticker */}
          <GIGWHeader />

          {/* Body Layout: Sidebar + Main Workspace */}
          <div className="flex-1 flex overflow-hidden">
            <SidebarNav />
            <main id="main-content" className="flex-1 industrial-grid relative overflow-y-auto bg-[#1a1a1a]">
              {children}
            </main>
          </div>

          {/* Floating Scroll to Top Button */}
          <ScrollToTop />
        </AuthGuard>
      </body>
    </html>
  );
}
