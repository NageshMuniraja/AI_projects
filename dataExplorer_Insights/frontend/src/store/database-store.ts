import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Database {
  id: string
  name: string
  type: string
  connectionParams: any
}

interface DatabaseState {
  databases: Database[]
  selectedDatabase: Database | null
  connectionParams: any
  addDatabase: (database: Database) => void
  removeDatabase: (id: string) => void
  setSelectedDatabase: (database: Database | null) => void
  setConnectionParams: (params: any) => void
}

export const useDatabaseStore = create<DatabaseState>()(
  persist(
    (set) => ({
      databases: [],
      selectedDatabase: null,
      connectionParams: {},

      addDatabase: (database) =>
        set((state) => ({
          databases: [...state.databases, database],
        })),

      removeDatabase: (id) =>
        set((state) => ({
          databases: state.databases.filter((db) => db.id !== id),
        })),

      setSelectedDatabase: (database) =>
        set({
          selectedDatabase: database,
          connectionParams: database?.connectionParams || {},
        }),

      setConnectionParams: (params) =>
        set({ connectionParams: params }),
    }),
    {
      name: 'database-storage',
    }
  )
)
