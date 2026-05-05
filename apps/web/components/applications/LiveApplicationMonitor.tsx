"use client";
import { useEffect, useRef, useState } from "react";
import { useApplicationStream, useCancelApplication, useRetryApplication, TERMINAL_STATUSES, type StatusEvent } from "@/hooks/useApplicationStream";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2, AlertCircle, AlertTriangle, Loader2,
  Square, RefreshCw, Bot, Terminal, Globe, Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Step definitions ──────────────────────────────────────────────────────────
const PIPELINE_STEPS = [
  { key: "jd_extraction",          label: "Reading JD",         icon: Globe },
  { key: "resume_personalization", label: "Tailoring resume",   icon: Zap },
  { key: "ats_optimization",       label: "ATS pass",           icon: Terminal },
  { key: "cv_generation",          label: "Generating CV",      icon: Bot },
  { key: "form_autofill",          label: "Filling form",       icon: Bot },
  { key: "done",                   label: "Submitted",          icon: CheckCircle2 },
];

// ── Simulated browser activity log ───────────────────────────────────────────
const STEP_LOGS: Record<string, string[]> = {
  jd_extraction:          ["Opening job URL…", "Parsing page HTML…", "Extracting role, skills, requirements…"],
  resume_personalization: ["Scoring resume bullets vs JD…", "Rewriting experience section…", "Injecting keywords…"],
  ats_optimization:       ["Checking keyword density…", "Normalising section headers…", "ATS score: calculating…"],
  cv_generation:          ["Rendering PDF template…", "Uploading to storage…"],
  form_autofill:          ["Navigating to apply page…", "Detecting form fields…", "Filling name, email, experience…", "Attaching CV…", "Clicking Submit…"],
  done:                   ["✓ Application submitted successfully"],
  error:                  ["✗ An error occurred — check details below"],
  cancelled:              ["⊘ Cancelled by user"],
};

