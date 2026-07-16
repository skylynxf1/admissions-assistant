"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { createSampleTranscript } from "@/data/sample-transcript";
import { academicPlanningServices } from "@/lib/services";
import type {
  AcademicAnalysisInput,
  AdvisorMessage,
  AnalysisResult,
  PlanningMode,
  ScenarioSettings,
  StudentProfile,
  TargetSchool,
  TranscriptData,
} from "@/lib/types";

const defaultProfile: StudentProfile = {
  firstName: "Alex",
  currentInstitution: "Bellevue College",
  institutionType: "in-state-community-college",
  residency: "in-state",
  targetTransferTerm: "Fall 2027",
  preferredCreditLoad: 15,
  currentlyEnrolled: true,
  hasExamCredit: true,
};

const defaultScenario: ScenarioSettings = {
  institutionType: defaultProfile.institutionType,
  residency: defaultProfile.residency,
  targetTransferTerm: defaultProfile.targetTransferTerm,
  preferredCreditLoad: defaultProfile.preferredCreditLoad,
  useExamCredit: true,
  attendSummer: false,
};

interface PersistedState {
  mode: PlanningMode;
  profile: StudentProfile;
  transcript: TranscriptData;
  targets: TargetSchool[];
  prioritySchoolId: string;
  scenario: ScenarioSettings;
}

interface AppContextValue extends PersistedState {
  analysis: AnalysisResult | null;
  analysisStatus: "idle" | "analyzing" | "ready" | "error";
  advisorMessages: AdvisorMessage[];
  setMode: (mode: PlanningMode) => void;
  setProfile: (profile: StudentProfile) => void;
  setTranscript: (transcript: TranscriptData) => void;
  setTargets: (targets: TargetSchool[]) => void;
  setPrioritySchoolId: (schoolId: string) => void;
  setScenario: (scenario: ScenarioSettings) => void;
  updateScenario: (updates: Partial<ScenarioSettings>) => void;
  rerunAnalysis: () => Promise<void>;
  setAdvisorMessages: (messages: AdvisorMessage[]) => void;
}

const AppContext = createContext<AppContextValue | null>(null);
const STORAGE_KEY = "pathwise-prototype-state-v2";

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<PlanningMode>("transfer");
  const [profile, setProfileState] = useState<StudentProfile>(defaultProfile);
  const [transcript, setTranscript] = useState<TranscriptData>(() => createSampleTranscript());
  const [targets, setTargets] = useState<TargetSchool[]>([
    { schoolId: "uw", majorIds: [] },
    { schoolId: "berkeley", majorIds: [] },
  ]);
  const [prioritySchoolId, setPrioritySchoolId] = useState("uw");
  const [scenario, setScenario] = useState<ScenarioSettings>(defaultScenario);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AppContextValue["analysisStatus"]>("idle");
  const [advisorMessages, setAdvisorMessages] = useState<AdvisorMessage[]>([
    {
      id: "advisor-welcome",
      role: "assistant",
      content: "Ask me about your courses, requirements, or transfer path. I’ll answer only from your reviewed transcript and the policy records saved in this plan.",
      createdAt: new Date(0).toISOString(),
      confidence: "medium",
      citationIds: [],
    },
  ]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as PersistedState;
        setMode(parsed.mode);
        setProfileState(parsed.profile);
        setTranscript(parsed.transcript);
        setTargets(parsed.targets);
        setPrioritySchoolId(parsed.prioritySchoolId || parsed.targets[0]?.schoolId || "uw");
        setScenario(parsed.scenario);
      }
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    } finally {
      setHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ mode, profile, transcript, targets, prioritySchoolId, scenario }));
  }, [hydrated, mode, profile, transcript, targets, prioritySchoolId, scenario]);

  const analysisInput = useMemo<AcademicAnalysisInput>(
    () => ({ profile, transcript, targets, scenario }),
    [profile, transcript, targets, scenario],
  );

  const rerunAnalysis = useCallback(async () => {
    if (targets.length === 0 || targets.every((target) => target.majorIds.length === 0)) {
      setAnalysis(null);
      setAnalysisStatus("idle");
      return;
    }
    setAnalysisStatus("analyzing");
    try {
      const result = await academicPlanningServices.scenarioSimulator.simulate(analysisInput);
      setAnalysis(result);
      setAnalysisStatus("ready");
    } catch {
      setAnalysisStatus("error");
    }
  }, [analysisInput, targets]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void rerunAnalysis(), 180);
    return () => window.clearTimeout(timeout);
  }, [rerunAnalysis]);

  const setProfile = useCallback((nextProfile: StudentProfile) => {
    setProfileState(nextProfile);
    setScenario((current) => ({
      ...current,
      institutionType: nextProfile.institutionType,
      residency: nextProfile.residency,
      targetTransferTerm: nextProfile.targetTransferTerm,
      preferredCreditLoad: nextProfile.preferredCreditLoad,
      useExamCredit: nextProfile.hasExamCredit,
    }));
  }, []);

  const updateScenario = useCallback((updates: Partial<ScenarioSettings>) => {
    setScenario((current) => ({ ...current, ...updates }));
  }, []);

  const value = useMemo<AppContextValue>(
    () => ({
      mode, profile, transcript, targets, prioritySchoolId, scenario, analysis, analysisStatus, advisorMessages,
      setMode, setProfile, setTranscript, setTargets, setPrioritySchoolId, setScenario, updateScenario, rerunAnalysis, setAdvisorMessages,
    }),
    [mode, profile, transcript, targets, prioritySchoolId, scenario, analysis, analysisStatus, advisorMessages, setProfile, updateScenario, rerunAnalysis],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error("useApp must be used inside AppProvider");
  return context;
}
