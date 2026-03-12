import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMe } from '../hooks/useMe'
import { useTickets } from '../hooks/useTickets'
import { useEvents } from '../hooks/useEvents'
import { updateMe, uploadAvatar } from '../api/people'
import { useQueryClient } from '@tanstack/react-query'
import Layout from '../components/Layout'
import { STATUS_COLORS } from '../components/Layout'
import MemberPassCard from '../components/MemberPassCard'
import EventTicketCard from '../components/EventTicketCard'
import { loginUrl } from '../lib/loginUrl'
import type { PersonUpdate } from '../types'

function SectionTitle({ title }: { title: string }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, color: '#555', marginBottom: 8 }}>
      {title}
    </div>
  )
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden', marginBottom: 20 }}>
      {children}
    </div>
  )
}

function InfoRow({ label, value, href }: { label: string; value: string; href?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
      <span style={{ color: '#888', fontSize: 13 }}>{label}</span>
      {href ? (
        <a href={href} target="_blank" rel="noreferrer" style={{ color: '#5b8fff', fontSize: 13, fontWeight: 500, textAlign: 'right', maxWidth: '65%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</a>
      ) : (
        <span style={{ color: '#fff', fontSize: 13, fontWeight: 500, textAlign: 'right', maxWidth: '65%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</span>
      )}
    </div>
  )
}

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
      <div style={{ padding: '24px 16px', width: '100%', maxWidth: 480 }}>
        <div className="flex flex-col items-center gap-3 mb-8">
          <div className="skeleton w-20 h-20 rounded-full" />
          <div className="skeleton h-5 w-40" />
          <div className="skeleton h-4 w-24" />
        </div>
        <div className="skeleton h-4 w-16 mb-2" />
        <div className="skeleton h-28 w-full rounded-xl mb-5" />
        <div className="skeleton h-4 w-16 mb-2" />
        <div className="skeleton h-20 w-full rounded-xl" />
      </div>
    </Layout>
  )

  if (error || !me) {
    window.location.href = loginUrl('/profile')
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
      <div style={{ padding: '24px 16px', width: '100%', maxWidth: 480 }}>

        {/* Avatar + name */}
        <div className="flex flex-col items-center gap-3 mb-8">
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
                style={{ background: '#1a1a1a' }}
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
            <div className="font-bold text-xl mb-1">{me.full_name}</div>
            <div className="flex items-center justify-center gap-2">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: STATUS_COLORS[me.status] }} />
              <span className="text-xs uppercase tracking-widest" style={{ color: STATUS_COLORS[me.status] }}>{me.status}</span>
            </div>
          </div>
        </div>

        {/* Contact / Edit */}
        {editing ? (
          <>
            <SectionTitle title="Edit Profile" />
            <Card>
              {(
                [
                  ['First name', 'first_name', me.first_name],
                  ['Last name', 'last_name', me.last_name],
                  ['Instagram', 'instagram_handle', me.instagram_handle],
                  ['Telegram', 'telegram_handle', me.telegram_handle ?? ''],
                ] as [string, keyof PersonUpdate, string][]
              ).map(([label, field, defaultValue]) => (
                <div key={field} style={{ padding: '10px 16px', borderBottom: '1px solid #1a1a1a' }}>
                  <div style={{ color: '#888', fontSize: 11, marginBottom: 6 }}>{label}</div>
                  <input
                    className="drop-input w-full rounded-lg px-3 py-2 text-sm"
                    style={{ background: '#0d0d0d', borderRadius: 8 }}
                    defaultValue={defaultValue}
                    onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                  />
                </div>
              ))}
              <div style={{ display: 'flex', gap: 8, padding: '12px 16px' }}>
                <button onClick={handleSave} disabled={saving} className="btn-primary flex-1" style={{ maxWidth: 'none' }}>
                  {saving ? 'Saving…' : 'Save'}
                </button>
                <button onClick={() => setEditing(false)} className="btn-outline flex-1" style={{ maxWidth: 'none' }}>
                  Cancel
                </button>
              </div>
            </Card>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <SectionTitle title="Contact" />
              <button
                onClick={() => setEditing(true)}
                style={{ background: 'none', border: 'none', color: '#5b8fff', fontSize: 12, fontWeight: 500, cursor: 'pointer', padding: 0, marginBottom: 8 }}
              >
                Edit
              </button>
            </div>
            <Card>
              <InfoRow label="Email" value={me.email} />
              <InfoRow label="Instagram" value={`@${me.instagram_handle}`} href={`https://instagram.com/${me.instagram_handle}`} />
              {me.telegram_handle && <InfoRow label="Telegram" value={`@${me.telegram_handle}`} href={`https://t.me/${me.telegram_handle.replace('@', '')}`} />}
            </Card>
          </>
        )}

        {/* Stats */}
        <SectionTitle title="Stats" />
        <Card>
          <InfoRow label="Events attended" value={String(me.events_attended)} />
          {me.event_tickets.length > 0 && <InfoRow label="Tickets" value={String(me.event_tickets.length)} />}
          {me.member_pass && <InfoRow label="Member #" value={String(me.member_pass.serial_number)} />}
          {me.referral_count > 0 && <InfoRow label="Referrals" value={String(me.referral_count)} />}
        </Card>

        {/* Referrals */}
        {(me.referer || (me.referrals && me.referrals.length > 0)) && (
          <>
            <SectionTitle title="Referrals" />
            <Card>
              {me.referer && (
                <div style={{ padding: '12px 16px', borderBottom: me.referrals?.length ? '1px solid #1a1a1a' : undefined }}>
                  <div style={{ color: '#888', fontSize: 11, marginBottom: 6 }}>Referred by</div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: STATUS_COLORS[me.referer.status] }} />
                    <span style={{ color: '#fff', fontSize: 13, fontWeight: 500 }}>{me.referer.full_name}</span>
                    <span style={{ color: '#555', fontSize: 11 }}>({me.referer.status})</span>
                  </div>
                </div>
              )}
              {me.referrals && me.referrals.length > 0 && (
                <div style={{ padding: '12px 16px' }}>
                  <div style={{ color: '#888', fontSize: 11, marginBottom: 8 }}>People you referred</div>
                  <div className="flex flex-col gap-2">
                    {me.referrals.map((r) => (
                      <div key={r.id} className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: STATUS_COLORS[r.status] }} />
                        <span style={{ color: '#fff', fontSize: 13 }}>{r.full_name}</span>
                        <span style={{ color: '#555', fontSize: 11 }}>({r.status})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </>
        )}

        {/* Member pass */}
        {me.member_pass && (
          <div style={{ marginBottom: 20 }}>
            <SectionTitle title="Membership Pass" />
            <div className="flex justify-center">
              <MemberPassCard pass={me.member_pass} eventsAttended={me.events_attended} />
            </div>
          </div>
        )}

        {/* Upcoming ticket */}
        {me.status !== 'member' && pendingTickets.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <SectionTitle title="Your Ticket" />
            <div style={{ color: '#555', fontSize: 11, marginBottom: 10 }}>Show this at the entrance</div>
            <div className="flex flex-col items-center gap-4">
              {pendingTickets.map((ticket) => {
                const ev = eventMap.get(ticket.event_id)
                if (!ev) return null
                return <EventTicketCard key={ticket.id} ticket={ticket} event={ev} />
              })}
            </div>
          </div>
        )}

        {/* Past tickets */}
        {pastTickets.length > 0 && (
          <>
            <SectionTitle title="Past Events" />
            <Card>
              {pastTickets.map((ticket) => {
                const ev = eventMap.get(ticket.event_id)
                return (
                  <div
                    key={ticket.id}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #1a1a1a', opacity: 0.7 }}
                  >
                    <div>
                      <div style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{ev?.name ?? 'Event'}</div>
                      <div style={{ color: '#555', fontSize: 11, marginTop: 2 }}>
                        {new Date(ticket.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
                      </div>
                    </div>
                    {ticket.attended_at && (
                      <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 6, background: '#1a3d28', color: '#4caf50' }}>
                        Attended
                      </span>
                    )}
                  </div>
                )
              })}
            </Card>
          </>
        )}

        {/* Google Photos */}
        {me.album_url && (
          <>
            <SectionTitle title="Your Photos" />
            <Card>
              <a
                href={`${me.album_url}?authuser=${me.email}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', color: '#5b8fff', fontSize: 13, fontWeight: 500, textDecoration: 'none' }}
              >
                <img src="/static/images/google_photos.svg" alt="" style={{ width: 16, height: 16 }} />
                Open in Google Photos
              </a>
            </Card>
            <div style={{ color: '#444', fontSize: 11, marginTop: -16, marginBottom: 20 }}>*only visible to you</div>
          </>
        )}

        <div style={{ marginTop: 8 }}>
          <Link to="/" className="btn-outline" style={{ display: 'inline-block' }}>← Home</Link>
        </div>

      </div>
    </Layout>
  )
}
