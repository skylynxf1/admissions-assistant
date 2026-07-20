"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Check, Cloud, HardDrive, LoaderCircle, Sparkles } from "lucide-react";
import { BrandMark } from "@/components/ui";
import { useApp } from "@/components/app-provider";

const steps = [
  { label: "Plan type", href: "/" },
  { label: "About you", href: "/onboarding" },
  { label: "Transcript", href: "/transcript" },
  { label: "Schools", href: "/targets" },
  { label: "Priority", href: "/program" },
];

export function FlowShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { draftStatus, saveDraft } = useApp();
  const activeIndex = Math.max(0, steps.findIndex((step) => step.href === pathname));
  const showProgress = pathname !== "/" && pathname !== "/dashboard";
  return (
    <div className="min-h-screen bg-[var(--paper)]">
      <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[rgba(255,253,245,.92)] backdrop-blur-lg">
        <div className="mx-auto flex h-[60px] max-w-[1440px] items-center gap-4 px-5 lg:px-8">
          <Link href="/" aria-label="Pathly home"><BrandMark /></Link>
          {showProgress && (
            <nav className="mx-auto hidden max-w-[560px] flex-1 items-center md:flex" aria-label="Planning progress">
              {steps.slice(1).map((step, index) => {
                const absoluteIndex = index + 1;
                const completed = absoluteIndex < activeIndex;
                const active = absoluteIndex === activeIndex;
                return (
                  <div key={step.href} className="flex items-center last:flex-none md:flex-1 md:last:flex-none">
                    {index > 0 && <div aria-hidden="true" className="mx-2.5 min-w-6 flex-1" style={{ borderTop: `3px dotted ${completed || active ? "var(--path-green)" : "var(--border)"}` }} />}
                    <Link href={step.href} className="flex items-center gap-2">
                      <span
                        aria-hidden="true"
                        className={`grid size-[26px] place-items-center rounded-full text-xs font-bold ${completed ? "bg-[var(--pip-mint)] text-[var(--forest)]" : active ? "bg-[var(--forest)] text-white" : "bg-[var(--cream)] text-[var(--muted-ink)]"}`}
                      >
                        {completed ? <Check className="size-3.5" /> : active ? <Sparkles className="size-3" /> : absoluteIndex}
                      </span>
                      <span className={`hidden text-xs font-semibold lg:block ${active ? "text-[var(--forest)]" : completed ? "text-[var(--path-green)]" : "text-[var(--muted-ink)]"}`}>{step.label}</span>
                    </Link>
                  </div>
                );
              })}
            </nav>
          )}
          <div className="ml-auto flex items-center gap-2">
            <button onClick={() => void saveDraft()} disabled={draftStatus === "saving"} className="flex items-center gap-1.5 rounded-[12px] px-3 py-2 text-sm font-semibold text-[var(--muted-ink)] hover:bg-[var(--mint-wash)] hover:text-[var(--forest)] disabled:cursor-wait disabled:opacity-60">
              {draftStatus === "saving" ? <LoaderCircle className="size-3.5 animate-spin" /> : draftStatus === "saved-cloud" ? <Cloud className="size-3.5 text-[var(--path-green)]" /> : draftStatus === "saved-local" ? <HardDrive className="size-3.5 text-[var(--path-green)]" /> : null}
              {draftStatus === "saving" ? "Saving…" : draftStatus === "saved-cloud" ? "Saved to cloud" : draftStatus === "saved-local" ? "Saved locally" : draftStatus === "error" ? "Save failed" : "Save draft"}
            </button>
            <div className="grid size-[34px] place-items-center rounded-full border-[1.5px] border-[var(--pip-mint)] bg-[var(--mint-wash)] text-[13px] font-bold text-[var(--forest)]">A</div>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}
