import './globals.css';

export const metadata = {
  title: 'Academic Thesis Writer',
  description: 'AI-powered thesis writing assistant with citation management.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
