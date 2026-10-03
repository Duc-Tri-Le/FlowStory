const BASE = ''  // same origin, proxied by Vite in dev

export async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText)
    throw new Error(`API ${res.status}: ${err}`)
  }
  return res.json()
}

export function getProxyDownloadUrl(url: string, filename: string = 'image.jpg'): string {
  return `/api/proxy/download?url=${encodeURIComponent(url)}&filename=${encodeURIComponent(filename)}`
}

export function downloadViaProxy(url: string, filename: string = 'image.jpg'): void {
  const link = document.createElement('a')
  link.href = getProxyDownloadUrl(url, filename)
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export async function patchAPI<T>(path: string, body: Record<string, unknown>): Promise<T> {
  return fetchAPI<T>(path, { method: 'PATCH', body: JSON.stringify(body) })
}

export async function postAPI<T = unknown>(path: string, body: unknown): Promise<T> {
  return fetchAPI<T>(path, { method: 'POST', body: JSON.stringify(body) })
}
