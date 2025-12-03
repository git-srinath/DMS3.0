'use client';

import localFont from "next/font/local";
import './globals.css';
import './fonts/fonts.css'; // Import local fonts CSS
import LayoutWrapper from '@/components/LayoutWrapper';
import { ThemeProvider } from '@/context/ThemeContext';
import { AuthProvider } from './context/AuthContext';

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

// Use local Inter font instead of Google Fonts
const inter = localFont({
  src: [
    {
      path: './fonts/Inter-Regular.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: './fonts/Inter-Medium.woff2',
      weight: '500',
      style: 'normal',
    },
    {
      path: './fonts/Inter-SemiBold.woff2',
      weight: '600',
      style: 'normal',
    },
    {
      path: './fonts/Inter-Bold.woff2',
      weight: '700',
      style: 'normal',
    },
  ],
  variable: '--font-inter',
});

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <title>DMS</title>
        <meta name="description" content="Data Management Solution | A tool for unified data management" />
        {/* Removed Google Fonts link - now using local fonts */}
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} ${inter.variable} antialiased font-sans`}>
        <ThemeProvider>
          <AuthProvider>
            <LayoutWrapper>{children}</LayoutWrapper>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
