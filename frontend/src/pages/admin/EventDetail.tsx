import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAdminEvent, useAdminDeleteEvent } from '../../hooks/useAdmin'

function InfoRow({ label, value }: { label: string; value?: string | number | null }) {
  if (value == null) return null
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #1a1a1a', gap: 12 }}>
      <span style={{ color: '#888', fontSize: 13, flexShrink: 0 }}>{label}</span>
      <span style={{ color: '#fff', fontSize: 13, fontWeight: 500, wordBreak: 'break-all', textAlign: 'right' }}>{String(value)}</span>
    </div>
  )
}

function fmt(iso: string) {
  return new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function AdminEventDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: ev, isLoading } = useAdminEvent(id!)
  const { mutateAsync: deleteEvent, isPending: deleting } = useAdminDeleteEvent()

  async function handleDelete() {
    if (!window.confirm(`Delete "${ev?.name}"? This cannot be undone.`)) return
    await deleteEvent(id!)
    navigate('/admin/events')
  }

  if (isLoading || !ev) return <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>Loading...</div>

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <Link to="/admin/events" style={{ color: '#555', fontSize: 13, textDecoration: 'none' }}>← Back</Link>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button onClick={handleDelete} disabled={deleting} style={{ background: 'none', border: 'none', color: '#7a1010', fontSize: 13, cursor: 'pointer', fontWeight: 600 }}>
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
          <Link to={`/event/${id}`} style={{ color: '#888', fontSize: 13, fontWeight: 600, textDecoration: 'none', background: '#111', border: '1px solid #333', padding: '6px 14px', borderRadius: 8 }}>View</Link>
          <Link to={`/admin/events/${id}/edit`} style={{ color: '#fff', fontSize: 13, fontWeight: 600, textDecoration: 'none', background: '#111', border: '1px solid #333', padding: '6px 14px', borderRadius: 8 }}>Edit</Link>
        </div>
      </div>

      <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, marginBottom: 24, marginTop: 0 }}>{ev.name}</h1>

      <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden', marginBottom: 20 }}>
        <InfoRow label="Starts" value={fmt(ev.starts_at)} />
        <InfoRow label="Ends" value={fmt(ev.ends_at)} />
        <InfoRow label="Capacity" value={ev.max_capacity} />
        <InfoRow label="Shared" value={ev.shared ? 'Yes' : 'No'} />
      </div>

      {(ev.video_url || ev.album_url || ev.track_url) && (
        <>
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, color: '#555', marginBottom: 8 }}>Media</div>
          <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden', marginBottom: 20 }}>
            {ev.image_url && <InfoRow label="Image" value={ev.image_url} />}
            {ev.video_url && <InfoRow label="Video" value={ev.video_url} />}
            {ev.album_url && <InfoRow label="Album" value={ev.album_url} />}
            {ev.track_url && <InfoRow label="Track" value={ev.track_url} />}
          </div>
        </>
      )}
    </div>
  )
}
