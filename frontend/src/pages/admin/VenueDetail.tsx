import { useParams, Link } from 'react-router-dom'
import { useAdminVenue } from '../../hooks/useAdmin'

function InfoRow({ label, value }: { label: string; value?: string | number | null }) {
  if (value == null || value === '') return null
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
      <span style={{ color: '#888', fontSize: 13 }}>{label}</span>
      <span style={{ color: '#fff', fontSize: 13, fontWeight: 500, textAlign: 'right', maxWidth: '60%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(value)}</span>
    </div>
  )
}

export default function AdminVenueDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: venue, isLoading } = useAdminVenue(id!)

  if (isLoading || !venue) return <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>Loading...</div>

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <Link to="/admin/venues" style={{ color: '#555', fontSize: 13, textDecoration: 'none' }}>← Back</Link>
        <Link to={`/admin/venues/${id}/edit`} style={{ color: '#fff', fontSize: 13, fontWeight: 600, textDecoration: 'none', background: '#111', border: '1px solid #333', padding: '6px 14px', borderRadius: 8 }}>Edit</Link>
      </div>

      <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, marginBottom: 24, marginTop: 0 }}>{venue.name}</h1>

      <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden', marginBottom: 20 }}>
        <InfoRow label="Name" value={venue.name} />
        <InfoRow label="Short Name" value={venue.short_name} />
        <InfoRow label="Address" value={venue.address} />
      </div>

      <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, color: '#555', marginBottom: 8 }}>Location</div>
      <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden', marginBottom: 20 }}>
        <InfoRow label="Latitude" value={venue.latitude} />
        <InfoRow label="Longitude" value={venue.longitude} />
        <InfoRow label="Google Maps" value={venue.google_maps_link} />
        <InfoRow label="Yandex Maps" value={venue.yandex_maps_link} />
      </div>
    </div>
  )
}
