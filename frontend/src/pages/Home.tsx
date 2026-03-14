import { useNextEvent, useEvents, useAllPhotos } from '../hooks/useEvents'
import { useMe, usePeopleStats } from '../hooks/useMe'
import { useTickets } from '../hooks/useTickets'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { STATUS_COLORS } from '../components/Layout'
import LoginBlock from '../components/LoginBlock'
import MemberPassCard from '../components/MemberPassCard'
import EventTicketCard from '../components/EventTicketCard'
import AlbumCarousel from '../components/AlbumCarousel'
import EventCard from '../components/EventCard'

function AlbumSkeleton() {
  return (
    <div className="w-full max-w-96 md:max-w-full space-y-2">
      <div className="skeleton w-full rounded-xl" style={{ aspectRatio: '3/2' }} />
      <div className="flex gap-1.5">
        {[0, 1, 2, 3].map(i => <div key={i} className="skeleton w-14 h-14 rounded-lg flex-none" />)}
      </div>
    </div>
  )
}

export default function Home() {
  const { data: me } = useMe()
  const { data: nextEvent } = useNextEvent()
  const { data: events } = useEvents()
  const { data: tickets } = useTickets()
  const { data: stats, isLoading: statsLoading } = usePeopleStats()
  const { data: allPhotos, isLoading: photosLoading } = useAllPhotos()

  document.title = 'Home | Drop Dead Disco'

  const now = new Date()
  const pastEvents = (events ?? []).filter(e => new Date(e.ends_at) < now)

  const nextEventTicket = nextEvent && tickets
    ? tickets.find(t => t.event_id === nextEvent.id)
    : null

  return (
    <Layout showFooter showVideo>
      {/* Guest hero */}
      {!me && (
        <Section className="pt-4">
          <div className="flex flex-col items-center gap-1 text-center w-full">
            <h1 className="text-4xl font-bold tracking-tight">Drop Dead Disco</h1>
            <p className="text-sm text-white/55 leading-relaxed max-w-80">
              Dance parties in secret locations in and around Yerevan. Verification required.
            </p>
          </div>
        </Section>
      )}

      {/* Guest: photos right after hero */}
      {!me && (photosLoading || (Array.isArray(allPhotos) && allPhotos.length > 0)) && (
        <Section>
          {photosLoading ? <AlbumSkeleton /> : <AlbumCarousel photos={allPhotos!} />}
        </Section>
      )}


      {/* Guest: sign up CTA */}
      {!me && (
        <Section title="Apply for access" subtitle="Sign up to get verified">
          <LoginBlock redirectUrl="/" />
        </Section>
      )}

      {/* Greeting */}
      {me && (
        <Section className="pt-4">
          <div className="flex items-center justify-between w-full">
            <div className="flex flex-col gap-0.5">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: STATUS_COLORS[me.status] }} />
                <span className="text-xs uppercase tracking-widest text-white/45">{me.status}</span>
              </div>
              <h1 className="text-2xl font-bold">{me.full_name}</h1>
              <div className="flex items-center gap-3 mt-1">
                {me.events_attended > 0 && (
                  <span className="text-sm text-white/70">🔥 {me.events_attended}</span>
                )}
                {me.referral_count > 0 && (
                  <span className="text-sm text-white/70">👥 {me.referral_count}</span>
                )}
              </div>
            </div>
            {me.avatar_url ? (
              <img src={me.avatar_url} alt={me.full_name} className="w-16 h-16 rounded-full object-cover" />
            ) : (
              <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center text-2xl font-bold">
                {me.first_name[0]}
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Pending: under review */}
      {me?.status === 'pending' && (
        <Section title="Your review is in progress" subtitle="We'll get back to you ASAP." sep>
            <img src="/static/images/review.gif" alt="reviewing" className="w-80 rounded-sm" />
        </Section>
      )}

      {/* Verified: ticket or buy-ticket CTA */}
      {me?.status === 'verified' && nextEvent && (
        nextEventTicket ? (
          <Section title="Your ticket" subtitle="Show this at the entrance" sep>
            <EventTicketCard ticket={nextEventTicket} event={nextEvent} />
          </Section>
        ) : (
          <Section title="Still no ticket?" subtitle={`Get yours for ${nextEvent.name}`} sep>
            <a href={`/buy-ticket?event_id=${nextEvent.id}`} className="btn-primary">
              🎟️ Buy your ticket
            </a>
          </Section>
        )
      )}

      {/* Member: membership pass */}
      {me?.status === 'member' && me.member_pass && (
        <Section title="Your Membership Pass" subtitle="Use this to enter any Drop event" sep>
          <MemberPassCard pass={me.member_pass} eventsAttended={me.events_attended} />
          {nextEvent && (
            <a href={`/buy-ticket?event_id=${nextEvent.id}`} className="btn-primary">
              🎟️ Buy your ticket
            </a>
          )}
        </Section>
      )}

      {/* Member: Google Photos */}
      {me?.status === 'member' && me.album_url && (
        <Section title="You at Drop" subtitle="Your photos in full quality" sep>
          <a
            href={`${me.album_url}?authuser=${me.email}`}
            rel="noopener noreferrer"
            className="btn-outline"
          >
            <img src="/static/images/google_photos.svg" alt="" className="w-4 h-4 mr-2" />
            Open in Google Photos
          </a>
          <p className="text-xs text-white/30 text-center">*only visible to you</p>
        </Section>
      )}

      {/* Next event card */}
      {nextEvent && (
        <Section>
          <EventCard event={nextEvent} className="w-full" />
          {(!me || (me.status !== 'verified' && me.status !== 'member')) && (
            <a href={`/buy-ticket?event_id=${nextEvent.id}`} className="btn-primary">
              🎟️ Buy your ticket
            </a>
          )}
        </Section>
      )}

      {/* Community blurb */}
      <Section sep>
        {statsLoading ? (
          <div className="flex gap-8 w-full">
            <div className="flex flex-col gap-1.5">
              <div className="skeleton h-9 w-10" />
              <div className="skeleton h-2.5 w-16" />
            </div>
            <div className="flex flex-col gap-1.5">
              <div className="skeleton h-9 w-10" />
              <div className="skeleton h-2.5 w-16" />
            </div>
          </div>
        ) : stats && (
          <div className="flex gap-8 w-full">
            {stats['member'] != null && (
              <div className="flex flex-col gap-0.5">
                <span className="text-3xl font-bold">{stats['member']}</span>
                <span className="text-xs text-white/40 uppercase tracking-widest">Members</span>
              </div>
            )}
            {stats['verified'] != null && (
              <div className="flex flex-col gap-0.5">
                <span className="text-3xl font-bold">{stats['verified']}</span>
                <span className="text-xs text-white/40 uppercase tracking-widest">Verified</span>
              </div>
            )}
          </div>
        )}
        <p className="text-sm text-white/40 leading-relaxed w-full mt-1">
          Drop Dead Disco is a hand-picked community hosting dance parties in secret locations around Yerevan.
          Every guest passes <strong className="text-white/60">verification</strong> before they can attend.
        </p>
      </Section>

      {/* Logged-in: photo carousel */}
      {me && (photosLoading || (Array.isArray(allPhotos) && allPhotos.length > 0)) && (
        <Section>
          {photosLoading ? <AlbumSkeleton /> : <AlbumCarousel photos={allPhotos!} />}
        </Section>
      )}

      {/* Past events grid */}
      {pastEvents.length > 0 && (
        <Section title="Previous events" subtitle="Photos and videos from past events" sep>
          <div className="w-full grid grid-cols-1 divide-y divide-white/10 lg:grid-cols-2 lg:gap-6 lg:divide-y-0">
            {pastEvents.map((event) => (
              <EventCard key={event.id} event={event} className="py-6 first:pt-0 lg:py-0" />
            ))}
          </div>
        </Section>
      )}

      {/* Playlist */}
      <Section title="Playlist" subtitle="Updated regularly with your favourites" sep>
        <iframe
          style={{ borderRadius: '12px' }}
          src="https://open.spotify.com/embed/playlist/49t6kUgW6nB7Kcv4d357qy?utm_source=generator"
          width="100%"
          height="352"
          frameBorder={0}
          allowFullScreen
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
          className="w-full"
        />
      </Section>
    </Layout>
  )
}
