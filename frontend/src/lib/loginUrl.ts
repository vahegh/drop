export function loginUrl(redirectPath = '/'): string {
  return `/login?redirect_url=${encodeURIComponent(redirectPath)}`
}
