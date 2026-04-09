import type { Metadata } from 'next';
import './globals.css';
import MockModeIndicator from './components/MockModeIndicator';

export const metadata: Metadata = {
  title: 'SRE Incident Triage Agent',
  description: 'Report and track production incidents with AI-powered triage',
  viewport: 'width=device-width, initial-scale=1',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <MockModeIndicator />
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
          {children}
        </div>
      </body>
    </html>
  );
}
