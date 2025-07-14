import { Inter } from "next/font/google";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { AuthProvider } from './contexts/AuthContext'
import { AppLayout } from './components/AppLayout'
import { GraphProvider } from './contexts/GraphContext'
import "./globals.css";
import type { Metadata } from "next";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Bali Love Chat",
  description: "AI-powered chat assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full`}>
        <AuthProvider>
          <AppLayout>
            <NuqsAdapter>{children}</NuqsAdapter>
          </AppLayout>
        </AuthProvider>
      </body>
    </html>
  );
}
