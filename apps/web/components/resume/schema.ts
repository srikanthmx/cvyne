import { z } from "zod";

export const resumeSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Invalid email"),
  phone: z.string().optional().nullable(),
  location: z.string().optional().nullable(),
  summary: z.string().optional().nullable(),
  linkedin: z.string().optional().nullable(),
  github: z.string().optional().nullable(),
  portfolio: z.string().optional().nullable(),
  skills: z.array(z.string()).optional(),
  experience: z.array(
    z.object({
      company: z.string().min(1, "Company is required"),
      role: z.string().min(1, "Role is required"),
      start: z.string().min(1, "Start date is required"),
      end: z.string().optional().nullable(),
      bullets: z.array(z.string()).optional(),
    })
  ).optional(),
  education: z.array(
    z.object({
      institution: z.string().min(1, "Institution is required"),
      degree: z.string().min(1, "Degree is required"),
      year: z.number().optional().nullable(),
    })
  ).optional(),
  projects: z.array(
    z.object({
      name: z.string().min(1, "Project name is required"),
      description: z.string().min(1, "Description is required"),
      url: z.string().optional().nullable(),
      tech: z.array(z.string()).optional(),
    })
  ).optional(),
  certifications: z.array(
    z.object({
      name: z.string().min(1, "Certification name is required"),
      issuer: z.string().min(1, "Issuer is required"),
      date: z.string().min(1, "Date is required"),
    })
  ).optional(),
});

export type ResumeFormData = z.infer<typeof resumeSchema>;
