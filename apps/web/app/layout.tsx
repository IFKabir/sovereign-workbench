import './globals.css';
import { Inter } from 'next/font/google';
import HeaderBar from '@/components/HeaderBar';
import SidebarNav from '@/components/SidebarNav';
import AuthGuard from '@/components/AuthGuard';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'MRPL Sovereign Intelligence Platform',
  description: 'Mangalore Refinery and Petrochemicals Limited — On-Premise Operational Copilot',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-sovereign-dark text-gray-100 min-h-screen flex`}>
        <AuthGuard>
          <SidebarNav />
          <div className="flex-1 flex flex-col h-screen overflow-hidden">
            <HeaderBar />
            <main className="flex-1 industrial-grid relative overflow-y-auto">
              {children}
            </main>
          </div>
        </AuthGuard>
      </body>
    </html>
  );
}
