"use client";

import { useMemo } from "react";
import { Sparkles, ArrowRight } from "lucide-react";
import type { ResumeSchema, TailoredResumeSchema, ExperienceEntry } from "shared-types";

interface ResumeDiffProps {
  base: ResumeSchema;
  tailored: TailoredResumeSchema;
}

/**
 * Side-by-side diff of base vs tailored resume.
 * Highlights:
 *  - Reordered bullets get a subtle "moved" badge
 *  - Reworded bullets render the new text with a "tweaked" indicator
 *  - New skills (keyword injections from JD) are highlighted in green
 *  - Removed/dropped skills are crossed out
 *
 * This isn't a perfect semantic diff — it's a visual cue layer that makes the
 * AI's work *legible* to a human in 2 seconds.
 */
export function ResumeDiff({ base, tailored }: ResumeDiffProps) {
  const skillChanges = useMemo(
    () => diffStringList(base.skills, tailored.skills),
    [base.skills, tailored.skills],
  );

  return (
    <div className="space-y-6">
      {tailored.changes_summary && tailored.changes_summary.length > 0 && (
        <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2 text-primary">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm font-medium">AI Edits Summary</span>
          </div>
          <ul className="text-sm text-foreground/80 space-y-1 ml-6 list-disc">
            {tailored.changes_summary.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Skills */}
      <DiffSection title="Skills">
        <div className="flex flex-wrap gap-1.5">
          {tailored.skills.map((s) => {
            const isNew = skillChanges.added.includes(s);
            return (
              <span
                key={s}
                className={`text-xs px-2 py-1 rounded-md border ${
                  isNew
                    ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300"
                    : "bg-muted border-border text-foreground/70"
                }`}
              >
                {isNew && <Sparkles className="w-3 h-3 inline mr-1" />}
                {s}
              </span>
            );
          })}
          {skillChanges.removed.map((s) => (
            <span
              key={`r-${s}`}
              className="text-xs px-2 py-1 rounded-md border border-border text-muted-foreground line-through"
              title="Removed in tailored version"
            >
              {s}
            </span>
          ))}
        </div>
      </DiffSection>

      {/* Experience — bullet diff */}
      <DiffSection title="Experience">
        <div className="space-y-4">
          {tailored.experience.map((tExp, i) => {
            const bExp = base.experience[i];
            return (
              <div key={`${tExp.company}-${i}`} className="border-l-2 border-primary/30 pl-4">
                <div className="text-sm font-medium">{tExp.role}</div>
                <div className="text-xs text-muted-foreground mb-2">
                  {tExp.company} · {tExp.start} – {tExp.end ?? "Present"}
                </div>
                <ul className="space-y-1.5">
                  {tExp.bullets.map((b, j) => (
                    <BulletDiff
                      key={j}
                      base={bExp?.bullets?.[j]}
                      tailored={b}
                    />
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </DiffSection>
    </div>
  );
}

function DiffSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs uppercase tracking-wider text-muted-foreground font-semibold mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

function BulletDiff({ base, tailored }: { base?: string; tailored: string }) {
  const isNew = !base;
  const isChanged = base !== undefined && base !== tailored;
  const isUnchanged = base === tailored;

  return (
    <li className="text-sm leading-snug">
      {isNew && (
        <span className="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 mr-2 align-middle">
          NEW
        </span>
      )}
      {isChanged && !isNew && (
        <span className="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 mr-2 align-middle">
          TWEAKED
        </span>
      )}
      {isUnchanged && (
        <span className="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded bg-muted text-muted-foreground mr-2 align-middle">
          KEPT
        </span>
      )}
      <span className={isChanged ? "text-foreground" : "text-foreground/70"}>{tailored}</span>
      {isChanged && !isNew && base && (
        <div className="ml-12 mt-1 text-xs text-muted-foreground italic flex items-start gap-1">
          <ArrowRight className="w-3 h-3 mt-0.5 shrink-0" />
          <span className="line-through">{base}</span>
        </div>
      )}
    </li>
  );
}

function diffStringList(base: string[], tailored: string[]) {
  const baseSet = new Set(base.map((s) => s.toLowerCase()));
  const tailoredSet = new Set(tailored.map((s) => s.toLowerCase()));
  return {
    added: tailored.filter((s) => !baseSet.has(s.toLowerCase())),
    removed: base.filter((s) => !tailoredSet.has(s.toLowerCase())),
  };
}
