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
    <aside className="fixed bottom-0 left-0 z-50 w-full border-t border-border bg-background/80 backdrop-blur-md md:static md:w-64 md:border-r md:border-t-0 md:bg-muted/30 flex flex-row md:flex-col px-2 md:px-4 py-2 md:py-6 gap-1 md:h-screen">
      <div className="hidden md:flex px-2 mb-6 items-center">
        <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">AutoApply AI</span>
      </div>

      <nav className="flex-1 flex flex-row md:flex-col justify-around md:justify-start gap-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={isActive ? "page" : undefined}
              className="group flex flex-col md:flex-row items-center justify-center md:justify-start gap-1 md:gap-3 px-2 md:px-3 py-2 rounded-xl text-xs md:text-sm font-medium transition-all
                hover:bg-muted aria-[current=page]:bg-primary/10 aria-[current=page]:text-primary"
            >
              <Icon size={20} className="md:w-4 md:h-4 transition-transform group-hover:scale-110" aria-hidden />
              <span className="md:inline">{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="hidden md:flex px-3 mt-auto pt-4 border-t border-border/50">
        <UserButton afterSignOutUrl="/sign-in" appearance={{ elements: { userButtonBox: "flex-row-reverse w-full justify-end", userButtonOuterIdentifier: "text-sm font-medium" } }} showName />
      </div>
    </aside>
  );
}
