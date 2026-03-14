import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMe } from '../hooks/useMe'
import Layout from '../components/Layout'
import Section from '../components/Section'
import GoogleButton from '../components/GoogleButton'
import { sendMagicLink } from '../api/auth'

export default function Login() {
  const [searchParams] = useSearchParams()
  const redirectUrl = searchParams.get('redirect_url') ?? '/'
  const token = searchParams.get('token')
  const [tokenError, setTokenError] = useState<string | null>(null)

  const [email, setEmail] = useState('')
  const [emailSent, setEmailSent] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [emailSubmitting, setEmailSubmitting] = useState(false)

  const { data: me, isLoading } = useMe()

  document.title = 'Login | Drop Dead Disco'

  useEffect(() => {
    if (!token) return
    fetch(`/api/client/auth/magic-link/verify?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        if (res.ok || res.redirected) {
          window.location.href = redirectUrl
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

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEmailError('')
    setEmailSubmitting(true)
    try {
      await sendMagicLink(email)
      setEmailSent(true)
    } catch {
      setEmailError('Something went wrong. Please try again.')
    } finally {
      setEmailSubmitting(false)
    }
  }

  return (
    <Layout showFooter={false} showVideo>
      <div className="flex flex-col gap-4 flex-1 w-full max-w-96 items-center justify-center px-4 py-6">
        <Section className="pb-2">
          <div className="flex flex-col items-center gap-3 text-center w-full">
            <h1 className="text-4xl font-bold tracking-tight">Get in.</h1>
            <p className="text-sm text-white/55 leading-relaxed max-w-80">
              Sign up to see Drop from the inside.
            </p>
          </div>
        </Section>

        <Section>
          <GoogleButton text="Continue with Google" variant="primary" redirectUrl={redirectUrl} style={{ maxWidth: 'none' }} />
        </Section>

        <div className="flex items-center gap-3 w-full">
          <div className="flex-1 h-px bg-white/10" />
          <span className="text-xs text-white/30 uppercase tracking-widest">or</span>
          <div className="flex-1 h-px bg-white/10" />
        </div>

        <Section>
          {emailSent ? (
            <p className="text-sm text-white/60 text-center">Check your inbox — a magic link is on its way.</p>
          ) : (
            <form onSubmit={handleEmailSubmit} className="flex flex-col gap-3 w-full">
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={e => { setEmail(e.target.value); setEmailError('') }}
                className="drop-input"
                required
              />
              {emailError && <p className="text-xs text-center" style={{ color: 'var(--drop-negative)' }}>{emailError}</p>}
              <button type="submit" className="btn-outline" disabled={emailSubmitting}>
                {emailSubmitting ? 'Sending…' : 'Continue with email'}
              </button>
            </form>
          )}
        </Section>
      </div>
    </Layout>
  )
}
