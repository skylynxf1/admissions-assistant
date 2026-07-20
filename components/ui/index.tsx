/* eslint-disable @next/next/no-img-element */
import { AlertTriangle, Archive, Check, CircleHelp, GitCompareArrows, Info, SearchCheck, Sparkles, UserRoundCheck } from "lucide-react";
import type { ConfidenceLevel, RequirementState, VerificationStatus } from "@/lib/types";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <img src="/pathly/logo/pathly-logo-192.png" width={34} height={34} alt="" className="block" />
      {!compact && (
        <span className="text-[22px] font-extrabold leading-none text-[var(--forest)]" style={{ fontFamily: "var(--font-heading)" }}>Pathly</span>
      )}
    </div>
  );
}

const pipPoses = {
  wave: "00",
  thinking: "01",
  celebrate: "02",
  caution: "03",
  roadmap: "04",
  "thumbs-up": "05",
} as const;

export type PipPose = keyof typeof pipPoses;

/**
 * Pip, the Pathly mascot. Always rendered from the mascot pack PNGs — never
 * redrawn with emoji, CSS, or SVG.
 */
export function PipAssistant({
  mode = "reaction", pose = "wave", size = 140, alt = "", className, style, children,
}: {
  mode?: "reaction" | "bubble" | "pet" | "loading";
  pose?: PipPose;
  size?: number;
  alt?: string;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}) {
  if (mode === "bubble") {
    return (
      <div className={className} style={{ position: "relative", maxWidth: 460, ...style }}>
        <img src="/pathly/assistant/pip-speech-bubble.png" alt={alt} className="block w-full" />
        <div className="absolute flex items-center text-[15px] font-medium leading-[22px] text-[var(--ink)]" style={{ left: "7%", right: "9%", top: "36%", bottom: "18%" }}>
          <div>{children}</div>
        </div>
      </div>
    );
  }
  if (mode === "pet") {
    return <img src="/pathly/pet/pip-mini-pet.png" alt={alt} width={size} className={`block ${className ?? ""}`} style={style} />;
  }
  if (mode === "loading") {
    return (
      <div className={`text-center ${className ?? ""}`} style={style}>
        <picture>
          <source srcSet="/pathly/loading/pip-loading-frame-00.png" media="(prefers-reduced-motion: reduce)" />
          <img src="/pathly/loading/pip-loading.gif" alt={alt || "Working on it"} width={size} className="mx-auto block" />
        </picture>
        {children && <div role="status" className="mt-3 text-base font-bold text-[var(--forest)]" style={{ fontFamily: "var(--font-heading)" }}>{children}</div>}
      </div>
    );
  }
  return (
    <div className={`text-center ${className ?? ""}`} style={style}>
      <img src={`/pathly/reactions/pip-reaction-${pipPoses[pose]}.png`} alt={alt} width={size} className="mx-auto block" />
      {children && <div className="mt-2 text-sm text-[var(--muted-ink)]">{children}</div>}
    </div>
  );
}

type ChipStatus = "verified" | "high-confidence" | "review" | "unresolved" | "deprecated" | "blocked" | "overlap";

const chipConfig: Record<ChipStatus, { bg: string; fg: string; bd: string; dotted?: boolean; icon: typeof Check; label: string }> = {
  verified: { bg: "var(--mint-wash)", fg: "var(--forest)", bd: "var(--pip-mint)", icon: Check, label: "Verified" },
  "high-confidence": { bg: "#EAF6F8", fg: "#2B6470", bd: "var(--sky)", icon: Check, label: "High confidence" },
  review: { bg: "#FDF3DC", fg: "#7A5B12", bd: "var(--butter)", icon: SearchCheck, label: "Needs review" },
  unresolved: { bg: "var(--paper)", fg: "var(--muted-ink)", bd: "var(--border)", dotted: true, icon: CircleHelp, label: "Unresolved" },
  deprecated: { bg: "#F0F0EC", fg: "var(--muted-ink)", bd: "#C9CFC9", icon: Archive, label: "Deprecated" },
  blocked: { bg: "#FBEDEB", fg: "var(--danger)", bd: "var(--danger)", icon: AlertTriangle, label: "Blocked" },
  overlap: { bg: "#FDF3DC", fg: "#7A5B12", bd: "var(--butter)", icon: Sparkles, label: "Opens more paths" },
};

