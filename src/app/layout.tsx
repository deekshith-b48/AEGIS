import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { Shield } from "lucide-react";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Project AEGIS - Anticipatory Engine for Geolocated Intervention against Scams",
  description: "Transform India's cybercrime response from reactive reporting to anticipatory disruption",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-orange-600 text-white p-4 shadow-lg">
            <div className="container mx-auto flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <Shield className="h-8 w-8" />
                <span className="text-xl font-bold">Project AEGIS</span>
                <span className="text-sm hidden md:block">Anticipatory Engine for Geolocated Intervention against Scams</span>
              </div>
              <div className="flex space-x-6">
                <Link href="/" className="hover:text-orange-200 transition-colors">
                  Home
                </Link>
                <Link href="/citizen" className="hover:text-orange-200 transition-colors">
                  File Complaint
                </Link>
                <Link href="/lea" className="hover:text-orange-200 transition-colors">
                  LEA Dashboard
                </Link>
              </div>
            </div>
          </nav>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="bg-gray-800 text-white p-6 mt-12">
            <div className="container mx-auto text-center">
              <p className="text-sm">
                © 2024 Project AEGIS. SIH 2025 Finals. Built for India's cybercrime response transformation.
              </p>
              <p className="text-xs mt-2 text-gray-400">
                Zero PII storage • DPDP Act 2023 compliant • Privacy by design
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
