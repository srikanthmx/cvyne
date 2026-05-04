"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { settingsApi } from "@/lib/api";
import { toast } from "sonner";

export function useApiKeys() {
  return useQuery({
    queryKey: ["api-keys"],
    queryFn: async () => {
      const { data, error } = await settingsApi.listApiKeys();
      if (error) throw error;
      return data;
    },
  });
}

export function useSaveApiKey() {
  return useMutation({
    mutationFn: async (body: Parameters<typeof settingsApi.saveApiKey>[0]) => {
      const { data, error } = await settingsApi.saveApiKey(body);
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      toast.success("API key saved securely");
    },
    onError: (error) => {
      toast.error("Failed to save API key: " + error.message);
    }
  });
}
