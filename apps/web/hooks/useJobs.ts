"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api";
import { toast } from "sonner";

export interface OptimisticJob {
  id: string;
  url: string;
  status: "pending" | "extracting" | "extracted" | "failed";
  company?: string;
  title?: string;
  created_at: string;
}

export function useJobsList() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: async (): Promise<OptimisticJob[]> => {
      // Placeholder until Kiro builds GET /api/v1/jobs/
      return [];
    },
  });
}

export function useExtractJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (url: string) => {
      const { data, error } = await jobsApi.extract(url);
      if (error) throw error;
      return { ...data, url }; // assuming data contains id
    },
    onMutate: async (url) => {
      await qc.cancelQueries({ queryKey: ["jobs"] });
      const previousJobs = qc.getQueryData<OptimisticJob[]>(["jobs"]) || [];
      const newJob: OptimisticJob = {
        id: `optimistic-${Date.now()}`,
        url,
        status: "pending",
        created_at: new Date().toISOString(),
      };
      qc.setQueryData<OptimisticJob[]>(["jobs"], [newJob, ...previousJobs]);
      return { previousJobs, newJob };
    },
    onSuccess: (data, variables, context) => {
      toast.success("Job extraction started");
      qc.setQueryData<OptimisticJob[]>(["jobs"], (old) => 
        old?.map(j => j.id === context?.newJob.id ? { ...j, id: data.id, status: "pending" } : j) || []
      );
    },
    onError: (error, variables, context) => {
      toast.error("Failed to extract job: " + error.message);
      if (context?.previousJobs) {
        qc.setQueryData(["jobs"], context.previousJobs);
      }
    }
  });
}

export function useJobStatus(jobId: string | null, enabled: boolean = true) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ["jobs", jobId],
    queryFn: async () => {
      if (!jobId) return null;
      const { data, error } = await jobsApi.get(jobId);
      if (error) throw error;
      
      // Update the jobs list cache with the new status
      qc.setQueryData<OptimisticJob[]>(["jobs"], (old) => 
        old?.map(j => j.id === jobId ? { ...j, ...data } : j) || []
      );
      
      return data;
    },
    enabled: !!jobId && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || status === "extracted" || status === "failed") return false;
      // Stop after 60 polls (~2 min) to prevent runaway polling
      if ((query.state.dataUpdateCount ?? 0) > 60) return false;
      return 2000;
    },
  });
}
