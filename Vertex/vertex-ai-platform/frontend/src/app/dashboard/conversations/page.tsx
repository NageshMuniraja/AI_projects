"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import api from "@/lib/api";
import { formatRelativeTime, truncate, getSentimentColor } from "@/lib/utils";
import type { Conversation } from "@/types";
import {
  MessageSquare,
  Globe,
  Phone,
  Mail,
  MessageCircle,
  Loader2,
  Search,
} from "lucide-react";
import { Input } from "@/components/ui/input";

const channelIcons: Record<string, React.ReactNode> = {
  whatsapp: <MessageCircle className="h-4 w-4 text-emerald-600" />,
  web: <Globe className="h-4 w-4 text-blue-600" />,
  voice: <Phone className="h-4 w-4 text-purple-600" />,
  email: <Mail className="h-4 w-4 text-amber-600" />,
};

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [channelFilter, setChannelFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    setLoading(true);
    api
      .getConversations({
        status: statusFilter || undefined,
        channel: channelFilter || undefined,
      })
      .then((data) => setConversations(data.items))
      .catch(() => setConversations([]))
      .finally(() => setLoading(false));
  }, [statusFilter, channelFilter]);

  const filteredConversations = conversations.filter((c) =>
    searchQuery
      ? c.contact_name.toLowerCase().includes(searchQuery.toLowerCase())
      : true
  );

  return (
    <div className="space-y-6 fade-in">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-medium text-slate-500 mr-1">Status:</span>
        {["", "active", "resolved", "escalated", "pending"].map((status) => (
          <Button
            key={status}
            variant={statusFilter === status ? "default" : "outline"}
            size="sm"
            onClick={() => setStatusFilter(status)}
          >
            {status
              ? status.charAt(0).toUpperCase() + status.slice(1)
              : "All"}
          </Button>
        ))}
        <div className="w-px h-6 bg-slate-200 mx-2" />
        <span className="text-sm font-medium text-slate-500 mr-1">Channel:</span>
        {["", "whatsapp", "web", "voice"].map((channel) => (
          <Button
            key={channel}
            variant={channelFilter === channel ? "default" : "outline"}
            size="sm"
            onClick={() =>
              setChannelFilter(channelFilter === channel && channel ? "" : channel)
            }
          >
            {channel ? (
              <span className="flex items-center gap-1.5">
                {channelIcons[channel]}
                {channel.charAt(0).toUpperCase() + channel.slice(1)}
              </span>
            ) : (
              "All"
            )}
          </Button>
        ))}
      </div>

      {/* Conversations List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      ) : filteredConversations.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <MessageSquare className="h-12 w-12 text-slate-300 mb-3" />
            <h3 className="text-lg font-semibold text-slate-700">
              No conversations found
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              {searchQuery || statusFilter || channelFilter
                ? "Try adjusting your filters"
                : "Conversations will appear here when customers start chatting with your AI agent."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {filteredConversations.map((conv) => (
            <Link
              key={conv.id}
              href={`/dashboard/conversations/${conv.id}`}
            >
              <Card className="hover:shadow-card-hover transition-all cursor-pointer">
                <CardContent className="p-4 flex items-center gap-4">
                  <Avatar name={conv.contact_name} size="md" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-medium text-slate-900 truncate">
                        {conv.contact_name || "Unknown Contact"}
                      </span>
                      {conv.sentiment && (
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium ${getSentimentColor(
                            conv.sentiment
                          )}`}
                        >
                          {conv.sentiment}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-500 truncate">
                      {truncate(conv.intent || "General inquiry", 80)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <div className="flex items-center gap-1.5">
                      {channelIcons[conv.channel] || (
                        <MessageSquare className="h-4 w-4 text-slate-400" />
                      )}
                    </div>
                    {conv.intent && (
                      <Badge variant="outline" className="text-xs hidden sm:inline-flex">
                        {conv.intent}
                      </Badge>
                    )}
                    <Badge
                      variant={
                        conv.status === "active"
                          ? "success"
                          : conv.status === "escalated"
                          ? "destructive"
                          : conv.status === "pending"
                          ? "warning"
                          : "outline"
                      }
                    >
                      {conv.status}
                    </Badge>
                    <span className="text-xs text-slate-400 whitespace-nowrap">
                      {formatRelativeTime(conv.last_message_at)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
