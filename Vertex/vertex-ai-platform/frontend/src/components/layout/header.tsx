"use client";

import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

const breadcrumbMap: Record<string, string> = {
  dashboard: "Dashboard",
  conversations: "Conversations",
  appointments: "Appointments",
  leads: "Leads",
  services: "Services",
  knowledge: "Knowledge Base",
  analytics: "Analytics",
  settings: "Settings",
};

export function Header() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const breadcrumbs = segments.map((segment, index) => {
    const label = breadcrumbMap[segment] || segment;
    const isLast = index === segments.length - 1;
    return { label, isLast, segment };
  });

  const pageTitle =
    breadcrumbs.length > 0
      ? breadcrumbs[breadcrumbs.length - 1].label
      : "Dashboard";

  return (
    <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-6 flex-shrink-0">
      <div>
        <nav className="flex items-center gap-1 text-sm text-slate-500 mb-0.5">
          {breadcrumbs.map((crumb, index) => (
            <span key={crumb.segment} className="flex items-center gap-1">
              {index > 0 && <ChevronRight className="h-3.5 w-3.5" />}
              <span
                className={
                  crumb.isLast
                    ? "text-slate-900 font-medium"
                    : "hover:text-slate-700"
                }
              >
                {crumb.label}
              </span>
            </span>
          ))}
        </nav>
        <h1 className="text-xl font-semibold text-slate-900">{pageTitle}</h1>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <div className="h-2 w-2 rounded-full bg-emerald-500 pulse-dot" />
          <span>System Online</span>
        </div>
      </div>
    </header>
  );
}
