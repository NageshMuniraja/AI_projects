"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import api from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { KnowledgeDocument } from "@/types";
import {
  BookOpen,
  Plus,
  Trash2,
  Loader2,
  FileText,
  HelpCircle,
  Shield,
  Package,
  File,
} from "lucide-react";

const docTypeIcons: Record<string, React.ReactNode> = {
  faq: <HelpCircle className="h-5 w-5 text-blue-500" />,
  policy: <Shield className="h-5 w-5 text-amber-500" />,
  product: <Package className="h-5 w-5 text-emerald-500" />,
  general: <File className="h-5 w-5 text-slate-500" />,
};

const docTypeOptions = [
  { value: "faq", label: "FAQ" },
  { value: "policy", label: "Policy" },
  { value: "product", label: "Product" },
  { value: "general", label: "General" },
];

export default function KnowledgePage() {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    title: "",
    content: "",
    doc_type: "general" as KnowledgeDocument["doc_type"],
    source_url: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getDocuments()
      .then(setDocs)
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  }, []);

  const handleAdd = async () => {
    if (!form.title.trim() || !form.content.trim()) return;
    setSaving(true);
    try {
      const doc = await api.createDocument({
        title: form.title,
        content: form.content,
        doc_type: form.doc_type,
        source_url: form.source_url || undefined,
      });
      setDocs((prev) => [...prev, doc]);
      setDialogOpen(false);
      setForm({ title: "", content: "", doc_type: "general", source_url: "" });
    } catch {
      // handle error
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    try {
      await api.deleteDocument(id);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch {
      // handle error
    }
  };

  const handleToggleActive = async (doc: KnowledgeDocument) => {
    try {
      const updated = await api.updateDocument(doc.id, {
        is_active: !doc.is_active,
      });
      setDocs((prev) => prev.map((d) => (d.id === doc.id ? updated : d)));
    } catch {
      // handle error
    }
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          Add documents to help your AI agent answer questions accurately.
        </p>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4" />
          Add Document
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      ) : docs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <BookOpen className="h-12 w-12 text-slate-300 mb-3" />
            <h3 className="text-lg font-semibold text-slate-700">
              No documents added
            </h3>
            <p className="text-sm text-slate-500 mt-1 mb-4 text-center max-w-md">
              Add FAQs, service descriptions, policies, and other information
              your AI agent should know about.
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4" />
              Add Your First Document
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {docs.map((doc) => (
            <Card
              key={doc.id}
              className="hover:shadow-card-hover transition-all"
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-slate-50 flex-shrink-0">
                    {docTypeIcons[doc.doc_type] || (
                      <FileText className="h-5 w-5 text-slate-400" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-medium text-slate-900 truncate">
                      {doc.title}
                    </h3>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <Badge variant="outline" className="text-xs capitalize">
                        {doc.doc_type}
                      </Badge>
                      <span className="text-xs text-slate-500">
                        {doc.chunk_count} chunks
                      </span>
                      <span className="text-xs text-slate-400">
                        Added {formatDate(doc.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Badge
                    variant={doc.is_active ? "success" : "outline"}
                    className="cursor-pointer"
                    onClick={() => handleToggleActive(doc)}
                  >
                    {doc.is_active ? "Active" : "Inactive"}
                  </Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDelete(doc.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent onClose={() => setDialogOpen(false)}>
          <DialogHeader>
            <DialogTitle>Add Knowledge Document</DialogTitle>
            <DialogDescription>
              Paste FAQ content, service descriptions, policies, or any
              information your AI should use when answering customers.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <Input
              id="doc-title"
              label="Document Title"
              placeholder="e.g., Pricing FAQ, Return Policy"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
            />
            <Select
              id="doc-type"
              label="Document Type"
              options={docTypeOptions}
              value={form.doc_type}
              onChange={(e) =>
                setForm({
                  ...form,
                  doc_type: e.target.value as KnowledgeDocument["doc_type"],
                })
              }
            />
            <Input
              id="doc-url"
              label="Source URL (optional)"
              placeholder="https://..."
              value={form.source_url}
              onChange={(e) => setForm({ ...form, source_url: e.target.value })}
            />
            <Textarea
              id="doc-content"
              label="Content"
              placeholder="Paste your content here... The AI will use this information to answer customer questions."
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              rows={10}
              required
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAdd}
              disabled={
                !form.title.trim() || !form.content.trim() || saving
              }
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                "Add Document"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
