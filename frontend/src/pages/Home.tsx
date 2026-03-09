import { Link } from 'react-router-dom'
import { useNextEvent, useEvents } from '../hooks/useEvents'
import { useMe } from '../hooks/useMe'
import { useTickets } from '../hooks/useTickets'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { STATUS_COLORS } from '../components/Layout'
import { loginUrl } from '../lib/loginUrl'

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })
}
function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

export default function Home() {
  const { data: me, isLoading: meLoading } = useMe()
  const { data: nextEvent } = useNextEvent()
  const { data: events } = useEvents()
  const { data: tickets } = useTickets()

  if (meLoading) return <Layout showFooter />

  const now = new Date()
  const pastEvents = (events ?? []).filter(e => new Date(e.ends_at) < now)

  const nextEventTicket = nextEvent && tickets
    ? tickets.find(t => t.event_id === nextEvent.id)
    : null

  return (
    <Layout showFooter>
      {/* Guest welcome header */}
      {!me && (
        <Section className="pt-8">
          <div className="flex flex-col items-center gap-2 text-center w-full">
            <h1 className="text-3xl font-bold tracking-tight">Drop Dead Disco</h1>
            {/* <p className="text-sm text-white/50 leading-relaxed">
              ask around
            </p> */}
          </div>
        </Section>
      )}

      {/* Greeting */}
      {me && (
        <Section className="pt-4">
          <div className="flex items-center justify-between w-full max-w-96">
            <div className="flex flex-col gap-0.5">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: STATUS_COLORS[me.status] }} />
                <span className="text-xs uppercase tracking-widest text-white/45">{me.status}</span>
              </div>
              <h1 className="text-2xl font-bold">{me.full_name}</h1>
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
        <Section title="Review in progress" sep>
          <div className="drop-card p-5 flex flex-col items-center gap-3 text-center">
            <img src="/static/images/review.gif" alt="reviewing" className="w-32 rounded-2xl" />
            <p className="text-sm text-white/70 leading-relaxed">
              We're working day and night to review your application!<br />
              We'll get back to you ASAP via email.
            </p>
          </div>
        </Section>
      )}

      {/* Verified: ticket or buy-ticket CTA */}
      {me?.status === 'verified' && nextEvent && (
        nextEventTicket ? (
          <Section title="Your ticket" subtitle="Show this at the entrance" sep>
            <div className="drop-card p-4 flex items-center justify-between w-full">
              <div className="flex flex-col gap-0.5">
                <p className="font-semibold text-sm">{nextEvent.name}</p>
                <p className="text-xs text-white/45">{fmtDate(nextEvent.starts_at)}</p>
              </div>
              <div className="flex gap-2">
                {nextEventTicket.apple_pass_url && (
                  <a href={nextEventTicket.apple_pass_url} target="_blank" rel="noopener noreferrer">
                    <img src="/static/images/apple_wallet.svg" alt="Apple Wallet" className="h-8" />
                  </a>
                )}
                {nextEventTicket.google_pass_url && (
                  <a href={nextEventTicket.google_pass_url} target="_blank" rel="noopener noreferrer">
                    <img src="/static/images/google_wallet.svg" alt="Google Wallet" className="h-8" />
                  </a>
                )}
              </div>
            </div>
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
          <div className="drop-card p-4 flex items-center justify-between w-full">
            <div className="flex flex-col gap-0.5">
              <p className="font-semibold">Member #{me.member_pass.serial_number}</p>
              <p className="text-xs text-white/45">Drop Dead Disco</p>
            </div>
            <div className="flex gap-2">
              {me.member_pass.apple_pass_url && (
                <a href={me.member_pass.apple_pass_url} target="_blank" rel="noopener noreferrer">
                  <img src="/static/images/apple_wallet.svg" alt="Apple Wallet" className="h-8" />
                </a>
              )}
              {me.member_pass.google_pass_url && (
                <a href={me.member_pass.google_pass_url} target="_blank" rel="noopener noreferrer">
                  <img src="/static/images/google_wallet.svg" alt="Google Wallet" className="h-8" />
                </a>
              )}
            </div>
          </div>
          {nextEvent && (
            <a href={`/buy-ticket?event_id=${nextEvent.id}`} className="btn-primary">
              🎟️ Buy your ticket
            </a>
          )}
        </Section>
      )}

      {/* Member: Google Photos */}
      {me?.status === 'member' && me.drive_folder_url && (
        <Section title="You at Drop" subtitle="Your photos in full quality" sep>
          <a
            href={`${me.drive_folder_url}?authuser=${me.email}`}
            target="_blank"
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
          <Link to={`/event/${nextEvent.id}`} className="w-full max-w-96 block">
            <div className="relative w-full overflow-hidden rounded-lg group cursor-pointer" style={{ aspectRatio: '4/5' }}>
              <img
                src={nextEvent.image_url}
                alt={nextEvent.name}
                className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-x-0 top-0 flex flex-col items-center pt-5 px-4">
                <h2
                  className="text-white font-bold text-2xl text-center leading-tight"
                  style={{ textShadow: '0 2px 12px rgba(0,0,0,0.9)' }}
                >
                  {nextEvent.name}
                </h2>
                <p className="text-white/70 text-sm mt-1 text-center" style={{ textShadow: '0 1px 6px rgba(0,0,0,0.8)' }}>
                  {fmtDate(nextEvent.starts_at)} · {fmtTime(nextEvent.starts_at)}
                </p>
              </div>
            </div>
          </Link>
          {(!me || (me.status !== 'verified' && me.status !== 'member')) && (
            <a href={`/buy-ticket?event_id=${nextEvent.id}`} className="btn-primary">
              🎟️ Buy your ticket
            </a>
          )}
        </Section>
      )}

      {/* Community blurb */}
      <Section sep>
        <p className="text-sm text-white/70 leading-relaxed w-full">
          Drop Dead Disco is a hand-picked community hosting dance parties in secret locations around Yerevan.
          Every guest has to pass <strong>verification</strong> before they're able to buy tickets and attend.{' '}
          <Link to="/about" className="underline underline-offset-2 text-white/55 hover:text-white/80">Read more</Link>
        </p>
      </Section>

      {/* Guest: sign up */}
      {!me && (
        <Section title="Wanna join the fun?" subtitle="Sign up to get verified">
          <div className="flex gap-2 w-full max-w-96">
            <a href={loginUrl('/')} className="btn-primary flex-1" style={{ maxWidth: 'none' }}>
              <img src="/static/images/google.svg" alt="" className="w-4 h-4 mr-2" />
              Sign up
            </a>
            <a href={loginUrl('/')} className="btn-outline flex-1" style={{ maxWidth: 'none' }}>
              <img src="/static/images/google.svg" alt="" className="w-4 h-4 mr-2 opacity-50" />
              Log in
            </a>
          </div>
        </Section>
      )}

      {/* Past events grid */}
      {pastEvents.length > 0 && (
        <Section title="Previous events" subtitle="Photos and videos from past events" sep>
          <div className="grid grid-cols-2 gap-3 w-full max-w-96">
            {pastEvents.map((event) => (
              <Link key={event.id} to={`/event/${event.id}`} className="block">
                <div className="relative rounded-lg overflow-hidden group" style={{ aspectRatio: '4/5' }}>
                  <img
                    src={event.image_url}
                    alt={event.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-x-0 top-0 p-3 flex justify-center">
                    <p
                      className="text-white font-bold text-sm text-center leading-tight"
                      style={{ textShadow: '0 1px 6px rgba(0,0,0,0.9)' }}
                    >
                      {event.name}
                    </p>
                  </div>
                </div>
              </Link>
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
          height="152"
          frameBorder={0}
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
          loading="lazy"
          className="w-full max-w-96"
        />
      </Section>
    </Layout>
  )
}
