declare function gtag(...args: unknown[]): void

export function gtagEvent(eventName: string, params: Record<string, unknown> = {}) {
  if (typeof gtag === 'function') {
    gtag('event', eventName, params)
  }
}
