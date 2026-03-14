import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { useEvent, useEventPhotos } from '../hooks/useEvents'
import { useMe } from '../hooks/useMe'
import Layout from '../components/Layout'
import Section from '../components/Section'
import AlbumCarousel from '../components/AlbumCarousel'
import EventCard from '../components/EventCard'
import { gtagEvent } from '../lib/analytics'

export default function Event() {
  const { id } = useParams<{ id: string }>()
  const { data: event, isLoading, error } = useEvent(id ?? '')
  const { data: me } = useMe()
  const { data: photos, isLoading: photosLoading } = useEventPhotos(id ?? '', !!event?.album_url)

  document.title = event ? `${event.name} | Drop Dead Disco` : 'Drop Dead Disco'

  const [descExpanded, setDescExpanded] = useState(false)
  const [descOverflows, setDescOverflows] = useState(false)
  const descRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (descRef.current) {
      setDescOverflows(descRef.current.scrollHeight > 130)
    }
  }, [event?.description])

  useEffect(() => {
    if (!event) return
    gtagEvent('view_item_list', {
      items: event.tiers.map(t => ({ item_id: t.id, item_name: t.name, price: t.price })),
    })
  }, [event?.id])

  if (isLoading) return (
    <Layout showFooter={false}>
      <div className="w-full max-w-96 md:max-w-2xl lg:max-w-3xl mt-4 space-y-4">
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
  const myTier = event.tiers.find(t => {
    if (!t.is_active) return false
    if (t.required_person_status && t.required_person_status !== me?.status) return false
    if (t.available_from && now < new Date(t.available_from)) return false
    if (t.available_until && now >= new Date(t.available_until)) return false
    return true
  })

  return (
    <Layout heroBg={event.image_url} showFooter={false}>
      {/* Two-column layout at lg: image left, details right */}
      <div className="w-full max-w-96 md:max-w-2xl lg:max-w-3xl mt-4 lg:flex lg:gap-8 lg:items-start">

        {/* Left column: event image - sticky on desktop */}
        <div className="lg:w-80 lg:flex-none lg:sticky lg:top-4">
          <EventCard
            event={event}
            linkTo={false}
            showEndsAt
            className="w-full"
            imageClassName='mx-4'
          />
        </div>

        {/* Right column: track, description, tiers */}
        <div className="lg:flex-1 flex flex-col min-w-0">
          {event.track_url && (
            <div className="py-4 lg:pt-0">
              <iframe
                style={{ borderRadius: '12px' }}
                src={`${event.track_url}?utm_source=generator`}
                width="100%"
                height="80"
                allowFullScreen
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                loading="lazy"
                className="w-full"
              />
            </div>
          )}

          {event.description && (
            <div className="flex flex-col gap-2 py-4 border-t border-white/10">
              <p className="text-xs uppercase tracking-wider text-white/40 w-full mb-1">About this event</p>
              <div className="overflow-hidden transition-all duration-300 ease-in-out"
                style={descOverflows && !descExpanded ? { height: '8em', maskImage: 'linear-gradient(black 0%, black 30%, transparent 100%)' } : undefined}
              >
                <div ref={descRef} className="w-full text-sm text-white/80 leading-relaxed prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{event.description}</ReactMarkdown>
                </div>
              </div>
              {descOverflows && (
                <button
                  onClick={() => setDescExpanded(v => !v)}
                  className="mt-1 text-sm text-white/45 hover:text-white/70 transition-colors w-full text-center"
                >
                  {descExpanded ? 'View less' : 'View more'}
                </button>
              )}
            </div>
          )}

          {!eventPassed && event.tiers.length > 0 && (
            <div className="flex flex-col gap-2 py-4 border-t border-white/10">
              <h2 className="text-xl font-medium px-2">Tickets</h2>
              {event.tiers.map(t => {
                const soldOut = (!!t.available_until && now >= new Date(t.available_until))
                  || (!!t.available_from && now < new Date(t.available_from))
                return (
                  <TicketCard
                    key={t.id}
                    label={t.name}
                    price={t.price}
                    soldOut={soldOut}
                    selected={myTier?.id === t.id}
                  />
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* YouTube - full width below columns */}
      {event.video_url && (
        <Section sep>
          <iframe
            src={event.video_url}
            title="Event video"
            frameBorder={0}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="w-full rounded-xl aspect-video"
          />
        </Section>
      )}

      {/* Photo album carousel - full width below columns */}
      {(photosLoading && !!event?.album_url || Array.isArray(photos) && photos.length > 0) && (
        <Section sep>
          <p className="text-xs uppercase tracking-wider text-white/40 w-full mb-3">Photos</p>
          {photosLoading ? (
            <div className="w-full max-w-96 md:max-w-full space-y-2">
              <div className="skeleton w-full rounded-xl" style={{ aspectRatio: '3/2' }} />
              <div className="flex gap-1.5">
                {[0, 1, 2, 3].map(i => <div key={i} className="skeleton w-14 h-14 rounded-lg flex-none" />)}
              </div>
            </div>
          ) : (
            <AlbumCarousel photos={photos!} />
          )}
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
              className="btn-primary h-16 text-base opacity-40 cursor-not-allowed max-w-sm md:max-w-lg"
            >
              🎟️ Buy your ticket
            </button>
          ) : (
            <a
              href={`/buy-ticket?event_id=${event.id}`}
              className="btn-primary h-16 text-base max-w-sm md:max-w-lg"
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
      className="w-full rounded-xl px-4 py-3 flex justify-between items-center transition-all"
      style={{
        background: selected ? 'rgba(255,255,255,0.1)' : 'var(--drop-card)',
        border: selected ? '1px solid rgba(255,255,255,0.3)' : '1px solid rgba(255,255,255,0.18)',
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