function ActivityLog({ logs }: { logs: string[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [logs]);

  return (
    <div
      ref={ref}
      className="h-36 overflow-y-auto bg-zinc-950 rounded-lg p-3 font-mono text-xs text-zinc-300 space-y-1 border border-zinc-800"
    >
      {logs.map((line, i) => (
        <div key={i} className="flex gap-2">
          <span className="text-zinc-600 select-none shrink-0">
            {String(i + 1).padStart(2, "0")}
          </span>
          <span className={cn(
            line.startsWith("✓") && "text-green-400",
            line.startsWith("✗") && "text-red-400",
            line.startsWith("⊘") && "text-zinc-500",
          )}>{line}</span>
        </div>
      ))}
      {/* blinking cursor on last line while active */}
      <div className="flex gap-2">
        <span className="text-zinc-600 select-none">▸</span>
        <span className="animate-pulse text-zinc-500">_</span>
      </div>
    </div>
  );
}

// ── Browser chrome mock ───────────────────────────────────────────────────────
function BrowserChrome({ url, step, status }: { url?: string; step: string; status: string }) {
  const isActive = !TERMINAL_STATUSES.has(status) && status !== "queued";
  return (
    <div className="rounded-xl border border-border overflow-hidden bg-muted/30">
      {/* address bar */}
      <div className="flex items-center gap-2 px-3 py-2 bg-muted/60 border-b border-border">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-400/60" />
          <div className="w-3 h-3 rounded-full bg-yellow-400/60" />
          <div className="w-3 h-3 rounded-full bg-green-400/60" />
        </div>
        <div className="flex-1 bg-background rounded-md px-3 py-1 text-xs text-muted-foreground font-mono truncate border border-border/50 flex items-center gap-2">
          {isActive && <Loader2 className="w-3 h-3 animate-spin shrink-0 text-primary" />}
          {url || "about:blank"}
        </div>
      </div>
      {/* viewport */}
      <div className="h-48 relative overflow-hidden bg-background flex items-center justify-center">
        {status === "queued" && (
          <div className="text-center text-muted-foreground">
            <Bot className="w-10 h-10 mx-auto mb-2 opacity-20" />
            <p className="text-xs">Waiting to start…</p>
          </div>
        )}
        {isActive && (
          <div className="w-full h-full p-4 space-y-3 animate-pulse">
            <div className="h-4 bg-muted rounded w-3/4" />
            <div className="h-3 bg-muted rounded w-1/2" />
            <div className="h-3 bg-muted rounded w-5/6" />
            <div className="h-3 bg-muted rounded w-2/3" />
            <div className="mt-4 h-8 bg-primary/10 rounded-lg w-1/3 border border-primary/20" />
            <div className="h-3 bg-muted rounded w-4/5" />
            <div className="h-3 bg-muted rounded w-3/5" />
          </div>
        )}
        {status === "submitted" && (
          <div className="text-center text-green-600">
            <CheckCircle2 className="w-12 h-12 mx-auto mb-2" />
            <p className="text-sm font-medium">Application submitted</p>
          </div>
        )}
        {status === "failed" && (
          <div className="text-center text-destructive">
            <AlertCircle className="w-10 h-10 mx-auto mb-2 opacity-60" />
            <p className="text-xs">Task failed</p>
          </div>
        )}
        {status === "requires_human" && (
          <div className="text-center text-yellow-600">
            <AlertTriangle className="w-10 h-10 mx-auto mb-2" />
            <p className="text-xs font-medium">CAPTCHA — needs you</p>
          </div>
        )}
        {status === "cancelled" && (
          <div className="text-center text-muted-foreground">
            <Square className="w-10 h-10 mx-auto mb-2 opacity-30" />
            <p className="text-xs">Cancelled</p>
          </div>
        )}
        {/* scanning overlay */}
        {isActive && (
          <div className="absolute inset-0 pointer-events-none">
            <div
              className="absolute left-0 right-0 h-0.5 bg-primary/30"
              style={{ animation: "scan 2s linear infinite" }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
interface Props {
  applicationId: string;
  jobUrl?: string;
  onClose?: () => void;
}

export function LiveApplicationMonitor({ applicationId, jobUrl, onClose }: Props) {
  const { event, done } = useApplicationStream(applicationId);
  const cancelMutation = useCancelApplication();
  const retryMutation = useRetryApplication();
  const [logs, setLogs] = useState<string[]>(["Initialising agent…"]);
  const logTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const status = event?.status ?? "queued";
  const progress = event?.progress ?? 0;
  const step = event?.step ?? "";

  // Drip-feed log lines when step changes
  useEffect(() => {
    logTimers.current.forEach(clearTimeout);
    logTimers.current = [];
    const lines = STEP_LOGS[step] ?? [];
    lines.forEach((line, i) => {
      const t = setTimeout(() => setLogs((prev) => [...prev, line]), i * 600);
      logTimers.current.push(t);
    });
    return () => logTimers.current.forEach(clearTimeout);
  }, [step]);

  const activeStepIdx = PIPELINE_STEPS.findIndex((s) => s.key === step);
  const isTerminal = TERMINAL_STATUSES.has(status);
  const isRunning = !isTerminal && status !== "queued";

  return (
    <Card className="w-full overflow-hidden border-border shadow-lg">
      <CardHeader className="pb-3 pt-4 px-5 flex flex-row items-center justify-between gap-4 border-b border-border bg-muted/20">
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center",
            isRunning ? "bg-primary/10" : "bg-muted",
          )}>
            <Bot className={cn("w-4 h-4", isRunning ? "text-primary" : "text-muted-foreground")} />
          </div>
          <div>
            <p className="text-sm font-semibold leading-none">AI Agent</p>
            <p className="text-xs text-muted-foreground mt-0.5 truncate max-w-[200px]">
              {jobUrl ? new URL(jobUrl).hostname : "Applying…"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <StatusBadge status={status} />
          {isRunning && (
            <Button
              size="sm"
              variant="destructive"
              className="h-7 px-3 text-xs gap-1.5"
              onClick={() => cancelMutation.mutate(applicationId)}
              disabled={cancelMutation.isPending}
            >
              <Square className="w-3 h-3" /> Stop
            </Button>
          )}
          {(status === "failed" || status === "cancelled") && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 px-3 text-xs gap-1.5"
              onClick={() => retryMutation.mutate(applicationId)}
              disabled={retryMutation.isPending}
            >
              <RefreshCw className={cn("w-3 h-3", retryMutation.isPending && "animate-spin")} /> Retry
            </Button>
          )}
          {onClose && isTerminal && (
            <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={onClose}>
              Dismiss
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-5 space-y-5">
        {/* Pipeline steps */}
        <div className="flex items-center gap-1">
          {PIPELINE_STEPS.map((s, idx) => {
            const Icon = s.icon;
            const isComplete = idx < activeStepIdx || status === "submitted";
            const isActive = idx === activeStepIdx && isRunning;
            return (
              <div key={s.key} className="flex items-center flex-1 last:flex-none">
                <div className="flex flex-col items-center gap-1">
                  <div className={cn(
                    "w-7 h-7 rounded-full flex items-center justify-center border-2 transition-all",
                    isComplete ? "bg-primary border-primary text-primary-foreground" :
                    isActive   ? "bg-background border-primary text-primary" :
                                 "bg-background border-muted text-muted-foreground",
                  )}>
                    {isActive
                      ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      : <Icon className="w-3.5 h-3.5" />
                    }
                  </div>
                  <span className={cn(
                    "text-[9px] font-medium text-center leading-tight w-14 hidden sm:block",
                    isActive ? "text-foreground" : "text-muted-foreground",
                  )}>{s.label}</span>
                </div>
                {idx < PIPELINE_STEPS.length - 1 && (
                  <div className={cn(
                    "flex-1 h-0.5 mx-1 mb-4 rounded transition-colors",
                    isComplete ? "bg-primary" : "bg-muted",
                  )} />
                )}
              </div>
            );
          })}
        </div>

        <Progress value={progress} className="h-1.5" />

        {/* Browser chrome */}
        <BrowserChrome url={jobUrl} step={step} status={status} />

        {/* Activity log */}
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1.5 flex items-center gap-1.5">
            <Terminal className="w-3 h-3" /> Agent log
          </p>
          <ActivityLog logs={logs} />
        </div>

        {/* Error / CAPTCHA callouts */}
        {status === "requires_human" && (
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 flex items-start gap-3">
            <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-700">CAPTCHA detected</p>
              <p className="text-xs text-yellow-600/80 mt-0.5">The agent hit a CAPTCHA. Complete it manually then retry.</p>
            </div>
          </div>
        )}
        {status === "failed" && event?.message && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3 flex items-start gap-3">
            <AlertCircle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
            <p className="text-xs text-destructive">{event.message}</p>
          </div>
        )}
      </CardContent>

      <style>{`
        @keyframes scan {
          0%   { top: 0; }
          100% { top: 100%; }
        }
      `}</style>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; className: string }> = {
    queued:         { label: "Queued",          className: "bg-muted text-muted-foreground" },
    processing:     { label: "Running",         className: "bg-blue-500/10 text-blue-500" },
    generating_cv:  { label: "Generating CV",   className: "bg-blue-500/10 text-blue-500" },
    filling_form:   { label: "Filling form",    className: "bg-blue-500/10 text-blue-500" },
    submitted:      { label: "Submitted",       className: "bg-green-500/10 text-green-600" },
    failed:         { label: "Failed",          className: "bg-red-500/10 text-red-500" },
    requires_human: { label: "Needs you",       className: "bg-yellow-500/10 text-yellow-600" },
    cancelled:      { label: "Cancelled",       className: "bg-muted text-muted-foreground" },
  };
  const { label, className } = map[status] ?? map.queued;
  return <Badge variant="secondary" className={cn("border-0 text-xs", className)}>{label}</Badge>;
}
