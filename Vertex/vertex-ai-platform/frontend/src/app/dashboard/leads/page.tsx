"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Avatar } from "@/components/ui/avatar";
import { Select } from "@/components/ui/select";
import api from "@/lib/api";
import { formatDate, getStatusColor } from "@/lib/utils";
import type { Lead } from "@/types";
import { Users, Loader2, TrendingUp, MessageCircle, Globe, Phone, Mail } from "lucide-react";

const sourceIcons: Record<string, React.ReactNode> = {
  whatsapp: <MessageCircle className="h-3.5 w-3.5 text-emerald-600" />,
  web: <Globe className="h-3.5 w-3.5 text-blue-600" />,
  voice: <Phone className="h-3.5 w-3.5 text-purple-600" />,
  email: <Mail className="h-3.5 w-3.5 text-amber-600" />,
};

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 70
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : score >= 40
      ? "bg-amber-50 text-amber-700 border-amber-200"
      : "bg-slate-50 text-slate-600 border-slate-200";

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold border ${color}`}
    >
      <TrendingUp className="h-3 w-3" />
      {score}
    </span>
  );
}

const statusOptions = [
  { value: "new", label: "New" },
  { value: "contacted", label: "Contacted" },
  { value: "qualified", label: "Qualified" },
  { value: "converted", label: "Converted" },
  { value: "lost", label: "Lost" },
];

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");

  useEffect(() => {
    setLoading(true);
    api
      .getLeads({ status: statusFilter || undefined })
      .then((data) => setLeads(data.items))
      .catch(() => setLeads([]))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  const updateLeadStatus = async (id: string, status: string) => {
    try {
      await api.updateLead(id, { status: status as Lead["status"] });
      setLeads((prev) =>
        prev.map((l) =>
          l.id === id ? { ...l, status: status as Lead["status"] } : l
        )
      );
    } catch {
      // handle error
    }
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-slate-500 mr-1">Status:</span>
          {["", "new", "contacted", "qualified", "converted", "lost"].map(
            (status) => (
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
            )
          )}
        </div>
        <Badge variant="outline">{leads.length} leads</Badge>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
            </div>
          ) : leads.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Users className="h-12 w-12 text-slate-300 mb-3" />
              <h3 className="text-lg font-semibold text-slate-700">
                No leads yet
              </h3>
              <p className="text-sm text-slate-500 mt-1">
                Your AI agent will automatically capture leads from
                conversations.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar name={lead.name || "Lead"} size="sm" />
                        <span className="font-medium text-slate-900">
                          {lead.name || "Unknown"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm space-y-0.5">
                        {lead.phone && (
                          <p className="text-slate-700">{lead.phone}</p>
                        )}
                        {lead.email && (
                          <p className="text-slate-500 text-xs">{lead.email}</p>
                        )}
                        {!lead.phone && !lead.email && (
                          <span className="text-slate-400">-</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        {sourceIcons[lead.source] || null}
                        <span className="text-sm capitalize">{lead.source}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <ScoreBadge score={lead.score} />
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={getStatusColor(lead.status)}
                        variant="outline"
                      >
                        {lead.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-slate-500">
                      {formatDate(lead.created_at)}
                    </TableCell>
                    <TableCell>
                      <Select
                        options={statusOptions}
                        value={lead.status}
                        onChange={(e) =>
                          updateLeadStatus(lead.id, e.target.value)
                        }
                        className="h-8 text-xs w-32"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
