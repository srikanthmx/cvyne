import { useQuery } from "@tanstack/react-query";

export type ApplicationItem = {
  id: string;
  company: string;
  role: string;
  status: "queued" | "processing" | "generating_cv" | "filling_form" | "submitted" | "failed" | "requires_human" | "cancelled";
  date: string;
  cv_url?: string;
  job_url?: string;
};

export function useApplicationsList() {
  return useQuery({
    queryKey: ["applications"],
    queryFn: async (): Promise<ApplicationItem[]> => {
      // Placeholder until GET /api/v1/applications/ is fully exposed
      return [];
    },
  });
}
