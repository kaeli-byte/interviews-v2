"use client";

import { BaseLayout, ContentCard, PageHeader } from "@/components/layouts/base-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiFetch, getServerTimingMetrics, type ServerTimingMetric } from "@/lib/api";
import { supabase } from "@/lib/supabase";
import { cn } from "@/lib/utils";
import { FileText, Link as LinkIcon, Loader2, Sparkles, UserRound, Wand2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type SetupMode = "new" | "load";

type Agent = {
  agent_id: string;
  name: string;
  description?: string;
};

type ResumeProfile = {
  profile_id: string;
  document_id?: string | null;
  name: string;
  headline: string;
  skills: string[];
  experience: Array<{ title?: string; company?: string; duration?: string; description?: string }>;
};

type JobProfile = {
  profile_id: string;
  document_id?: string | null;
  company: string;
  role: string;
  requirements?: string[];
  nice_to_have?: string[];
  responsibilities?: string[];
};

type DocumentSnapshot = {
  document_id: string;
  type: string;
  source_type?: string | null;
  filename?: string | null;
  mime_type?: string | null;
  source_url?: string | null;
  parse_status?: string | null;
  created_at?: string | null;
};

type ContextResponse = {
  context_id: string;
  agent_id: string;
  custom_instructions?: string | null;
  startup_prompt: string;
  match_analysis: {
    match_score?: number;
    matched_requirements?: string[];
    gap_requirements?: string[];
  };
  resume_profile: ResumeProfile;
  job_profile: JobProfile;
  resume_document?: DocumentSnapshot | null;
  job_document?: DocumentSnapshot | null;
  agent: {
    agent_id: string;
    name: string;
  };
};

type SessionSummary = {
  session_id: string;
  interview_context_id?: string | null;
  agent_id?: string | null;
  state: string;
  created_at?: string | null;
  editable: boolean;
  candidate_name?: string | null;
  target_role?: string | null;
  company?: string | null;
  agent_name?: string | null;
};

type SessionDetail = {
  session_id: string;
  interview_context_id: string;
  agent_id?: string | null;
  state: string;
  created_at: string;
  editable: boolean;
  context?: ContextResponse;
};

type SetupDebugTiming = {
  agents: ServerTimingMetric[];
  sessions: ServerTimingMetric[];
  sessionDetail: ServerTimingMetric[];
};

async function parseResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data as T;
}

