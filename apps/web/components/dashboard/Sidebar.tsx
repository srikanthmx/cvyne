"use client";

// TODO (Antigravity): implement full sidebar with nav + UserButton
// See docs/agents/ANTIGRAVITY.md for spec

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Briefcase, FileText, Send, Settings } from "lucide-react";
import { UserButton } from "@clerk/nextjs";

const NAV_ITEMS = [
  { href: "/dashboard/jobs", label: "Jobs", icon: Briefcase },
  { href: "/dashboard/resumes", label: "Resumes", icon: FileText },
  { href: "/dashboard/applications", label: "Applications", icon: Send },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 border-r border-border bg-muted/30 flex flex-col px-3 py-6 gap-1">
      <div className="px-3 mb-6">
        <span className="font-semibold text-lg tracking-tight">AutoApply AI</span>
      </div>

      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={pathname.startsWith(href) ? "page" : undefined}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors
              hover:bg-muted aria-[current=page]:bg-primary aria-[current=page]:text-primary-foreground"
          >
            <Icon size={16} aria-hidden />
            {label}
          </Link>
        ))}
      </nav>

      <div className="px-3">
        <UserButton afterSignOutUrl="/login" />
      </div>
    </aside>
  );
}
