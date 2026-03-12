import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useEvent } from '../hooks/useEvents'
import { useMe } from '../hooks/useMe'
import { initiatePayment } from '../api/payments'
import { createPerson, checkEmail } from '../api/people'
import Layout from '../components/Layout'
import Section from '../components/Section'
import GoogleButton from '../components/GoogleButton'
import PaymentProviderSelector from '../components/PaymentProviderSelector'
import { gtagEvent } from '../lib/analytics'
import { isIOS, isAndroid } from '../lib/ua'
import type { PaymentProvider, TicketTierResponse, PersonStatus, CheckEmailResponse } from '../types'

function resolveClientTier(tiers: TicketTierResponse[], status?: PersonStatus): TicketTierResponse | null {
  const now = new Date()
  for (const t of tiers) {
    if (!t.is_active) continue
    if (t.required_person_status && t.required_person_status !== status) continue
    if (t.available_from && now < new Date(t.available_from)) continue
    if (t.available_until && now >= new Date(t.available_until)) continue
    return t
  }
  return null
}

function resolvePrice(tiers: TicketTierResponse[], status?: PersonStatus): number {
  return resolveClientTier(tiers, status)?.price ?? 0
}

type AdditionalAttendee =
  | { kind: 'existing'; id: string; full_name: string; status: PersonStatus }
  | { kind: 'new'; email: string; first_name: string; last_name: string; instagram: string }

