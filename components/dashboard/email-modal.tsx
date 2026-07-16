"use client";

import { useEffect, useState } from "react";
import { Check, Copy, LoaderCircle, Mail, X } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { academicPlanningServices } from "@/lib/services";
import type { AnalysisAlert, DraftEmail } from "@/lib/types";

export function EmailModal({ alert, onClose }: { alert: AnalysisAlert; onClose: () => void }) {
  const { profile, transcript, targets, scenario } = useApp();
  const [draft, setDraft] = useState<DraftEmail | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    void academicPlanningServices.uncertaintyHandler
      .draftEmail(alert, { profile, transcript, targets, scenario })
      .then(setDraft);
  }, [alert, profile, transcript, targets, scenario]);

  const copyDraft = async () => {
    if (!draft) return;
    await navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="fixed inset-0 z-[60] grid place-items-center bg-slate-950/35 p-4 backdrop-blur-sm" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4"><div className="flex items-center gap-3"><div className="grid size-9 place-items-center rounded-xl bg-teal-50 text-teal-700"><Mail className="size-4" /></div><div><h2 className="font-semibold text-slate-900">Draft a confirmation email</h2><p className="text-xs text-slate-500">For the {alert.office}</p></div></div><button onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"><X className="size-5" /></button></header>
        {!draft ? <div className="flex min-h-72 items-center justify-center gap-2 text-sm text-slate-500"><LoaderCircle className="size-4 animate-spin text-teal-600" /> Preparing a precise policy question…</div> : (
          <div className="p-5 sm:p-6">
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">Review the recipient and all details before sending. This prototype does not send email.</div>
            <label className="mt-4 block"><span className="field-label">Office</span><input readOnly value={draft.toOffice} className="field bg-slate-50" /></label>
            <label className="mt-4 block"><span className="field-label">Subject</span><input readOnly value={draft.subject} className="field bg-slate-50" /></label>
            <label className="mt-4 block"><span className="field-label">Message</span><textarea readOnly value={draft.body} rows={11} className="field resize-none bg-slate-50 text-sm leading-6" /></label>
            <div className="mt-5 flex justify-end gap-2"><button onClick={onClose} className="secondary-button">Close</button><button onClick={() => void copyDraft()} className="primary-button">{copied ? <Check className="size-4" /> : <Copy className="size-4" />}{copied ? "Copied" : "Copy draft"}</button></div>
          </div>
        )}
      </div>
    </div>
  );
}
