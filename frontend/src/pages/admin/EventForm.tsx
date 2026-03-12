import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAdminEvent, useAdminCreateEvent, useAdminUpdateEvent, useAdminTiers, useAdminCreateTier, useAdminUpdateTier, useAdminDeleteTier } from '../../hooks/useAdmin'
import type { TicketTierResponse } from '../../types'
import { useAdminVenues } from '../../hooks/useAdmin'

const EMPTY = {
  name: '', description: '', image_url: '', video_url: '', album_url: '', track_url: '',
  starts_at: '', ends_at: '', venue_id: '', area: '',
  max_capacity: '', shared: 'false',
}

const EMPTY_TIER = {
  name: '', price: '', sort_order: '0', is_active: 'true',
  available_from: '', available_until: '', required_person_status: '',
  ecrm_good_code: '', ecrm_good_name: '',
}

// UTC ISO from DB → local time for the input (uses local time getters)
const toLocal = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// Local input value → UTC ISO string for the DB (e.g. "2025-06-01T18:00:00.000Z")
const fromLocal = (local: string) => {
  if (!local) return ''
  return new Date(local).toISOString()
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

function DateTimeField({ label, value, onChange }: {
  label: string; value: string; onChange: (v: string) => void
}) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: 'block', color: '#888', fontSize: 12, marginBottom: 5 }}>{label}</label>
      <input
        type="datetime-local"
        value={toLocal(value)}
        onChange={e => onChange(fromLocal(e.target.value))}
        style={{
          width: '100%', background: '#111', color: '#fff',
          border: '1px solid #1a1a1a', borderRadius: 8,
          padding: '10px 12px', fontSize: 14, boxSizing: 'border-box',
          outline: 'none', colorScheme: 'dark'  // ← makes the picker UI dark
        }}
      />
    </div>
  )
}
function SectionHeader({ title }: { title: string }) {
  return <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, color: '#555', marginTop: 24, marginBottom: 12 }}>{title}</div>
}

function TierRow({ tier, eventId, onEdit }: { tier: TicketTierResponse; eventId: string; onEdit: (t: TicketTierResponse) => void }) {
  const { mutateAsync: deleteTier } = useAdminDeleteTier(eventId)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', background: '#111', borderRadius: 8, marginBottom: 8, border: '1px solid #1a1a1a' }}>
      <div style={{ flex: 1 }}>
        <div style={{ color: '#fff', fontSize: 14 }}>{tier.name}</div>
        <div style={{ color: '#666', fontSize: 12 }}>{tier.price.toLocaleString()} AMD · sort {tier.sort_order}{tier.required_person_status ? ` · ${tier.required_person_status}` : ''}{!tier.is_active ? ' · inactive' : ''}</div>
      </div>
      <button onClick={() => onEdit(tier)} style={{ color: '#aaa', fontSize: 12, background: 'none', border: 'none', cursor: 'pointer' }}>Edit</button>
      <button onClick={() => deleteTier(tier.id)} style={{ color: '#f44', fontSize: 12, background: 'none', border: 'none', cursor: 'pointer' }}>Delete</button>
    </div>
  )
}

