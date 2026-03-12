import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAdminPerson, useAdminUpdatePersonStatus, useAdminDeletePerson, useAdminDeleteTicket, useAdminDeletePayment, useAdminRefundPayment } from '../../hooks/useAdmin'

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

function StatusDot({ status }: { status: string }) {
  return <span style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%', background: STATUS_BG[status] ?? '#333', marginRight: 5, flexShrink: 0 }} />
}

export default function AdminPersonDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: person, isLoading } = useAdminPerson(id!)
  const { mutate: updateStatus, isPending } = useAdminUpdatePersonStatus()
  const { mutateAsync: deletePerson, isPending: deletingPerson } = useAdminDeletePerson()
  const { mutateAsync: deleteTicket } = useAdminDeleteTicket()
  const { mutateAsync: deletePayment } = useAdminDeletePayment()
  const { mutateAsync: refundPayment } = useAdminRefundPayment()

  function confirm(status: string) {
    if (window.confirm(`Set status to ${status}?`)) {
      updateStatus({ id: id!, status })
    }
  }

  async function handleDeletePerson() {
    if (!window.confirm(`Permanently delete ${person?.full_name}? This cannot be undone.`)) return
    await deletePerson(id!)
    navigate('/admin/people')
  }

  async function handleDeleteTicket(ticketId: string) {
    if (!window.confirm('Delete this ticket?')) return
    await deleteTicket(ticketId)
  }

  async function handleDeletePayment(orderId: number) {
    if (!window.confirm(`Delete payment #${orderId}?`)) return
    await deletePayment(orderId)
  }

  async function handleRefundPayment(orderId: number) {
    if (!window.confirm(`Refund payment #${orderId}?`)) return
    try {
      await refundPayment(orderId)
    } catch (e: any) {
      alert(`Refund failed: ${e?.response?.data?.detail ?? e?.message ?? 'Unknown error'}`)
    }
  }

  if (isLoading || !person) {
    return <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>Loading...</div>
  }

  const statusBg = STATUS_BG[person.status] ?? '#333'
  const tickets = person.event_tickets ?? []
  const bindings = person.card_bindings ?? []
  const payments = person.payments ?? []
  const drinkVouchers = person.drink_vouchers ?? []
  const referrals = person.referrals ?? []

  // Payments indexed by order_id for inline display in tickets
  const paymentByOrderId = new Map<any, any>(payments.map((p: any) => [p.order_id, p]))
  // Order IDs linked to tickets — excluded from the standalone payments section
  const ticketOrderIds = new Set(tickets.map((t: any) => t.payment_order_id).filter(Boolean))
  const unlinkedPayments = payments.filter((p: any) => !ticketOrderIds.has(p.order_id))

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <Link to="/admin/people" style={{ color: '#555', fontSize: 13, textDecoration: 'none' }}>← Back</Link>
        <Link to={`/admin/people/${id}/edit`} style={{ color: '#5b8fff', fontSize: 13, textDecoration: 'none', fontWeight: 500 }}>Edit</Link>
      </div>

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

      {/* Referrals */}
      {(person.referer || referrals.length > 0) && (
        <>
          <SectionTitle title="Referrals" />
          <Card>
            {person.referer && (
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
                <div style={{ color: '#888', fontSize: 11, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>Referred by</div>
                <Link to={`/admin/people/${person.referer.id}`} style={{ display: 'inline-flex', alignItems: 'center', color: '#5b8fff', fontSize: 13, fontWeight: 500, textDecoration: 'none' }}>
                  <StatusDot status={person.referer.status} />
                  {person.referer.full_name}
                  <span style={{ color: '#555', fontSize: 11, marginLeft: 6 }}>({person.referer.status})</span>
                </Link>
              </div>
            )}
            {referrals.length > 0 && (
              <div style={{ padding: '12px 16px' }}>
                <div style={{ color: '#888', fontSize: 11, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>Referred people</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {referrals.map((r: any) => (
                    <Link key={r.id} to={`/admin/people/${r.id}`} style={{ display: 'inline-flex', alignItems: 'center', color: '#5b8fff', fontSize: 13, fontWeight: 500, textDecoration: 'none' }}>
                      <StatusDot status={r.status} />
                      {r.full_name}
                      <span style={{ color: '#555', fontSize: 11, marginLeft: 6 }}>({r.status})</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </>
      )}

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
      {person.album_url && (
        <>
          <SectionTitle title="Photo Album" />
          <Card>
            <InfoRow label="Album" value="Open in Google Photos" href={person.album_url} />
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

      {/* Unlinked Payments (not tied to any ticket) */}
      {unlinkedPayments.length > 0 && (
        <>
          <SectionTitle title={`Payments (${unlinkedPayments.length})`} />
          <Card>
            {unlinkedPayments.map((p: any) => (
              <div key={p.order_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
                <div>
                  <div style={{ color: '#fff', fontSize: 13, fontWeight: 600, fontFamily: 'monospace' }}>#{p.order_id}</div>
                  <div style={{ color: '#555', fontSize: 11, marginTop: 2 }}>{p.provider} · {fmt(p.created_at)}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{p.amount.toLocaleString()} AMD</div>
                    <span style={{
                      fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 4, marginTop: 3, display: 'inline-block',
                      background: p.status === 'CONFIRMED' ? '#1a3d28' : p.status === 'REFUNDED' ? '#3d2a00' : p.status === 'REJECTED' ? '#3d1010' : '#1a1a1a',
                      color: p.status === 'CONFIRMED' ? '#4caf50' : p.status === 'REFUNDED' ? '#ffa726' : p.status === 'REJECTED' ? '#f44' : '#888',
                    }}>{p.status}</span>
                  </div>
                  {p.status === 'CONFIRMED' && <button onClick={() => handleRefundPayment(p.order_id)} style={{ background: 'none', border: 'none', color: '#ffa726', fontSize: 11, fontWeight: 600, cursor: 'pointer', padding: '4px 6px', lineHeight: 1 }} title="Refund payment">Refund</button>}
                  {p.status === 'CREATED' && <button onClick={() => handleDeletePayment(p.order_id)} style={{ background: 'none', border: 'none', color: '#555', fontSize: 16, cursor: 'pointer', padding: '4px 6px', lineHeight: 1 }} title="Delete payment">×</button>}
                </div>
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
            {tickets.map((t: any) => {
              const linkedPayment = t.payment_order_id ? paymentByOrderId.get(t.payment_order_id) : null
              return (
                <div key={t.id} style={{ padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ color: '#fff', fontSize: 13, fontWeight: 600, fontFamily: 'monospace' }}>#{t.id.slice(0, 8)}</div>
                      <div style={{ color: '#555', fontSize: 11, marginTop: 2 }}>
                        {fmt(t.created_at)}
                        {t.payment_order_id && <span style={{ color: '#444', marginLeft: 6 }}>· order #{t.payment_order_id}</span>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{
                        fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 6,
                        background: t.attended_at ? '#1a3d28' : '#1a1a1a',
                        color: t.attended_at ? '#4caf50' : '#555',
                      }}>
                        {t.attended_at ? 'attended' : 'not attended'}
                      </span>
                      <button onClick={() => handleDeleteTicket(t.id)} style={{ background: 'none', border: 'none', color: '#555', fontSize: 16, cursor: 'pointer', padding: '4px 6px', lineHeight: 1 }} title="Delete ticket">×</button>
                    </div>
                  </div>
                  {linkedPayment && (
                    <div style={{ marginTop: 8, padding: '8px 10px', background: '#0d0d0d', borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ color: '#666', fontSize: 11 }}>
                        {linkedPayment.provider} · {fmt(linkedPayment.created_at)}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ color: '#aaa', fontSize: 12, fontWeight: 600 }}>{linkedPayment.amount.toLocaleString()} AMD</span>
                        <span style={{
                          fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 4,
                          background: linkedPayment.status === 'CONFIRMED' ? '#1a3d28' : linkedPayment.status === 'REFUNDED' ? '#3d2a00' : linkedPayment.status === 'REJECTED' ? '#3d1010' : '#1a1a1a',
                          color: linkedPayment.status === 'CONFIRMED' ? '#4caf50' : linkedPayment.status === 'REFUNDED' ? '#ffa726' : linkedPayment.status === 'REJECTED' ? '#f44' : '#888',
                        }}>{linkedPayment.status}</span>
                        {linkedPayment.status === 'CONFIRMED' && <button onClick={() => handleRefundPayment(linkedPayment.order_id)} style={{ background: 'none', border: 'none', color: '#ffa726', fontSize: 11, fontWeight: 600, cursor: 'pointer', padding: '2px 4px', lineHeight: 1 }} title="Refund payment">Refund</button>}
                        {linkedPayment.status === 'CREATED' && <button onClick={() => handleDeletePayment(linkedPayment.order_id)} style={{ background: 'none', border: 'none', color: '#555', fontSize: 14, cursor: 'pointer', padding: '2px 4px', lineHeight: 1 }} title="Delete payment">×</button>}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </Card>
        </>
      )}

      {/* Drink Vouchers */}
      {drinkVouchers.length > 0 && (
        <>
          <SectionTitle title={`Drink Vouchers (${drinkVouchers.length})`} />
          <Card>
            {drinkVouchers.map((v: any) => (
              <div key={v.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
                <div>
                  <div style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{v.drink_name}</div>
                  <div style={{ color: '#555', fontSize: 11, marginTop: 2 }}>{fmt(v.created_at)}</div>
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 6,
                  background: v.used_at ? '#1a3d28' : '#1a1a1a',
                  color: v.used_at ? '#4caf50' : '#888',
                }}>
                  {v.used_at ? `used ${fmt(v.used_at)}` : 'unused'}
                </span>
              </div>
            ))}
          </Card>
        </>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
        <button onClick={handleDeletePerson} disabled={deletingPerson}
          style={{ flex: 1, height: 48, background: '#1a0a0a', color: '#f44', border: '1px solid #3d1010', borderRadius: 10, fontWeight: 700, fontSize: 15, cursor: 'pointer' }}>
          {deletingPerson ? 'Deleting…' : 'Delete Person'}
        </button>
      </div>
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
