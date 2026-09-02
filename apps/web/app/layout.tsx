import './globals.css';
import { Inter } from 'next/font/google';
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
      <body className={`${inter.className} bg-[#1a1a1a] text-[#e8e8e8] min-h-screen flex`}>
        <AuthGuard>
          {/* Main Layout: Sidebar + Full Workspace */}
          <div className="w-full h-screen flex overflow-hidden">
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