/** Pathly status chip — status icons always pair with text, never color alone. */
export function StatusChip({ status = "verified", label, className }: { status?: ChipStatus; label?: string; className?: string }) {
  const config = chipConfig[status];
  const Icon = config.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1 text-[13px] font-semibold ${className ?? ""}`}
      style={{ background: config.bg, color: config.fg, border: `1px ${config.dotted ? "dotted" : "solid"} ${config.bd}` }}
    >
      <Icon className="size-3" aria-hidden="true" />{label || config.label}
    </span>
  );
}

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const statuses: Record<ConfidenceLevel, ChipStatus> = { high: "verified", medium: "review", low: "blocked" };
  const labels: Record<ConfidenceLevel, string> = { high: "High", medium: "Medium", low: "Low" };
  return <StatusChip status={statuses[level]} label={labels[level]} />;
}

export function StateBadge({ state }: { state: RequirementState }) {
  const config = {
    complete: { label: "Complete", classes: "bg-[var(--mint-wash)] text-[var(--forest)] border-[var(--pip-mint)]", icon: Check },
    "in-progress": { label: "In progress", classes: "bg-[#EAF6F8] text-[#2B6470] border-[var(--sky)]", icon: Sparkles },
    missing: { label: "Missing", classes: "bg-[#FBEDEB] text-[var(--danger)] border-[var(--danger)]", icon: AlertTriangle },
    uncertain: { label: "Confirm", classes: "bg-[#FDF3DC] text-[#7A5B12] border-[var(--butter)]", icon: Info },
  }[state];
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${config.classes}`}>
      <Icon className="size-3" />{config.label}
    </span>
  );
}

export function VerificationBadge({ status }: { status: VerificationStatus }) {
  const config = {
    confirmed: { label: "Confirmed", classes: "bg-[var(--mint-wash)] text-[var(--forest)] border-[var(--pip-mint)]", icon: SearchCheck },
    likely: { label: "Likely", classes: "bg-[#EAF6F8] text-[#2B6470] border-[var(--sky)]", icon: Check },
    unclear: { label: "Unclear", classes: "bg-[#FDF3DC] text-[#7A5B12] border-[var(--butter)]", icon: CircleHelp },
    "manual-evaluation": { label: "Requires manual evaluation", classes: "bg-[#F3F0FA] text-[#5D4E8C] border-[var(--lavender)]", icon: UserRoundCheck },
    conflicting: { label: "Conflicting information", classes: "bg-[#FBEDEB] text-[var(--danger)] border-[var(--danger)]", icon: GitCompareArrows },
  }[status];
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${config.classes}`}>
      <Icon className="size-3" />{config.label}
    </span>
  );
}

export function SampleDataBanner({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`flex items-start gap-2.5 rounded-[var(--radius-control)] border border-[var(--butter)] bg-[var(--surface-attention)] text-[#4C380A] ${compact ? "px-3 py-2 text-xs" : "px-4 py-3 text-sm"}`}>
      <Info className="mt-0.5 size-4 shrink-0 text-[#8A6810]" />
      <p><strong>Sample data:</strong> Demo policy results and citations are not verified official guidance. Confirm uncertain items before making academic decisions.</p>
    </div>
  );
}

export function ProgressBar({ value, tone = "teal" }: { value: number; tone?: "teal" | "violet" | "amber" }) {
  const tones = { teal: "bg-[var(--path-green)]", violet: "bg-[var(--lavender)]", amber: "bg-[var(--butter)]" };
  return (
    <div className="h-2 overflow-hidden rounded-full bg-[var(--mint-wash)]">
      <div className={`h-full rounded-full transition-all duration-500 ${tones[tone]}`} style={{ width: `${Math.max(2, Math.min(value, 100))}%` }} />
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-[var(--radius-card)] border-2 border-dotted border-[var(--border)] bg-white px-6 py-12 text-center">
      <PipAssistant pose="wave" size={96} alt="Pip waving" />
      <h3 className="mt-3 text-lg font-bold text-[var(--forest)]">{title}</h3>
      <p className="mx-auto mt-1 max-w-md text-sm text-[var(--muted-ink)]">{description}</p>
    </div>
  );
}
