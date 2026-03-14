import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { signup } from '../api/auth'

export default function Signup() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const token = searchParams.get('token')
  const displayEmail = searchParams.get('email') ?? ''

  const [firstName, setFirstName] = useState(searchParams.get('first_name') ?? '')
  const [lastName, setLastName] = useState(searchParams.get('last_name') ?? '')
  const [instagram, setInstagram] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  document.title = 'Sign Up | Drop Dead Disco'

  if (!token) {
    navigate('/login')
    return <Layout showFooter showVideo />
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await signup({ token: token!, first_name: firstName, last_name: lastName, instagram_handle: instagram })
      window.location.href = '/'
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Layout showFooter showVideo>
      <Section className="pt-10">
        <h1 className="text-3xl font-bold text-center">Almost there</h1>
      </Section>

      <Section title="Complete your profile" subtitle={displayEmail} sep>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 w-full">
          <input
            className="drop-input"
            placeholder="First name"
            value={firstName}
            onChange={e => setFirstName(e.target.value)}
            autoComplete="given-name"
            required
          />
          <input
            className="drop-input"
            placeholder="Last name"
            value={lastName}
            onChange={e => setLastName(e.target.value)}
            autoComplete="family-name"
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
