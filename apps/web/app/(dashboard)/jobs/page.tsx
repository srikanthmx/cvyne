"use client";
import { JobUrlInput } from "@/components/jobs/JobUrlInput";
import { JobQueue } from "@/components/jobs/JobQueue";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function JobsPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2 bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">Job Queue</h1>
        <p className="text-muted-foreground">Paste URLs to extract job details and initiate applications.</p>
      </div>

      <Card className="border-border shadow-sm bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle>Add New Jobs</CardTitle>
          <CardDescription>Supports LinkedIn, Indeed, Greenhouse, Lever, and standard career pages.</CardDescription>
        </CardHeader>
        <CardContent>
          <JobUrlInput />
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold tracking-tight">Active Queue</h2>
        <JobQueue />
      </div>
    </div>
  );
}
