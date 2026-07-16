"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Check } from "lucide-react";
import { BrandMark } from "@/components/ui";

const steps = [
  { label: "Plan type", href: "/" },
  { label: "About you", href: "/onboarding" },
  { label: "Transcript", href: "/transcript" },
  { label: "Targets", href: "/targets" },
  { label: "Plan", href: "/dashboard" },
];

export function FlowShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const activeIndex = Math.max(0, steps.findIndex((step) => step.href === pathname));
  return (
    <div className="min-h-screen bg-[var(--canvas)]">
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-5 lg:px-8">
          <Link href="/" aria-label="Pathwise home"><BrandMark /></Link>
          <div className="hidden items-center gap-2 md:flex">
            <span className="rounded-full bg-lime-100 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-lime-800">Hackathon demo</span>
            <span className="text-xs text-slate-400">No API key needed</span>
          </div>
          <div className="flex items-center gap-2">
            <button className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">Save draft</button>
            <div className="grid size-8 place-items-center rounded-full bg-gradient-to-br from-teal-500 to-cyan-700 text-xs font-bold text-white">AS</div>
          </div>
        </div>
      </header>
      {pathname !== "/" && (
        <div className="border-b border-slate-200 bg-white">
          <nav className="mx-auto flex max-w-4xl items-center justify-between px-5 py-3" aria-label="Planning progress">
            {steps.slice(1).map((step, index) => {
              const absoluteIndex = index + 1;
              const completed = absoluteIndex < activeIndex;
              const active = absoluteIndex === activeIndex;
              return (
                <div key={step.href} className="flex flex-1 items-center last:flex-none">
                  <Link href={step.href} className="flex items-center gap-2">
                    <span className={`grid size-7 place-items-center rounded-full text-xs font-bold ${completed ? "bg-teal-600 text-white" : active ? "bg-[var(--ink)] text-white" : "bg-slate-100 text-slate-400"}`}>
                      {completed ? <Check className="size-3.5" /> : absoluteIndex}
                    </span>
                    <span className={`hidden text-xs font-semibold sm:block ${active ? "text-slate-900" : "text-slate-400"}`}>{step.label}</span>
                  </Link>
                  {index < steps.length - 2 && <div className={`mx-3 h-px flex-1 ${completed ? "bg-teal-500" : "bg-slate-200"}`} />}
                </div>
              );
            })}
          </nav>
        </div>
      )}
      {children}
    </div>
  );
}
