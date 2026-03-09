export function loginUrl(redirectPath = '/app'): string {
  return `/app/login?redirect_url=${encodeURIComponent(redirectPath)}`
}
