"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import type { AnalyticsSummary } from "@/types";
import {
  MessageSquare,
  Zap,
  Calendar,
  Users,
  Clock,
  ThumbsUp,
  TrendingUp,
  BarChart3,
  Loader2,
  MessageCircle,
  Globe,
  Phone,
} from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

function MetricCard({ label, value, icon, color, subtitle }: MetricCardProps) {
  return (
    <Card className="stat-card">
      <CardContent className="p-5">
        <div className="flex items-start gap-3">
          <div
            className={`flex items-center justify-center h-10 w-10 rounded-lg flex-shrink-0 ${color}`}
          >
            {icon}
          </div>
          <div>
            <p className="text-sm text-slate-500">{label}</p>
            <p className="text-2xl font-bold text-slate-900 mt-0.5">
              {typeof value === "number" ? value.toLocaleString() : value}
            </p>
            {subtitle && (
              <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

const channelIcons: Record<string, React.ReactNode> = {
  whatsapp: <MessageCircle className="h-4 w-4 text-emerald-600" />,
  web: <Globe className="h-4 w-4 text-blue-600" />,
  voice: <Phone className="h-4 w-4 text-purple-600" />,
};

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getAnalytics()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-400">
        <BarChart3 className="h-12 w-12 mb-3" />
        <p className="text-lg font-medium">No analytics data available</p>
        <p className="text-sm mt-1">
          Analytics will populate as your AI agent handles conversations.
        </p>
      </div>
    );
  }

  const maxMessages = Math.max(
    ...(data.messages_by_day || []).map((d) => d.count).concat([1]),
    1
  );

  const totalChannelConvos = (data.conversations_by_channel || []).reduce(
    (sum, c) => sum + c.count,
    0
  );

  const totalSentiments = (data.sentiment_distribution || []).reduce(
    (sum, s) => sum + s.count,
    0
  );

  const formatSeconds = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Conversations"
          value={data.total_conversations}
          icon={<MessageSquare className="h-5 w-5 text-primary-600" />}
          color="bg-primary-50"
        />
        <MetricCard
          label="Active Conversations"
          value={data.active_conversations}
          icon={<Zap className="h-5 w-5 text-amber-600" />}
          color="bg-amber-50"
          subtitle={`${data.escalated_conversations} escalated`}
        />
        <MetricCard
          label="Total Messages"
          value={data.total_messages}
          icon={<MessageCircle className="h-5 w-5 text-blue-600" />}
          color="bg-blue-50"
        />
        <MetricCard
          label="Appointments"
          value={data.total_appointments}
          icon={<Calendar className="h-5 w-5 text-emerald-600" />}
          color="bg-emerald-50"
          subtitle={`${data.upcoming_appointments} upcoming`}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Leads"
          value={data.total_leads}
          icon={<Users className="h-5 w-5 text-purple-600" />}
          color="bg-purple-50"
          subtitle={`${data.qualified_leads} qualified, ${data.converted_leads} converted`}
        />
        <MetricCard
          label="Avg Response Time"
          value={formatSeconds(data.avg_response_time_seconds)}
          icon={<Clock className="h-5 w-5 text-rose-600" />}
          color="bg-rose-50"
        />
        <MetricCard
          label="Avg Resolution Time"
          value={formatSeconds(data.avg_resolution_time_seconds)}
          icon={<TrendingUp className="h-5 w-5 text-indigo-600" />}
          color="bg-indigo-50"
        />
        <MetricCard
          label="Satisfaction Score"
          value={`${(data.satisfaction_score * 100).toFixed(0)}%`}
          icon={<ThumbsUp className="h-5 w-5 text-emerald-600" />}
          color="bg-emerald-50"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Messages Over Time */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Messages Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            {data.messages_by_day && data.messages_by_day.length > 0 ? (
              <div className="flex items-end gap-1 h-48">
                {data.messages_by_day.map((day) => (
                  <div
                    key={day.date}
                    className="flex-1 flex flex-col items-center gap-1"
                    title={`${day.date}: ${day.count} messages`}
                  >
                    <div
                      className="w-full bg-primary-400 rounded-t-sm hover:bg-primary-500 transition-colors min-h-[2px]"
                      style={{
                        height: `${(day.count / maxMessages) * 100}%`,
                      }}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-48 text-slate-400">
                <p className="text-sm">No message data yet</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Channel Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Channel Distribution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(data.conversations_by_channel || []).map((ch) => {
              const pct =
                totalChannelConvos > 0
                  ? Math.round((ch.count / totalChannelConvos) * 100)
                  : 0;
              return (
                <div key={ch.channel}>
                  <div className="flex items-center justify-between text-sm mb-1.5">
                    <div className="flex items-center gap-2">
                      {channelIcons[ch.channel] || (
                        <MessageSquare className="h-4 w-4 text-slate-400" />
                      )}
                      <span className="capitalize font-medium">
                        {ch.channel}
                      </span>
                    </div>
                    <span className="text-slate-500">
                      {pct}% ({ch.count})
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
            {(!data.conversations_by_channel ||
              data.conversations_by_channel.length === 0) && (
              <p className="text-sm text-slate-400">No channel data yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {data.sentiment_distribution &&
            data.sentiment_distribution.length > 0 ? (
              <div className="space-y-3">
                {data.sentiment_distribution.map((s) => {
                  const pct =
                    totalSentiments > 0
                      ? Math.round((s.count / totalSentiments) * 100)
                      : 0;
                  const color =
                    s.sentiment === "positive"
                      ? "bg-emerald-500"
                      : s.sentiment === "negative"
                      ? "bg-red-500"
                      : "bg-slate-400";
                  return (
                    <div key={s.sentiment}>
                      <div className="flex items-center justify-between text-sm mb-1.5">
                        <span className="capitalize font-medium">
                          {s.sentiment}
                        </span>
                        <span className="text-slate-500">
                          {pct}% ({s.count})
                        </span>
                      </div>
                      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${color} rounded-full transition-all`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-slate-400">No sentiment data yet</p>
            )}
          </CardContent>
        </Card>

        {/* Top Intents */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Intents</CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_intents && data.top_intents.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {data.top_intents.map((intent) => (
                  <Badge
                    key={intent.intent}
                    variant="default"
                    className="text-sm py-1.5 px-3"
                  >
                    {intent.intent}{" "}
                    <span className="ml-1 opacity-70">({intent.count})</span>
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">
                Intents will appear as customers interact with your AI agent
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
