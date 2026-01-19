import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ToastContainer";
import ErrorBoundary from "@/components/ErrorBoundary";
import { LocaleProvider } from "@/contexts/LocaleContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { headers } from "next/headers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "EduConnect - Find Your Perfect Tutor",
  description: "Connect with expert tutors for personalized 1-on-1 learning",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: [
      { url: "/apple-icon.svg", type: "image/svg+xml" },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const nonce = headers().get("x-nonce") ?? undefined;

  return (
    <html lang="en" suppressHydrationWarning>
      <body 
        className={`${inter.className} bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 antialiased transition-colors duration-200`} 
        data-nonce={nonce}
      >
        <ErrorBoundary>
          <ThemeProvider>
            <LocaleProvider>
              <ToastProvider>{children}</ToastProvider>
            </LocaleProvider>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
