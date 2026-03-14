import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Layout from '../components/Layout'
import Section from '../components/Section'
import GoogleButton from '../components/GoogleButton'
import { signupWithGoogle, sendMagicLink } from '../api/auth'

interface PendingSignup {
  access_token: string
  email: string
  first_name: string
  last_name: string
  avatar_url: string | null
}

export default function Signup() {
  const [searchParams] = useSearchParams()
  const redirectUrl = searchParams.get('redirect_url') ?? '/'

  const [pending, setPending] = useState<PendingSignup | null>(null)
  const [pendingChecked, setPendingChecked] = useState(false)

  // Profile completion form state
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [instagram, setInstagram] = useState('')
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Email magic link state
  const [email, setEmail] = useState('')
  const [emailSent, setEmailSent] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [emailSubmitting, setEmailSubmitting] = useState(false)

  document.title = 'Sign Up | Drop Dead Disco'

  useEffect(() => {
    const raw = sessionStorage.getItem('drop_signup')
    if (raw) {
      const data: PendingSignup = JSON.parse(raw)
      setPending(data)
      setFirstName(data.first_name)
      setLastName(data.last_name)
    }
    setPendingChecked(true)
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!pending) return
    setFormError('')
    setSubmitting(true)
    try {
      await signupWithGoogle({
        access_token: pending.access_token,
        first_name: firstName,
        last_name: lastName,
        instagram_handle: instagram,
      })
      sessionStorage.removeItem('drop_signup')
      window.location.href = redirectUrl
    } catch {
      setFormError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
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

  if (!pendingChecked) return <Layout showFooter />

  // Profile completion after Google OAuth
  if (pending) {
    return (
      <Layout showFooter>
        <Section className="pt-10">
          <h1 className="text-3xl font-bold text-center">Almost there</h1>
        </Section>

        <Section title="Complete your profile" subtitle={pending.email} sep>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3 w-full">
            <input
              className="drop-input"
              placeholder="First name"
              value={firstName}
              onChange={e => setFirstName(e.target.value)}
              required
            />
            <input
              className="drop-input"
              placeholder="Last name"
              value={lastName}
              onChange={e => setLastName(e.target.value)}
              required
            />
            <input
              className="drop-input"
              placeholder="Instagram handle (e.g. @username)"
              value={instagram}
              onChange={e => setInstagram(e.target.value)}
              required
            />
            {formError && <p className="text-sm text-red-400 text-center">{formError}</p>}
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit'}
            </button>
          </form>
        </Section>
      </Layout>
    )
  }

  // Main signup page
  return (
    <Layout showFooter>
      <Section className="pt-10">
        <h1 className="text-3xl font-bold text-center">Apply for access</h1>
      </Section>

      <Section title="Sign in with Google" subtitle="Fastest way to get started" sep>
        <GoogleButton text="Continue with Google" variant="primary" redirectUrl={redirectUrl} style={{ maxWidth: 'none' }} />
      </Section>

      <Section title="Or use your email" subtitle="We'll send you a magic link" sep>
        {emailSent ? (
          <p className="text-sm text-white/60 text-center">Check your inbox — a magic link is on its way.</p>
        ) : (
          <form onSubmit={handleEmailSubmit} className="flex flex-col gap-3 w-full">
            <input
              className="drop-input"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
            {emailError && <p className="text-sm text-red-400 text-center">{emailError}</p>}
            <button type="submit" className="btn-primary" disabled={emailSubmitting}>
              {emailSubmitting ? 'Sending…' : 'Continue with email'}
            </button>
          </form>
        )}
      </Section>
    </Layout>
  )
}
