declare function gtag(...args: unknown[]): void

export function gtagConfig(params: Record<string, unknown> = {}) {
  if (typeof gtag === 'function') {
    gtag('config', 'G-152G4X4VLJ', params)
  }
}

export function gtagEvent(eventName: string, params: Record<string, unknown> = {}) {
  if (typeof gtag === 'function') {
    gtag('event', eventName, params)
  }
}
