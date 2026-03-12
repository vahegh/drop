import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Layout from '../components/Layout'
import Section from '../components/Section'
import client from '../api/client'

type State = 'unsubscribed' | 'resubscribed'

export default function Unsubscribe() {
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') ?? ''
  useEffect(() => { document.title = 'Unsubscribe | Drop Dead Disco' }, [])

  const [state, setState] = useState<State>('unsubscribed')
  const [loading, setLoading] = useState(false)

  async function handleResubscribe() {
    setLoading(true)
    try { await client.post('/people/resubscribe', { email }) } catch {}
    setState('resubscribed')
    setLoading(false)
  }

  async function handleUnsubscribe() {
    setLoading(true)
    try { await client.post('/people/unsubscribe', { email }) } catch {}
    setState('unsubscribed')
    setLoading(false)
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

  if (state === 'resubscribed') {
    return (
      <Layout showFooter>
        <Section className="pt-10" title="You're back!" subtitle="You'll receive emails from Drop Dead Disco again." sep>
          <button onClick={handleUnsubscribe} disabled={loading} className="btn-outline text-sm text-white/40 border-white/10">
            {loading ? 'Processing…' : 'Unsubscribe again'}
          </button>
        </Section>
      </Layout>
    )
  }

  return (
    <Layout showFooter>
      <Section className="pt-10" title="You have unsubscribed from Drop Dead Disco." subtitle="We're sad to see you go." sep>
        <button onClick={handleResubscribe} disabled={loading} className="btn-primary">
          {loading ? 'Processing…' : 'Resubscribe'}
        </button>
      </Section>
    </Layout>
  )
}
