import { Inter } from "next/font/google";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { AuthProvider } from './contexts/AuthContext'
import Header from './components/Header'
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
        <div
          className="flex flex-col h-full w-full"
          style={{ background: "rgb(38, 38, 41)" }}
        >
          <AuthProvider>
            <Header />
            <NuqsAdapter>{children}</NuqsAdapter>
          </AuthProvider>
        </div>
      </body>
    </html>
  );
}
