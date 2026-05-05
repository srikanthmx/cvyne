"use client";
import { useEffect, useState, useCallback } from "react";
import { applicationsApi } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export type StatusEvent = {
  application_id: string;
  status: "queued" | "processing" | "generating_cv" | "filling_form" | "submitted" | "failed" | "requires_human" | "cancelled";
  step: string;
  progress: number;
  code?: string;
  message?: string;
};

export const TERMINAL_STATUSES = new Set(["submitted", "failed", "requires_human", "cancelled"]);

export function useApplicationStream(applicationId: string | null) {
  const [event, setEvent] = useState<StatusEvent | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!applicationId) return;
    const es = applicationsApi.streamStatus(applicationId);
    let closed = false;

    const close = () => {
      if (!closed) { es.close(); closed = true; }
    };

    es.addEventListener("status_update", (e) => {
      try {
        const parsed = JSON.parse((e as MessageEvent).data) as StatusEvent;
        setEvent(parsed);
        if (TERMINAL_STATUSES.has(parsed.status)) { setDone(true); close(); }
      } catch {}
    });

    es.addEventListener("done", () => { setDone(true); close(); });
    es.onerror = close;

    return close;
  }, [applicationId]);

  return { event, done };
}

export type Screenshot = {
  step: number;
  screenshot_b64: string;
  url?: string | null;
  title?: string | null;
};

/**
 * Like useApplicationStream but accumulates all events into an array for
 * activity-log style UIs. Also captures browser screenshots emitted by the
 * BrowserAgent so the UI can show a live "agent's-eye view".
 */
export function useApplicationActivityStream(applicationId: string | null) {
  const [events, setEvents] = useState<StatusEvent[]>([]);
  const [screenshots, setScreenshots] = useState<Screenshot[]>([]);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!applicationId) return;
    setEvents([]);
    setScreenshots([]);
    setDone(false);

    const es = applicationsApi.streamStatus(applicationId);
    let closed = false;
    const close = () => {
      if (!closed) { es.close(); closed = true; }
    };

    es.addEventListener("status_update", (e) => {
      try {
        const parsed = JSON.parse((e as MessageEvent).data);
        // Backend multiplexes two payload kinds on the same channel:
        //   { kind: "screenshot", screenshot_b64, step, url, title }
        //   StatusEvent (no `kind` field)
        if (parsed.kind === "screenshot") {
          setScreenshots((prev) => [...prev, parsed as Screenshot].slice(-30));
          return;
        }
        const status = parsed as StatusEvent;
        setEvents((prev) => [...prev, status]);
        if (TERMINAL_STATUSES.has(status.status)) { setDone(true); close(); }
      } catch {}
    });

    es.addEventListener("done", () => { setDone(true); close(); });
    es.onerror = close;

    return close;
  }, [applicationId]);

  return {
    events,
    screenshots,
    latestScreenshot: screenshots[screenshots.length - 1] ?? null,
    done,
    latest: events[events.length - 1] ?? null,
  };
}

export function useCancelApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/applications/${id}/cancel`, {
        method: "POST",
        headers: { Authorization: `Bearer ${await (window as any).Clerk?.session?.getToken()}` },
      });
      if (!res.ok) throw new Error("Failed to cancel");
      return res.json();
    },
    onSuccess: () => {
      toast.success("Application cancelled");
      qc.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: () => toast.error("Failed to cancel application"),
  });
}

export function useRetryApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/applications/${id}/retry`, {
        method: "POST",
        headers: { Authorization: `Bearer ${await (window as any).Clerk?.session?.getToken()}` },
      });
      if (!res.ok) throw new Error("Failed to retry");
      return res.json();
    },
    onSuccess: () => {
      toast.success("Application re-queued");
      qc.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: () => toast.error("Failed to retry application"),
  });
}
