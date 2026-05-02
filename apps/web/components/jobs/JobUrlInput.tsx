"use client";

// TODO (Antigravity): implement full job URL input with bulk paste support
// See docs/agents/ANTIGRAVITY.md for spec

export function JobUrlInput() {
  return (
    <div className="rounded-lg border border-border p-4 space-y-3">
      <label htmlFor="job-urls" className="text-sm font-medium">
        Paste job URLs <span className="text-muted-foreground">(one per line)</span>
      </label>
      <textarea
        id="job-urls"
        rows={4}
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm resize-none
          placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        placeholder="https://linkedin.com/jobs/view/...&#10;https://greenhouse.io/..."
      />
      <button
        type="button"
        className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:opacity-90"
      >
        Extract &amp; Apply
      </button>
    </div>
  );
}
