import { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMe } from '../hooks/useMe'
import Layout from '../components/Layout'
import Section from '../components/Section'
import GoogleButton from '../components/GoogleButton'
import { sendMagicLink } from '../api/auth'

function MagicLinkDialog({ onClose }: { onClose: () => void }) {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const overlayRef = useRef<HTMLDivElement>(null)

  function validateEmail(v: string) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
  }

  async function handleSend() {
    if (!validateEmail(email)) {
      setError('Enter a valid email')
      return
    }
    setLoading(true)
    await sendMagicLink(email)
    setLoading(false)
    setSent(true)
  }

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)' }}
      onClick={(e) => { if (e.target === overlayRef.current) onClose() }}
    >
      <div
        className="w-full max-w-96 rounded-3xl p-6 flex flex-col gap-4"
        style={{ background: 'var(--drop-card)' }}
      >
        {!sent ? (
          <Section title="Log in with email link" subtitle="If you are already registered, you can log in using a link sent to your email.">
            <input
              type="email"
              placeholder="Verified email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError('') }}
              className="w-full max-w-96 h-10 rounded-xl px-3 text-sm outline outline-1 outline-white/20 bg-transparent focus:outline-accent"
              style={{ fontFamily: 'Montserrat' }}
            />
            {error && <p className="text-xs" style={{ color: 'var(--drop-negative)' }}>{error}</p>}
            <button className="btn-primary" disabled={loading} onClick={handleSend}>
              {loading ? 'Sending…' : 'Send link'}
            </button>
          </Section>
        ) : (
          <Section title="Check your email!" subtitle="If verified, you'll receive a link to log in.">
            <a
              href="https://mail.google.com"
              
              rel="noopener noreferrer"
              className="btn-primary"
              style={{ gap: '8px' }}
            >
              <img src="/static/images/gmail.svg" alt="" style={{ width: '18px', height: '18px' }} />
              Open Gmail
            </a>
          </Section>
        )}
      </div>
    </div>
  )
}

export default function Login() {
  const [searchParams] = useSearchParams()
  const redirectUrl = searchParams.get('redirect_url') ?? '/'
  const token = searchParams.get('token')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [tokenError, setTokenError] = useState<string | null>(null)

  const { data: me, isLoading } = useMe()

  document.title = 'Login | Drop Dead Disco'

  // Handle magic link token in URL
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
      <Layout showFooter={false}>
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
    <Layout showFooter={false}>
      {dialogOpen && <MagicLinkDialog onClose={() => setDialogOpen(false)} />}

      <div
        className="flex flex-col gap-4 w-full max-w-96 items-center justify-center rounded-3xl px-4 py-6"
        style={{ background: 'transparent' }}
      >
        <img src="/static/images/logo_gray.png" alt="Drop Dead Disco" className="w-24 h-12 object-contain" />

        <Section title="Sign up" subtitle="You must be verified to purchase tickets.">
          <GoogleButton text="Sign up with Google" variant="primary" redirectUrl={redirectUrl} />
        </Section>

        <div className="w-full max-w-96 h-px" style={{ background: 'rgba(255,255,255,0.1)' }} />

        <Section title="Log In" subtitle="Log in using your verified Google account or a link sent to your email.">
          <GoogleButton text="Log in with Google" variant="outline" redirectUrl={redirectUrl} />
          <span className="text-sm text-white/45">OR</span>
          <button className="btn-outline" onClick={() => setDialogOpen(true)}>
            Log in with email link
          </button>
        </Section>
      </div>
    </Layout>
  )
}
