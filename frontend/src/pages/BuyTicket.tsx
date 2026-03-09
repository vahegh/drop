import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useEvent } from '../hooks/useEvents'
import { useMe } from '../hooks/useMe'
import { initiatePayment } from '../api/payments'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { loginUrl } from '../lib/loginUrl'
import { gtagEvent } from '../lib/analytics'
import type { PaymentProvider } from '../types'

const PROVIDERS: { label: string; icon: string; value: PaymentProvider }[] = [
  { label: 'Card', icon: '/static/images/visa.svg', value: 'VPOS' },
  { label: 'MyAmeria', icon: '/static/images/myameria.png', value: 'MYAMERIA' },
  { label: 'IDRAM', icon: '/static/images/idram.png', value: 'IDRAM' },
  { label: 'Apple Pay', icon: '/static/images/applePay.svg', value: 'APPLEPAY' },
  { label: 'Google Pay', icon: '/static/images/google_pay.svg', value: 'GOOGLEPAY' },
]

export default function BuyTicket() {
  const [params] = useSearchParams()
  const eventId = params.get('event_id') ?? ''

  const { data: event, isLoading: eventLoading } = useEvent(eventId)
  const { data: me } = useMe()

  const [provider, setProvider] = useState<PaymentProvider>('VPOS')
  const [saveCard, setSaveCard] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!event || !me) return
    const now = new Date()
    const earlyBirdActive = event.early_bird_date ? new Date(event.early_bird_date) > now : false
    const price =
      me.status === 'member' ? event.member_ticket_price
      : earlyBirdActive && event.early_bird_price ? event.early_bird_price
      : event.general_admission_price
    gtagEvent('begin_checkout', { currency: 'AMD', value: price, items: [{ item_id: event.id, price }] })
  }, [event?.id, me?.id])

  if (!eventId) return (
    <Layout>
      <div className="flex items-center justify-center min-h-[60vh] text-white/45">No event selected.</div>
    </Layout>
  )

  if (eventLoading) return (
    <Layout>
      <div className="w-full max-w-96 h-32 rounded-3xl bg-white/5 animate-pulse mt-4" />
    </Layout>
  )

  if (!event) return (
    <Layout>
      <div className="flex items-center justify-center min-h-[60vh] text-white/45">Event not found.</div>
    </Layout>
  )

  if (!me) {
    return (
      <Layout heroBg={event.image_url}>
        <Section className="pt-8">
          <div className="drop-card p-6 flex flex-col gap-4 items-center text-center">
            <p className="text-sm text-white/70">
              Sign in to buy a ticket for <strong>{event.name}</strong>.
            </p>
            <a
              href={loginUrl(`/buy-ticket?event_id=${eventId}`)}
              className="btn-primary"
            >
              <img src="/static/images/google.svg" alt="" className="w-4 h-4 mr-2" />
              Sign in with Google
            </a>
          </div>
        </Section>
      </Layout>
    )
  }

  const now = new Date()
  const earlyBirdActive = event.early_bird_date ? new Date(event.early_bird_date) > now : false
  const price =
    me.status === 'member'
      ? event.member_ticket_price
      : earlyBirdActive && event.early_bird_price
      ? event.early_bird_price
      : event.general_admission_price

  const ticketLabel =
    me.status === 'member' ? 'Member Ticket' :
    earlyBirdActive ? 'Early Bird Ticket' : 'Standard Ticket'

  async function handlePay() {
    if (!me) return
    gtagEvent('add_to_cart', { currency: 'AMD', value: price, items: [{ item_id: event!.id, price }] })
    setLoading(true)
    setError(null)
    try {
      const res = await initiatePayment({
        event_id: event!.id,
        provider,
        attendees: [{ person_id: me.id }],
        save_card: saveCard,
      })
      window.location.href = res.redirect_url
    } catch {
      setError('Unable to start payment. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout heroBg={event.image_url}>
      <Section className="pt-4">
        <Link to={`/event/${event.id}`} className="text-sm text-white/45 hover:text-white/80 w-full">
          ← Back
        </Link>

        {/* Event summary */}
        <div
          className="drop-card p-4 flex gap-3 items-center"
          style={{ background: 'var(--drop-card)' }}
        >
          <img src={event.image_url} alt={event.name} className="w-16 h-16 rounded-2xl object-cover flex-none" />
          <div className="flex flex-col gap-0.5">
            <p className="font-semibold text-sm">{event.name}</p>
            <p className="text-xs text-white/45">{me.full_name}</p>
          </div>
        </div>

        {/* Price summary */}
        <div className="drop-card p-4 w-full flex flex-col gap-2">
          <div className="flex justify-between text-sm">
            <span className="text-white/70">1 × {ticketLabel}</span>
            <span className="font-semibold">{price.toLocaleString()} AMD</span>
          </div>
          <div className="h-px bg-white/10" />
          <div className="flex justify-between font-bold">
            <span>Total</span>
            <span>{price.toLocaleString()} AMD</span>
          </div>
        </div>
      </Section>

      {/* Payment method selector */}
      <Section title="Payment method">
        <div className="flex flex-col gap-2 w-full max-w-96">
          {PROVIDERS.map((p) => (
            <button
              key={p.value}
              onClick={() => setProvider(p.value)}
              className="w-full rounded-3xl px-4 py-3 flex items-center gap-3 transition-all text-sm font-medium"
              style={{
                background: provider === p.value ? 'rgba(255,255,255,0.12)' : 'var(--drop-card)',
                border: provider === p.value ? '1px solid rgba(255,255,255,0.35)' : '1px solid rgba(255,255,255,0.05)',
              }}
            >
              <img src={p.icon} alt={p.label} className="w-8 h-5 object-contain" />
              <span>{p.label}</span>
              {provider === p.value && (
                <span className="ml-auto text-xs text-white/45">Selected</span>
              )}
            </button>
          ))}
        </div>

        {provider === 'VPOS' && (
          <label className="flex items-center gap-2 text-sm text-white/55 cursor-pointer w-full">
            <input
              type="checkbox"
              checked={saveCard}
              onChange={(e) => setSaveCard(e.target.checked)}
              className="rounded accent-white"
            />
            Save card for future payments
          </label>
        )}
      </Section>

      {error && (
        <p className="text-sm w-full max-w-96" style={{ color: 'var(--drop-negative)' }}>
          {error}
        </p>
      )}

      {/* Pay button */}
      <div className="w-full max-w-96 pb-4">
        <button
          onClick={handlePay}
          disabled={loading}
          className="btn-primary h-14 text-base"
          style={{ maxWidth: '100%' }}
        >
          {loading ? 'Processing…' : `Pay ${price.toLocaleString()} AMD`}
        </button>
      </div>
    </Layout>
  )
}
