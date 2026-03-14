"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { UserPlus, Loader2 } from "lucide-react";

const industries = [
  { value: "healthcare", label: "Healthcare" },
  { value: "dental", label: "Dental" },
  { value: "legal", label: "Legal Services" },
  { value: "real_estate", label: "Real Estate" },
  { value: "automotive", label: "Automotive" },
  { value: "hospitality", label: "Hospitality" },
  { value: "education", label: "Education" },
  { value: "fitness", label: "Fitness & Wellness" },
  { value: "salon", label: "Salon & Beauty" },
  { value: "restaurant", label: "Restaurant" },
  { value: "retail", label: "Retail" },
  { value: "professional_services", label: "Professional Services" },
  { value: "other", label: "Other" },
];

export default function SignupPage() {
  const [fullName, setFullName] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [industry, setIndustry] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { signup, isLoading, error, clearError } = useAuthStore();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await signup({
        full_name: fullName,
        business_name: businessName,
        industry,
        email,
        password,
      });
      router.push("/dashboard");
    } catch {
      // Error is handled by the store
    }
  };

  return (
    <Card className="shadow-xl border-slate-200/60">
      <CardHeader className="text-center pb-2">
        <CardTitle className="text-2xl">Create your account</CardTitle>
        <CardDescription>
          Get started with Vertex AI in minutes
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4 pt-4">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {error}
            </div>
          )}
          <Input
            id="full_name"
            label="Full name"
            type="text"
            placeholder="John Doe"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
          <Input
            id="business_name"
            label="Business name"
            type="text"
            placeholder="Acme Inc."
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
            required
          />
          <Select
            id="industry"
            label="Industry"
            options={industries}
            placeholder="Select your industry"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            required
          />
          <Input
            id="email"
            label="Email address"
            type="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <Input
            id="password"
            label="Password"
            type="password"
            placeholder="Minimum 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
          />
        </CardContent>
        <CardFooter className="flex-col gap-4">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <UserPlus className="h-4 w-4" />
            )}
            {isLoading ? "Creating account..." : "Create account"}
          </Button>
          <p className="text-sm text-slate-500 text-center">
            Already have an account?{" "}
            <Link
              href="/login"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
