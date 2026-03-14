'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { api } from '@/lib/api';

const steps = [
  { title: 'Business Details', description: 'Tell us about your business' },
  { title: 'Services', description: 'Add your services and pricing' },
  { title: 'AI Configuration', description: 'Customize your AI assistant' },
  { title: 'Go Live!', description: 'Get your widget embed code' },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    business_name: '',
    business_phone: '',
    business_email: '',
    business_address: '',
    ai_persona_name: '',
    ai_tone: 'professional',
    greeting_message: '',
    services: [{ name: '', price: '', duration_minutes: '' }],
  });

  const addService = () => {
    setForm(f => ({
      ...f,
      services: [...f.services, { name: '', price: '', duration_minutes: '' }],
    }));
  };

  const updateService = (index: number, field: string, value: string) => {
    setForm(f => ({
      ...f,
      services: f.services.map((s, i) => i === index ? { ...s, [field]: value } : s),
    }));
  };

  const saveAndNext = async () => {
    if (step === 0) {
      await api.patch('/tenant/', {
        business_name: form.business_name,
        business_phone: form.business_phone,
        business_email: form.business_email,
        business_address: form.business_address,
      });
    } else if (step === 1) {
      for (const svc of form.services) {
        if (svc.name.trim()) {
          await api.post('/services/', {
            name: svc.name,
            price: svc.price ? parseFloat(svc.price) : undefined,
            duration_minutes: svc.duration_minutes ? parseInt(svc.duration_minutes) : undefined,
          });
        }
      }
    } else if (step === 2) {
      await api.patch('/tenant/', {
        ai_persona_name: form.ai_persona_name,
        ai_tone: form.ai_tone,
        greeting_message: form.greeting_message,
      });
    }

    if (step < steps.length - 1) {
      setStep(s => s + 1);
    } else {
      router.push('/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        {/* Progress */}
        <div className="flex justify-between mb-8">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                i <= step ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-500'
              }`}>
                {i + 1}
              </div>
              {i < steps.length - 1 && (
                <div className={`w-12 h-0.5 ${i < step ? 'bg-indigo-600' : 'bg-slate-200'}`} />
              )}
            </div>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{steps[step].title}</CardTitle>
            <p className="text-sm text-slate-500">{steps[step].description}</p>
          </CardHeader>
          <CardContent className="space-y-4">
            {step === 0 && (
              <>
                <Input placeholder="Business Name" value={form.business_name} onChange={e => setForm(f => ({ ...f, business_name: e.target.value }))} />
                <Input placeholder="Phone" value={form.business_phone} onChange={e => setForm(f => ({ ...f, business_phone: e.target.value }))} />
                <Input placeholder="Email" type="email" value={form.business_email} onChange={e => setForm(f => ({ ...f, business_email: e.target.value }))} />
                <Textarea placeholder="Address" value={form.business_address} onChange={e => setForm(f => ({ ...f, business_address: e.target.value }))} rows={2} />
              </>
            )}

            {step === 1 && (
              <>
                {form.services.map((svc, i) => (
                  <div key={i} className="flex gap-2">
                    <Input placeholder="Service name" value={svc.name} onChange={e => updateService(i, 'name', e.target.value)} className="flex-1" />
                    <Input placeholder="Price" type="number" value={svc.price} onChange={e => updateService(i, 'price', e.target.value)} className="w-24" />
                    <Input placeholder="Min" type="number" value={svc.duration_minutes} onChange={e => updateService(i, 'duration_minutes', e.target.value)} className="w-20" />
                  </div>
                ))}
                <Button variant="outline" size="sm" onClick={addService}>+ Add Service</Button>
              </>
            )}

            {step === 2 && (
              <>
                <Input placeholder="AI Assistant Name (e.g., Dr. AI)" value={form.ai_persona_name} onChange={e => setForm(f => ({ ...f, ai_persona_name: e.target.value }))} />
                <select className="w-full border rounded-lg px-3 py-2 text-sm" value={form.ai_tone} onChange={e => setForm(f => ({ ...f, ai_tone: e.target.value }))}>
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="casual">Casual</option>
                </select>
                <Textarea placeholder="Greeting message for customers" value={form.greeting_message} onChange={e => setForm(f => ({ ...f, greeting_message: e.target.value }))} rows={3} />
              </>
            )}

            {step === 3 && (
              <div className="text-center py-6">
                <p className="text-5xl mb-4">🎉</p>
                <h3 className="text-xl font-bold">Your AI Agent is Ready!</h3>
                <p className="text-sm text-slate-500 mt-2 mb-6">
                  Add this code to your website to enable the chat widget.
                </p>
                <pre className="text-xs bg-slate-900 text-emerald-400 p-4 rounded-lg text-left overflow-x-auto">
{`<script
  src="https://your-domain.com/widget/vertex-widget.js"
  data-tenant-slug="your-slug"
></script>`}
                </pre>
              </div>
            )}

            <div className="flex justify-between pt-4">
              {step > 0 ? (
                <Button variant="outline" onClick={() => setStep(s => s - 1)}>Back</Button>
              ) : <div />}
              <Button onClick={saveAndNext}>
                {step === steps.length - 1 ? 'Go to Dashboard' : 'Next'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
