import QRCode from 'react-qr-code'
import type { EventTicketResponse, EventResponse } from '../types'

interface Props {
  ticket: EventTicketResponse
  event: EventResponse
}

export default function EventTicketCard({ ticket, event }: Props) {
  const startsAt = new Date(event.starts_at)
  return (
    <div
      className="flex flex-col items-center gap-4 px-0 py-4 w-full max-w-96 rounded-xl"
      style={{ border: '1px solid rgba(255,255,255,0.15)', background: 'var(--drop-card)' }}
    >
      <div className="flex flex-col items-center gap-0 px-6 w-full">
        <p className="text-2xl font-medium text-center">{event.name}</p>
      </div>
      <div className="w-3/4 bg-white p-3 rounded-xl">
        <QRCode value={ticket.id} style={{ width: '100%', height: 'auto' }} />
      </div>
      <div className="flex items-center justify-between w-full px-6">
        <div className="flex flex-col gap-0">
          <span className="text-xs text-white/45">Event date</span>
          <span className="font-bold text-lg">
            {startsAt.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit' })}
          </span>
        </div>
        <div className="flex flex-col gap-0 text-right">
          <span className="text-xs text-white/45">Start time</span>
          <span className="font-bold text-lg">
            {startsAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
      {(ticket.apple_pass_url || ticket.google_pass_url) && (
        <div className="flex gap-2 justify-center">
          {ticket.apple_pass_url && (
            <a href={ticket.apple_pass_url} rel="noopener noreferrer">
              <img src="/static/images/apple_wallet.svg" alt="Apple Wallet" className="h-8" />
            </a>
          )}
          {ticket.google_pass_url && (
            <a href={ticket.google_pass_url} rel="noopener noreferrer">
              <img src="/static/images/google_wallet.svg" alt="Google Wallet" className="h-8" />
            </a>
          )}
        </div>
      )}
    </div>
  )
}
