import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { useEvent } from '../hooks/useEvents'
import { useMe } from '../hooks/useMe'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { gtagEvent } from '../lib/analytics'

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })
}
function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

export default function Event() {
  const { id } = useParams<{ id: string }>()
  const { data: event, isLoading, error } = useEvent(id ?? '')
  const { data: me } = useMe()

  useEffect(() => {
    if (!event) return
    gtagEvent('view_item_list', {
      items: [
        { item_id: 'ticket_member', price: event.member_ticket_price },
        { item_id: 'ticket_early_bird', price: event.early_bird_price },
        { item_id: 'ticket_general', price: event.general_admission_price },
      ],
    })
  }, [event?.id])

  if (isLoading) return (
    <Layout showFooter={false}>
      <div className="w-full max-w-96 mt-4 space-y-4">
        <div className="skeleton w-full rounded-2xl" style={{ aspectRatio: '4/5', minHeight: 420 }} />
        <div className="skeleton h-7 w-3/4" />
        <div className="skeleton h-4 w-1/2" />
        <div className="skeleton h-16 w-full rounded-xl" />
        <div className="skeleton h-16 w-full rounded-xl" />
        <div className="skeleton h-16 w-full rounded-xl" />
      </div>
    </Layout>
  )
  if (error || !event) return (
    <Layout showFooter={false}>
      <div className="flex items-center justify-center min-h-[60vh] text-white/45">Event not found.</div>
    </Layout>
  )

  const now = new Date()
  const eventPassed = new Date(event.ends_at) < now
//   const eventPassed = false
  const earlyBirdActive = event.early_bird_date ? new Date(event.early_bird_date) > now : false
  const isMember = me?.status === 'member'

  return (
    <Layout heroBg={event.image_url} showFooter={false}>
      {/* Event image - matches event_card() aspect-4/5, name at top */}
      <div className="w-full max-w-96 mt-4">
        <div className="relative rounded-xl overflow-hidden w-full" style={{ aspectRatio: '4/5' }}>
          <img
            src={event.image_url}
            alt={event.name}
            className="absolute inset-0 w-full h-full object-cover"
          />
          <div className="absolute inset-x-0 top-0 pt-5 px-5 flex flex-col items-center">
            <h1
              className="text-white font-bold text-2xl text-center leading-tight"
              style={{ textShadow: '0 2px 12px rgba(0,0,0,0.9)' }}
            >
              {event.name}
            </h1>
            {!eventPassed && (
              <p className="text-white/70 text-sm mt-1 text-center" style={{ textShadow: '0 1px 6px rgba(0,0,0,0.8)' }}>
                {fmtDate(event.starts_at)} · {fmtTime(event.starts_at)}–{fmtTime(event.ends_at)}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Spotify track */}
      {event.track_url && (
        <Section>
          <iframe
            style={{ borderRadius: '12px' }}
            src={`${event.track_url}?utm_source=generator`}
            width="100%"
            height="152"
            frameBorder={0}
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
            className="w-full max-w-96"
          />
        </Section>
      )}

      {/* Description - rendered as markdown */}
      {event.description && (
        <Section sep>
          <p className="text-xs uppercase tracking-wider text-white/40 w-full mb-1">About this event</p>
          <div className="w-full text-sm text-white/80 leading-relaxed prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{event.description}</ReactMarkdown>
          </div>
        </Section>
      )}

      {/* Ticket tiers */}
      {!eventPassed && (
        <Section title="Tickets" sep>
          <TicketCard label="Members" price={event.member_ticket_price} selected={isMember} />
          <TicketCard
            label="Early Bird"
            price={event.early_bird_price}
            soldOut={!earlyBirdActive}
            selected={earlyBirdActive && !isMember}
          />
          <TicketCard
            label="Standard"
            price={event.general_admission_price}
            selected={!earlyBirdActive && !isMember}
          />
        </Section>
      )}

      {/* YouTube */}
      {event.video_url && (
        <Section sep>
          <iframe
            src={event.video_url}
            title="Event video"
            frameBorder={0}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="w-full max-w-96 rounded-xl aspect-video"
          />
        </Section>
      )}

      {/* Spacer for fixed CTA */}
      {!eventPassed && <div className="h-20 w-full" />}

      {/* Fixed buy button */}
      {!eventPassed && (
        <div className="fixed bottom-4 left-0 right-0 flex justify-center px-4 z-50">
          {me?.status === 'rejected' ? (
            <button
              disabled
              className="btn-primary h-16 text-base opacity-40 cursor-not-allowed"
              style={{ maxWidth: '24rem' }}
            >
              🎟️ Buy your ticket
            </button>
          ) : (
            <a
              href={`/buy-ticket?event_id=${event.id}`}
              className="btn-primary h-16 text-base"
              style={{ maxWidth: '24rem' }}
            >
              🎟️ Buy your ticket
            </a>
          )}
        </div>
      )}
    </Layout>
  )
}

interface TicketCardProps {
  label: string
  price?: number | null
  soldOut?: boolean
  selected?: boolean
}

function TicketCard({ label, price, soldOut, selected }: TicketCardProps) {
  return (
    <div
      className="w-full max-w-96 rounded-xl px-4 py-3 flex justify-between items-center transition-all"
      style={{
        background: selected ? 'rgba(255,255,255,0.1)' : 'var(--drop-card)',
        border: selected ? '1px solid rgba(255,255,255,0.3)' : '1px solid rgba(255,255,255,0.05)',
        opacity: soldOut ? 0.4 : 1,
      }}
    >
      <div>
        <p className="font-semibold text-sm">{label}</p>
        {soldOut && <p className="text-xs text-white/45">Sold out</p>}
      </div>
      {price != null && (
        <p className="font-semibold text-sm">{price.toLocaleString()} AMD</p>
      )}
    </div>
  )
}
