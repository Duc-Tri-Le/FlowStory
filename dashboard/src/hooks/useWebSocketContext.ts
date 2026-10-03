import { useContext } from 'react'
import { WebSocketContext, type WebSocketContextValue, type WorkerSnapshot } from '../contexts/WebSocketContext'

export type { WebSocketContextValue, WorkerSnapshot }

export function useWebSocketContext(): WebSocketContextValue {
  const ctx = useContext(WebSocketContext)
  if (!ctx) throw new Error('useWebSocketContext must be used within a WebSocketProvider')
  return ctx
}
