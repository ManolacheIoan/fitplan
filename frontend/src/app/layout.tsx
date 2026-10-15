import type { Metadata, Viewport } from "next";
import { Archivo } from "next/font/google";
import { ServiceWorker } from "@/components/ServiceWorker";
import "./globals.css";

// Self-hosted at build time by next/font: no runtime request to Google.
const archivo = Archivo({ variable: "--font-archivo", subsets: ["latin", "latin-ext"] });

export const metadata: Metadata = {
  title: { default: "FitPlan", template: "%s · FitPlan" },
  description: "Plan de antrenament și estimări nutriționale orientative.",
  icons: { icon: "/icon.svg", apple: "/apple-touch-icon.png" },
};

export const viewport: Viewport = {
  themeColor: "#0b0d10",
  width: "device-width",
  initialScale: 1,
};

// Applies the saved theme before first paint to avoid a flash of the wrong theme.
const themeScript = `try{if(localStorage.getItem("theme")==="light")document.documentElement.dataset.theme="light"}catch(e){}`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ro" className={`${archivo.variable} h-full antialiased`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="flex min-h-full flex-col font-sans">
        {children}
        <ServiceWorker />
      </body>
    </html>
  );
}