function TierForm({ eventId, editing, onDone }: { eventId: string; editing: TicketTierResponse | null; onDone: () => void }) {
  const { mutateAsync: createTier, isPending: creating } = useAdminCreateTier(eventId)
  const { mutateAsync: updateTier, isPending: updating } = useAdminUpdateTier(eventId)
  const [f, setF] = useState(EMPTY_TIER)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (editing) setF({
      name: editing.name,
      price: String(editing.price),
      sort_order: String(editing.sort_order),
      is_active: String(editing.is_active),
      available_from: editing.available_from ?? '',
      available_until: editing.available_until ?? '',
      required_person_status: editing.required_person_status ?? '',
      ecrm_good_code: editing.ecrm_good_code ?? '',
      ecrm_good_name: editing.ecrm_good_name ?? '',
    })
    else setF(EMPTY_TIER)
  }, [editing])

  function set(k: keyof typeof EMPTY_TIER, v: string) { setF(prev => ({ ...prev, [k]: v })) }

  async function submit() {
    setErr('')
    try {
      const body: Record<string, unknown> = {
        name: f.name,
        price: parseInt(f.price),
        sort_order: parseInt(f.sort_order),
        is_active: f.is_active === 'true',
      }
      if (f.available_from) body.available_from = f.available_from
      if (f.available_until) body.available_until = f.available_until
      if (f.required_person_status) body.required_person_status = f.required_person_status
      if (f.ecrm_good_code) body.ecrm_good_code = f.ecrm_good_code
      if (f.ecrm_good_name) body.ecrm_good_name = f.ecrm_good_name

      if (editing) await updateTier({ tierId: editing.id, body })
      else await createTier(body)
      onDone()
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? 'Failed')
    }
  }

  const loading = creating || updating

  return (
    <div style={{ background: '#0d0d0d', border: '1px solid #222', borderRadius: 10, padding: 16, marginBottom: 16 }}>
      <div style={{ color: '#aaa', fontSize: 12, marginBottom: 12 }}>{editing ? 'Edit tier' : 'New tier'}</div>
      <Field label="Name" value={f.name} onChange={v => set('name', v)} placeholder="General Admission" />
      <Field label="Price (AMD)" value={f.price} onChange={v => set('price', v)} type="number" />
      <Field label="Sort Order" value={f.sort_order} onChange={v => set('sort_order', v)} type="number" />
      <div style={{ marginBottom: 14 }}>
        <label style={{ display: 'block', color: '#888', fontSize: 12, marginBottom: 5 }}>Required Status</label>
        <select value={f.required_person_status} onChange={e => set('required_person_status', e.target.value)}
          style={{ width: '100%', background: '#111', color: '#fff', border: '1px solid #1a1a1a', borderRadius: 8, padding: '10px 12px', fontSize: 14 }}>
          <option value="">Any (no restriction)</option>
          <option value="pending">Pending</option>
          <option value="verified">Verified</option>
          <option value="member">Member</option>
        </select>
      </div>
      <Field label="Available From (ISO, optional)" value={f.available_from} onChange={v => set('available_from', v)} placeholder="2025-06-01T00:00:00" />
      <Field label="Available Until (ISO, optional)" value={f.available_until} onChange={v => set('available_until', v)} placeholder="2025-06-07T00:00:00" />
      <Field label="ECRM Good Code (optional)" value={f.ecrm_good_code} onChange={v => set('ecrm_good_code', v)} placeholder="0001" />
      <Field label="ECRM Good Name (optional)" value={f.ecrm_good_name} onChange={v => set('ecrm_good_name', v)} placeholder="General Admission Event Entry" />
      <div style={{ marginBottom: 14 }}>
        <label style={{ display: 'block', color: '#888', fontSize: 12, marginBottom: 5 }}>Active</label>
        <select value={f.is_active} onChange={e => set('is_active', e.target.value)}
          style={{ width: '100%', background: '#111', color: '#fff', border: '1px solid #1a1a1a', borderRadius: 8, padding: '10px 12px', fontSize: 14 }}>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      </div>
      {err && <div style={{ color: '#f44', fontSize: 12, marginBottom: 10 }}>{err}</div>}
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={submit} disabled={loading}
          style={{ flex: 1, height: 40, background: '#fff', color: '#000', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 14, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
          {loading ? 'Saving...' : editing ? 'Save' : 'Add Tier'}
        </button>
        <button onClick={onDone}
          style={{ padding: '0 16px', height: 40, background: 'none', color: '#666', border: '1px solid #333', borderRadius: 8, fontSize: 14, cursor: 'pointer' }}>
          Cancel
        </button>
      </div>
    </div>
  )
}

export default function AdminEventForm() {
  const { id } = useParams<{ id?: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const { data: existing } = useAdminEvent(id ?? '')
  const { data: tiers } = useAdminTiers(id ?? '')
  const { data: venues } = useAdminVenues()
  const { mutateAsync: create, isPending: creating } = useAdminCreateEvent()
  const { mutateAsync: update, isPending: updating } = useAdminUpdateEvent()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [showTierForm, setShowTierForm] = useState(false)
  const [editingTier, setEditingTier] = useState<TicketTierResponse | null>(null)

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
      venue_id: existing.venue_id ?? '',
      area: existing.area ?? '',
      max_capacity: String(existing.max_capacity ?? ''),
      shared: String(existing.shared ?? 'false'),
    })
  }, [existing])

  function set(k: FormKey, v: string) { setForm(f => ({ ...f, [k]: v })) }

  async function submit() {
    setError('')
    try {
        const body: Record<string, unknown> = {
        name: form.name,
        description: form.description,
        image_url: form.image_url,
        video_url: form.video_url || null,
        album_url: form.album_url || null,
        track_url: form.track_url || null,
        starts_at: form.starts_at,
        ends_at: form.ends_at,
        venue_id: form.venue_id,
        area: form.area || null,
        max_capacity: parseInt(form.max_capacity),
        shared: form.shared === 'true',
      }
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

      <SectionHeader title="Details" />
      <Field label="Name" value={form.name} onChange={v => set('name', v)} />
      <Field label="Description" value={form.description} onChange={v => set('description', v)} />

      <SectionHeader title="Media" />
      <Field label="Image URL" value={form.image_url} onChange={v => set('image_url', v)} />
      <Field label="Video URL (optional)" value={form.video_url} onChange={v => set('video_url', v)} />
      <Field label="Album URL (optional)" value={form.album_url} onChange={v => set('album_url', v)} />
      <Field label="Track URL (optional)" value={form.track_url} onChange={v => set('track_url', v)} />

      <SectionHeader title="Dates (ISO format)" />
        <DateTimeField label="Starts at" value={form.starts_at} onChange={v => set('starts_at', v)} />
        <DateTimeField label="Ends at" value={form.ends_at} onChange={v => set('ends_at', v)} />

      <SectionHeader title="Venue & Capacity" />
      <Field label="Area hint (optional, e.g. Kentron)" value={form.area} onChange={v => set('area', v)} />
        <div style={{ marginBottom: 14 }}>
        <label style={{ display: 'block', color: '#888', fontSize: 12, marginBottom: 5 }}>Venue</label>
        <select
            value={form.venue_id}
            onChange={e => set('venue_id', e.target.value)}
            style={{ width: '100%', background: '#111', color: '#fff', border: '1px solid #1a1a1a', borderRadius: 8, padding: '10px 12px', fontSize: 14 }}
        >
            <option value="">Select a venue...</option>
            {(venues ?? []).map((v: { id: string; name: string }) => (
            <option key={v.id} value={v.id}>{v.name}</option>
            ))}
        </select>
        </div>
      <Field label="Max Capacity" value={form.max_capacity} onChange={v => set('max_capacity', v)} type="number" />

      <SectionHeader title="Other" />
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

      {isEdit && id && (
        <>
          <SectionHeader title="Ticket Tiers" />
          {(tiers ?? []).map((t: TicketTierResponse) => (
            <TierRow key={t.id} tier={t} eventId={id} onEdit={tier => { setEditingTier(tier); setShowTierForm(true) }} />
          ))}
          {showTierForm || editingTier ? (
            <TierForm
              eventId={id}
              editing={editingTier}
              onDone={() => { setShowTierForm(false); setEditingTier(null) }}
            />
          ) : (
            <button onClick={() => setShowTierForm(true)}
              style={{ width: '100%', height: 40, background: 'none', color: '#aaa', border: '1px solid #333', borderRadius: 8, fontSize: 14, cursor: 'pointer', marginTop: 4 }}>
              + Add Tier
            </button>
          )}
        </>
      )}
    </div>
  )
}
