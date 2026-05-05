"use client";

import { use, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Sparkles,
  Send,
  Loader2,
  Building2,
  MapPin,
  Briefcase,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CVPreview } from "@/components/cv/CVPreview";
import { ResumeDiff } from "@/components/apply/ResumeDiff";
import { LiveActivityFeed } from "@/components/apply/LiveActivityFeed";
import { BrowserViewport } from "@/components/apply/BrowserViewport";
import { useJob, useResumesList, usePreviewApplication, useSubmitApplication } from "@/hooks/useApply";
import { useApplicationActivityStream } from "@/hooks/useApplicationStream";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const THEMES = [
  { value: "ats", label: "ATS Clean", description: "Maximum compatibility" },
  { value: "modern", label: "Modern", description: "Clean & contemporary" },
  { value: "creative", label: "Creative", description: "Stand out" },
  { value: "portfolio", label: "Portfolio", description: "For designers & devs" },
];

export default function ApplyPage({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = use(params);
  const router = useRouter();

  const { data: job, isLoading: jobLoading } = useJob(jobId);
  const { data: resumes, isLoading: resumesLoading } = useResumesList();

  const baseResume = useMemo(
    () => resumes?.find((r: any) => r.is_base) ?? resumes?.[0],
    [resumes],
  );

  const [theme, setTheme] = useState("ats");
  const [generateCoverLetter, setGenerateCoverLetter] = useState(false);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [applicationId, setApplicationId] = useState<string | null>(null);

  useEffect(() => {
    if (baseResume?.id && !resumeId) setResumeId(baseResume.id);
  }, [baseResume, resumeId]);

  const preview = usePreviewApplication();
  const submit = useSubmitApplication();
  const stream = useApplicationActivityStream(applicationId);

  const handlePreview = () => {
    if (!resumeId) return;
    preview.mutate({ job_id: jobId, resume_id: resumeId, theme, generate_cover_letter: generateCoverLetter });
  };

  const handleSubmit = async () => {
    if (!resumeId) return;
    const result = await submit.mutateAsync({
      job_id: jobId,
      resume_id: resumeId,
      theme,
      generate_cover_letter: generateCoverLetter,
    });
    setApplicationId(result.id);
  };

  // Auto-trigger preview once we have the job + resume
  useEffect(() => {
    if (job?.status === "extracted" && resumeId && !preview.data && !preview.isPending) {
      handlePreview();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job?.status, resumeId]);

  const previewUrl = preview.data?.cv_preview_url
    ? `${API_URL}${preview.data.cv_preview_url}`
    : null;

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard/jobs")}>
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to jobs
        </Button>
        {!applicationId && preview.data && (
          <Button variant="outline" size="sm" onClick={handlePreview} disabled={preview.isPending}>
            <RefreshCw className={`w-4 h-4 mr-1.5 ${preview.isPending ? "animate-spin" : ""}`} />
            Regenerate preview
          </Button>
        )}
      </div>

      {/* Job header card */}
      <Card>
        <CardContent className="p-6">
          {jobLoading ? (
            <div className="h-20 animate-pulse bg-muted rounded" />
          ) : !job?.jd ? (
            <div className="flex items-center gap-3 text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-sm">Extracting job description from {new URL(job?.url ?? "https://example.com").hostname}…</span>
            </div>
          ) : (
            <div className="flex items-start justify-between gap-6">
              <div className="space-y-2 min-w-0">
                <div className="flex items-baseline gap-3 flex-wrap">
                  <h1 className="text-2xl font-bold tracking-tight">{job.jd.title}</h1>
                  {job.jd.experience_level && (
                    <Badge variant="secondary" className="text-xs">{job.jd.experience_level}</Badge>
                  )}
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                  <span className="flex items-center gap-1.5"><Building2 className="w-4 h-4" /> {job.jd.company}</span>
                  {job.jd.location && (
                    <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4" /> {job.jd.location}</span>
                  )}
                  {job.jd.employment_type && (
                    <span className="flex items-center gap-1.5"><Briefcase className="w-4 h-4" /> {job.jd.employment_type}</span>
                  )}
                </div>
                {job.jd.skills_required?.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {job.jd.skills_required.slice(0, 12).map((s: string) => (
                      <span key={s} className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Three-column workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Settings + Resume Diff */}
        <div className="lg:col-span-7 space-y-6">
          {/* Settings strip */}
          <Card>
            <CardContent className="p-4 flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Resume</span>
                <Select value={resumeId ?? ""} onValueChange={setResumeId} disabled={resumesLoading}>
                  <SelectTrigger className="w-56 h-9"><SelectValue placeholder="Select a resume" /></SelectTrigger>
                  <SelectContent>
                    {(resumes ?? []).map((r: any) => (
                      <SelectItem key={r.id} value={r.id}>
                        {r.name} {r.is_base && "(base)"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Theme</span>
                <Select value={theme} onValueChange={setTheme}>
                  <SelectTrigger className="w-44 h-9"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {THEMES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={generateCoverLetter}
                  onChange={(e) => setGenerateCoverLetter(e.target.checked)}
                  className="rounded border-border"
                />
                Cover letter
              </label>
            </CardContent>
          </Card>

          {/* Diff */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="w-4 h-4 text-primary" />
                AI-tailored resume
              </CardTitle>
            </CardHeader>
            <CardContent>
              {preview.isPending ? (
                <DiffSkeleton />
              ) : preview.data ? (
                <ResumeDiff base={preview.data.base_resume} tailored={preview.data.tailored_resume} />
              ) : preview.isError ? (
                <div className="text-sm text-destructive">
                  Couldn't generate preview: {preview.error?.message}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">Waiting for the JD to be ready…</div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: CV preview */}
        <div className="lg:col-span-5 space-y-6">
          <div className="lg:sticky lg:top-6">
            <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold mb-2 px-1">
              Live CV preview
            </div>
            <CVPreview url={previewUrl} loading={preview.isPending} className="h-[700px]" />
          </div>
        </div>
      </div>

      {/* Live monitor (only after submit) */}
      {applicationId && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <Card className="lg:col-span-5">
            <CardHeader>
              <CardTitle className="text-base">Application progress</CardTitle>
            </CardHeader>
            <CardContent>
              <LiveActivityFeed events={stream.events} done={stream.done} />
            </CardContent>
          </Card>
          <div className="lg:col-span-7 space-y-2">
            <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold px-1">
              Agent's-eye view
            </div>
            <BrowserViewport
              latest={stream.latestScreenshot}
              history={stream.screenshots}
            />
          </div>
        </div>
      )}

      {/* Sticky submit bar */}
      {!applicationId && (
        <div className="fixed bottom-0 left-0 md:left-64 right-0 z-40 bg-background/90 backdrop-blur-md border-t border-border px-6 py-3 flex items-center justify-between shadow-2xl">
          <div className="text-sm text-muted-foreground">
            {preview.data ? (
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                Ready to apply — review the diff and CV preview
              </span>
            ) : (
              <span>Generating preview…</span>
            )}
          </div>
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={!preview.data || submit.isPending}
            className="shadow-lg"
          >
            {submit.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
            Submit Application
          </Button>
        </div>
      )}
    </div>
  );
}

function DiffSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-3 bg-muted rounded w-3/4" />
      <div className="h-3 bg-muted rounded w-full" />
      <div className="h-3 bg-muted rounded w-5/6" />
      <div className="h-3 bg-muted rounded w-2/3" />
      <div className="h-3 bg-muted rounded w-4/5" />
    </div>
  );
}
