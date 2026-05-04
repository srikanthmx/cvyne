"use client";
import { useApplicationStream } from "@/hooks/useApplicationStream";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, AlertTriangle, Loader2, FileText, Download } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  "Extracting JD",
  "Personalizing resume",
  "Generating CV",
  "Filling form",
  "Submitted"
];

export function ApplicationStatus({ applicationId }: { applicationId: string }) {
  const { event, done } = useApplicationStream(applicationId);

  // Fallback defaults if no event yet
  const status = event?.status || "queued";
  const progress = event?.progress || 0;
  const currentStep = event?.step || "";
  
  // Calculate active index based on progress roughly, or step name
  let activeIndex = 0;
  if (progress > 0) activeIndex = 1;
  if (progress > 30) activeIndex = 2;
  if (progress > 60) activeIndex = 3;
  if (status === "submitted" || done) activeIndex = 4;

  return (
    <Card className="w-full max-w-xl mx-auto overflow-hidden">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-8">
          <h3 className="font-semibold text-lg">Application Status</h3>
          <div className="flex items-center gap-2">
            {status === "processing" && <Loader2 className="w-4 h-4 animate-spin text-primary" />}
            {status === "submitted" && <CheckCircle2 className="w-5 h-5 text-green-500" />}
            {status === "failed" && <AlertCircle className="w-5 h-5 text-destructive" />}
            {status === "requires_human" && <AlertTriangle className="w-5 h-5 text-yellow-500" />}
            <span className="text-sm font-medium capitalize text-muted-foreground">
              {status.replace("_", " ")}
            </span>
          </div>
        </div>

        <div className="relative mb-8">
          <Progress value={progress} className="h-2 w-full absolute top-1/2 -mt-1 z-0" />
          <div className="flex justify-between relative z-10 px-2">
            {STEPS.map((step, idx) => {
              const isCompleted = idx < activeIndex || status === "submitted";
              const isActive = idx === activeIndex && status !== "submitted" && status !== "failed";
              
              return (
                <div key={step} className="flex flex-col items-center gap-2">
                  <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center border-2 transition-colors",
                    isCompleted ? "bg-primary border-primary text-primary-foreground" :
                    isActive ? "bg-background border-primary text-primary" :
                    "bg-background border-muted text-muted-foreground"
                  )}>
                    {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : <span className="text-xs">{idx + 1}</span>}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-between relative z-10 px-1 mt-3">
             {STEPS.map((step, idx) => {
               const isActive = idx === activeIndex;
               return (
                 <div key={`label-${step}`} className="w-16 text-center">
                   <span className={cn("text-[10px] leading-tight font-medium hidden sm:inline-block", isActive ? "text-foreground" : "text-muted-foreground")}>
                     {step}
                   </span>
                 </div>
               )
             })}
          </div>
        </div>

        {status === "requires_human" && (
          <div className="bg-yellow-500/10 text-yellow-600 border border-yellow-500/20 rounded-lg p-4 flex items-start gap-3 mb-4">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-sm">CAPTCHA detected</p>
              <p className="text-xs opacity-90 mt-1">Please open the browser to finish manually.</p>
              <Button size="sm" variant="outline" className="mt-3 border-yellow-500/30 text-yellow-700 hover:bg-yellow-500/20">
                Open Browser
              </Button>
            </div>
          </div>
        )}

        {status === "failed" && (
          <div className="bg-destructive/10 text-destructive border border-destructive/20 rounded-lg p-4 flex items-start gap-3 mb-4">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-sm">Application Failed</p>
              <p className="text-xs opacity-90 mt-1">{event?.message || "An unexpected error occurred."}</p>
              <Button size="sm" variant="outline" className="mt-3 border-destructive/30 text-destructive hover:bg-destructive/20">
                Retry Application
              </Button>
            </div>
          </div>
        )}

        {status === "submitted" && (
          <div className="bg-green-500/10 text-green-700 border border-green-500/20 rounded-lg p-4 flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <p className="font-medium text-sm">Successfully Submitted</p>
            </div>
            <Button size="sm" variant="outline" className="border-green-500/30 text-green-700 hover:bg-green-500/20">
              <Download className="w-4 h-4 mr-2" /> Download CV
            </Button>
          </div>
        )}

      </CardContent>
    </Card>
  );
}
