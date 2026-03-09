import { useState } from 'react'
import { Link } from 'react-router-dom'
import QRCode from 'react-qr-code'
import { useMe } from '../hooks/useMe'
import { useTickets } from '../hooks/useTickets'
import { useEvents } from '../hooks/useEvents'
import { updateMe, uploadAvatar } from '../api/people'
import { useQueryClient } from '@tanstack/react-query'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { STATUS_COLORS } from '../components/Layout'
import { loginUrl } from '../lib/loginUrl'
import type { PersonUpdate } from '../types'

export default function Profile() {
  const { data: me, isLoading, error } = useMe()
  const { data: tickets } = useTickets()
  const { data: events } = useEvents()
  const qc = useQueryClient()

  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState<PersonUpdate>({})
  const [saving, setSaving] = useState(false)
  const [avatarLoading, setAvatarLoading] = useState(false)

  if (isLoading) return (
    <Layout>
      <div className="w-full max-w-96 space-y-3 mt-4">
        <div className="h-20 w-20 rounded-full bg-white/5 animate-pulse mx-auto" />
        <div className="h-6 w-48 bg-white/5 animate-pulse mx-auto rounded" />
      </div>
    </Layout>
  )

  if (error || !me) {
    window.location.href = loginUrl('/app/profile')
    return null
  }

  const eventMap = new Map((events ?? []).map(e => [e.id, e]))

  async function handleSave() {
    setSaving(true)
    try {
      await updateMe(form)
      await qc.invalidateQueries({ queryKey: ['me'] })
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  async function handleAvatarUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setAvatarLoading(true)
    try {
      await uploadAvatar(file)
      await qc.invalidateQueries({ queryKey: ['me'] })
    } finally {
      setAvatarLoading(false)
    }
  }

  const pendingTickets = (tickets ?? []).filter(t => {
    const ev = eventMap.get(t.event_id)
    return ev && new Date(ev.ends_at) >= new Date()
  })
  const pastTickets = (tickets ?? []).filter(t => {
    const ev = eventMap.get(t.event_id)
    return ev && new Date(ev.ends_at) < new Date()
  })

  return (
    <Layout>
      {/* Avatar + name */}
      <Section className="pt-6">
        <div className="flex flex-col items-center gap-3 w-full">
          <label className="cursor-pointer relative group">
            {me.avatar_url ? (
              <img
                src={me.avatar_url}
                alt={me.full_name}
                className={`w-20 h-20 rounded-full object-cover transition-opacity ${avatarLoading ? 'opacity-50' : ''}`}
              />
            ) : (
              <div
                className="w-20 h-20 rounded-full flex items-center justify-center text-3xl font-bold"
                style={{ background: 'var(--drop-card)' }}
              >
                {me.first_name[0]}
              </div>
            )}
            <div className="absolute inset-0 rounded-full bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-xs text-white">
              Edit
            </div>
            <input type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} />
          </label>

          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full" style={{ background: STATUS_COLORS[me.status] }} />
              <span className="text-xs uppercase tracking-widest" style={{ color: STATUS_COLORS[me.status] }}>
                {me.status}
              </span>
            </div>
            <h1 className="text-xl font-bold">{me.full_name}</h1>
            <a
              href={`https://instagram.com/${me.instagram_handle}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-white/45 hover:text-white/80 transition-colors"
            >
              @{me.instagram_handle}
            </a>
          </div>
        </div>
      </Section>

      {/* Stats */}
      <Section>
        <div className="drop-card px-4 py-3 flex justify-around w-full">
          <Stat label="Events attended" value={String(me.events_attended)} />
          {me.event_tickets.length > 0 && (
            <Stat label="Tickets" value={String(me.event_tickets.length)} />
          )}
          {me.member_pass && (
            <Stat label="Member #" value={String(me.member_pass.serial_number)} />
          )}
        </div>
      </Section>

      {/* Edit profile */}
      {editing ? (
        <Section title="Edit profile" sep>
          <div className="flex flex-col gap-3 w-full max-w-96">
            {(
              [
                ['First name', 'first_name', me.first_name],
                ['Last name', 'last_name', me.last_name],
                ['Instagram', 'instagram_handle', me.instagram_handle],
                ['Telegram', 'telegram_handle', me.telegram_handle ?? ''],
              ] as [string, keyof PersonUpdate, string][]
            ).map(([label, field, defaultValue]) => (
              <div key={field} className="flex flex-col gap-1">
                <label className="text-xs text-white/45">{label}</label>
                <input
                  className="w-full rounded-2xl px-4 py-3 text-sm bg-white/8 border border-white/10 focus:border-white/30 focus:outline-none transition-colors"
                  defaultValue={defaultValue}
                  onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                />
              </div>
            ))}
            <div className="flex gap-2 pt-1">
              <button onClick={handleSave} disabled={saving} className="btn-primary flex-1" style={{ maxWidth: 'none' }}>
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button onClick={() => setEditing(false)} className="btn-outline flex-1" style={{ maxWidth: 'none' }}>
                Cancel
              </button>
            </div>
          </div>
        </Section>
      ) : (
        <Section sep>
          <div className="drop-card p-4 flex flex-col gap-3 w-full">
            <InfoRow label="Email" value={me.email} />
            <InfoRow label="Instagram" value={`@${me.instagram_handle}`} />
            {me.telegram_handle && <InfoRow label="Telegram" value={`@${me.telegram_handle}`} />}
          </div>
          <button onClick={() => setEditing(true)} className="btn-outline">
            Edit profile
          </button>
        </Section>
      )}

      {/* Member pass — mirrors member_card() in components.py */}
      {me.member_pass && (
        <Section title="Membership Pass" sep>
          <div
            className="flex flex-col items-center gap-4 px-0 py-4 w-full max-w-96 rounded-3xl"
            style={{ border: `1px solid ${STATUS_COLORS['member']}`, background: 'var(--drop-card)' }}
          >
            <div className="flex items-center justify-between w-full px-6">
              <div className="flex flex-col gap-0">
                <span className="text-xs text-white/45">Member ID</span>
                <span className="font-bold text-lg">{String(me.member_pass.serial_number).padStart(3, '0')}</span>
              </div>
              <div className="flex flex-col gap-0 text-right">
                <span className="text-xs text-white/45">Events</span>
                <span className="font-bold text-lg">{me.events_attended}</span>
              </div>
            </div>
            <div className="w-3/4 bg-white p-3 rounded-2xl">
              <QRCode value={me.member_pass.id} style={{ width: '100%', height: 'auto' }} />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">MEMBER SINCE</span>
              <span className="font-semibold text-sm" style={{ color: STATUS_COLORS['member'] }}>
                {new Date(me.member_pass.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }).toUpperCase()}
              </span>
            </div>
            {(me.member_pass.apple_pass_url || me.member_pass.google_pass_url) && (
              <div className="flex gap-2 w-full px-6 justify-center">
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
            )}
          </div>
        </Section>
      )}

      {/* Upcoming ticket — mirrors event_ticket() in components.py */}
      {pendingTickets.length > 0 && (
        <Section title="Your ticket" subtitle="Show this at the entrance" sep>
          {pendingTickets.map((ticket) => {
            const ev = eventMap.get(ticket.event_id)
            const startsAt = ev ? new Date(ev.starts_at) : null
            return (
              <div
                key={ticket.id}
                className="flex flex-col items-center gap-4 px-0 py-4 w-full max-w-96 rounded-3xl"
                style={{ border: '1px solid rgba(255,255,255,0.15)', background: 'var(--drop-card)' }}
              >
                {ev && (
                  <div className="flex flex-col items-center gap-0 px-6 w-full">
                    <p className="text-2xl font-medium text-center">{ev.name}</p>
                  </div>
                )}
                <div className="w-3/4 bg-white p-3 rounded-2xl">
                  <QRCode value={ticket.id} style={{ width: '100%', height: 'auto' }} />
                </div>
                {startsAt && (
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
                )}
                {(ticket.apple_pass_url || ticket.google_pass_url) && (
                  <div className="flex gap-2 justify-center">
                    {ticket.apple_pass_url && (
                      <a href={ticket.apple_pass_url} target="_blank" rel="noopener noreferrer">
                        <img src="/static/images/apple_wallet.svg" alt="Apple Wallet" className="h-8" />
                      </a>
                    )}
                    {ticket.google_pass_url && (
                      <a href={ticket.google_pass_url} target="_blank" rel="noopener noreferrer">
                        <img src="/static/images/google_wallet.svg" alt="Google Wallet" className="h-8" />
                      </a>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </Section>
      )}

      {/* Past tickets */}
      {pastTickets.length > 0 && (
        <Section title="Past events" sep>
          <div className="flex flex-col gap-2 w-full max-w-96">
            {pastTickets.map((ticket) => {
              const ev = eventMap.get(ticket.event_id)
              return (
                <div
                  key={ticket.id}
                  className="drop-card px-4 py-3 flex items-center justify-between"
                  style={{ opacity: 0.7 }}
                >
                  <div>
                    <p className="text-sm font-semibold">{ev?.name ?? 'Event'}</p>
                    <p className="text-xs text-white/45">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {ticket.attended_at && (
                    <span
                      className="text-xs px-2 py-1 rounded-full"
                      style={{ background: 'rgba(0,201,81,0.15)', color: '#00c951' }}
                    >
                      Attended
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        </Section>
      )}

      {/* Google Drive photos */}
      {me.drive_folder_url && (
        <Section title="You at Drop" subtitle="Your photos from past events, in full quality." sep>
          <a
            href={`${me.drive_folder_url}?authuser=${me.email}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-outline"
          >
            <img src="/static/images/google_photos.svg" alt="" className="w-4 h-4 mr-2" />
            Open in Google Photos
          </a>
          <p className="text-xs text-white/35 text-center">*only visible to you</p>
        </Section>
      )}

      <Section sep className="pb-4">
        <Link to="/app" className="btn-outline">← Home</Link>
      </Section>
    </Layout>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-center gap-0">
      <span className="text-xl font-bold">{value}</span>
      <span className="text-xs text-white/45 text-center">{label}</span>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center border-b border-white/8 pb-3 last:border-0 last:pb-0">
      <span className="text-sm text-white/45">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  )
}
