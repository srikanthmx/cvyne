"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useExtractJob } from "@/hooks/useJobs";
import { Sparkles, Loader2 } from "lucide-react";

export function JobUrlInput() {
  const [urls, setUrls] = useState("");
  const extractMutation = useExtractJob();

  const handleExtract = () => {
    const list = urls.split("\n").map(u => u.trim()).filter(u => u);
    list.forEach(url => extractMutation.mutate(url));
    setUrls("");
  };

  return (
    <div className="space-y-4">
      <Textarea
        placeholder="Paste job URLs here (one per line)..."
        className="min-h-[120px] font-mono text-sm bg-muted/20"
        value={urls}
        onChange={(e) => setUrls(e.target.value)}
      />
      <div className="flex justify-end">
        <Button 
          onClick={handleExtract} 
          disabled={!urls.trim() || extractMutation.isPending}
          className="w-full sm:w-auto transition-all"
        >
          {extractMutation.isPending ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4 mr-2 text-yellow-400" />
          )}
          Extract & Apply
        </Button>
      </div>
    </div>
  );
}
