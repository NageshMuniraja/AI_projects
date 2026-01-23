import { create } from 'zustand'

interface QueryState {
  currentQuery: string | null
  results: any[] | null
  insights: any | null
  visualizations: any[] | null
  isLoading: boolean
  error: string | null
  setCurrentQuery: (query: string | null) => void
  setResults: (results: any[] | null) => void
  setInsights: (insights: any | null) => void
  setVisualizations: (visualizations: any[] | null) => void
  setLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
  clearQuery: () => void
}

export const useQueryStore = create<QueryState>((set) => ({
  currentQuery: null,
  results: null,
  insights: null,
  visualizations: null,
  isLoading: false,
  error: null,

  setCurrentQuery: (query) => set({ currentQuery: query }),
  setResults: (results) => set({ results }),
  setInsights: (insights) => set({ insights }),
  setVisualizations: (visualizations) => set({ visualizations }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  clearQuery: () =>
    set({
      currentQuery: null,
      results: null,
      insights: null,
      visualizations: null,
      error: null,
    }),
}))
