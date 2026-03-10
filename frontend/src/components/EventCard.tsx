import { Link } from 'react-router-dom'

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })
}
function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

interface EventCardProps {
  event: {
    id: string
    name: string
    image_url: string
    starts_at: string
    ends_at?: string
    area?: string | null
  }
  linkTo?: boolean
  showEndsAt?: boolean
  showDate?: boolean
  compact?: boolean
  className?: string
}

export default function EventCard({
  event,
  linkTo = true,
  showEndsAt = false,
  showDate = true,
  compact = false,
  className = '',
}: EventCardProps) {
  const inner = (
    <>
      <div className="relative rounded-xl overflow-hidden w-full" style={{ aspectRatio: '4/5' }}>
        <img
          src={event.image_url}
          alt={event.name}
          className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
      </div>
      <div className="mt-4 px-0.5">
        <p className={`font-bold leading-tight ${compact ? 'text-sm' : 'text-2xl'}`}>{event.name}</p>
        {showDate && (
          <p className={`text-white/60 mt-0.5 ${compact ? 'text-xs' : 'text-sm'}`}>
            {fmtDate(event.starts_at)} · {fmtTime(event.starts_at)}
            {showEndsAt && event.ends_at ? `–${fmtTime(event.ends_at)}` : ''}
          </p>
        )}
        <p className={`text-white/35 mt-0.5 ${compact ? 'text-xs' : 'text-sm'}`}>
          Secret location{event.area ? ` · ${event.area}` : ''}
        </p>
      </div>
    </>
  )

  if (linkTo) {
    return (
      <Link to={`/event/${event.id}`} className={`block group ${className}`}>
        {inner}
      </Link>
    )
  }

  return <div className={`group ${className}`}>{inner}</div>
}
