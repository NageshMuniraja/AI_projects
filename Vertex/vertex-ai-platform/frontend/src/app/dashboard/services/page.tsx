"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import api from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Service } from "@/types";
import {
  Briefcase,
  Plus,
  Pencil,
  Trash2,
  Loader2,
  DollarSign,
  Clock,
} from "lucide-react";

interface ServiceFormData {
  name: string;
  description: string;
  duration_minutes: number;
  price: number;
  currency: string;
  category: string;
  is_active: boolean;
}

const emptyForm: ServiceFormData = {
  name: "",
  description: "",
  duration_minutes: 30,
  price: 0,
  currency: "USD",
  category: "",
  is_active: true,
};

export default function ServicesPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<ServiceFormData>(emptyForm);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getServices()
      .then(setServices)
      .catch(() => setServices([]))
      .finally(() => setLoading(false));
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
    setEditingId(null);
    setDialogOpen(true);
  };

  const openEdit = (service: Service) => {
    setForm({
      name: service.name,
      description: service.description,
      duration_minutes: service.duration_minutes,
      price: service.price,
      currency: service.currency,
      category: service.category || "",
      is_active: service.is_active,
    });
    setEditingId(service.id);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editingId) {
        const updated = await api.updateService(editingId, form);
        setServices((prev) =>
          prev.map((s) => (s.id === editingId ? updated : s))
        );
      } else {
        const created = await api.createService(form);
        setServices((prev) => [...prev, created]);
      }
      setDialogOpen(false);
    } catch {
      // handle error
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this service?")) return;
    try {
      await api.deleteService(id);
      setServices((prev) => prev.filter((s) => s.id !== id));
    } catch {
      // handle error
    }
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <p className="text-slate-500 text-sm">
          Manage the services your AI agent can offer and book.
        </p>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" />
          Add Service
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      ) : services.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Briefcase className="h-12 w-12 text-slate-300 mb-3" />
            <h3 className="text-lg font-semibold text-slate-700">
              No services yet
            </h3>
            <p className="text-sm text-slate-500 mt-1 mb-4">
              Add services that your AI agent can present and book for customers.
            </p>
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" />
              Add Your First Service
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((service) => (
            <Card key={service.id} className="hover:shadow-card-hover transition-all">
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-900 truncate">
                      {service.name}
                    </h3>
                    {service.category && (
                      <Badge variant="outline" className="mt-1 text-xs">
                        {service.category}
                      </Badge>
                    )}
                  </div>
                  <Badge
                    variant={service.is_active ? "success" : "outline"}
                    className="flex-shrink-0"
                  >
                    {service.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>

                <p className="text-sm text-slate-500 mb-4 line-clamp-2">
                  {service.description || "No description"}
                </p>

                <div className="flex items-center gap-4 mb-4 text-sm">
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <DollarSign className="h-4 w-4 text-emerald-500" />
                    <span className="font-semibold">
                      {service.price > 0
                        ? `${service.currency} ${service.price.toFixed(2)}`
                        : "Free"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <Clock className="h-4 w-4 text-blue-500" />
                    <span>{service.duration_minutes} min</span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                  <span className="text-xs text-slate-400">
                    Added {formatDate(service.created_at)}
                  </span>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openEdit(service)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(service.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent onClose={() => setDialogOpen(false)}>
          <DialogHeader>
            <DialogTitle>
              {editingId ? "Edit Service" : "Add New Service"}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <Input
              id="service-name"
              label="Service Name"
              placeholder="e.g., General Consultation"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
            <Textarea
              id="service-desc"
              label="Description"
              placeholder="Describe this service..."
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              rows={3}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                id="service-duration"
                label="Duration (minutes)"
                type="number"
                min={5}
                value={form.duration_minutes}
                onChange={(e) =>
                  setForm({
                    ...form,
                    duration_minutes: parseInt(e.target.value) || 0,
                  })
                }
              />
              <Input
                id="service-price"
                label="Price"
                type="number"
                min={0}
                step={0.01}
                value={form.price}
                onChange={(e) =>
                  setForm({
                    ...form,
                    price: parseFloat(e.target.value) || 0,
                  })
                }
              />
            </div>
            <Input
              id="service-category"
              label="Category (optional)"
              placeholder="e.g., Dental, Legal, Fitness"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) =>
                  setForm({ ...form, is_active: e.target.checked })
                }
                className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-slate-700">Active (visible to customers)</span>
            </label>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || !form.name.trim()}
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : editingId ? (
                "Save Changes"
              ) : (
                "Create Service"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
