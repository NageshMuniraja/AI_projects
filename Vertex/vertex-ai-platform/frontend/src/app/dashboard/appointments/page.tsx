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
import api from "@/lib/api";
import { formatDateTime, getStatusColor } from "@/lib/utils";
import type { Appointment } from "@/types";
import { Calendar, Loader2, Check, X, Clock } from "lucide-react";

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");

  useEffect(() => {
    setLoading(true);
    api
      .getAppointments({ status: statusFilter || undefined })
      .then((data) => setAppointments(data.items))
      .catch(() => setAppointments([]))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  const updateStatus = async (id: string, status: string) => {
    try {
      await api.updateAppointment(id, {
        status: status as Appointment["status"],
      });
      setAppointments((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: status as Appointment["status"] } : a
        )
      );
    } catch {
      // handle error
    }
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-medium text-slate-500 mr-1">Status:</span>
        {["", "scheduled", "confirmed", "completed", "cancelled", "no_show"].map(
          (status) => (
            <Button
              key={status}
              variant={statusFilter === status ? "default" : "outline"}
              size="sm"
              onClick={() => setStatusFilter(status)}
            >
              {status
                ? status.charAt(0).toUpperCase() + status.slice(1).replace("_", " ")
                : "All"}
            </Button>
          )
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
            </div>
          ) : appointments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Calendar className="h-12 w-12 text-slate-300 mb-3" />
              <h3 className="text-lg font-semibold text-slate-700">
                No appointments
              </h3>
              <p className="text-sm text-slate-500 mt-1">
                Appointments booked by your AI agent will appear here.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Service</TableHead>
                  <TableHead>Date & Time</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {appointments.map((appt) => (
                  <TableRow key={appt.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar name={appt.customer_name} size="sm" />
                        <div>
                          <p className="font-medium text-slate-900">
                            {appt.customer_name}
                          </p>
                          <p className="text-xs text-slate-500">
                            {appt.customer_phone || appt.customer_email || ""}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {appt.service_name || "-"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDateTime(appt.scheduled_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm text-slate-600">
                        <Clock className="h-3.5 w-3.5" />
                        {appt.duration_minutes} min
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={getStatusColor(appt.status)}
                        variant="outline"
                      >
                        {appt.status.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-slate-500 max-w-[150px] truncate">
                      {appt.notes || "-"}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {appt.status === "scheduled" && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                updateStatus(appt.id, "confirmed")
                              }
                              title="Confirm"
                            >
                              <Check className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() =>
                                updateStatus(appt.id, "cancelled")
                              }
                              title="Cancel"
                            >
                              <X className="h-3.5 w-3.5 text-red-500" />
                            </Button>
                          </>
                        )}
                        {appt.status === "confirmed" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              updateStatus(appt.id, "completed")
                            }
                          >
                            Complete
                          </Button>
                        )}
                      </div>
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
