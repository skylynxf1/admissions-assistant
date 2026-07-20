import type { Metadata } from "next";
import { DM_Mono, Inter, Nunito } from "next/font/google";
import { AppProvider } from "@/components/app-provider";
import { FlowShell } from "@/components/app-shell";
import "./globals.css";

const nunito = Nunito({ subsets: ["latin"], weight: ["600", "700", "800"], variable: "--font-nunito" });
const inter = Inter({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-inter" });
const dmMono = DM_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-dm-mono" });

export const metadata: Metadata = {
  title: "Pathly — There is a path forward",
  description: "An academic planning OS for transfer students. Map what transfers, what counts, and which courses keep the most options open.",
  icons: { icon: "/pathly/logo/favicon-32.png" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" className={`${nunito.variable} ${inter.variable} ${dmMono.variable}`}>
      <body className="antialiased">
        <AppProvider><FlowShell>{children}</FlowShell></AppProvider>
      </body>
    </html>
  );
}
