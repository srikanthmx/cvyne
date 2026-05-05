import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="h-[60vh] flex flex-col items-center justify-center text-muted-foreground space-y-4">
      <div className="relative">
        <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
        <Loader2 className="w-10 h-10 animate-spin text-primary relative z-10" />
      </div>
      <p className="text-sm font-medium animate-pulse">Loading content...</p>
    </div>
  );
}
