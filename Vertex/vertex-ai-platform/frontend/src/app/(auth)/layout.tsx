import { Sparkles } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-white to-primary-50 px-4">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex items-center justify-center h-11 w-11 rounded-xl bg-primary-600 shadow-lg">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <span className="text-2xl font-bold text-slate-900">Vertex AI</span>
      </div>
      <div className="w-full max-w-md">{children}</div>
      <p className="mt-8 text-sm text-slate-400">
        Powered by Vertex AI Platform
      </p>
    </div>
  );
}
