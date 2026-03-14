"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import api from "@/lib/api";
import { formatTime, formatDate, getSentimentColor } from "@/lib/utils";
import type { Conversation, Message } from "@/types";
import {
  Send,
  ArrowLeft,
  Loader2,
  MessageCircle,
  Globe,
  Phone,
  User,
  Clock,
  Tag,
} from "lucide-react";

export default function ConversationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function load() {
      try {
        const [convo, msgs] = await Promise.all([
          api.getConversation(id),
          api.getMessages(id),
        ]);
        setConversation(convo);
        setMessages(msgs);
      } catch {
        // handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || sending) return;
    setSending(true);

    const tempMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: id,
      role: "user",
      content: input,
      message_type: "text",
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempMsg]);
    const messageText = input;
    setInput("");

    try {
      const response = await api.sendMessage(id, messageText);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempMsg.id),
        { ...tempMsg, id: `user-${Date.now()}` },
        response,
      ]);
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== tempMsg.id));
      setInput(messageText);
    } finally {
      setSending(false);
    }
  };

  const channelIcon =
    conversation?.channel === "whatsapp" ? (
      <MessageCircle className="h-4 w-4" />
    ) : conversation?.channel === "voice" ? (
      <Phone className="h-4 w-4" />
    ) : (
      <Globe className="h-4 w-4" />
    );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6 fade-in">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Card className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <CardHeader className="border-b border-slate-100 py-3 px-4 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => router.push("/dashboard/conversations")}
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <Avatar
                  name={conversation?.contact_name || "Customer"}
                  size="sm"
                />
                <div>
                  <CardTitle className="text-base">
                    {conversation?.contact_name || "Customer Chat"}
                  </CardTitle>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    {channelIcon}
                    <span className="capitalize">{conversation?.channel}</span>
                    <span>-</span>
                    <span>{messages.length} messages</span>
                  </div>
                </div>
              </div>
              <Badge
                variant={
                  conversation?.status === "active"
                    ? "success"
                    : conversation?.status === "escalated"
                    ? "destructive"
                    : "outline"
                }
              >
                {conversation?.status}
              </Badge>
            </div>
          </CardHeader>

          {/* Messages */}
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-400">
                <MessageCircle className="h-10 w-10 mb-2" />
                <p className="text-sm">No messages yet</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`chat-bubble rounded-2xl px-4 py-2.5 ${
                      msg.role === "user"
                        ? "bg-primary-600 text-white rounded-br-md"
                        : msg.role === "system"
                        ? "bg-amber-50 text-amber-800 border border-amber-200 rounded-bl-md"
                        : "bg-slate-100 text-slate-900 rounded-bl-md"
                    }`}
                  >
                    {msg.role === "assistant" && (
                      <p className="text-[10px] font-medium text-primary-600 mb-1">
                        AI Assistant
                      </p>
                    )}
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    <p
                      className={`text-[10px] mt-1 ${
                        msg.role === "user"
                          ? "text-primary-200"
                          : "text-slate-400"
                      }`}
                    >
                      {formatTime(msg.created_at)}
                    </p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </CardContent>

          {/* Input */}
          <div className="border-t border-slate-100 p-4 flex-shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                sendMessage();
              }}
              className="flex gap-2"
            >
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message..."
                disabled={sending}
                className="flex-1"
              />
              <Button
                type="submit"
                disabled={sending || !input.trim()}
                size="icon"
              >
                {sending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          </div>
        </Card>
      </div>

      {/* Metadata Sidebar */}
      <div className="w-72 space-y-4 hidden lg:block flex-shrink-0">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Contact Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-slate-400" />
              <div>
                <p className="text-slate-500 text-xs">Name</p>
                <p className="font-medium">
                  {conversation?.contact_name || "Unknown"}
                </p>
              </div>
            </div>
            {conversation?.contact_phone && (
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-slate-400" />
                <div>
                  <p className="text-slate-500 text-xs">Phone</p>
                  <p className="font-medium">{conversation.contact_phone}</p>
                </div>
              </div>
            )}
            {conversation?.contact_email && (
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-slate-400" />
                <div>
                  <p className="text-slate-500 text-xs">Email</p>
                  <p className="font-medium">{conversation.contact_email}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Conversation Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4 text-slate-400" />
              <div>
                <p className="text-slate-500 text-xs">Intent</p>
                <p className="font-medium capitalize">
                  {conversation?.intent || "Unknown"}
                </p>
              </div>
            </div>
            <div>
              <p className="text-slate-500 text-xs mb-1">Sentiment</p>
              {conversation?.sentiment && (
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${getSentimentColor(
                    conversation.sentiment
                  )}`}
                >
                  {conversation.sentiment}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-slate-400" />
              <div>
                <p className="text-slate-500 text-xs">Started</p>
                <p className="font-medium">
                  {conversation?.created_at
                    ? formatDate(conversation.created_at)
                    : "-"}
                </p>
              </div>
            </div>
            <div>
              <p className="text-slate-500 text-xs">Language</p>
              <p className="font-medium uppercase">
                {conversation?.language || "en"}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" size="sm" className="w-full">
              Escalate to Agent
            </Button>
            <Button variant="outline" size="sm" className="w-full">
              Mark as Resolved
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
