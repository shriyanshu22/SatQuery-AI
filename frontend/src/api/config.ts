const STORAGE_KEY = 'geolens_api_base_url'
const DEFAULT_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return saved.replace(/\/+$/, '')
  }
  return DEFAULT_URL.replace(/\/+$/, '')
}

export function setApiBaseUrl(url: string): void {
  if (typeof window !== 'undefined') {
    const sanitized = url.trim().replace(/\/+$/, '')
    if (sanitized) {
      localStorage.setItem(STORAGE_KEY, sanitized)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }
}

export function resetApiBaseUrl(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(STORAGE_KEY)
  }
}
