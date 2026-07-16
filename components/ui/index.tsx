import { AlertTriangle, Check, CircleHelp, GitCompareArrows, Info, SearchCheck, Sparkles, UserRoundCheck } from "lucide-react";
import type { ConfidenceLevel, RequirementState, VerificationStatus } from "@/lib/types";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="grid size-9 place-items-center rounded-xl bg-[var(--ink)] text-white shadow-sm">
        <svg viewBox="0 0 32 32" className="size-5" aria-hidden="true">
          <path d="M6 23.5 15.8 7 26 23.5h-5.1l-5.1-8.8-5.2 8.8H6Z" fill="currentColor" />
          <path d="M11.5 23.5h9" stroke="#b8ef70" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      </div>
      {!compact && (
        <span className="text-[17px] font-semibold tracking-[-0.03em] text-[var(--ink)]">Pathwise</span>
      )}
    </div>
  );
}

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const styles = {
    high: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    medium: "bg-amber-50 text-amber-700 ring-amber-200",
    low: "bg-rose-50 text-rose-700 ring-rose-200",
  };
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize ring-1 ring-inset ${styles[level]}`}>{level}</span>;
}

export function StateBadge({ state }: { state: RequirementState }) {
  const config = {
    complete: { label: "Complete", classes: "bg-emerald-50 text-emerald-700", icon: Check },
    "in-progress": { label: "In progress", classes: "bg-blue-50 text-blue-700", icon: Sparkles },
    missing: { label: "Missing", classes: "bg-rose-50 text-rose-700", icon: AlertTriangle },
    uncertain: { label: "Confirm", classes: "bg-amber-50 text-amber-700", icon: Info },
  }[state];
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${config.classes}`}>
      <Icon className="size-3" />{config.label}
    </span>
  );
}

export function VerificationBadge({ status }: { status: VerificationStatus }) {
  const config = {
    confirmed: { label: "Confirmed", classes: "bg-emerald-50 text-emerald-700 ring-emerald-200", icon: SearchCheck },
    likely: { label: "Likely", classes: "bg-blue-50 text-blue-700 ring-blue-200", icon: Check },
    unclear: { label: "Unclear", classes: "bg-amber-50 text-amber-800 ring-amber-200", icon: CircleHelp },
    "manual-evaluation": { label: "Requires manual evaluation", classes: "bg-violet-50 text-violet-700 ring-violet-200", icon: UserRoundCheck },
    conflicting: { label: "Conflicting information", classes: "bg-rose-50 text-rose-700 ring-rose-200", icon: GitCompareArrows },
  }[status];
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset ${config.classes}`}>
      <Icon className="size-3" />{config.label}
    </span>
  );
}

export function SampleDataBanner({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50/80 text-amber-950 ${compact ? "px-3 py-2 text-xs" : "px-4 py-3 text-sm"}`}>
      <Info className="mt-0.5 size-4 shrink-0 text-amber-600" />
      <p><strong>Sample data:</strong> Demo policy results and citations are not verified official guidance. Confirm uncertain items before making academic decisions.</p>
    </div>
  );
}

export function ProgressBar({ value, tone = "teal" }: { value: number; tone?: "teal" | "violet" | "amber" }) {
  const tones = { teal: "bg-teal-500", violet: "bg-violet-500", amber: "bg-amber-500" };
  return (
    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
      <div className={`h-full rounded-full transition-all duration-500 ${tones[tone]}`} style={{ width: `${Math.max(2, Math.min(value, 100))}%` }} />
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center">
      <div className="mx-auto mb-3 grid size-10 place-items-center rounded-xl bg-white text-slate-400 shadow-sm"><Info className="size-5" /></div>
      <h3 className="font-semibold text-slate-900">{title}</h3>
      <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">{description}</p>
    </div>
  );
}
