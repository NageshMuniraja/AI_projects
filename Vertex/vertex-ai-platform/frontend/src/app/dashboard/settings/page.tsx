"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/store/auth-store";
import api from "@/lib/api";
import type { Tenant, TenantSettings } from "@/types";
import {
  Building2,
  Bot,
  Palette,
  Plug,
  Loader2,
  Save,
  Check,
  MessageCircle,
  Phone,
  Calendar,
} from "lucide-react";

type TabKey = "business" | "ai" | "widget" | "integration";

const tabs: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: "business", label: "Business Info", icon: <Building2 className="h-4 w-4" /> },
  { key: "ai", label: "AI Configuration", icon: <Bot className="h-4 w-4" /> },
  { key: "widget", label: "Widget", icon: <Palette className="h-4 w-4" /> },
  { key: "integration", label: "Integrations", icon: <Plug className="h-4 w-4" /> },
];

const toneOptions = [
  { value: "professional", label: "Professional" },
  { value: "friendly", label: "Friendly" },
  { value: "casual", label: "Casual" },
  { value: "formal", label: "Formal" },
];

const positionOptions = [
  { value: "bottom-right", label: "Bottom Right" },
  { value: "bottom-left", label: "Bottom Left" },
];

export default function SettingsPage() {
  const { tenant, loadUser } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("business");
  const [tenantData, setTenantData] = useState<Tenant | null>(null);

  useEffect(() => {
    api
      .getTenant()
      .then(setTenantData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const updateField = (field: string, value: string | boolean) => {
    if (!tenantData) return;
    setTenantData({ ...tenantData, [field]: value });
    setSaved(false);
  };

  const updateSettings = (field: keyof TenantSettings, value: string) => {
    if (!tenantData) return;
    setTenantData({
      ...tenantData,
      settings: { ...tenantData.settings, [field]: value },
    });
    setSaved(false);
  };

  const handleSave = async () => {
    if (!tenantData) return;
    setSaving(true);
    try {
      await api.updateTenant({
        name: tenantData.name,
        industry: tenantData.industry,
        settings: tenantData.settings,
      });
      setSaved(true);
      loadUser();
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // handle error
    } finally {
      setSaving(false);
    }
  };

  if (loading || !tenantData) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  const settings = tenantData.settings;

  return (
    <div className="space-y-6 fade-in">
      {/* Save bar */}
      <div className="flex items-center justify-end gap-3">
        {saved && (
          <Badge variant="success" className="gap-1">
            <Check className="h-3 w-3" />
            Changes saved
          </Badge>
        )}
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              activeTab === tab.key
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Business Info */}
      {activeTab === "business" && (
        <Card>
          <CardHeader>
            <CardTitle>Business Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 max-w-xl">
            <Input
              id="business-name"
              label="Business Name"
              value={tenantData.name || ""}
              onChange={(e) => updateField("name", e.target.value)}
            />
            <Input
              id="business-industry"
              label="Industry"
              value={tenantData.industry || ""}
              onChange={(e) => updateField("industry", e.target.value)}
            />
            <Input
              id="business-slug"
              label="Slug (URL identifier)"
              value={tenantData.slug || ""}
              disabled
              className="bg-slate-50"
            />
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Plan
              </label>
              <Badge variant="default" className="text-sm capitalize">
                {tenantData.plan}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Configuration */}
      {activeTab === "ai" && (
        <Card>
          <CardHeader>
            <CardTitle>AI Agent Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 max-w-xl">
            <Input
              id="ai-persona"
              label="AI Persona Name"
              value={settings.ai_persona_name || ""}
              onChange={(e) =>
                updateSettings("ai_persona_name", e.target.value)
              }
              placeholder="e.g., Dr. AI Assistant, Beauty Bot"
            />
            <p className="text-xs text-slate-500 -mt-2">
              The name your AI will use to introduce itself
            </p>

            <Select
              id="ai-tone"
              label="Tone of Voice"
              options={toneOptions}
              value={settings.ai_tone || "professional"}
              onChange={(e) => updateSettings("ai_tone", e.target.value)}
            />

            <Textarea
              id="ai-greeting"
              label="Greeting Message"
              value={settings.greeting_message || ""}
              onChange={(e) =>
                updateSettings("greeting_message", e.target.value)
              }
              rows={3}
              placeholder="The first message customers see when they start a chat"
            />

            <Textarea
              id="ai-instructions"
              label="Custom Instructions"
              value={settings.custom_instructions || ""}
              onChange={(e) =>
                updateSettings("custom_instructions", e.target.value)
              }
              rows={6}
              placeholder="Special instructions for your AI (e.g., 'Always recommend our premium package', 'Don't discuss competitor pricing')"
            />
            <p className="text-xs text-slate-500 -mt-2">
              These instructions are included in every AI response generation
            </p>
          </CardContent>
        </Card>
      )}

      {/* Widget Settings */}
      {activeTab === "widget" && (
        <Card>
          <CardHeader>
            <CardTitle>Chat Widget Customization</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 max-w-xl">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Primary Color
              </label>
              <div className="flex gap-3 items-center">
                <input
                  type="color"
                  value={settings.widget_primary_color || "#6366f1"}
                  onChange={(e) =>
                    updateSettings("widget_primary_color", e.target.value)
                  }
                  className="w-12 h-10 rounded border border-slate-300 cursor-pointer"
                />
                <Input
                  value={settings.widget_primary_color || "#6366f1"}
                  onChange={(e) =>
                    updateSettings("widget_primary_color", e.target.value)
                  }
                  className="w-32"
                />
                {/* Color preview */}
                <div
                  className="h-10 flex-1 rounded-lg flex items-center justify-center text-white text-sm font-medium"
                  style={{
                    backgroundColor:
                      settings.widget_primary_color || "#6366f1",
                  }}
                >
                  Preview
                </div>
              </div>
            </div>

            <Select
              id="widget-position"
              label="Widget Position"
              options={positionOptions}
              value={settings.widget_position || "bottom-right"}
              onChange={(e) =>
                updateSettings("widget_position", e.target.value)
              }
            />

            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <h3 className="text-sm font-medium text-slate-700 mb-2">
                Embed Code
              </h3>
              <pre className="text-xs bg-slate-900 text-emerald-400 p-4 rounded-lg overflow-x-auto">
                {`<script
  src="https://vertex-ai.com/widget.js"
  data-tenant="${tenantData.slug}"
  data-color="${settings.widget_primary_color || "#6366f1"}"
  data-position="${settings.widget_position || "bottom-right"}"
></script>`}
              </pre>
              <p className="text-xs text-slate-500 mt-2">
                Add this code to your website to enable the AI chat widget.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integrations */}
      {activeTab === "integration" && (
        <div className="space-y-4 max-w-2xl">
          <Card>
            <CardContent className="p-6 flex items-center gap-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-50 flex-shrink-0">
                <MessageCircle className="h-6 w-6 text-emerald-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-900">
                  WhatsApp Business
                </h3>
                <p className="text-sm text-slate-500">
                  Connect your WhatsApp Business number to handle customer
                  messages with AI.
                </p>
                {settings.whatsapp_phone_number && (
                  <p className="text-sm text-emerald-600 mt-1">
                    Connected: {settings.whatsapp_phone_number}
                  </p>
                )}
              </div>
              <Badge variant={settings.whatsapp_phone_number ? "success" : "outline"}>
                {settings.whatsapp_phone_number ? "Connected" : "Setup"}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 flex items-center gap-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-blue-50 flex-shrink-0">
                <Phone className="h-6 w-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-900">Voice (Twilio)</h3>
                <p className="text-sm text-slate-500">
                  Enable AI voice calls for appointment reminders and customer
                  support.
                </p>
              </div>
              <Badge variant="outline">Coming Soon</Badge>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 flex items-center gap-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-purple-50 flex-shrink-0">
                <Calendar className="h-6 w-6 text-purple-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-900">
                  Google Calendar
                </h3>
                <p className="text-sm text-slate-500">
                  Sync AI-booked appointments to your Google Calendar
                  automatically.
                </p>
              </div>
              <Badge variant="outline">Coming Soon</Badge>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
