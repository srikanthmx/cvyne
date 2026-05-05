"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import type { components } from "shared-types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type PreviewResponse = {
  job: any;
  base_resume: any;
  tailored_resume: any;
  cv_preview_url: string;
  cover_letter: string | null;
};

async function authedFetch(path: string, init?: RequestInit) {
  const token = await (window as any).Clerk?.session?.getToken?.();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      "Content-Type": "application/json",
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

export function useResumesList() {
  return useQuery({
    queryKey: ["resumes"],
    queryFn: () => authedFetch("/api/v1/resumes/"),
  });
}

export function useJob(jobId: string | null) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => authedFetch(`/api/v1/jobs/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (q) => {
      const status = (q.state.data as any)?.status;
      return status === "pending" || status === "extracting" ? 2000 : false;
    },
  });
}

/**
 * The "magic moment" mutation — runs personalization + ATS + CV generation
 * synchronously and returns everything the Apply page needs.
 */
export function usePreviewApplication() {
  return useMutation<PreviewResponse, Error, { job_id: string; resume_id: string; theme?: string; generate_cover_letter?: boolean }>({
    mutationFn: (body) =>
      authedFetch("/api/v1/applications/preview", {
        method: "POST",
        body: JSON.stringify({ theme: "ats", generate_cover_letter: false, ...body }),
      }),
    onError: (e) => toast.error("Preview failed", { description: e.message }),
  });
}

export function useSubmitApplication() {
  const qc = useQueryClient();
  return useMutation<{ id: string }, Error, { job_id: string; resume_id: string; theme?: string; generate_cover_letter?: boolean }>({
    mutationFn: (body) =>
      authedFetch("/api/v1/applications/", {
        method: "POST",
        body: JSON.stringify({ theme: "ats", generate_cover_letter: false, ...body }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      toast.success("Application submitted to the queue");
    },
    onError: (e) => toast.error("Submit failed", { description: e.message }),
  });
}
