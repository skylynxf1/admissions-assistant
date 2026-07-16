"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Bot, LoaderCircle, MessageCircle, Sparkles, X } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { academicPlanningServices } from "@/lib/services";
import type { AdvisorMessage } from "@/lib/types";

const quickQuestions = ["What should I take next term?", "Does my AP Calculus credit count?", "Am I ready to apply?"];

export function AdvisorPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { profile, transcript, targets, scenario, analysis, advisorMessages, setAdvisorMessages } = useApp();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [advisorMessages, loading]);

  const ask = async (text = question) => {
    const clean = text.trim();
    if (!clean || !analysis || loading) return;
    const userMessage: AdvisorMessage = { id: `user-${Date.now()}`, role: "user", content: clean, createdAt: new Date().toISOString() };
    const nextHistory = [...advisorMessages, userMessage];
    setAdvisorMessages(nextHistory);
    setQuestion("");
    setLoading(true);
    try {
      const answer = await academicPlanningServices.advisorChat.answer({ profile, transcript, targets, scenario, analysis, history: nextHistory, question: clean });
      await new Promise((resolve) => window.setTimeout(resolve, 450));
      setAdvisorMessages([...nextHistory, answer.message]);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/25 backdrop-blur-[2px]" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <aside className="flex h-full w-full max-w-[440px] flex-col border-l border-slate-200 bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div className="flex items-center gap-3"><div className="grid size-9 place-items-center rounded-xl bg-[var(--ink)] text-lime-200"><Sparkles className="size-4" /></div><div><h2 className="font-semibold text-slate-900">Pathwise advisor</h2><p className="text-xs text-slate-500">Grounded in this sample scenario</p></div></div>
          <button onClick={onClose} aria-label="Close advisor" className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"><X className="size-5" /></button>
        </header>
        <div className="border-b border-amber-200 bg-amber-50 px-5 py-2.5 text-xs leading-5 text-amber-900">Demo answers use unverified sample policy data and are not official academic advice.</div>
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
          {advisorMessages.map((message) => (
            <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === "user" ? "rounded-br-md bg-[var(--ink)] text-white" : "rounded-bl-md border border-slate-200 bg-slate-50 text-slate-700"}`}>
                {message.role === "assistant" && <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-teal-700"><Bot className="size-3.5" /> Sample advisor</div>}
                <p>{message.content}</p>
                {message.role === "assistant" && message.citationIds && message.citationIds.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5">{message.citationIds.map((citationId) => { const citation = analysis?.citations.find((item) => item.id === citationId); return citation ? <a key={citationId} href={citation.url} target="_blank" rel="noreferrer" className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-teal-700 ring-1 ring-slate-200">Sample source · {citation.publisher}</a> : null; })}</div>}
              </div>
            </div>
          ))}
          {loading && <div className="flex justify-start"><div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500"><LoaderCircle className="size-4 animate-spin text-teal-600" /> Reasoning across your scenario…</div></div>}
        </div>
        <div className="border-t border-slate-200 bg-white p-4">
          <div className="mb-3 flex gap-2 overflow-x-auto pb-1">{quickQuestions.map((item) => <button key={item} onClick={() => void ask(item)} disabled={loading || !analysis} className="shrink-0 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-teal-300 hover:bg-teal-50">{item}</button>)}</div>
          <form onSubmit={(event) => { event.preventDefault(); void ask(); }} className="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white p-2 focus-within:border-teal-500 focus-within:ring-2 focus-within:ring-teal-100">
            <textarea aria-label="Ask the advisor" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about your transfer plan…" rows={2} className="min-h-12 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none" />
            <button type="submit" disabled={!question.trim() || loading || !analysis} aria-label="Send question" className="grid size-10 shrink-0 place-items-center rounded-xl bg-[var(--ink)] text-white disabled:opacity-40"><ArrowUp className="size-4" /></button>
          </form>
          <p className="mt-2 text-center text-[10px] text-slate-400">Facts and estimates are separated; uncertain conclusions should be confirmed.</p>
        </div>
      </aside>
    </div>
  );
}

export function AdvisorButton({ onClick }: { onClick: () => void }) {
  return <button onClick={onClick} className="fixed bottom-5 right-5 z-30 flex items-center gap-2 rounded-full bg-[var(--ink)] px-4 py-3 text-sm font-semibold text-white shadow-xl shadow-slate-900/20 transition hover:-translate-y-0.5"><MessageCircle className="size-4 text-lime-200" /> Ask advisor</button>;
}
