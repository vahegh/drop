import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAdminVenue, useAdminCreateVenue, useAdminUpdateVenue } from '../../hooks/useAdmin'

const EMPTY = { name: '', short_name: '', area: '', address: '', latitude: '', longitude: '', google_maps_link: '', yandex_maps_link: '' }
type FormKey = keyof typeof EMPTY

function Field({ label, value, onChange, placeholder, type = 'text' }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string
}) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: 'block', color: '#888', fontSize: 12, marginBottom: 5 }}>{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        style={{ width: '100%', background: '#111', color: '#fff', border: '1px solid #1a1a1a', borderRadius: 8, padding: '10px 12px', fontSize: 14, boxSizing: 'border-box', outline: 'none' }} />
    </div>
  )
}

function Section({ title }: { title: string }) {
  return <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, color: '#555', marginTop: 24, marginBottom: 12 }}>{title}</div>
}

export default function AdminVenueForm() {
  const { id } = useParams<{ id?: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const { data: existing } = useAdminVenue(id ?? '')
  const { mutateAsync: create, isPending: creating } = useAdminCreateVenue()
  const { mutateAsync: update, isPending: updating } = useAdminUpdateVenue()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')

  useEffect(() => {
    if (existing) setForm({
      name: existing.name ?? '', short_name: existing.short_name ?? '', area: existing.area ?? '',
      address: existing.address ?? '', latitude: String(existing.latitude ?? ''), longitude: String(existing.longitude ?? ''),
      google_maps_link: existing.google_maps_link ?? '', yandex_maps_link: existing.yandex_maps_link ?? '',
    })
  }, [existing])

  function set(k: FormKey, v: string) { setForm(f => ({ ...f, [k]: v })) }

  async function submit() {
    setError('')
    try {
      const body: Record<string, unknown> = {
        name: form.name, short_name: form.short_name,
        area: form.area, address: form.address,
        latitude: parseFloat(form.latitude) || 0,
        longitude: parseFloat(form.longitude) || 0,
        google_maps_link: form.google_maps_link,
        yandex_maps_link: form.yandex_maps_link,
      }
      if (isEdit) await update({ id: id!, body })
      else await create(body)
      navigate(isEdit ? `/admin/venues/${id}` : '/admin/venues')
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed')
    }
  }

  const loading = creating || updating

  return (
    <div style={{ padding: 24, maxWidth: 520 }}>
      <Link to={isEdit ? `/admin/venues/${id}` : '/admin/venues'} style={{ color: '#555', fontSize: 13, textDecoration: 'none', display: 'inline-block', marginBottom: 20 }}>← Back</Link>
      <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, marginBottom: 24, marginTop: 0 }}>{isEdit ? 'Edit Venue' : 'New Venue'}</h1>

      <Section title="Details" />
      <Field label="Name" value={form.name} onChange={v => set('name', v)} />
      <Field label="Short Name" value={form.short_name} onChange={v => set('short_name', v)} />
      <Field label="Area" value={form.area} onChange={v => set('area', v)} placeholder="e.g. Kentron" />
      <Field label="Address" value={form.address} onChange={v => set('address', v)} />

      <Section title="Coordinates" />
      <Field label="Latitude" value={form.latitude} onChange={v => set('latitude', v)} type="number" placeholder="40.1792" />
      <Field label="Longitude" value={form.longitude} onChange={v => set('longitude', v)} type="number" placeholder="44.4991" />

      <Section title="Map Links" />
      <Field label="Google Maps URL" value={form.google_maps_link} onChange={v => set('google_maps_link', v)} />
      <Field label="Yandex Maps URL" value={form.yandex_maps_link} onChange={v => set('yandex_maps_link', v)} />

      {error && <div style={{ color: '#f44', fontSize: 13, marginBottom: 16 }}>{error}</div>}

      <button onClick={submit} disabled={loading}
        style={{ width: '100%', height: 48, background: '#fff', color: '#000', border: 'none', borderRadius: 10, fontWeight: 700, fontSize: 15, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, marginTop: 8 }}>
        {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Venue'}
      </button>
    </div>
  )
}
