import { createContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { fetchAPI, patchAPI } from '../api/client'
import type { ModelsConfig } from '../types'

export interface ModelsContextValue {
  models: ModelsConfig | null
  loading: boolean
  error: string | null
  refreshModels: () => Promise<void>
  updateModels: (patch: Partial<ModelsConfig>) => Promise<boolean>
}

export const ModelsContext = createContext<ModelsContextValue | undefined>(undefined)

export function ModelsProvider({ children }: { children: ReactNode }) {
  const [models, setModels] = useState<ModelsConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refreshModels = useCallback(async () => {
    try {
      const data = await fetchAPI<ModelsConfig>('/api/models')
      setModels(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshModels()
  }, [refreshModels])

  const updateModels = useCallback(async (patch: Partial<ModelsConfig>): Promise<boolean> => {
    try {
      const res = await patchAPI<{ status: string; models: ModelsConfig }>('/api/models', patch)
      if (res?.models) {
        setModels(res.models)
      } else {
        await refreshModels()
      }
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      return false
    }
  }, [refreshModels])

  return (
    <ModelsContext.Provider value={{ models, loading, error, refreshModels, updateModels }}>
      {children}
    </ModelsContext.Provider>
  )
}
