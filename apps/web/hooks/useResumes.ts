import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { resumesApi } from "@/lib/api";
import { toast } from "sonner";

export function useResumes() {
  return useQuery({
    queryKey: ["resumes"],
    queryFn: async () => {
      const { data, error } = await resumesApi.list();
      if (error) throw error;
      return data;
    },
  });
}

export function useParseResume() {
  return useMutation({
    mutationFn: async (file: File) => {
      const { data, error } = await resumesApi.parseUpload(file);
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      toast.success("Resume parsed successfully");
    },
    onError: (error) => {
      toast.error("Failed to parse resume: " + error.message);
    },
  });
}

export function useCreateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Parameters<typeof resumesApi.create>[0]) => {
      const { data, error } = await resumesApi.create(body);
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      toast.success("Resume saved successfully");
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
    onError: (error) => {
      toast.error("Failed to save resume: " + error.message);
    },
  });
}
