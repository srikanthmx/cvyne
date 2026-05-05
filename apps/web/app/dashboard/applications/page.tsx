"use client";
import { useApplicationsList } from "@/hooks/useApplicationsList";
import { LiveApplicationMonitor } from "@/components/applications/LiveApplicationMonitor";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  CheckCircle2, AlertCircle, AlertTriangle,
  Download, RefreshCw, Send, Loader2, Square,
} from "lucide-react";
import { useState } from "react";
import { useCancelApplication, useRetryApplication } from "@/hooks/useApplicationStream";

export default function ApplicationsPage() {
  const { data: applications, isLoading } = useApplicationsList();
  const [filter, setFilter] = useState<string>("all");
  const [activeMonitor, setActiveMonitor] = useState<string | null>(null);
  const cancelMutation = useCancelApplication();
  const retryMutation = useRetryApplication();

  const filteredApps = applications?.filter(
    (app) => filter === "all" || app.status === filter,
  ) ?? [];

  // Auto-open monitor for the most recent in-progress application
  const inProgress = applications?.find((a) =>
    ["queued", "processing", "generating_cv", "filling_form"].includes(a.status),
  );

  const monitorId = activeMonitor ?? inProgress?.id ?? null;
  const monitorApp = applications?.find((a) => a.id === monitorId);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Applications</h1>
        <p className="text-muted-foreground">Track and manage your automated job applications.</p>
      </div>

      {/* Live monitor — shown when an application is active or selected */}
      {monitorId && (
        <LiveApplicationMonitor
          applicationId={monitorId}
          jobUrl={monitorApp?.job_url}
          onClose={() => setActiveMonitor(null)}
        />
      )}

      {/* Filter tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {["all", "processing", "submitted", "failed", "requires_human", "cancelled"].map((s) => (
          <Button
            key={s}
            variant={filter === s ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(s)}
            className="capitalize rounded-full shrink-0"
          >
            {s.replace("_", " ")}
          </Button>
        ))}
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b border-border">
                <tr>
                  <th className="px-6 py-4 font-medium">Date</th>
                  <th className="px-6 py-4 font-medium">Company</th>
                  <th className="px-6 py-4 font-medium">Role</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {isLoading
                  ? Array.from({ length: 3 }).map((_, i) => (
                      <tr key={i}>
                        {Array.from({ length: 5 }).map((_, j) => (
                          <td key={j} className="px-6 py-4">
                            <Skeleton className="h-4 w-24" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : filteredApps.length === 0
                  ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                        <div className="flex flex-col items-center justify-center">
                          <Send className="w-10 h-10 mb-4 opacity-20" />
                          <p>No applications found.</p>
                        </div>
                      </td>
                    </tr>
                  )
                  : filteredApps.map((app) => {
                      const isActive = ["queued", "processing", "generating_cv", "filling_form"].includes(app.status);
                      return (
                        <tr
                          key={app.id}
                          className={`hover:bg-muted/30 transition-colors cursor-pointer ${activeMonitor === app.id ? "bg-primary/5" : ""}`}
                          onClick={() => setActiveMonitor(app.id === activeMonitor ? null : app.id)}
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-muted-foreground">
                            {new Date(app.date).toLocaleDateString(undefined, {
                              month: "short", day: "numeric", year: "numeric",
                            })}
                          </td>
                          <td className="px-6 py-4 font-medium">{app.company}</td>
                          <td className="px-6 py-4 text-muted-foreground">{app.role}</td>
                          <td className="px-6 py-4">
                            <StatusBadge status={app.status} />
                          </td>
                          <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-end gap-2">
                              {app.cv_url && (
                                <Button size="sm" variant="ghost" className="h-8 px-2 text-muted-foreground">
                                  <Download className="w-4 h-4 mr-1" /> CV
                                </Button>
                              )}
                              {isActive && (
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  className="h-8 gap-1.5"
                                  onClick={() => cancelMutation.mutate(app.id)}
                                  disabled={cancelMutation.isPending}
                                >
                                  <Square className="w-3 h-3" /> Stop
                                </Button>
                              )}
                              {(app.status === "failed" || app.status === "cancelled") && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-8 gap-1.5"
                                  onClick={() => retryMutation.mutate(app.id)}
                                  disabled={retryMutation.isPending}
                                >
                                  <RefreshCw className={`w-3 h-3 ${retryMutation.isPending ? "animate-spin" : ""}`} />
                                  Retry
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { icon: React.ReactNode; label: string; className: string }> = {
    queued:         { icon: <Loader2 className="w-3 h-3" />,              label: "Queued",       className: "bg-muted text-muted-foreground" },
    processing:     { icon: <Loader2 className="w-3 h-3 animate-spin" />, label: "Running",      className: "bg-blue-500/10 text-blue-500" },
    generating_cv:  { icon: <Loader2 className="w-3 h-3 animate-spin" />, label: "Generating",   className: "bg-blue-500/10 text-blue-500" },
    filling_form:   { icon: <Loader2 className="w-3 h-3 animate-spin" />, label: "Filling form", className: "bg-blue-500/10 text-blue-500" },
    submitted:      { icon: <CheckCircle2 className="w-3 h-3" />,         label: "Submitted",    className: "bg-green-500/10 text-green-600" },
    failed:         { icon: <AlertCircle className="w-3 h-3" />,          label: "Failed",       className: "bg-red-500/10 text-red-500" },
    requires_human: { icon: <AlertTriangle className="w-3 h-3" />,        label: "Needs you",    className: "bg-yellow-500/10 text-yellow-600" },
    cancelled:      { icon: <Square className="w-3 h-3" />,               label: "Cancelled",    className: "bg-muted text-muted-foreground" },
  };
  const { icon, label, className } = map[status] ?? map.queued;
  return (
    <Badge variant="secondary" className={`border-0 gap-1 ${className}`}>
      {icon} {label}
    </Badge>
  );
}
