"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import { Avatar } from "@/components/ui/avatar";
import {
  LayoutDashboard,
  MessageSquare,
  Calendar,
  Users,
  Briefcase,
  BookOpen,
  BarChart3,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/conversations", label: "Conversations", icon: MessageSquare },
  { href: "/dashboard/appointments", label: "Appointments", icon: Calendar },
  { href: "/dashboard/leads", label: "Leads", icon: Users },
  { href: "/dashboard/services", label: "Services", icon: Briefcase },
  { href: "/dashboard/knowledge", label: "Knowledge Base", icon: BookOpen },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-white border-r border-slate-200 transition-all duration-300 flex-shrink-0",
        collapsed ? "w-[72px]" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-slate-200">
        <Link href="/dashboard" className="flex items-center gap-2.5 min-w-0">
          <div className="flex items-center justify-center h-9 w-9 rounded-lg bg-primary-600 flex-shrink-0">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <span className="text-lg font-bold text-slate-900 truncate">
              Vertex AI
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "sidebar-link flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium",
                isActive
                  ? "active bg-primary-50 text-primary-700"
                  : "text-slate-600 hover:text-slate-900"
              )}
              title={collapsed ? item.label : undefined}
            >
              <item.icon
                className={cn(
                  "h-5 w-5 flex-shrink-0",
                  isActive ? "text-primary-600" : "text-slate-400"
                )}
              />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="px-3 py-2">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full py-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* User */}
      <div className="border-t border-slate-200 p-3">
        <div className="flex items-center gap-3">
          <Avatar
            name={user?.full_name || "User"}
            src={user?.avatar_url}
            size="sm"
          />
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">
                {user?.full_name || "User"}
              </p>
              <p className="text-xs text-slate-500 truncate">
                {user?.email || ""}
              </p>
            </div>
          )}
          {!collapsed && (
            <button
              onClick={logout}
              className="text-slate-400 hover:text-red-600 transition-colors cursor-pointer"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
