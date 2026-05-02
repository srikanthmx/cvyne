/** Mirrors apps/api/models/job.py — keep in sync. */

export type JobStatus = "pending" | "extracting" | "extracted" | "failed";

export type ApplicationStatus =
  | "queued"
  | "processing"
  | "generating_cv"
  | "filling_form"
  | "submitted"
  | "failed"
  | "requires_human";

export type CVTheme = "ats" | "modern" | "creative" | "portfolio";

export interface JDSchema {
  title: string;
  company: string;
  location?: string;
  remote?: boolean;
  employment_type?: string;
  experience_level?: string;
  skills_required: string[];
  skills_preferred: string[];
  description: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  apply_url?: string;
}

export interface JobResponse {
  id: string;
  url: string;
  status: JobStatus;
  jd?: JDSchema;
}

export interface ApplicationStatusEvent {
  application_id: string;
  status: ApplicationStatus;
  step: string;
  progress: number;
  message?: string;
  error_code?: string;
}

export interface ApplicationResponse {
  id: string;
  job_id: string;
  resume_id: string;
  status: ApplicationStatus;
  cv_url?: string;
  error?: string;
  attempts: number;
}
