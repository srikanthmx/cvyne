"use client";

import { useEffect, useState } from "react";
import { Loader2, FileText, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CVPreviewProps {
  url: string | null;
  filename?: string;
  loading?: boolean;
  className?: string;
}

/**
 * Inline PDF preview. Uses an <iframe> for native browser rendering — no PDF.js
 * dependency needed for v1. Modern browsers handle PDFs out of the box.
 */
export function CVPreview({ url, filename = "cv.pdf", loading, className }: CVPreviewProps) {
  const [pdfReady, setPdfReady] = useState(false);

  useEffect(() => {
    setPdfReady(false);
  }, [url]);

  if (loading || !url) {
    return (
      <div className={`flex flex-col items-center justify-center bg-muted/20 border border-dashed border-border rounded-xl p-12 text-center ${className ?? "min-h-[600px]"}`}>
        {loading ? (
          <>
            <div className="relative">
              <FileText className="w-16 h-16 text-muted-foreground/30" />
              <Loader2 className="w-6 h-6 text-primary animate-spin absolute -bottom-1 -right-1" />
            </div>
            <p className="mt-4 font-medium text-sm">Generating your tailored CV…</p>
            <p className="text-xs text-muted-foreground mt-1">This usually takes 8–15 seconds</p>
          </>
        ) : (
          <>
            <FileText className="w-16 h-16 text-muted-foreground/30" />
            <p className="mt-4 text-sm text-muted-foreground">CV preview will appear here</p>
          </>
        )}
      </div>
    );
  }

  return (
    <div className={`relative bg-card border border-border rounded-xl overflow-hidden shadow-sm ${className ?? "h-[700px]"}`}>
      {!pdfReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/40 z-10">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
        </div>
      )}
      <iframe
        src={`${url}#toolbar=0&navpanes=0&view=FitH`}
        className="w-full h-full"
        title="CV preview"
        onLoad={() => setPdfReady(true)}
      />
      <a
        href={url}
        download={filename}
        className="absolute top-3 right-3 z-20"
      >
        <Button size="sm" variant="secondary" className="shadow-md backdrop-blur-md bg-background/80">
          <Download className="w-4 h-4 mr-1.5" /> Download
        </Button>
      </a>
    </div>
  );
}
