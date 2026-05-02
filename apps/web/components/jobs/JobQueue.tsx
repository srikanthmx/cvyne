"use client";

// TODO (Antigravity): implement job queue list with status badges and real-time updates

export function JobQueue() {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
        Job Queue
      </h2>
      <div className="rounded-lg border border-border p-8 text-center text-muted-foreground text-sm">
        No jobs yet. Paste a URL above to get started.
      </div>
    </div>
  );
}

JobQueue.Skeleton = function JobQueueSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />
      ))}
    </div>
  );
};
