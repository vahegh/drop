import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAdminEvent, useAdminCreateEvent, useAdminUpdateEvent } from '../../hooks/useAdmin'

const EMPTY = {
  name: '', description: '', image_url: '', video_url: '', album_url: '', track_url: '',
  starts_at: '', ends_at: '', early_bird_date: '', venue_id: '',
  max_capacity: '', general_admission_price: '', early_bird_price: '', member_ticket_price: '', shared: 'false',
}

type FormKey = keyof typeof EMPTY

function Field({ label, value, onChange, placeholder, type = 'text' }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string
}) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: 'block', color: '#888', fontSize: 12, marginBottom: 5 }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{ width: '100%', background: '#111', color: '#fff', border: '1px solid #1a1a1a', borderRadius: 8, padding: '10px 12px', fontSize: 14, boxSizing: 'border-box', outline: 'none' }}
      />
    </div>
  )
}

function Section({ title }: { title: string }) {
  return <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, color: '#555', marginTop: 24, marginBottom: 12 }}>{title}</div>
}

export default function AdminEventForm() {
  const { id } = useParams<{ id?: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const { data: existing } = useAdminEvent(id ?? '')
  const { mutateAsync: create, isPending: creating } = useAdminCreateEvent()
  const { mutateAsync: update, isPending: updating } = useAdminUpdateEvent()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')

  useEffect(() => {
    if (existing) setForm({
      name: existing.name ?? '',
      description: existing.description ?? '',
      image_url: existing.image_url ?? '',
      video_url: existing.video_url ?? '',
      album_url: existing.album_url ?? '',
      track_url: existing.track_url ?? '',
      starts_at: existing.starts_at ?? '',
      ends_at: existing.ends_at ?? '',
      early_bird_date: existing.early_bird_date ?? '',
      venue_id: existing.venue_id ?? '',
      max_capacity: String(existing.max_capacity ?? ''),
      general_admission_price: String(existing.general_admission_price ?? ''),
      early_bird_price: String(existing.early_bird_price ?? ''),
      member_ticket_price: String(existing.member_ticket_price ?? ''),
      shared: String(existing.shared ?? 'false'),
    })
  }, [existing])

  function set(k: FormKey, v: string) { setForm(f => ({ ...f, [k]: v })) }

  async function submit() {
    setError('')
    try {
      const body: Record<string, unknown> = {
        name: form.name, description: form.description, image_url: form.image_url,
        starts_at: form.starts_at, ends_at: form.ends_at, venue_id: form.venue_id,
        general_admission_price: parseInt(form.general_admission_price),
        member_ticket_price: parseInt(form.member_ticket_price),
        max_capacity: parseInt(form.max_capacity),
        shared: form.shared === 'true',
      }
      if (form.video_url) body.video_url = form.video_url
      if (form.album_url) body.album_url = form.album_url
      if (form.track_url) body.track_url = form.track_url
      if (form.early_bird_date) body.early_bird_date = form.early_bird_date
      if (form.early_bird_price) body.early_bird_price = parseInt(form.early_bird_price)

      if (isEdit) await update({ id: id!, body })
      else await create(body)
      navigate(isEdit ? `/admin/events/${id}` : '/admin/events')
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed')
    }
  }

  const loading = creating || updating

  return (
    <div style={{ padding: 24, maxWidth: 520 }}>
      <Link to={isEdit ? `/admin/events/${id}` : '/admin/events'} style={{ color: '#555', fontSize: 13, textDecoration: 'none', display: 'inline-block', marginBottom: 20 }}>← Back</Link>
      <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, marginBottom: 24, marginTop: 0 }}>{isEdit ? 'Edit Event' : 'New Event'}</h1>

      <Section title="Details" />
      <Field label="Name" value={form.name} onChange={v => set('name', v)} />
      <Field label="Description" value={form.description} onChange={v => set('description', v)} />

      <Section title="Media" />
      <Field label="Image URL" value={form.image_url} onChange={v => set('image_url', v)} />
      <Field label="Video URL (optional)" value={form.video_url} onChange={v => set('video_url', v)} />
      <Field label="Album URL (optional)" value={form.album_url} onChange={v => set('album_url', v)} />
      <Field label="Track URL (optional)" value={form.track_url} onChange={v => set('track_url', v)} />

      <Section title="Dates (ISO format)" />
      <Field label="Starts at" value={form.starts_at} onChange={v => set('starts_at', v)} placeholder="2025-06-01T22:00:00" />
      <Field label="Ends at" value={form.ends_at} onChange={v => set('ends_at', v)} placeholder="2025-06-02T06:00:00" />
      <Field label="Early Bird Cutoff (optional)" value={form.early_bird_date} onChange={v => set('early_bird_date', v)} placeholder="2025-05-25T00:00:00" />

      <Section title="Venue & Capacity" />
      <Field label="Venue ID (UUID)" value={form.venue_id} onChange={v => set('venue_id', v)} />
      <Field label="Max Capacity" value={form.max_capacity} onChange={v => set('max_capacity', v)} type="number" />

      <Section title="Pricing (AMD)" />
      <Field label="General Admission" value={form.general_admission_price} onChange={v => set('general_admission_price', v)} type="number" />
      <Field label="Early Bird (optional)" value={form.early_bird_price} onChange={v => set('early_bird_price', v)} type="number" />
      <Field label="Member" value={form.member_ticket_price} onChange={v => set('member_ticket_price', v)} type="number" />

      <Section title="Other" />
      <div style={{ marginBottom: 14 }}>
        <label style={{ color: '#888', fontSize: 12, marginBottom: 5, display: 'block' }}>Shared</label>
        <select value={form.shared} onChange={e => set('shared', e.target.value)}
          style={{ background: '#111', color: '#fff', border: '1px solid #1a1a1a', borderRadius: 8, padding: '10px 12px', fontSize: 14, width: '100%' }}>
          <option value="false">No</option>
          <option value="true">Yes</option>
        </select>
      </div>

      {error && <div style={{ color: '#f44', fontSize: 13, marginBottom: 16 }}>{error}</div>}

      <button onClick={submit} disabled={loading}
        style={{ width: '100%', height: 48, background: '#fff', color: '#000', border: 'none', borderRadius: 10, fontWeight: 700, fontSize: 15, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, marginTop: 8 }}>
        {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Event'}
      </button>
    </div>
  )
}
