import type { Metadata } from 'next';
import './globals.css';
import MockModeIndicator from './components/MockModeIndicator';

export const metadata: Metadata = {
  title: 'SRE Incident Triage - Intelligent Incident Management',
  description: 'AI-powered incident intake and triage platform for production support. Reduce MTTR with intelligent analysis and team notifications.',
  viewport: 'width=device-width, initial-scale=1',
  icons: {
    icon: '/favicon.svg',
  },
  openGraph: {
    title: 'SRE Incident Triage',
    description: 'Transform incident response with AI-powered analysis',
    type: 'website',
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
        {children}
      </body>
    </html>
  );
}
