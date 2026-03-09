import { useParams, Link } from 'react-router-dom'
import { useAdminPerson, useAdminUpdatePersonStatus } from '../../hooks/useAdmin'

const STATUS_BG: Record<string, string> = {
  pending: '#555', verified: '#1a6e3c', member: '#4a2fa0', rejected: '#7a1010',
}

function InfoRow({ label, value, href }: { label: string; value?: string | number | null; href?: string }) {
  if (value == null || value === '') return null
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
      <span style={{ color: '#888', fontSize: 13 }}>{label}</span>
      {href ? (
        <a href={href} target="_blank" rel="noreferrer" style={{ color: '#5b8fff', fontSize: 13, fontWeight: 500, textAlign: 'right', maxWidth: '60%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(value)}</a>
      ) : (
        <span style={{ color: '#fff', fontSize: 13, fontWeight: 500, textAlign: 'right', maxWidth: '60%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(value)}</span>
      )}
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

function SectionTitle({ title }: { title: string }) {
  return <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, color: '#555', marginBottom: 8 }}>{title}</div>
}

function fmt(iso?: string | null) {
  if (!iso) return null
  return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function AdminPersonDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: person, isLoading } = useAdminPerson(id!)
  const { mutate: updateStatus, isPending } = useAdminUpdatePersonStatus()

  function confirm(status: string) {
    if (window.confirm(`Set status to ${status}?`)) {
      updateStatus({ id: id!, status })
    }
  }

  if (isLoading || !person) {
    return <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>Loading...</div>
  }

  const statusBg = STATUS_BG[person.status] ?? '#333'
  const tickets = person.event_tickets ?? []
  const bindings = person.card_bindings ?? []

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <Link to="/admin/people" style={{ color: '#555', fontSize: 13, textDecoration: 'none', display: 'inline-block', marginBottom: 20 }}>← Back</Link>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 }}>
        {person.avatar_url ? (
          <img src={person.avatar_url} alt="" style={{ width: 60, height: 60, borderRadius: 30, objectFit: 'cover' }} />
        ) : (
          <div style={{ width: 60, height: 60, borderRadius: 30, background: '#222', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 700, color: '#fff' }}>
            {person.first_name?.[0]}{person.last_name?.[0]}
          </div>
        )}
        <div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#fff', marginBottom: 8 }}>{person.first_name} {person.last_name}</div>
          <span style={{ background: statusBg, color: '#fff', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 10, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            {person.status}
          </span>
        </div>
      </div>

      {/* Contact */}
      <SectionTitle title="Contact" />
      <Card>
        <InfoRow label="Email" value={person.email} href={`mailto:${person.email}`} />
        <InfoRow label="Instagram" value={person.instagram_handle ? `@${person.instagram_handle}` : null} href={person.instagram_handle ? `https://instagram.com/${person.instagram_handle}` : undefined} />
        <InfoRow label="Telegram" value={person.telegram_handle ? `@${person.telegram_handle}` : null} href={person.telegram_handle ? `https://t.me/${person.telegram_handle.replace('@','')}` : undefined} />
      </Card>

      {/* Stats */}
      <SectionTitle title="Stats" />
      <Card>
        <InfoRow label="Events Attended" value={person.events_attended} />
        <InfoRow label="Total Tickets" value={tickets.length} />
        <InfoRow label="Referrals" value={person.referral_count} />
      </Card>

      {/* Member Pass */}
      {person.member_pass && (
        <>
          <SectionTitle title="Member Pass" />
          <Card>
            <InfoRow label="Serial #" value={person.member_pass.serial_number} />
            <InfoRow label="Apple Pass" value="Open" href={person.member_pass.apple_pass_url} />
            <InfoRow label="Google Pass" value="Open" href={person.member_pass.google_pass_url} />
            <InfoRow label="Issued" value={fmt(person.member_pass.created_at)} />
          </Card>
        </>
      )}

      {/* Drive */}
      {person.drive_folder_url && (
        <>
          <SectionTitle title="Drive" />
          <Card>
            <InfoRow label="Folder" value="Open in Drive" href={person.drive_folder_url} />
          </Card>
        </>
      )}

      {/* Cards */}
      {bindings.length > 0 && (
        <>
          <SectionTitle title={`Saved Cards (${bindings.length})`} />
          <Card>
            {bindings.map((b: any) => (
              <div key={b.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
                <span style={{ color: '#fff', fontSize: 13, fontFamily: 'monospace' }}>{b.masked_card_number}</span>
                <span style={{ color: '#888', fontSize: 12 }}>exp {b.card_expiry_date} · {b.is_active ? '✓ active' : 'inactive'}</span>
              </div>
            ))}
          </Card>
        </>
      )}

      {/* Tickets */}
      {tickets.length > 0 && (
        <>
          <SectionTitle title={`Tickets (${tickets.length})`} />
          <Card>
            {tickets.map((t: any) => (
              <div key={t.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
                <div>
                  <div style={{ color: '#fff', fontSize: 13, fontWeight: 600, fontFamily: 'monospace' }}>#{t.id.slice(0, 8)}</div>
                  <div style={{ color: '#555', fontSize: 11, marginTop: 2 }}>{fmt(t.created_at)}</div>
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 6,
                  background: t.attended_at ? '#1a3d28' : '#1a1a1a',
                  color: t.attended_at ? '#4caf50' : '#555',
                }}>
                  {t.attended_at ? 'attended' : 'not attended'}
                </span>
              </div>
            ))}
          </Card>
        </>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
        {person.status !== 'verified' && (
          <button onClick={() => confirm('verified')} disabled={isPending}
            style={{ flex: 1, height: 48, background: '#1a6e3c', color: '#fff', border: 'none', borderRadius: 10, fontWeight: 700, fontSize: 15, cursor: 'pointer' }}>
            Verify
          </button>
        )}
        {person.status !== 'member' && (
          <button onClick={() => confirm('member')} disabled={isPending}
            style={{ flex: 1, height: 48, background: '#4a2fa0', color: '#fff', border: 'none', borderRadius: 10, fontWeight: 700, fontSize: 15, cursor: 'pointer' }}>
            Member
          </button>
        )}
        {person.status !== 'rejected' && (
          <button onClick={() => confirm('rejected')} disabled={isPending}
            style={{ flex: 1, height: 48, background: '#7a1010', color: '#fff', border: 'none', borderRadius: 10, fontWeight: 700, fontSize: 15, cursor: 'pointer' }}>
            Reject
          </button>
        )}
      </div>
    </div>
  )
}
