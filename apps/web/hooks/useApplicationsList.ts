import { useQuery } from "@tanstack/react-query";

export type ApplicationItem = {
  id: string;
  company: string;
  role: string;
  status: "queued" | "processing" | "submitted" | "failed" | "requires_human";
  date: string;
  cv_url?: string;
};

export function useApplicationsList() {
  return useQuery({
    queryKey: ["applications"],
    queryFn: async (): Promise<ApplicationItem[]> => {
      // Placeholder until GET /api/v1/applications/ is fully exposed
      return [
        {
          id: "mock-1",
          company: "Vercel",
          role: "Frontend Engineer",
          status: "submitted",
          date: new Date(Date.now() - 86400000).toISOString(),
          cv_url: "#",
        },
        {
          id: "mock-2",
          company: "Stripe",
          role: "Product Engineer",
          status: "failed",
          date: new Date(Date.now() - 172800000).toISOString(),
        },
      ];
    },
  });
}
