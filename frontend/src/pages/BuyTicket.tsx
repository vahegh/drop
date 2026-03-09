import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useEvent } from '../hooks/useEvents'
import { useMe } from '../hooks/useMe'
import { initiatePayment } from '../api/payments'
import { createPerson, checkEmail } from '../api/people'
import Layout from '../components/Layout'
import Section from '../components/Section'
import GoogleButton from '../components/GoogleButton'
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
  const { data: me, isLoading: meLoading } = useMe()

  const [provider, setProvider] = useState<PaymentProvider>('VPOS')
  const [saveCard, setSaveCard] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Guest checkout state
  const [guestStep, setGuestStep] = useState<'form' | 'confirm'>('form')
  const [guestFirstName, setGuestFirstName] = useState('')
  const [guestLastName, setGuestLastName] = useState('')
  const [guestEmail, setGuestEmail] = useState('')
  const [guestInstagram, setGuestInstagram] = useState('')
  const [guestFormError, setGuestFormError] = useState<string | null>(null)

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
      <div className="w-full max-w-96 mt-4 space-y-3">
        <div className="skeleton h-20 w-full rounded-3xl" />
        <div className="skeleton h-6 w-3/4" />
        <div className="skeleton h-4 w-1/2" />
      </div>
    </Layout>
  )

  if (!event) return (
    <Layout>
      <div className="flex items-center justify-center min-h-[60vh] text-white/45">Event not found.</div>
    </Layout>
  )

  if (meLoading) return (
    <Layout heroBg={event.image_url}>
      <div className="w-full max-w-96 mt-4 space-y-4">
        <div className="skeleton h-24 w-full rounded-3xl" />
        <div className="skeleton h-12 w-full rounded-xl" />
        <div className="skeleton h-12 w-full rounded-xl" />
        <div className="skeleton h-12 w-full rounded-xl" />
        <div className="skeleton h-14 w-full rounded-xl" />
        <div className="skeleton h-12 w-full rounded-xl" />
      </div>
    </Layout>
  )

  if (!me) {
    const guestPrice = (() => {
      const now = new Date()
      const earlyBirdActive = event.early_bird_date ? new Date(event.early_bird_date) > now : false
      return earlyBirdActive && event.early_bird_price ? event.early_bird_price : event.general_admission_price
    })()

    function validateGuestForm() {
      if (!guestFirstName.trim()) return 'First name is required.'
      if (!guestLastName.trim()) return 'Last name is required.'
      if (!guestEmail.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(guestEmail)) return 'A valid email is required.'
      const ig = guestInstagram.replace(/^@/, '').trim()
      if (!ig) return 'Instagram handle is required.'
      return null
    }

    function handleGuestContinue() {
      const err = validateGuestForm()
      if (err) { setGuestFormError(err); return }
      setGuestFormError(null)
      setGuestStep('confirm')
    }

    async function handleGuestPay() {
      setLoading(true)
      setError(null)
      try {
        const ig = guestInstagram.replace(/^@/, '').trim()
        const { exists } = await checkEmail(guestEmail)
        if (exists) {
          setError('This email is already registered. Please sign in with Google to continue.')
          setLoading(false)
          return
        }
        if (!event) return
        const person = await createPerson({
          first_name: guestFirstName.trim(),
          last_name: guestLastName.trim(),
          email: guestEmail.trim(),
          instagram_handle: ig,
        })
        gtagEvent('begin_checkout', { currency: 'AMD', value: guestPrice, items: [{ item_id: event.id, price: guestPrice }] })
        const res = await initiatePayment({
          event_id: event.id,
          provider,
          attendees: [{ person_id: person.id }],
          save_card: saveCard,
        })
        window.location.href = res.redirect_url
      } catch {
        setError('Something went wrong. Please try again.')
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
          <div className="drop-card p-4 flex gap-3 items-center">
            <img src={event.image_url} alt={event.name} className="w-16 h-16 rounded-2xl object-cover flex-none" />
            <div className="flex flex-col gap-0.5">
              <p className="font-semibold text-sm">{event.name}</p>
              <p className="text-xs text-white/45">Standard Ticket - {guestPrice.toLocaleString()} AMD</p>
            </div>
          </div>

        </Section>

        <Section title="New here?" subtitle="Enter your details below to continue as a guest.">
          {guestStep === 'form' ? (
            <div className="drop-card p-5 flex flex-col gap-4 w-full">
              <p className="text-sm font-semibold">Your details</p>
              <div className="flex gap-3">
                <div className="flex flex-col gap-1 flex-1 min-w-0">
                  <label className="text-xs text-white/45">First name</label>
                  <input
                    type="text"
                    value={guestFirstName}
                    onChange={e => setGuestFirstName(e.target.value)}
                    placeholder="Alex"
                    className="w-full bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20"
                  />
                </div>
                <div className="flex flex-col gap-1 flex-1 min-w-0">
                  <label className="text-xs text-white/45">Last name</label>
                  <input
                    type="text"
                    value={guestLastName}
                    onChange={e => setGuestLastName(e.target.value)}
                    placeholder="Smith"
                    className="w-full bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-white/45">Email</label>
                <input
                  type="email"
                  value={guestEmail}
                  onChange={e => setGuestEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-white/45">Instagram</label>
                <input
                  type="text"
                  value={guestInstagram}
                  onChange={e => setGuestInstagram(e.target.value)}
                  placeholder="@yourhandle"
                  className="bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20"
                />
              </div>
              {guestFormError && (
                <p className="text-xs" style={{ color: 'var(--drop-negative)' }}>{guestFormError}</p>
              )}
              <button onClick={handleGuestContinue} className="btn-primary h-11 text-sm mt-1">
                Continue
              </button>
            </div>
          ) : (
            <div className="drop-card p-5 flex flex-col gap-4 w-full">
              <div className="flex items-center gap-2">
                <button onClick={() => setGuestStep('form')} className="text-xs text-white/45 hover:text-white/80">
                  ← Edit
                </button>
                <p className="text-sm font-semibold">Confirm your details</p>
              </div>
              <div className="flex flex-col gap-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-white/45">Name</span>
                  <span>{guestFirstName.trim()} {guestLastName.trim()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/45">Email</span>
                  <span>{guestEmail.trim()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/45">Instagram</span>
                  <span>@{guestInstagram.replace(/^@/, '').trim()}</span>
                </div>
                <div className="h-px bg-white/10" />
                <div className="flex justify-between font-bold">
                  <span>Total</span>
                  <span>{guestPrice.toLocaleString()} AMD</span>
                </div>
              </div>
              {error && (
                <p className="text-xs" style={{ color: 'var(--drop-negative)' }}>{error}</p>
              )}
            </div>
          )}
        </Section>

        {guestStep === 'confirm' && (
          <>
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

            <div className="w-full max-w-96 pb-4">
              <button
                onClick={handleGuestPay}
                disabled={loading}
                className="btn-primary h-14 text-base"
                style={{ maxWidth: '100%' }}
              >
                {loading ? 'Processing…' : `Pay ${guestPrice.toLocaleString()} AMD`}
              </button>
            </div>
          </>
        )}

        <div className="w-full max-w-96 flex items-center gap-3 text-white/20 text-xs px-1">
          <div className="flex-1 h-px bg-white/10" />
          or
          <div className="flex-1 h-px bg-white/10" />
        </div>
        <div className="w-full max-w-96 pb-6">
          <GoogleButton text="Sign in with Google" variant="outline" redirectUrl={`/buy-ticket?event_id=${eventId}`} />
        </div>
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
