"use client";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="h-[60vh] flex flex-col items-center justify-center space-y-6 text-center max-w-md mx-auto px-4">
      <div className="w-16 h-16 bg-destructive/10 text-destructive rounded-full flex items-center justify-center">
        <AlertCircle className="w-8 h-8" />
      </div>
      <div>
        <h2 className="text-2xl font-bold tracking-tight mb-2">Something went wrong!</h2>
        <p className="text-muted-foreground text-sm">
          {error.message || "An unexpected error occurred while loading this page."}
        </p>
      </div>
      <Button onClick={() => reset()} variant="default" size="lg">
        Try again
      </Button>
    </div>
  );
}
