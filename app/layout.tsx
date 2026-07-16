import type { Metadata } from "next";
import { AppProvider } from "@/components/app-provider";
import { FlowShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pathwise — Academic Planning OS",
  description: "A multi-path academic planning and transfer simulation prototype.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <AppProvider><FlowShell>{children}</FlowShell></AppProvider>
      </body>
    </html>
  );
}
