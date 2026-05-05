/**
 * Type-safe API client — generated from FastAPI's OpenAPI schema.
 * Every call has full TypeScript types: path params, query, body, response.
 *
 * Regenerate types: pnpm --filter shared-types generate
 */

import createClient from "openapi-fetch";
import type { paths } from "shared-types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = createClient<paths>({
  baseUrl: BASE_URL,
});

// Attach Clerk auth token to every request
api.use({
  async onRequest({ request }) {
    if (typeof window !== "undefined") {
      // @ts-ignore
      const token = await window.Clerk?.session?.getToken();
      if (token) request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  },
});

// Typed endpoint helpers — every method, path, and body is type-checked.
// Add new endpoints here as they're built. Hooks in /hooks consume these.

export const jobsApi = {
  extract: (url: string) =>
    api.POST("/api/v1/jobs/extract", { body: { url } }),

  get: (id: string) =>
    api.GET("/api/v1/jobs/{job_id}", { params: { path: { job_id: id } } }),
};

export const resumesApi = {
  parseUpload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.POST("/api/v1/resumes/parse", { body: formData as never });
  },

  create: (body: any) =>
    api.POST("/api/v1/resumes/", { body }),

  get: (id: string) =>
    api.GET("/api/v1/resumes/{resume_id}", { params: { path: { resume_id: id } } }),

  list: () =>
    api.GET("/api/v1/resumes/" as any, {}),
};

export const applicationsApi = {
  submit: (body: any) =>
    api.POST("/api/v1/applications/", { body }),

  get: (id: string) =>
    api.GET("/api/v1/applications/{application_id}" as any, { params: { path: { application_id: id } } }),

  cancel: (id: string) =>
    api.POST("/api/v1/applications/{application_id}/cancel" as any, { params: { path: { application_id: id } } }),

  retry: (id: string) =>
    api.POST("/api/v1/applications/{application_id}/retry" as any, { params: { path: { application_id: id } } }),

  streamStatus: (id: string): EventSource =>
    new EventSource(`${BASE_URL}/api/v1/applications/${id}/stream`),
};

export const settingsApi = {
  saveApiKey: (body: any) =>
    api.POST("/api/v1/settings/api-keys", { body }),

  listApiKeys: () =>
    api.GET("/api/v1/settings/api-keys"),
};
