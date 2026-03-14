import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GoogleButton from './GoogleButton'
import Section from './Section'
import { sendMagicLink } from '../api/auth'

interface LoginBlockProps {
  redirectUrl?: string
}

export default function LoginBlock({ redirectUrl = '/' }: LoginBlockProps) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [emailSent, setEmailSent] = useState(false)
  const [emailError, setEmailError] = useState('')
  const [emailSubmitting, setEmailSubmitting] = useState(false)

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEmailError('')
    setEmailSubmitting(true)
    try {
      const result = await sendMagicLink(email)
      if (result.status === 'new_user') {
        const params = new URLSearchParams({ token: result.token, email: result.email })
        navigate(`/signup?${params}`)
      } else {
        setEmailSent(true)
      }
    } catch {
      setEmailError('Something went wrong. Please try again.')
    } finally {
      setEmailSubmitting(false)
    }
  }

  return (
    <>
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
          <p className="text-sm text-white/60 text-center">Check your inbox - a magic link is on its way.</p>
        ) : (
          <form onSubmit={handleEmailSubmit} className="flex flex-col gap-3 w-full">
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={e => { setEmail(e.target.value); setEmailError('') }}
              className="drop-input"
              autoComplete="email"
              required
            />
            {emailError && <p className="text-xs text-center" style={{ color: 'var(--drop-negative)' }}>{emailError}</p>}
            <button type="submit" className="btn-outline" disabled={emailSubmitting}>
              {emailSubmitting ? 'Sending…' : 'Continue with email'}
            </button>
          </form>
        )}
      </Section>
    </>
  )
}
