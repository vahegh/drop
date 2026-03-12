import QRCode from 'react-qr-code'
import type { MemberCardResponse } from '../types'

interface Props {
  pass: MemberCardResponse
  eventsAttended: number
}

export default function MemberPassCard({ pass, eventsAttended }: Props) {
  return (
    <div
      className="flex flex-col items-center gap-4 px-0 py-4 w-full max-w-96 rounded-xl border border-white/20"
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
      <div className="w-3/5 bg-white p-3 rounded-sm">
        <QRCode value={pass.id} style={{ width: '100%', height: 'auto' }} />
      </div>
      <div className="flex items-center gap-2">
        <span className="font-semibold text-sm">MEMBER SINCE</span>
        <span className="font-semibold text-sm" style={{ color: '#7c5cbf' }}>
          {new Date(pass.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }).toUpperCase()}
        </span>
      </div>
      {(() => {
        const ua = navigator.userAgent
        const isIOS = /iPhone|iPad|iPod/i.test(ua)
        const isAndroid = /Android/i.test(ua)
        if (isIOS && pass.apple_pass_url)
          return (
            <a
              href={pass.apple_pass_url}
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-2 rounded-xl border border-white/30 bg-transparent text-white font-semibold text-sm"
            >
              <img src="/static/images/apple_wallet.svg" alt="" className="h-5" />
              Add to Apple Wallet
            </a>
          )
        if (isAndroid && pass.google_pass_url)
          return (
            <a
              href={pass.google_pass_url}
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-2 rounded-xl border border-white/30 bg-transparent text-white font-semibold text-sm"
            >
              <img src="/static/images/google_wallet.svg" alt="" className="h-5" />
              Add to Google Wallet
            </a>
          )
        return null
      })()}
    </div>
  )
}
