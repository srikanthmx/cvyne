"use client";
import { useApplicationsList } from "@/hooks/useApplicationsList";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle2, AlertCircle, AlertTriangle, Download, RefreshCw, Send, Loader2 } from "lucide-react";
import { useState } from "react";

export default function ApplicationsPage() {
  const { data: applications, isLoading } = useApplicationsList();
  const [filter, setFilter] = useState<string>("all");

  const filteredApps = applications?.filter(app => filter === "all" || app.status === filter) || [];

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Application History</h1>
        <p className="text-muted-foreground">Track and manage your automated job applications.</p>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {["all", "submitted", "processing", "failed", "requires_human"].map((status) => (
          <Button 
            key={status}
            variant={filter === status ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(status)}
            className="capitalize rounded-full"
          >
            {status.replace("_", " ")}
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
                {isLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i}>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-24" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-32" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-40" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-6 w-20 rounded-full" /></td>
                      <td className="px-6 py-4 flex justify-end"><Skeleton className="h-8 w-24" /></td>
                    </tr>
                  ))
                ) : filteredApps.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center justify-center">
                        <Send className="w-10 h-10 mb-4 opacity-20" />
                        <p>No applications found.</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredApps.map((app) => (
                    <tr key={app.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-muted-foreground">
                        {new Date(app.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="px-6 py-4 font-medium text-foreground">{app.company}</td>
                      <td className="px-6 py-4 text-muted-foreground">{app.role}</td>
                      <td className="px-6 py-4">
                        {app.status === "submitted" && <Badge variant="secondary" className="bg-green-500/10 text-green-500 border-0"><CheckCircle2 className="w-3 h-3 mr-1" /> Submitted</Badge>}
                        {app.status === "failed" && <Badge variant="secondary" className="bg-red-500/10 text-red-500 border-0"><AlertCircle className="w-3 h-3 mr-1" /> Failed</Badge>}
                        {app.status === "processing" && <Badge variant="secondary" className="bg-blue-500/10 text-blue-500 border-0"><Loader2 className="w-3 h-3 mr-1 animate-spin" /> Processing</Badge>}
                        {app.status === "requires_human" && <Badge variant="secondary" className="bg-yellow-500/10 text-yellow-600 border-0"><AlertTriangle className="w-3 h-3 mr-1" /> CAPTCHA</Badge>}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {app.cv_url && (
                            <Button size="sm" variant="ghost" className="h-8 px-2 text-muted-foreground hover:text-foreground">
                              <Download className="w-4 h-4 mr-2" /> CV
                            </Button>
                          )}
                          {app.status === "failed" && (
                            <Button size="sm" variant="outline" className="h-8">
                              <RefreshCw className="w-3 h-3 mr-2" /> Retry
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
