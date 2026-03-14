"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { useAuthStore } from "@/store/auth-store";
import api from "@/lib/api";
import { formatRelativeTime, truncate } from "@/lib/utils";
import type { Conversation, AnalyticsSummary } from "@/types";
import {
  MessageSquare,
  Zap,
  Calendar,
  Users,
  Plus,
  BookOpen,
  ArrowRight,
  Loader2,
  TrendingUp,
} from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ title, value, change, icon, color }: StatCardProps) {
  return (
    <Card className="stat-card">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>
            <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
            {change && (
              <p className="mt-1 flex items-center gap-1 text-sm text-emerald-600">
                <TrendingUp className="h-3.5 w-3.5" />
                {change}
              </p>
            )}
          </div>
          <div
            className={`flex items-center justify-center h-11 w-11 rounded-xl ${color}`}
          >
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { tenant } = useAuthStore();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [recentConversations, setRecentConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [analyticsData, convoData] = await Promise.allSettled([
          api.getAnalytics(),
          api.getConversations({ page_size: 5 }),
        ]);

        if (analyticsData.status === "fulfilled") {
          setAnalytics(analyticsData.value);
        }
        if (convoData.status === "fulfilled") {
          setRecentConversations(convoData.value.items);
        }
      } catch {
        // Silently handle errors for dashboard
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  const stats = analytics || {
    total_conversations: 0,
    active_conversations: 0,
    total_appointments: 0,
    total_leads: 0,
    messages_by_day: [],
  };

  const messageCounts = (stats.messages_by_day || []).map((d) => d.count);
  const maxMessages = messageCounts.length > 0 ? Math.max(...messageCounts, 1) : 1;

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">
          Welcome back{tenant ? `, ${tenant.name}` : ""}
        </h2>
        <p className="text-slate-500 mt-1">
          Here&apos;s what&apos;s happening with your AI agent today.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Conversations"
          value={stats.total_conversations}
          change="+12% from last week"
          icon={<MessageSquare className="h-5 w-5 text-primary-600" />}
          color="bg-primary-50"
        />
        <StatCard
          title="Active Chats"
          value={stats.active_conversations}
          icon={<Zap className="h-5 w-5 text-amber-600" />}
          color="bg-amber-50"
        />
        <StatCard
          title="Appointments"
          value={stats.total_appointments}
          change="+5 this week"
          icon={<Calendar className="h-5 w-5 text-emerald-600" />}
          color="bg-emerald-50"
        />
        <StatCard
          title="Leads Captured"
          value={stats.total_leads}
          change="+8 this week"
          icon={<Users className="h-5 w-5 text-blue-600" />}
          color="bg-blue-50"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Messages by Day</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.messages_by_day && stats.messages_by_day.length > 0 ? (
              <div className="flex items-end gap-2 h-48">
                {stats.messages_by_day.slice(-14).map((day) => (
                  <div
                    key={day.date}
                    className="flex-1 flex flex-col items-center gap-1"
                  >
                    <span className="text-xs text-slate-500 font-medium">
                      {day.count}
                    </span>
                    <div
                      className="w-full bg-primary-500 rounded-t-sm min-h-[4px] transition-all hover:bg-primary-600"
                      style={{
                        height: `${(day.count / maxMessages) * 100}%`,
                      }}
                    />
                    <span className="text-[10px] text-slate-400">
                      {new Date(day.date).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-slate-400">
                <MessageSquare className="h-10 w-10 mb-2" />
                <p className="text-sm">No message data yet</p>
                <p className="text-xs mt-1">
                  Charts will appear once your AI agent starts handling conversations
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link href="/dashboard/conversations">
              <Button variant="outline" className="w-full justify-start gap-3">
                <MessageSquare className="h-4 w-4 text-primary-600" />
                View Conversations
              </Button>
            </Link>
            <Link href="/dashboard/services">
              <Button variant="outline" className="w-full justify-start gap-3 mt-2">
                <Plus className="h-4 w-4 text-emerald-600" />
                Add New Service
              </Button>
            </Link>
            <Link href="/dashboard/knowledge">
              <Button variant="outline" className="w-full justify-start gap-3 mt-2">
                <BookOpen className="h-4 w-4 text-blue-600" />
                Add Knowledge Doc
              </Button>
            </Link>
            <Link href="/dashboard/settings">
              <Button variant="outline" className="w-full justify-start gap-3 mt-2">
                <Zap className="h-4 w-4 text-amber-600" />
                Configure AI Agent
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-base">Recent Conversations</CardTitle>
          <Link href="/dashboard/conversations">
            <Button variant="ghost" size="sm">
              View all <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {recentConversations.length > 0 ? (
            <div className="space-y-3">
              {recentConversations.map((convo) => (
                <Link
                  key={convo.id}
                  href={`/dashboard/conversations/${convo.id}`}
                  className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  <Avatar name={convo.contact_name} size="sm" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-slate-900">
                        {convo.contact_name}
                      </p>
                      <Badge
                        variant={
                          convo.status === "active"
                            ? "success"
                            : convo.status === "escalated"
                            ? "destructive"
                            : "outline"
                        }
                      >
                        {convo.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-500 truncate">
                      {truncate(convo.intent || "General inquiry", 60)}
                    </p>
                  </div>
                  <span className="text-xs text-slate-400 flex-shrink-0">
                    {formatRelativeTime(convo.last_message_at)}
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <MessageSquare className="h-10 w-10 mb-2" />
              <p className="text-sm font-medium">No conversations yet</p>
              <p className="text-xs mt-1">
                Your AI agent&apos;s conversations will appear here
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
