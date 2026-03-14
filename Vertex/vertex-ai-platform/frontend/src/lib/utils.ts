import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

export function formatDateTime(dateString: string): string {
  return `${formatDate(dateString)} at ${formatTime(dateString)}`;
}

export function formatRelativeTime(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function getSentimentColor(sentiment?: string): string {
  switch (sentiment) {
    case "positive":
      return "text-emerald-600 bg-emerald-50";
    case "negative":
      return "text-red-600 bg-red-50";
    default:
      return "text-slate-600 bg-slate-50";
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "active":
    case "confirmed":
    case "qualified":
      return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "resolved":
    case "completed":
    case "converted":
      return "text-blue-700 bg-blue-50 border-blue-200";
    case "escalated":
    case "cancelled":
    case "lost":
      return "text-red-700 bg-red-50 border-red-200";
    case "pending":
    case "new":
    case "scheduled":
      return "text-amber-700 bg-amber-50 border-amber-200";
    case "contacted":
      return "text-purple-700 bg-purple-50 border-purple-200";
    case "no_show":
      return "text-slate-700 bg-slate-50 border-slate-200";
    default:
      return "text-slate-700 bg-slate-50 border-slate-200";
  }
}

export function getChannelIcon(channel: string): string {
  switch (channel) {
    case "whatsapp":
      return "MessageCircle";
    case "web":
      return "Globe";
    case "voice":
      return "Phone";
    case "email":
      return "Mail";
    default:
      return "MessageSquare";
  }
}
