import { Link } from 'react-router-dom'
import { useAdminVenues } from '../../hooks/useAdmin'

export default function AdminVenues() {
  const { data, isLoading, isError, refetch } = useAdminVenues()

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, margin: 0 }}>Venues</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button onClick={() => refetch()} style={{ color: '#555', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>Refresh</button>
          <Link to="/admin/venues/create" style={{ background: '#fff', color: '#000', padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 700, textDecoration: 'none' }}>+ New</Link>
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
            <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>No venues</div>
          ) : (
            (data ?? []).map((v: any, i: number) => (
              <Link key={v.id} to={`/admin/venues/${v.id}`}
                style={{ display: 'block', padding: '14px 16px', textDecoration: 'none', borderBottom: i < data.length - 1 ? '1px solid #1a1a1a' : 'none' }}>
                <div style={{ color: '#fff', fontSize: 15, fontWeight: 600 }}>{v.name}</div>
                {v.address && <div style={{ color: '#888', fontSize: 13, marginTop: 2 }}>{v.address}</div>}
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  )
}
