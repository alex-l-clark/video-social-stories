import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Video Social Stories',
  description: 'AI-powered personalized video stories for social learning',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}