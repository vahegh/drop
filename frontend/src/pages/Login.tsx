import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMe } from '../hooks/useMe'
import Layout from '../components/Layout'
import Section from '../components/Section'
import LoginBlock from '../components/LoginBlock'

export default function Login() {
  const [searchParams] = useSearchParams()
  const redirectUrl = searchParams.get('redirect_url') ?? '/'
  const token = searchParams.get('token')
  const [tokenError, setTokenError] = useState<string | null>(null)

  const { data: me, isLoading } = useMe()

  document.title = 'Login | Drop Dead Disco'

  useEffect(() => {
    if (!token) return
    fetch(`/api/client/auth/magic-link/verify?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        if (res.ok || res.redirected) {
          const dest = new URL(res.url)
          window.location.href = dest.pathname.startsWith('/signup')
            ? dest.pathname + dest.search
            : redirectUrl
        } else {
          const body = await res.json().catch(() => ({}))
          setTokenError(body.detail ?? 'Invalid or expired link')
        }
      })
      .catch(() => setTokenError('Something went wrong'))
  }, [token, redirectUrl])

  useEffect(() => {
    if (!isLoading && me) {
      window.location.href = redirectUrl
    }
  }, [me, isLoading, redirectUrl])

  if (token) {
    return (
      <Layout showFooter={false} showVideo>
        <Section className="pt-10">
          {tokenError ? (
            <>
              <p className="text-center text-white/70">{tokenError}</p>
              <a href="/login" className="btn-primary" style={{ marginTop: '8px' }}>Try again</a>
            </>
          ) : (
            <p className="text-center text-white/70">Signing you in…</p>
          )}
        </Section>
      </Layout>
    )
  }

  return (
    <Layout showFooter={false} showVideo>
      <div className="flex flex-col gap-4 flex-1 w-full max-w-96 items-center justify-center px-4 py-6">
        <Section className="pb-2">
          <div className="flex flex-col items-center gap-1 text-center w-full">
            <h1 className="text-7xl font-semibold tracking-tight">Get in.</h1>
            <p className="text-sm text-white/55 leading-relaxed max-w-80">
              Experience the Drop from the inside.
            </p>
          </div>
        </Section>

        <LoginBlock redirectUrl={redirectUrl} />
      </div>
    </Layout>
  )
}
