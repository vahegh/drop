import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Layout from '../components/Layout'
import Section from '../components/Section'
import client from '../api/client'

type State = 'idle' | 'unsubscribed' | 'deleted' | 'not_found' | 'error'

export default function Unsubscribe() {
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') ?? ''
  const [state, setState] = useState<State>('idle')
  const [loading, setLoading] = useState<'unsub' | 'delete' | null>(null)

  async function handleUnsubscribe() {
    setLoading('unsub')
    try {
      await client.post('/people/unsubscribe', { email })
      setState('unsubscribed')
    } catch {
      setState('error')
    } finally {
      setLoading(null)
    }
  }

  async function handleDelete() {
    if (!confirm('Are you sure you want to delete your account?')) return
    setLoading('delete')
    try {
      await client.delete('/people/by-email', { data: { email } })
      setState('deleted')
    } catch {
      setState('error')
    } finally {
      setLoading(null)
    }
  }

  if (!email) {
    return (
      <Layout showFooter>
        <Section className="pt-10">
          <p className="text-white/60 text-sm text-center">No email address provided.</p>
        </Section>
      </Layout>
    )
  }

  if (state === 'unsubscribed') {
    return (
      <Layout showFooter>
        <Section className="pt-10" title="You have unsubscribed from Drop Dead Disco." subtitle="We're sad to see you go." sep />
      </Layout>
    )
  }

  if (state === 'deleted') {
    return (
      <Layout showFooter>
        <Section className="pt-10" title="Your account will be deleted shortly." sep />
      </Layout>
    )
  }

  if (state === 'error') {
    return (
      <Layout showFooter>
        <Section className="pt-10">
          <p className="text-white/60 text-sm text-center">Something went wrong. Please try again.</p>
        </Section>
      </Layout>
    )
  }

  return (
    <Layout showFooter>
      <Section
        className="pt-10"
        title="Unsubscribe?"
        subtitle={`It may take a few days for you to stop receiving email from us at ${email}`}
        sep
      >
        <div className="flex flex-col gap-3 w-full max-w-96">
          <button
            onClick={handleUnsubscribe}
            disabled={loading !== null}
            className="btn-primary"
          >
            {loading === 'unsub' ? 'Unsubscribing…' : 'Unsubscribe'}
          </button>
          <button
            onClick={handleDelete}
            disabled={loading !== null}
            className="btn-outline"
            style={{ borderColor: 'rgba(251,44,54,0.5)', color: '#fb2c36' }}
          >
            {loading === 'delete' ? 'Deleting…' : 'Delete my account instead'}
          </button>
        </div>
      </Section>
    </Layout>
  )
}
