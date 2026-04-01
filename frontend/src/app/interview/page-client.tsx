"use client";

import { BaseLayout, ContentCard, PageHeader } from "@/components/layouts/base-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LiquidGlassVoiceAssistant } from "@/components/ui/lg-voice-assistant";
import { apiFetch, getServerTimingMetrics, type ServerTimingMetric } from "@/lib/api";
import { Loader2, Sparkles } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

type InterviewContext = {
  context_id?: string;
  session_id?: string;
  startup_prompt: string;
  agent: {
    name: string;
    prompt_template: string;
  };
  resume_profile: {
    name?: string;
    headline?: string;
  };
  job_profile: {
    company?: string;
    role?: string;
  };
  match_analysis: {
    match_score?: number;
  };
};

type InterviewDebugTiming = {
  session: ServerTimingMetric[];
  context: ServerTimingMetric[];
  sessionCreate: ServerTimingMetric[];
  client: Array<{ name: string; duration: number; detail?: string }>;
};

async function parseResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data as T;
}

export default function InterviewPageClient() {
  const searchParams = useSearchParams();
  const contextId = searchParams.get("context_id");
  const agentId = searchParams.get("agent_id");
  const sessionIdParam = searchParams.get("session_id");
  const [context, setContext] = useState<InterviewContext | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(contextId || sessionIdParam));
  const [error, setError] = useState<string | null>(null);
  const [timings, setTimings] = useState<InterviewDebugTiming>({
    session: [],
    context: [],
    sessionCreate: [],
    client: [],
  });

  const logTimingMetrics = (label: string, metrics: ServerTimingMetric[]) => {
    if (!metrics.length) {
      return;
    }
    console.debug(`[interview] ${label} Server-Timing`, metrics);
  };

  const recordClientMetric = (name: string, duration: number, detail?: string) => {
    const metric = { name, duration: Number(duration.toFixed(2)), detail };
    setTimings((current) => ({
      ...current,
      client: [...current.client.filter((item) => item.name !== name), metric],
    }));
    console.debug("[interview] client metric", metric);
  };

  useEffect(() => {
    if (!contextId && !sessionIdParam) {
      setLoading(false);
      return;
    }

    let active = true;
    const prepare = async () => {
      performance.mark("interview-prepare-start");
      try {
        if (!active) {
          return;
        }

        if (sessionIdParam) {
          const sessionResponse = await apiFetch(`/api/interview-prep/${sessionIdParam}`);
          const sessionTimings = getServerTimingMetrics(sessionResponse);
          const session = await parseResponse<InterviewContext>(sessionResponse);
          if (!active) {
            return;
          }
          setTimings((current) => ({ ...current, session: sessionTimings }));
          logTimingMetrics("session detail", sessionTimings);
          setSessionId(session.session_id || null);
          setContext(session);
          return;
        }

        const prepResponse = await apiFetch("/api/interview-prep", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            context_id: contextId,
            agent_id: agentId || undefined,
          }),
        });
        const sessionCreateTimings = getServerTimingMetrics(prepResponse);
        const prep = await parseResponse<InterviewContext>(prepResponse);

        if (!active) {
          return;
        }

        setTimings((current) => ({
          ...current,
          sessionCreate: sessionCreateTimings,
        }));
        logTimingMetrics("interview prep", sessionCreateTimings);
        setContext(prep);
        setSessionId(prep.session_id || null);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to prepare interview");
        }
      } finally {
        if (active) {
          performance.mark("interview-prepare-end");
          try {
            performance.measure("interview-prepare", "interview-prepare-start", "interview-prepare-end");
            const measure = performance.getEntriesByName("interview-prepare").at(-1);
            if (measure) {
              recordClientMetric("interview.prepare.client", measure.duration);
            }
          } catch {
            // Ignore browser measure failures.
          }
          setLoading(false);
        }
      }
    };

    void prepare();
    return () => {
      active = false;
    };
  }, [agentId, contextId, sessionIdParam]);

  return (
    <BaseLayout>
      <PageHeader
        title="Start Interview"
        description="The voice assistant uses the saved interview context, role mission, and candidate-role match summary."
      />

      <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <Card className="border-white/10 bg-black/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Loaded Context
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {loading ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Preparing the saved setup...
              </div>
            ) : error ? (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-red-200">
                {error}
              </div>
            ) : context ? (
              <>
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <div className="font-medium">{context.agent.name}</div>
                  <div className="mt-1 text-muted-foreground">
                    {context.resume_profile.name || "Candidate"} targeting {context.job_profile.role || "role"} at {context.job_profile.company || "company"}.
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Candidate</div>
                    <div className="mt-2 font-medium">{context.resume_profile.name || "Unknown"}</div>
                    <div className="text-muted-foreground">{context.resume_profile.headline || "No headline extracted"}</div>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Target role</div>
                    <div className="mt-2 font-medium">{context.job_profile.role || "Unknown role"}</div>
                    <div className="text-muted-foreground">{context.job_profile.company || "Unknown company"}</div>
                  </div>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Match score</div>
                  <div className="mt-2 text-2xl font-semibold">{context.match_analysis.match_score ?? 0}%</div>
                </div>
                {sessionId ? (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-muted-foreground">
                    Session id
                    <div className="mt-1 break-all font-mono text-foreground">{sessionId}</div>
                  </div>
                ) : null}
                {process.env.NODE_ENV !== "production" ? (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-muted-foreground">
                    <div className="font-medium text-foreground">Performance Debug</div>
                    <div>Session: {timings.session.length ? timings.session.map((metric) => `${metric.name}=${metric.duration ?? "n/a"}ms`).join(", ") : "n/a"}</div>
                    <div>Context: {timings.context.length ? timings.context.map((metric) => `${metric.name}=${metric.duration ?? "n/a"}ms`).join(", ") : "n/a"}</div>
                    <div>Session create: {timings.sessionCreate.length ? timings.sessionCreate.map((metric) => `${metric.name}=${metric.duration ?? "n/a"}ms`).join(", ") : "n/a"}</div>
                    <div>Client: {timings.client.length ? timings.client.map((metric) => `${metric.name}=${metric.duration}ms`).join(", ") : "n/a"}</div>
                  </div>
                ) : null}
              </>
            ) : (
              <div className="text-muted-foreground">No setup context provided. Start from the Setup Interview page.</div>
            )}
          </CardContent>
        </Card>

        <ContentCard>
          <div className="flex flex-col items-center">
            <h3 className="mb-4 text-lg font-semibold">Voice Assistant</h3>
            <LiquidGlassVoiceAssistant />
          </div>
        </ContentCard>
      </div>
    </BaseLayout>
  );
}
