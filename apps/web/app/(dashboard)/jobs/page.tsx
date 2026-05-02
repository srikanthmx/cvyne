import { Suspense } from "react";
import { JobUrlInput } from "@/components/jobs/JobUrlInput";
import { JobQueue } from "@/components/jobs/JobQueue";

export const metadata = { title: "Jobs — AutoApply AI" };

export default function JobsPage() {
  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Job Applications</h1>
        <p className="text-muted-foreground mt-1">
          Paste job URLs to extract, personalize, and auto-apply.
        </p>
      </div>

      <JobUrlInput />

      <Suspense fallback={<JobQueue.Skeleton />}>
        <JobQueue />
      </Suspense>
    </div>
  );
}
