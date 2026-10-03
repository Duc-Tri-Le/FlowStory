import { useContext } from 'react'
import { ModelsContext, type ModelsContextValue } from '../contexts/ModelsContext'

export { ModelsContext }
export type { ModelsContextValue }

export function useModelsContext(): ModelsContextValue {
  const ctx = useContext(ModelsContext)
  if (!ctx) {
    throw new Error('useModelsContext must be used within a ModelsProvider')
  }
  return ctx
}
