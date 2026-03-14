import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { signupWithGoogle } from '../api/auth'

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
  const navigate = useNavigate()

  const [pending, setPending] = useState<PendingSignup | null>(null)
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [instagram, setInstagram] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  document.title = 'Sign Up | Drop Dead Disco'

  useEffect(() => {
    const raw = sessionStorage.getItem('drop_signup')
    if (!raw) {
      navigate('/login')
      return
    }
    const data: PendingSignup = JSON.parse(raw)
    setPending(data)
    setFirstName(data.first_name)
    setLastName(data.last_name)
  }, [navigate])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!pending) return
    setError('')
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
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!pending) return <Layout showFooter showVideo />

  return (
    <Layout showFooter showVideo>
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
          {error && <p className="text-sm text-red-400 text-center">{error}</p>}
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit'}
          </button>
        </form>
      </Section>
    </Layout>
  )
}
