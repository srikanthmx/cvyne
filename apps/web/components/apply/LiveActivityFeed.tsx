"use client";

import { useEffect, useRef } from "react";
import {
  Loader2,
  Check,
  XCircle,
  AlertTriangle,
  Sparkles,
  FileSearch,
  PenLine,
  FileText,
  MousePointerClick,
  Send,
  Hand,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

type StepKey =
  | "queued"
  | "jd_extraction"
  | "resume_personalization"
  | "ats_optimization"
  | "cover_letter"
  | "cv_generation"
  | "form_autofill"
  | "done"
  | "error";

interface LiveEvent {
  status: string;
  step?: string;
  progress?: number;
  message?: string | null;
  error_code?: string | null;
}

interface LiveActivityFeedProps {
  events: LiveEvent[];
  done: boolean;
  className?: string;
}

const STEPS: { key: StepKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: "queued", label: "Queued", icon: Sparkles },
  { key: "jd_extraction", label: "Reading the job posting", icon: FileSearch },
  { key: "resume_personalization", label: "Tailoring your resume", icon: PenLine },
  { key: "ats_optimization", label: "Optimizing for ATS", icon: Sparkles },
  { key: "cv_generation", label: "Generating CV PDF", icon: FileText },
  { key: "form_autofill", label: "Filling the application form", icon: MousePointerClick },
  { key: "done", label: "Submitted", icon: Send },
];

/**
 * Real-time activity feed driven by the SSE event stream from /applications/{id}/stream.
 * Renders a stepper + live progress bar + scrolling activity log.
 *
 * Visual heartbeat: always shows progress *something*, never a static screen.
 */
export function LiveActivityFeed({ events, done, className }: LiveActivityFeedProps) {
  const scrollerRef = useRef<HTMLDivElement>(null);
  const latest = events[events.length - 1];
  const progress = latest?.progress ?? 0;
  const currentStep = (latest?.step ?? "queued") as StepKey;
  const isError = latest?.status === "failed" || latest?.error_code;
  const requiresHuman = latest?.status === "requires_human";

  // Auto-scroll the activity log
  useEffect(() => {
    scrollerRef.current?.scrollTo({
      top: scrollerRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [events.length]);

  return (
    <div className={cn("space-y-6", className)}>
      {/* Big progress bar */}
      <div className="space-y-2">
        <div className="flex items-baseline justify-between">
          <span className="text-sm font-medium">
            {done
              ? requiresHuman
                ? "Needs your attention"
                : isError
                  ? "Something went wrong"
                  : "Application submitted"
              : "In progress"}
          </span>
          <span className="text-sm tabular-nums text-muted-foreground">
            {progress}%
          </span>
        </div>
        <Progress
          value={progress}
          className={cn(
            "h-2",
            isError && "[&>div]:bg-destructive",
            requiresHuman && "[&>div]:bg-amber-500",
            done && !isError && !requiresHuman && "[&>div]:bg-emerald-500",
          )}
        />
      </div>

      {/* Stepper */}
      <ol className="space-y-3">
        {STEPS.filter((s) => s.key !== "done" || done).map((step) => {
          const state = stepState(events, step.key, done);
          return <StepItem key={step.key} step={step} state={state} />;
        })}
      </ol>

      {/* Activity log */}
      <div className="bg-muted/30 border border-border rounded-lg overflow-hidden">
        <div className="px-3 py-2 border-b border-border bg-background/50 text-xs uppercase tracking-wider text-muted-foreground font-semibold">
          Activity
        </div>
        <div ref={scrollerRef} className="max-h-48 overflow-y-auto p-3 space-y-1.5 font-mono text-xs">
          {events.length === 0 ? (
            <div className="text-muted-foreground italic">Waiting for the agent to start…</div>
          ) : (
            events.map((e, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-muted-foreground/60">▸</span>
                <span className="text-foreground/80">
                  {e.message || `${e.step ?? "—"} (${e.progress ?? 0}%)`}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {requiresHuman && (
        <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800 rounded-lg p-4 flex items-start gap-3">
          <Hand className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-medium text-amber-900 dark:text-amber-200">
              Manual step required
            </div>
            <div className="text-sm text-amber-800/80 dark:text-amber-200/80 mt-0.5">
              {latest?.message ?? "The agent encountered a CAPTCHA or unfamiliar field — please open the application in a browser tab to complete it."}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function stepState(
  events: LiveEvent[],
  stepKey: StepKey,
  done: boolean,
): "pending" | "active" | "complete" | "error" {
  const seen = events.find((e) => e.step === stepKey);
  const latest = events[events.length - 1];
  const latestIdx = STEPS.findIndex((s) => s.key === latest?.step);
  const myIdx = STEPS.findIndex((s) => s.key === stepKey);

  if (latest?.status === "failed" && seen) return "error";
  if (latest?.status === "submitted" || done) return myIdx <= latestIdx ? "complete" : "pending";
  if (myIdx < latestIdx) return "complete";
  if (myIdx === latestIdx) return "active";
  return "pending";
}

function StepItem({
  step,
  state,
}: {
  step: { key: StepKey; label: string; icon: React.ComponentType<{ className?: string }> };
  state: "pending" | "active" | "complete" | "error";
}) {
  const Icon = step.icon;
  return (
    <li className="flex items-center gap-3">
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center transition-all",
          state === "pending" && "bg-muted text-muted-foreground",
          state === "active" && "bg-primary text-primary-foreground ring-4 ring-primary/20",
          state === "complete" && "bg-emerald-500 text-white",
          state === "error" && "bg-destructive text-destructive-foreground",
        )}
      >
        {state === "active" && <Loader2 className="w-4 h-4 animate-spin" />}
        {state === "complete" && <Check className="w-4 h-4" />}
        {state === "error" && <XCircle className="w-4 h-4" />}
        {state === "pending" && <Icon className="w-4 h-4" />}
      </div>
      <span
        className={cn(
          "text-sm transition-colors",
          state === "pending" && "text-muted-foreground",
          state === "active" && "text-foreground font-medium",
          state === "complete" && "text-foreground/80",
          state === "error" && "text-destructive",
        )}
      >
        {step.label}
      </span>
    </li>
  );
}
