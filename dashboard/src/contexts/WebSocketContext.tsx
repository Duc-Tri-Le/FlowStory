import { createContext, useCallback, useState, type ReactNode } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import type { WSEvent } from '../types'

export interface WorkerSnapshot {
  active: number
  slots: number
}

export interface WebSocketContextValue {
  isConnected: boolean
  lastEvent: WSEvent | null
  /** Rolling log of real event_bus events (request_update, worker_tick, urls_refreshed), newest first. */
  events: WSEvent[]
  /** From the initial /ws/dashboard snapshot message: real active/slots worker counts. */
  worker: WorkerSnapshot | null
}

export const WebSocketContext = createContext<WebSocketContextValue | null>(null)

const MAX_EVENTS = 200

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [events, setEvents] = useState<WSEvent[]>([])
  const [worker, setWorker] = useState<WorkerSnapshot | null>(null)

  const handleMessage = useCallback((event: WSEvent) => {
    // The initial snapshot and keepalive ping are sent directly by the WS endpoint (agent/main.py),
    // not through event_bus, so they don't share WSEvent's {type, data, timestamp} shape.
    const raw = event as unknown as { type: string; worker?: WorkerSnapshot }
    if (raw.type === 'snapshot') {
      if (raw.worker) setWorker(raw.worker)
      return
    }
    if (raw.type === 'ping') return
    setEvents(prev => [event, ...prev].slice(0, MAX_EVENTS))
  }, [])

  const { isConnected, lastEvent } = useWebSocket(handleMessage)

  return (
    <WebSocketContext.Provider value={{ isConnected, lastEvent, events, worker }}>
      {children}
    </WebSocketContext.Provider>
  )
}
