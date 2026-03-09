import { Link } from 'react-router-dom'
import { useAdminEvents } from '../../hooks/useAdmin'

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function AdminEvents() {
  const { data, isLoading, isError, refetch } = useAdminEvents()

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, margin: 0 }}>Events</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button onClick={() => refetch()} style={{ color: '#555', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>Refresh</button>
          <Link to="/admin/events/create" style={{ background: '#fff', color: '#000', padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 700, textDecoration: 'none' }}>+ New</Link>
        </div>
      </div>

      {isLoading ? (
        <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>Loading...</div>
      ) : isError ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ color: '#555', fontSize: 14, marginBottom: 12 }}>Failed to load</div>
          <button onClick={() => refetch()} style={{ background: '#111', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', cursor: 'pointer' }}>Retry</button>
        </div>
      ) : (
        <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden' }}>
          {(data ?? []).length === 0 ? (
            <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>No events</div>
          ) : (
            (data ?? []).map((ev: any, i: number) => (
              <Link key={ev.id} to={`/admin/events/${ev.id}`}
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', textDecoration: 'none', borderBottom: i < data.length - 1 ? '1px solid #1a1a1a' : 'none' }}>
                <div>
                  <div style={{ color: '#fff', fontSize: 15, fontWeight: 600 }}>{ev.name}</div>
                  <div style={{ color: '#888', fontSize: 13, marginTop: 2 }}>{fmtDate(ev.starts_at)}</div>
                </div>
                <div style={{ color: '#555', fontSize: 13 }}>{ev.max_capacity} cap</div>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  )
}
