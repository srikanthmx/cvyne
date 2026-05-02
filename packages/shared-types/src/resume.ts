/** Mirrors apps/api/models/resume.py — keep in sync. Antigravity owns this file. */

export interface ExperienceEntry {
  company: string;
  role: string;
  start: string; // ISO date
  end: string | null;
  location?: string;
  bullets: string[];
}

export interface EducationEntry {
  institution: string;
  degree: string;
  field?: string;
  year: number;
}

export interface ProjectEntry {
  name: string;
  description: string;
  url?: string;
  tech: string[];
  bullets: string[];
}

export interface CertificationEntry {
  name: string;
  issuer: string;
  date?: string;
  url?: string;
}

export interface ResumeSchema {
  name: string;
  email: string;
  phone?: string;
  location?: string;
  summary?: string;
  linkedin?: string;
  github?: string;
  portfolio?: string;
  skills: string[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];
  certifications: CertificationEntry[];
}

export interface TailoredResumeSchema extends ResumeSchema {
  tailored_for_job_id?: string;
  ats_score?: number;
  keyword_coverage?: number;
  changes_summary: string[];
}

export interface ResumeResponse {
  id: string;
  name: string;
  data: ResumeSchema;
  is_base: boolean;
}
