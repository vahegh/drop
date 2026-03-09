import QRCode from 'react-qr-code'
import { STATUS_COLORS } from './Layout'
import type { MemberCardResponse } from '../types'

interface Props {
  pass: MemberCardResponse
  eventsAttended: number
}

export default function MemberPassCard({ pass, eventsAttended }: Props) {
  return (
    <div
      className="flex flex-col items-center gap-4 px-0 py-4 w-full max-w-96 rounded-xl"
      style={{ border: `1px solid ${STATUS_COLORS['member']}`, background: 'var(--drop-card)' }}
    >
      <div className="flex items-center justify-between w-full px-6">
        <div className="flex flex-col gap-0">
          <span className="text-xs text-white/45">Member ID</span>
          <span className="font-bold text-lg">{String(pass.serial_number).padStart(3, '0')}</span>
        </div>
        <div className="flex flex-col gap-0 text-right">
          <span className="text-xs text-white/45">Events</span>
          <span className="font-bold text-lg">{eventsAttended}</span>
        </div>
      </div>
      <div className="w-3/4 bg-white p-3 rounded-xl">
        <QRCode value={pass.id} style={{ width: '100%', height: 'auto' }} />
      </div>
      <div className="flex items-center gap-2">
        <span className="font-semibold text-sm">MEMBER SINCE</span>
        <span className="font-semibold text-sm" style={{ color: STATUS_COLORS['member'] }}>
          {new Date(pass.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }).toUpperCase()}
        </span>
      </div>
      {(pass.apple_pass_url || pass.google_pass_url) && (
        <div className="flex gap-2 w-full px-6 justify-center">
          {pass.apple_pass_url && (
            <a href={pass.apple_pass_url} target="_blank" rel="noopener noreferrer">
              <img src="/static/images/apple_wallet.svg" alt="Apple Wallet" className="h-8" />
            </a>
          )}
          {pass.google_pass_url && (
            <a href={pass.google_pass_url} target="_blank" rel="noopener noreferrer">
              <img src="/static/images/google_wallet.svg" alt="Google Wallet" className="h-8" />
            </a>
          )}
        </div>
      )}
    </div>
  )
}
