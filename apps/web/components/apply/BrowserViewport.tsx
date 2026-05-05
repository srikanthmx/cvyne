"use client";

import { useEffect, useRef } from "react";
import { Globe, Eye, Lock } from "lucide-react";
import type { Screenshot } from "@/hooks/useApplicationStream";

interface BrowserViewportProps {
  latest: Screenshot | null;
  history: Screenshot[];
  className?: string;
}

/**
 * "Agent's-eye view" — renders the most recent browser screenshot from
 * browser-use's per-step callback, plus a thumbnail strip of prior frames.
 *
 * Styled like a Chrome window so it reads as "live browser session" not
 * "random screenshot dump".
 */
export function BrowserViewport({ latest, history, className }: BrowserViewportProps) {
  const stripRef = useRef<HTMLDivElement>(null);

  // Auto-scroll thumbnail strip to the right (newest)
  useEffect(() => {
    stripRef.current?.scrollTo({ left: stripRef.current.scrollWidth, behavior: "smooth" });
  }, [history.length]);

  if (!latest) {
    return (
      <div className={`bg-muted/20 border border-dashed border-border rounded-xl p-12 text-center ${className ?? ""}`}>
        <Eye className="w-12 h-12 mx-auto text-muted-foreground/40" />
        <p className="mt-3 text-sm text-muted-foreground">
          Browser activity will appear here once the agent starts filling the form.
        </p>
      </div>
    );
  }

  const dataUrl = latest.screenshot_b64.startsWith("data:")
    ? latest.screenshot_b64
    : `data:image/png;base64,${latest.screenshot_b64}`;

  return (
    <div className={`bg-card border border-border rounded-xl overflow-hidden shadow-md ${className ?? ""}`}>
      {/* Chrome chrome */}
      <div className="bg-muted/60 border-b border-border px-3 py-2 flex items-center gap-2">
        <div className="flex gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400/80" />
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/80" />
        </div>
        <div className="flex-1 mx-2 px-3 py-1 bg-background rounded-md flex items-center gap-2 text-xs text-muted-foreground border border-border min-w-0">
          <Lock className="w-3 h-3 shrink-0" />
          <span className="truncate">{latest.url ?? "about:blank"}</span>
        </div>
        <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          LIVE
        </span>
      </div>

      {/* Screenshot frame */}
      <div className="relative bg-black">
        <img
          src={dataUrl}
          alt={`Step ${latest.step}: ${latest.title ?? "browser frame"}`}
          className="w-full h-auto block"
        />
        <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-white text-[10px] font-mono backdrop-blur-sm">
          step {latest.step}
        </div>
      </div>

      {/* Thumbnail strip */}
      {history.length > 1 && (
        <div ref={stripRef} className="flex gap-1.5 p-2 overflow-x-auto bg-muted/20 border-t border-border scrollbar-thin">
          {history.slice(-12).map((s, i) => {
            const url = s.screenshot_b64.startsWith("data:")
              ? s.screenshot_b64
              : `data:image/png;base64,${s.screenshot_b64}`;
            return (
              <img
                key={`${s.step}-${i}`}
                src={url}
                alt={`Step ${s.step}`}
                className={`h-12 w-auto rounded border ${
                  s.step === latest.step ? "border-primary ring-1 ring-primary/50" : "border-border opacity-60"
                }`}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
