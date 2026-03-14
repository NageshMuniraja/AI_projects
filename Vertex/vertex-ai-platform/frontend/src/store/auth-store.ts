"use client";

import { create } from "zustand";
import type { User, Tenant } from "@/types";
import api from "@/lib/api";

interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  signup: (data: {
    business_name: string;
    industry: string;
    email: string;
    password: string;
    full_name: string;
  }) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  tenant: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.login({ email, password });
      const user = await api.getMe();
      const tenant = await api.getTenant();
      set({ user, tenant, isAuthenticated: true, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  signup: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await api.signup(data);
      if (typeof window !== "undefined") {
        localStorage.setItem("access_token", tokens.access_token);
        localStorage.setItem("refresh_token", tokens.refresh_token);
      }
      const user = await api.getMe();
      const tenant = await api.getTenant();
      set({ user, tenant, isAuthenticated: true, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Signup failed";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
    set({ user: null, tenant: null, isAuthenticated: false });
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  },

  loadUser: async () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("access_token");
    if (!token) {
      set({ isAuthenticated: false, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const user = await api.getMe();
      const tenant = await api.getTenant();
      set({ user, tenant, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      set({ isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
