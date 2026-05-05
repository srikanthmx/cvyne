"use client";
import Link from "next/link";
import { useJobsList, useJobStatus, type OptimisticJob } from "@/hooks/useJobs";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, Play, AlertCircle, CheckCircle2 } from "lucide-react";

function getDomain(url: string) {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

function JobRow({ job }: { job: OptimisticJob }) {
  // Poll if pending
  useJobStatus(job.id, job.status === "pending");

  const domain = getDomain(job.url);
  const faviconUrl = domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : "";

  return (
    <Card className="hover:shadow-sm transition-all group overflow-hidden border-muted-foreground/20">
      <CardContent className="p-4 flex items-center gap-4">
        <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center shrink-0 overflow-hidden border border-border">
          {faviconUrl ? (
            <img src={faviconUrl} alt="Company logo" className="w-6 h-6 object-contain" />
          ) : (
            <div className="w-6 h-6 bg-primary/20 rounded-full" />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-semibold text-base truncate">
              {job.title || "Extracting Role..."}
            </h4>
            {job.status === "pending" && (
              <Badge variant="secondary" className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" /> Extracting
              </Badge>
            )}
            {job.status === "extracted" && (
              <Badge variant="secondary" className="bg-green-500/10 text-green-500 hover:bg-green-500/20">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Ready
              </Badge>
            )}
            {job.status === "failed" && (
              <Badge variant="destructive" className="bg-red-500/10 text-red-500 hover:bg-red-500/20">
                <AlertCircle className="w-3 h-3 mr-1" /> Failed
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground truncate">
            {job.company || domain || job.url}
          </p>
        </div>

        <div className="shrink-0 flex items-center gap-2">
          {job.status === "extracted" && (
            <Link href={`/dashboard/apply/${job.id}`}>
              <Button size="sm" className="shadow-sm">
                <Play className="w-4 h-4 mr-1.5" /> Generate CV & Apply
              </Button>
            </Link>
          )}
          {job.status === "failed" && (
            <Button size="sm" variant="outline" className="text-destructive border-destructive/30 hover:bg-destructive/10">
              Retry
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function JobQueue() {
  const { data: jobs, isLoading } = useJobsList();

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse bg-muted/40">
            <CardContent className="p-4 h-20" />
          </Card>
        ))}
      </div>
    );
  }

  if (!jobs?.length) {
    return (
      <div className="text-center py-12 px-4 border border-dashed rounded-xl border-border bg-muted/10">
        <p className="text-muted-foreground">No jobs in your queue yet. Paste a URL above to start.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {jobs.map((job) => (
        <JobRow key={job.id} job={job} />
      ))}
    </div>
  );
}
