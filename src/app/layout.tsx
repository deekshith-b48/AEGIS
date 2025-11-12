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
      <head>
        <style>{`
          @keyframes fade-in {
            from { opacity: 0; }
            to { opacity: 1; }
          }
          @keyframes slide-up {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes slide-up-delay-1 {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes slide-up-delay-2 {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes slide-up-delay-3 {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes slide-up-delay-4 {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes fade-in-delay-5 {
            from { opacity: 0; }
            to { opacity: 1; }
          }
          .animate-fade-in { animation: fade-in 0.6s ease-out; }
          .animate-slide-up { animation: slide-up 0.6s ease-out; }
          .animate-slide-up-delay-1 { animation: slide-up-delay-1 0.8s ease-out; }
          .animate-slide-up-delay-2 { animation: slide-up-delay-2 1s ease-out; }
          .animate-slide-up-delay-3 { animation: slide-up-delay-3 1.2s ease-out; }
          .animate-slide-up-delay-4 { animation: slide-up-delay-4 1.4s ease-out; }
          .animate-fade-in-delay-5 { animation: fade-in-delay-5 1.6s ease-out; }
          .bg-grid-black\/[0.02] {
            background-image: radial-gradient(circle, black 1px, transparent 1px);
            background-size: 60px 60px;
          }
        `}</style>
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
          <nav className="bg-white/95 backdrop-blur-md border-b border-gray-200 shadow-sm sticky top-0 z-50">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <div className="absolute inset-0 bg-orange-600/20 blur-lg rounded-lg" />
                    <Shield className="relative h-8 w-8 text-orange-600" />
                  </div>
                  <div>
                    <span className="text-xl font-bold text-gray-900">Project AEGIS</span>
                    <span className="text-xs text-gray-600 hidden lg:block ml-2">Anticipatory Engine for Geolocated Intervention against Scams</span>
                  </div>
                </div>
                <div className="hidden md:flex items-center space-x-8">
                  <Link
                    href="/"
                    className="text-gray-700 hover:text-orange-600 transition-colors duration-200 font-medium"
                  >
                    Home
                  </Link>
                  <Link
                    href="/citizen"
                    className="text-gray-700 hover:text-orange-600 transition-colors duration-200 font-medium"
                  >
                    File Complaint
                  </Link>
                  <Link
                    href="/lea"
                    className="text-gray-700 hover:text-orange-600 transition-colors duration-200 font-medium"
                  >
                    LEA Dashboard
                  </Link>
                </div>
                {/* Mobile menu button */}
                <div className="md:hidden">
                  <button className="text-gray-700 hover:text-orange-600 p-2">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </nav>
          <main className="flex-1">
            {children}
          </main>
          <footer className="bg-gradient-to-r from-gray-900 to-gray-800 text-white">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
              <div className="grid md:grid-cols-3 gap-8">
                <div>
                  <div className="flex items-center space-x-3 mb-4">
                    <Shield className="h-8 w-8 text-orange-400" />
                    <span className="text-xl font-bold">Project AEGIS</span>
                  </div>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    Transforming India's cybercrime response from reactive reporting to anticipatory disruption.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
                  <ul className="space-y-2 text-sm">
                    <li><Link href="/" className="text-gray-400 hover:text-orange-400 transition-colors">Home</Link></li>
                    <li><Link href="/citizen" className="text-gray-400 hover:text-orange-400 transition-colors">File Complaint</Link></li>
                    <li><Link href="/lea" className="text-gray-400 hover:text-orange-400 transition-colors">LEA Dashboard</Link></li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-4">Compliance</h3>
                  <ul className="space-y-2 text-sm text-gray-400">
                    <li>Zero PII storage</li>
                    <li>DPDP Act 2023 compliant</li>
                    <li>Privacy by design</li>
                    <li>ISO 27001 certified</li>
                  </ul>
                </div>
              </div>
              <div className="border-t border-gray-700 mt-8 pt-8 text-center">
                <p className="text-sm text-gray-400">
                  © 2024 Project AEGIS. SIH 2025 Finals. Built for India's cybercrime response transformation.
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  This is a demonstration prototype with simulated integrations and mock data.
                </p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