export default function SetupInterviewPage() {
  const router = useRouter();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [setupMode, setSetupMode] = useState<SetupMode>("new");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [jdMode, setJdMode] = useState("file");
  const [jdText, setJdText] = useState("");
  const [jdUrl, setJdUrl] = useState("");
  const [customInstructions, setCustomInstructions] = useState("");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [resumeDocumentId, setResumeDocumentId] = useState<string | null>(null);
  const [jobDocumentId, setJobDocumentId] = useState<string | null>(null);
  const [resumeProfile, setResumeProfile] = useState<ResumeProfile | null>(null);
  const [jobProfile, setJobProfile] = useState<JobProfile | null>(null);
  const [savedContext, setSavedContext] = useState<ContextResponse | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [editingSession, setEditingSession] = useState<SessionDetail | null>(null);
  const [busyStep, setBusyStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [timings, setTimings] = useState<SetupDebugTiming>({ agents: [], sessions: [], sessionDetail: [] });
  const displayedJobRequirements = jobProfile?.requirements ?? [];
  const displayedJobResponsibilities = jobProfile?.responsibilities ?? [];

  const recordClientMeasure = (name: string, startMark: string, endMark: string) => {
    if (typeof performance === "undefined") {
      return;
    }
    try {
      performance.measure(name, startMark, endMark);
    } catch {
      return;
    }
  };

  const logTimingMetrics = (label: string, metrics: ServerTimingMetric[]) => {
    if (!metrics.length) {
      return;
    }
    console.debug(`[setup] ${label} Server-Timing`, metrics);
  };

  const fetchSessionDetail = async (sessionId: string): Promise<SessionDetail> => {
    const response = await apiFetch(`/api/sessions/${sessionId}`);
    const metrics = getServerTimingMetrics(response);
    setTimings((current) => ({ ...current, sessionDetail: metrics }));
    logTimingMetrics(`session detail ${sessionId}`, metrics);
    return parseResponse<SessionDetail>(response);
  };

  useEffect(() => {
    let active = true;

    const boot = async () => {
      performance.mark("setup-auth-start");
      const { data } = await supabase.auth.getUser();
      performance.mark("setup-auth-end");
      recordClientMeasure("setup-auth", "setup-auth-start", "setup-auth-end");
      if (!data.user) {
        router.replace("/signin");
        return;
      }

      try {
        performance.mark("setup-boot-fetch-start");
        const [agentsResponse, sessionsResponse] = await Promise.all([
          apiFetch("/api/agents"),
          apiFetch("/api/sessions?limit=8"),
        ]);
        performance.mark("setup-boot-fetch-end");
        recordClientMeasure("setup-boot-fetch", "setup-boot-fetch-start", "setup-boot-fetch-end");
        const loadedAgents = await parseResponse<Agent[]>(agentsResponse);
        const loadedSessions = await parseResponse<SessionSummary[]>(sessionsResponse);
        const agentTimings = getServerTimingMetrics(agentsResponse);
        const sessionTimings = getServerTimingMetrics(sessionsResponse);
        if (!active) {
          return;
        }
        setTimings((current) => ({ ...current, agents: agentTimings, sessions: sessionTimings }));
        logTimingMetrics("agents", agentTimings);
        logTimingMetrics("sessions", sessionTimings);
        setAgents(loadedAgents);
        setSelectedAgentId(loadedAgents[0]?.agent_id ?? "");
        setSessions(loadedSessions);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load agents");
        }
      } finally {
        if (active) {
          setIsCheckingAuth(false);
        }
      }
    };

    void boot();
    return () => {
      active = false;
    };
  }, [router]);

  const resetDraft = () => {
    setResumeFile(null);
    setJdFile(null);
    setJdMode("file");
    setJdText("");
    setJdUrl("");
    setCustomInstructions("");
    setResumeDocumentId(null);
    setJobDocumentId(null);
    setResumeProfile(null);
    setJobProfile(null);
    setSavedContext(null);
    setEditingSession(null);
    setError(null);
  };

  const refreshSessions = async () => {
    const sessionsResponse = await apiFetch("/api/sessions?limit=8");
    const sessionTimings = getServerTimingMetrics(sessionsResponse);
    setTimings((current) => ({ ...current, sessions: sessionTimings }));
    logTimingMetrics("sessions refresh", sessionTimings);
    const loadedSessions = await parseResponse<SessionSummary[]>(sessionsResponse);
    setSessions(loadedSessions);
  };

  useEffect(() => {
    if (isCheckingAuth) {
      return;
    }
    performance.mark("setup-render-end");
    try {
      performance.measure("setup-render", "setup-boot-fetch-end", "setup-render-end");
    } catch {
      return;
    }
  }, [isCheckingAuth, sessions.length]);

  const hasResumeReplacement = Boolean(resumeFile);
  const hasJobReplacement = jdMode === "file" ? Boolean(jdFile) : jdMode === "text" ? Boolean(jdText.trim()) : Boolean(jdUrl.trim());

  const canAnalyze = useMemo(() => {
    if (editingSession) {
      return hasResumeReplacement || hasJobReplacement;
    }
    return hasResumeReplacement && hasJobReplacement;
  }, [editingSession, hasJobReplacement, hasResumeReplacement]);

  const canSave = Boolean((resumeProfile || editingSession?.context?.resume_profile) && (jobProfile || editingSession?.context?.job_profile) && selectedAgentId);

  const loadSessionForEditing = async (session: SessionSummary) => {
    if (!session.editable) {
      setError("This session has already started. Create a new setup to use updated inputs.");
      return;
    }
    setBusyStep("Loading saved setup");
    try {
      const detailedSession = await fetchSessionDetail(session.session_id);
      setSetupMode("load");
      setEditingSession(detailedSession);
      setSavedContext(detailedSession.context ?? null);
      setSelectedAgentId(detailedSession.agent_id || detailedSession.context?.agent_id || "");
      setCustomInstructions(detailedSession.context?.custom_instructions || "");
      setResumeProfile(detailedSession.context?.resume_profile || null);
      setJobProfile(detailedSession.context?.job_profile || null);
      setResumeDocumentId(detailedSession.context?.resume_document?.document_id || detailedSession.context?.resume_profile?.document_id || null);
      setJobDocumentId(detailedSession.context?.job_document?.document_id || detailedSession.context?.job_profile?.document_id || null);
      setResumeFile(null);
      setJdFile(null);
      setJdText("");
      setJdUrl(detailedSession.context?.job_document?.source_type === "url" ? (detailedSession.context?.job_document?.source_url || "") : "");
      setJdMode(detailedSession.context?.job_document?.source_type === "url" ? "url" : "file");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load saved setup");
    } finally {
      setBusyStep(null);
    }
  };

  const analyzeSetup = async () => {
    if (!canAnalyze) {
      return;
    }

    setError(null);
    setSavedContext(null);

    try {
      let nextResumeProfile = editingSession?.context?.resume_profile || resumeProfile;
      let nextJobProfile = editingSession?.context?.job_profile || jobProfile;

      if (resumeFile) {
        setBusyStep("Uploading resume");
        const resumeForm = new FormData();
        resumeForm.append("file", resumeFile);
        const resumeUploadResponse = await apiFetch("/api/documents/resume", {
          method: "POST",
          body: resumeForm,
        });
        const resumeUpload = await parseResponse<{ document_id: string }>(resumeUploadResponse);
        setResumeDocumentId(resumeUpload.document_id);

        setBusyStep("Analyzing resume");
        const resumeProfileResponse = await apiFetch("/api/profiles/extract-from-resume", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ document_id: resumeUpload.document_id }),
        });
        nextResumeProfile = await parseResponse<ResumeProfile>(resumeProfileResponse);
        setResumeProfile(nextResumeProfile);
      }

      if (hasJobReplacement) {
        let uploadedJobDocumentId = "";
        setBusyStep("Preparing job description");
        if (jdMode === "file") {
          const jobForm = new FormData();
          jobForm.append("file", jdFile as File);
          const uploadResponse = await apiFetch("/api/documents/job-description/file", {
            method: "POST",
            body: jobForm,
          });
          const upload = await parseResponse<{ document_id: string }>(uploadResponse);
          uploadedJobDocumentId = upload.document_id;
        } else if (jdMode === "text") {
          const uploadResponse = await apiFetch("/api/documents/job-description/text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: jdText }),
          });
          const upload = await parseResponse<{ document_id: string }>(uploadResponse);
          uploadedJobDocumentId = upload.document_id;
        } else {
          const uploadResponse = await apiFetch("/api/documents/job-description/url", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: jdUrl }),
          });
          const upload = await parseResponse<{ document_id: string }>(uploadResponse);
          uploadedJobDocumentId = upload.document_id;
        }
        setJobDocumentId(uploadedJobDocumentId);

        setBusyStep("Analyzing role");
        const jobProfileResponse = await apiFetch("/api/profiles/extract-from-jd", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ document_id: uploadedJobDocumentId }),
        });
        nextJobProfile = await parseResponse<JobProfile>(jobProfileResponse);
        setJobProfile(nextJobProfile);
      }

      if (!nextResumeProfile || !nextJobProfile) {
        throw new Error("Both resume and job description profiles are required.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze setup");
    } finally {
      setBusyStep(null);
    }
  };

  const saveContext = async (startAfterSave: boolean) => {
    const activeResumeProfile = resumeProfile || editingSession?.context?.resume_profile;
    const activeJobProfile = jobProfile || editingSession?.context?.job_profile;
    if (!activeResumeProfile || !activeJobProfile || !selectedAgentId) {
      return;
    }

    setError(null);
    setBusyStep(
      editingSession
        ? (startAfterSave ? "Updating setup and opening interview" : "Updating setup")
        : (startAfterSave ? "Saving setup and starting interview" : "Saving setup")
    );
    try {
      if (editingSession) {
        const response = await apiFetch(`/api/sessions/${editingSession.session_id}/setup`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            resume_profile_id: activeResumeProfile.profile_id,
            job_profile_id: activeJobProfile.profile_id,
            agent_id: selectedAgentId,
            custom_instructions: customInstructions || null,
          }),
        });
        const session = await parseResponse<SessionDetail>(response);
        setSavedContext(session.context || null);
        setEditingSession(session);
        setResumeProfile(session.context?.resume_profile || activeResumeProfile);
        setJobProfile(session.context?.job_profile || activeJobProfile);
        await refreshSessions();
        if (startAfterSave) {
          router.push(`/interview?session_id=${session.session_id}&context_id=${session.interview_context_id}&agent_id=${selectedAgentId}`);
        }
      } else {
        const response = await apiFetch("/api/interview-contexts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            resume_profile_id: activeResumeProfile.profile_id,
            job_profile_id: activeJobProfile.profile_id,
            agent_id: selectedAgentId,
            custom_instructions: customInstructions || null,
          }),
        });
        const context = await parseResponse<ContextResponse>(response);
        setSavedContext(context);
        if (startAfterSave) {
          router.push(`/interview?context_id=${context.context_id}&agent_id=${context.agent_id}`);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save setup");
    } finally {
      setBusyStep(null);
    }
  };

  const resumeExistingSession = (session: SessionSummary) => {
    const params = new URLSearchParams({ session_id: session.session_id });
    if (session.interview_context_id) {
      params.set("context_id", session.interview_context_id);
    }
    if (session.agent_id) {
      params.set("agent_id", session.agent_id);
    }
    router.push(`/interview?${params.toString()}`);
  };

  if (isCheckingAuth) {
    return (
      <BaseLayout>
        <div className="flex min-h-[60vh] items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </BaseLayout>
    );
  }

  return (
    <BaseLayout>
      <PageHeader
        title="Setup Interview"
        description="Upload the candidate story, ingest the target role, choose the voice assistant, and save a reusable interview context."
      />

      <Tabs
        value={setupMode}
        onValueChange={(value) => {
          const nextMode = value as SetupMode;
          setSetupMode(nextMode);
          if (nextMode === "new" && editingSession) {
            resetDraft();
            setSetupMode("new");
          }
        }}
        className="space-y-6"
      >
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="new">New Setup</TabsTrigger>
          <TabsTrigger value="load">Load Existing</TabsTrigger>
        </TabsList>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <TabsContent value="load" className="mt-0 space-y-6">
            <ContentCard>
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold">Load Existing Session</h2>
                    <p className="text-sm text-muted-foreground">
                      Resume a saved interview or load a pending session into edit mode.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => void refreshSessions().catch((err) => {
                        setError(err instanceof Error ? err.message : "Failed to refresh sessions");
                      })}
                    >
                      Refresh
                    </Button>
                    {editingSession ? (
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => {
                          resetDraft();
                          setSetupMode("load");
                        }}
                      >
                        Clear Edit Mode
                      </Button>
                    ) : null}
                  </div>
                </div>

                {sessions.length ? (
                  <div className="grid gap-3">
                    {sessions.slice(0, 8).map((session) => (
                      <div
                        key={session.session_id}
                        className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 lg:flex-row lg:items-center lg:justify-between"
                      >
                        <div className="space-y-1">
                          <div className="font-medium">
                            {session.candidate_name || "Candidate"} for {session.target_role || "role"}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {session.company || "Unknown company"} with {session.agent_name || "assistant"}
                          </div>
                          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                            {session.state} · {session.created_at ? new Date(session.created_at).toLocaleString() : "Unknown date"}
                          </div>
                          {!session.editable ? (
                            <div className="text-xs text-amber-200/80">
                              Editing disabled because this session is no longer pending or already has interview history. You can still open it.
                            </div>
                          ) : null}
                        </div>
                        <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={() => resumeExistingSession(session)}
                          >
                            Resume Session
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            disabled={!session.editable}
                            onClick={() => void loadSessionForEditing(session)}
                          >
                            Edit Setup
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.03] px-4 py-5 text-sm text-muted-foreground">
                    No saved sessions yet. Complete a setup once, then you can load it from here regardless of status.
                  </div>
                )}
                {process.env.NODE_ENV !== "production" ? (
                  <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-xs text-muted-foreground">
                    <div className="font-medium text-foreground">Timing Debug</div>
                    <div>Agents: {timings.agents.length ? timings.agents.map((metric) => `${metric.name}=${metric.duration ?? "n/a"}ms`).join(", ") : "n/a"}</div>
                    <div>Sessions: {timings.sessions.length ? timings.sessions.map((metric) => `${metric.name}=${metric.duration ?? "n/a"}ms`).join(", ") : "n/a"}</div>
                    <div>Session detail: {timings.sessionDetail.length ? timings.sessionDetail.map((metric) => `${metric.name}=${metric.duration ?? "n/a"}ms`).join(", ") : "n/a"}</div>
                  </div>
                ) : null}
              </div>
            </ContentCard>
          </TabsContent>

          <TabsContent value="new" className="mt-0" />

          <ContentCard>
            <div className="grid gap-6 lg:grid-cols-2">
              <Card className="border-white/10 bg-black/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <UserRound className="h-4 w-4 text-primary" />
                    Resume
                  </CardTitle>
                  <CardDescription>
                    {editingSession
                      ? "Replace the linked resume only if you want to update this pending session."
                      : "Upload a PDF or DOCX resume for parsing and structured analysis."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Input type="file" accept=".pdf,.docx,application/pdf,.docx" onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)} />
                  <p className="text-sm text-muted-foreground">
                    {resumeFile
                      ? resumeFile.name
                      : editingSession?.context?.resume_document?.filename || "No resume selected yet."}
                  </p>
                  {editingSession?.context?.resume_document ? (
                    <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-muted-foreground">
                      Current linked resume: {editingSession.context.resume_document.filename || "Existing document"}
                    </div>
                  ) : null}
                </CardContent>
              </Card>

              <Card className="border-white/10 bg-black/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <FileText className="h-4 w-4 text-primary" />
                    Job Description
                  </CardTitle>
                  <CardDescription>
                    {editingSession
                      ? "Replace the linked job description only if you want to update this pending session."
                      : "Provide the target role as a file, pasted text, or URL."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Tabs value={jdMode} onValueChange={setJdMode}>
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="file">File</TabsTrigger>
                      <TabsTrigger value="text">Text</TabsTrigger>
                      <TabsTrigger value="url">URL</TabsTrigger>
                    </TabsList>
                    <TabsContent value="file" className="space-y-3">
                      <Input type="file" accept=".pdf,.docx,application/pdf,.docx" onChange={(e) => setJdFile(e.target.files?.[0] ?? null)} />
                      <p className="text-sm text-muted-foreground">
                        {jdFile
                          ? jdFile.name
                          : editingSession?.context?.job_document?.source_type === "file"
                            ? (editingSession.context.job_document.filename || "Existing job description file")
                            : "No job description file selected yet."}
                      </p>
                    </TabsContent>
                    <TabsContent value="text">
                      <textarea
                        className="min-h-40 w-full rounded-xl border border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/30"
                        placeholder="Paste the job description here..."
                        value={jdText}
                        onChange={(e) => setJdText(e.target.value)}
                      />
                    </TabsContent>
                    <TabsContent value="url" className="space-y-3">
                      <div className="relative">
                        <LinkIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input className="pl-9" placeholder="https://company.com/jobs/role" value={jdUrl} onChange={(e) => setJdUrl(e.target.value)} />
                      </div>
                    </TabsContent>
                  </Tabs>
                  {editingSession?.context?.job_document ? (
                    <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-muted-foreground">
                      Current linked JD: {editingSession.context.job_document.filename || editingSession.context.job_document.source_url || "Existing document"}
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            </div>
          </ContentCard>

          <ContentCard>
            <div className="grid gap-6 lg:grid-cols-[0.7fr_1.3fr]">
              <Card className="border-white/10 bg-black/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Sparkles className="h-4 w-4 text-primary" />
                    Voice Assistant
                  </CardTitle>
                  <CardDescription>v1 exposes the narrative architect agent only, but the selector remains future-safe.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <select
                    value={selectedAgentId}
                    onChange={(e) => setSelectedAgentId(e.target.value)}
                    className="w-full rounded-xl border border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] px-3 py-2.5 text-sm"
                  >
                    {agents.map((agent) => (
                      <option key={agent.agent_id} value={agent.agent_id}>
                        {agent.name}
                      </option>
                    ))}
                  </select>
                  <textarea
                    className="min-h-32 w-full rounded-xl border border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder="Optional custom setup instructions for this interview context"
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                  />
                </CardContent>
              </Card>

              <Card className="border-white/10 bg-black/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Wand2 className="h-4 w-4 text-primary" />
                    Analysis Workspace
                  </CardTitle>
                  <CardDescription>
                    {editingSession
                      ? "Re-run analysis only for the inputs you replace. Agent-only changes can be saved without reanalysis."
                      : "Run parsing and profile extraction before saving the interview setup."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <Button onClick={analyzeSetup} disabled={!canAnalyze || Boolean(busyStep)}>
                      {busyStep ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                      Analyze Inputs
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      {busyStep || (editingSession ? "Replace a resume or job description to refresh the extracted profiles." : "Resume + role analysis has not started yet.")}
                    </span>
                  </div>
                  {error ? (
                    <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                      {error}
                    </div>
                  ) : null}
                  {(resumeDocumentId || jobDocumentId) && (
                    <div className="grid gap-3 md:grid-cols-2">
                      <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-muted-foreground">
                        Resume document id
                        <div className="mt-1 break-all font-mono text-xs text-foreground">{resumeDocumentId || "Pending"}</div>
                      </div>
                      <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-muted-foreground">
                        Job document id
                        <div className="mt-1 break-all font-mono text-xs text-foreground">{jobDocumentId || "Pending"}</div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </ContentCard>
        </div>

        <div className="space-y-6">
          <Card className="border-white/10 bg-black/20">
            <CardHeader>
              <CardTitle>Parsed Summaries</CardTitle>
              <CardDescription>Review the extracted profiles before you persist the interview context.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <h3 className="text-sm font-medium text-primary">Candidate Snapshot</h3>
                {resumeProfile ? (
                  <div className="mt-3 space-y-3 text-sm">
                    <div>
                      <div className="font-medium">{resumeProfile.name}</div>
                      <div className="text-muted-foreground">{resumeProfile.headline}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {resumeProfile.skills.slice(0, 10).map((skill) => (
                        <span key={skill} className="rounded-full border border-white/10 px-2.5 py-1 text-xs text-muted-foreground">
                          {skill}
                        </span>
                      ))}
                    </div>
                    <div className="space-y-2">
                      {resumeProfile.experience.slice(0, 3).map((item, index) => (
                        <div key={`${item.title}-${index}`} className="rounded-xl border border-white/10 px-3 py-2">
                          <div className="font-medium">{item.title || "Role"}</div>
                          <div className="text-muted-foreground">{item.company || "Company"} {item.duration ? `· ${item.duration}` : ""}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-muted-foreground">Run analysis to generate the structured resume profile.</p>
                )}
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <h3 className="text-sm font-medium text-primary">Role Snapshot</h3>
                {jobProfile ? (
                  <div className="mt-3 space-y-3 text-sm">
                    <div>
                      <div className="font-medium">{jobProfile.role}</div>
                      <div className="text-muted-foreground">{jobProfile.company}</div>
                    </div>
                    <div>
                      <div className="mb-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">Requirements</div>
                      <ul className="space-y-1.5 text-muted-foreground">
                        {displayedJobRequirements.slice(0, 6).map((item) => (
                          <li key={item}>• {item}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <div className="mb-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">Responsibilities</div>
                      <ul className="space-y-1.5 text-muted-foreground">
                        {displayedJobResponsibilities.slice(0, 4).map((item) => (
                          <li key={item}>• {item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-muted-foreground">Run analysis to generate the structured job profile.</p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-black/20">
            <CardHeader>
              <CardTitle>Interview Context</CardTitle>
              <CardDescription>Persist the reusable setup, then start the live voice interview when ready.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {savedContext ? (
                <div className="rounded-2xl border border-emerald-400/30 bg-emerald-400/10 p-4 text-sm">
                  <div className="font-medium text-emerald-100">Setup saved</div>
                  <div className="mt-1 text-emerald-200/80">Context id: {savedContext.context_id}</div>
                  <div className="mt-2 text-emerald-200/80">
                    Match score: {savedContext.match_analysis?.match_score ?? 0}%
                  </div>
                </div>
              ) : null}
              <div className="grid gap-3 sm:grid-cols-2">
                <Button onClick={() => saveContext(false)} disabled={!canSave || Boolean(busyStep)} variant="secondary">
                  {editingSession ? "Save Changes" : "Save Setup"}
                </Button>
                <Button onClick={() => saveContext(true)} disabled={!canSave || Boolean(busyStep)}>
                  {editingSession ? "Update And Open Interview" : "Save And Start Interview"}
                </Button>
              </div>
              <p className={cn("text-sm text-muted-foreground", !canSave && "opacity-70")}>
                {editingSession
                  ? "Save remains disabled until this pending session has a resume profile, a job profile, and a selected voice assistant."
                  : "Save remains disabled until both documents are parsed and a voice assistant is selected."}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
      </Tabs>
    </BaseLayout>
  );
}
