/**
 * Type-safe API client — all backend calls go through here.
 * Never use raw fetch in components.
 */

import ky from "ky";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = ky.create({
  prefixUrl: `${BASE_URL}/api/v1`,
  hooks: {
    beforeRequest: [
      async (request) => {
        // Attach Clerk session token for authenticated requests
        if (typeof window !== "undefined") {
          const { getToken } = await import("@clerk/nextjs/client");
          const token = await getToken();
          if (token) request.headers.set("Authorization", `Bearer ${token}`);
        }
      },
    ],
  },
  retry: { limit: 2, methods: ["get"] },
});

// Typed endpoint helpers — import these in hooks, not the raw api instance
export const jobsApi = {
  extract: (url: string) =>
    api.post("jobs/extract", { json: { url } }).json(),

  get: (id: string) =>
    api.get(`jobs/${id}`).json(),
};

export const resumesApi = {
  create: (data: unknown) =>
    api.post("resumes", { json: data }).json(),

  get: (id: string) =>
    api.get(`resumes/${id}`).json(),

  personalize: (id: string, jd: unknown) =>
    api.post(`resumes/${id}/personalize`, { json: jd }).json(),
};

export const applicationsApi = {
  submit: (data: unknown) =>
    api.post("applications", { json: data }).json(),

  get: (id: string) =>
    api.get(`applications/${id}`).json(),

  streamStatus: (id: string): EventSource =>
    new EventSource(`${BASE_URL}/api/v1/applications/${id}/stream`),
};

export const settingsApi = {
  saveApiKey: (data: unknown) =>
    api.post("settings/api-keys", { json: data }).json(),

  listApiKeys: () =>
    api.get("settings/api-keys").json(),
};