export default function BuyTicket() {
  const [params] = useSearchParams()
  const eventId = params.get('event_id') ?? ''

  const { data: event, isLoading: eventLoading } = useEvent(eventId)
  const { data: me, isLoading: meLoading } = useMe()

  const [provider, setProvider] = useState<PaymentProvider>(
    isIOS ? 'APPLEPAY' : isAndroid ? 'GOOGLEPAY' : 'VPOS'
  )
  const [saveCard, setSaveCard] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dismissTicketNotice, setDismissTicketNotice] = useState(false)

  // Guest checkout state
  const [guestStep, setGuestStep] = useState<'email' | 'details' | 'confirm'>('email')
  const [guestFirstName, setGuestFirstName] = useState('')
  const [guestLastName, setGuestLastName] = useState('')
  const [guestEmail, setGuestEmail] = useState('')
  const [guestInstagram, setGuestInstagram] = useState('')
  const [guestFormError, setGuestFormError] = useState<string | null>(null)
  const [guestEmailChecking, setGuestEmailChecking] = useState(false)
  const [guestLoginHint, setGuestLoginHint] = useState<string | null>(null)

  // Multi-attendee state (logged-in only)
  const [additionalAttendees, setAdditionalAttendees] = useState<AdditionalAttendee[]>([])
  const [addEmail, setAddEmail] = useState('')
  const [lookupResult, setLookupResult] = useState<CheckEmailResponse | null>(null)
  const [addStep, setAddStep] = useState<'idle' | 'found' | 'create'>('idle')
  const [addSearching, setAddSearching] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)
  const [newFirst, setNewFirst] = useState('')
  const [newLast, setNewLast] = useState('')
  const [newInstagram, setNewInstagram] = useState('')

  useEffect(() => {
    if (!event || !me) return
    const price = resolvePrice(event.tiers, me.status)
    gtagEvent('begin_checkout', { currency: 'AMD', value: price, items: [{ item_id: event.id, price }] })
  }, [event?.id, me?.id])

  useEffect(() => {
    if (!me || isIOS || isAndroid) return
    const b = me.card_bindings.find(b => b.is_active)
    if (b) setProvider('BINDING')
  }, [me?.id])

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

  const tiers = event.tiers
  const guestPrice = resolvePrice(tiers, 'pending')

  // Logged-in derived values
  const activeBinding = me?.card_bindings.find(b => b.is_active) ?? null
  const myTier = me ? resolveClientTier(tiers, me.status) : null
  const myPrice = me ? resolvePrice(tiers, me.status) : 0
  const ticketLabel = myTier?.name ?? (me?.status === 'member' ? 'Member Ticket' : 'Standard Ticket')
  const alreadyHasTicket = me?.event_tickets.some(t => t.event_id === eventId) ?? false
  const additionalTotal = additionalAttendees.reduce((sum, a) => {
    const status: PersonStatus = a.kind === 'existing' ? a.status : 'pending'
    return sum + resolvePrice(tiers, status)
  }, 0)
  const totalPrice = myPrice + additionalTotal

  const showPayment = me != null || guestStep === 'confirm'

  // Guest handlers
  async function handleGuestEmailContinue() {
    if (!guestEmail.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(guestEmail)) {
      setGuestFormError('A valid email is required.')
      return
    }
    setGuestFormError(null)
    setGuestEmailChecking(true)
    try {
      const result = await checkEmail(guestEmail.trim())
      if (result.exists) {
        if (result.status === 'rejected') {
          setGuestFormError('This account has been rejected. Please contact us for help.')
        } else {
          setGuestLoginHint(guestEmail.trim())
        }
      } else {
        setGuestStep('details')
      }
    } catch {
      setGuestFormError('Something went wrong. Please try again.')
    } finally {
      setGuestEmailChecking(false)
    }
  }

  function validateGuestDetails() {
    if (!guestFirstName.trim()) return 'First name is required.'
    if (!guestLastName.trim()) return 'Last name is required.'
    const ig = guestInstagram.replace(/^@/, '').trim()
    if (!ig) return 'Instagram handle is required.'
    return null
  }

  function handleGuestContinue() {
    const err = validateGuestDetails()
    if (err) { setGuestFormError(err); return }
    setGuestFormError(null)
    setGuestStep('confirm')
  }

  async function handleGuestPay() {
    if (!event) return
    setLoading(true)
    setError(null)
    try {
      const ig = guestInstagram.replace(/^@/, '').trim()
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

  // Logged-in handlers
  async function handleSearchAttendee() {
    const email = addEmail.trim()
    if (!email) return
    if (me && email === me.email) { setAddError("That's your own email - already included."); return }
    if (additionalAttendees.some(a => a.kind === 'new' && a.email === email)) { setAddError('This person is already added.'); return }
    setAddError(null)
    setAddSearching(true)
    setLookupResult(null)
    try {
      const result = await checkEmail(email)
      if (result.exists) {
        if (me && result.id === me.id) { setAddError("That's you - already included."); return }
        if (additionalAttendees.some(a => a.kind === 'existing' && a.id === result.id)) { setAddError('This person is already added.'); return }
      }
      setLookupResult(result)
      setAddStep(result.exists ? 'found' : 'create')
      if (!result.exists) {
        setNewFirst('')
        setNewLast('')
        setNewInstagram('')
      }
    } catch {
      // ignore
    } finally {
      setAddSearching(false)
    }
  }

  function handleAddExisting() {
    if (!lookupResult?.id || !lookupResult.full_name) return
    setAdditionalAttendees(prev => [...prev, {
      kind: 'existing',
      id: lookupResult.id!,
      full_name: lookupResult.full_name!,
      status: lookupResult.status!,
    }])
    resetAddForm()
  }

  function handleAddNew() {
    if (!newFirst.trim() || !newLast.trim() || !addEmail.trim()) return
    const email = addEmail.trim()
    setAdditionalAttendees(prev => [...prev, {
      kind: 'new',
      email,
      first_name: newFirst.trim(),
      last_name: newLast.trim(),
      instagram: newInstagram.replace(/^@/, '').trim(),
    }])
    resetAddForm()
  }

  function resetAddForm() {
    setAddEmail('')
    setLookupResult(null)
    setAddStep('idle')
    setNewFirst('')
    setNewLast('')
    setNewInstagram('')
    setAddError(null)
  }

  async function handlePay() {
    if (!me || !event) return
    gtagEvent('add_to_cart', { currency: 'AMD', value: totalPrice, items: [{ item_id: event.id, price: totalPrice }] })
    setLoading(true)
    setError(null)
    try {
      const resolvedAttendees: { person_id: string }[] = [{ person_id: me.id }]
      for (const a of additionalAttendees) {
        if (a.kind === 'existing') {
          resolvedAttendees.push({ person_id: a.id })
        } else {
          const created = await createPerson({
            first_name: a.first_name,
            last_name: a.last_name,
            email: a.email,
            instagram_handle: a.instagram || 'n/a',
          })
          resolvedAttendees.push({ person_id: created.id })
        }
      }
      const res = await initiatePayment({
        event_id: event.id,
        provider,
        attendees: resolvedAttendees,
        save_card: saveCard,
        ...(provider === 'BINDING' && activeBinding ? { card_id: activeBinding.id } : {}),
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
        <div className="drop-card p-4 flex gap-3 items-center">
          <img src={event.image_url} alt={event.name} className="w-16 h-16 rounded-2xl object-cover flex-none" />
          <div className="flex flex-col gap-0.5">
            <p className="font-semibold text-sm">{event.name}</p>
            {me ? (
              <p className="text-xs text-white/45">{me.full_name}</p>
            ) : (
              <p className="text-xs text-white/45">Standard Ticket - {guestPrice.toLocaleString()} AMD</p>
            )}
          </div>
        </div>

        {/* Already has ticket notice (logged-in only) */}
        {me && alreadyHasTicket && !dismissTicketNotice && (
          <div className="drop-card p-4 w-full flex flex-col gap-3 border border-white/20">
            <p className="text-sm font-semibold">You already have a ticket for this event</p>
            <div className="flex gap-2">
              <Link to="/profile" className="btn-primary flex-1 py-2 text-sm text-center">
                View Ticket
              </Link>
              <button
                onClick={() => setDismissTicketNotice(true)}
                className="text-sm text-white/45 hover:text-white/70 px-3"
              >
                Buy for others
              </button>
            </div>
          </div>
        )}

        {/* Price summary (logged-in only) */}
        {me && (
          <div className="drop-card p-4 w-full flex flex-col gap-2">
            <div className="flex justify-between text-sm">
              <span className="text-white/70">1 × {ticketLabel}</span>
              <span className="font-semibold">{myPrice.toLocaleString()} AMD</span>
            </div>
            {additionalAttendees.map((a, i) => {
              const status: PersonStatus = a.kind === 'existing' ? a.status : 'pending'
              const price = resolvePrice(tiers, status)
              const tier = resolveClientTier(tiers, status)
              const label = tier?.name ?? 'Standard Ticket'
              const name = a.kind === 'existing' ? a.full_name : `${a.first_name} ${a.last_name}`
              return (
                <div key={i} className="flex justify-between text-sm items-center">
                  <span className="text-white/70 flex items-center gap-2">
                    1 × {label} ({name})
                    <button onClick={() => setAdditionalAttendees(prev => prev.filter((_, j) => j !== i))} className="text-white/30 hover:text-white/70 text-xs">×</button>
                  </span>
                  <span className="font-semibold">{price.toLocaleString()} AMD</span>
                </div>
              )
            })}
            <div className="h-px bg-white/10" />
            <div className="flex justify-between font-bold">
              <span>Total</span>
              <span>{totalPrice.toLocaleString()} AMD</span>
            </div>
          </div>
        )}
      </Section>

      {/* Identity section */}
      {!me ? (
        <Section title="New here?" subtitle="Enter your details below to continue as a guest.">
          {guestStep === 'email' && (
            <div className="drop-card p-5 flex flex-col gap-4 w-full">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-white/45">Email</label>
                <input
                  type="email"
                  value={guestEmail}
                  onChange={e => { setGuestEmail(e.target.value); setGuestLoginHint(null); setGuestFormError(null) }}
                  placeholder="you@example.com"
                  className="bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20"
                  onKeyDown={e => { if (e.key === 'Enter') handleGuestEmailContinue() }}
                />
              </div>
              {guestFormError && (
                <p className="text-xs" style={{ color: 'var(--drop-negative)' }}>{guestFormError}</p>
              )}
              {guestLoginHint ? (
                <GoogleButton
                  text="Continue with Google"
                  variant="primary"
                  loginHint={guestLoginHint}
                  redirectUrl={`/buy-ticket?event_id=${eventId}`}
                />
              ) : (
                <button onClick={handleGuestEmailContinue} disabled={guestEmailChecking} className="btn-primary h-11 text-sm mt-1">
                  {guestEmailChecking ? 'Checking…' : 'Continue'}
                </button>
              )}
            </div>
          )}

          {guestStep === 'details' && (
            <div className="drop-card p-5 flex flex-col gap-4 w-full">
              <div className="flex items-center gap-2">
                <button onClick={() => { setGuestStep('email'); setGuestFormError(null) }} className="text-xs text-white/45 hover:text-white/80">
                  ← Edit email
                </button>
                <p className="text-xs text-white/45">{guestEmail.trim()}</p>
              </div>
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
          )}

          {guestStep === 'confirm' && (
            <div className="drop-card p-5 flex flex-col gap-4 w-full">
              <div className="flex items-center gap-2">
                <button onClick={() => setGuestStep('details')} className="text-xs text-white/45 hover:text-white/80">
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
      ) : (
        <Section title="Add another person">
          {addStep === 'idle' && (
            <div className="flex flex-col gap-2 w-full">
              <div className="flex gap-2">
                <input
                  type="email"
                  value={addEmail}
                  onChange={e => { setAddEmail(e.target.value); setAddError(null) }}
                  placeholder="friend@example.com"
                  className="flex-1 bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20"
                  onKeyDown={e => { if (e.key === 'Enter') handleSearchAttendee() }}
                />
                <button onClick={handleSearchAttendee} disabled={addSearching} className="btn-primary px-4 py-2 text-sm">
                  {addSearching ? '…' : 'Search'}
                </button>
              </div>
              {addError && <p className="text-xs" style={{ color: 'var(--drop-negative)' }}>{addError}</p>}
            </div>
          )}

          {addStep === 'found' && lookupResult && (
            <div className="drop-card p-4 w-full flex flex-col gap-3">
              <div className="flex justify-between text-sm">
                <div>
                  <p className="font-semibold">{lookupResult.full_name}</p>
                  <p className="text-xs text-white/45">{lookupResult.status}</p>
                </div>
                <span className="text-sm font-semibold">
                  {resolvePrice(tiers, lookupResult.status ?? undefined).toLocaleString()} AMD
                </span>
              </div>
              <div className="flex gap-2">
                <button onClick={handleAddExisting} className="btn-primary flex-1 py-2 text-sm">Add</button>
                <button onClick={resetAddForm} className="text-sm text-white/45 hover:text-white/70 px-3">Cancel</button>
              </div>
            </div>
          )}

          {addStep === 'create' && (
            <div className="drop-card p-4 w-full flex flex-col gap-3">
              <p className="text-sm font-semibold">Not found — enter their details</p>
              <p className="text-xs text-white/45">{addEmail}</p>
              <div className="flex gap-2">
                <div className="flex flex-col gap-1 flex-1">
                  <label className="text-xs text-white/45">First name</label>
                  <input type="text" value={newFirst} onChange={e => setNewFirst(e.target.value)} placeholder="Alex"
                    className="w-full bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20" />
                </div>
                <div className="flex flex-col gap-1 flex-1">
                  <label className="text-xs text-white/45">Last name</label>
                  <input type="text" value={newLast} onChange={e => setNewLast(e.target.value)} placeholder="Smith"
                    className="w-full bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20" />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-white/45">Instagram (optional)</label>
                <input type="text" value={newInstagram} onChange={e => setNewInstagram(e.target.value)} placeholder="@handle"
                  className="w-full bg-white/8 rounded-xl px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-white/30 placeholder:text-white/20" />
              </div>
              <div className="flex gap-2">
                <button onClick={handleAddNew} className="btn-primary flex-1 py-2 text-sm">Add</button>
                <button onClick={resetAddForm} className="text-sm text-white/45 hover:text-white/70 px-3">Cancel</button>
              </div>
            </div>
          )}
        </Section>
      )}

      {/* Payment method — gated by showPayment */}
      {showPayment && (
        <Section title="Payment method">
          <PaymentProviderSelector
            provider={provider}
            setProvider={setProvider}
            saveCard={saveCard}
            setSaveCard={setSaveCard}
            cardBinding={me ? activeBinding : null}
          />
        </Section>
      )}

      {error && !(!me && guestStep === 'confirm') && (
        <p className="text-sm w-full max-w-96" style={{ color: 'var(--drop-negative)' }}>
          {error}
        </p>
      )}

      {/* Pay button — gated by showPayment */}
      {showPayment && (
        <div className="w-full max-w-96 pb-4">
          <button
            onClick={!me ? handleGuestPay : handlePay}
            disabled={loading}
            className="btn-primary h-14 text-base"
            style={{ maxWidth: '100%' }}
          >
            {loading ? 'Processing…' : `Pay ${(!me ? guestPrice : totalPrice).toLocaleString()} AMD`}
          </button>
        </div>
      )}

      {/* Sign-in alternative — guest only */}
      {!me && (
        <>
          <div className="w-full max-w-96 flex items-center gap-3 text-white/20 text-xs px-1">
            <div className="flex-1 h-px bg-white/10" />
            or
            <div className="flex-1 h-px bg-white/10" />
          </div>
          <div className="w-full max-w-96 pb-6">
            <GoogleButton text="Sign in with Google" variant="outline" redirectUrl={`/buy-ticket?event_id=${eventId}`} />
          </div>
        </>
      )}
    </Layout>
  )
}
