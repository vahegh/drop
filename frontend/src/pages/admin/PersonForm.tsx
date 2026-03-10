import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAdminPerson, useAdminUpdatePerson } from '../../hooks/useAdmin'

const EMPTY = {
  first_name: '', last_name: '', email: '', instagram_handle: '',
  telegram_handle: '', album_url: '', avatar_url: '', referer_id: '',
}

type FormKey = keyof typeof EMPTY

function Field({ label, value, onChange, type = 'text', placeholder }: {
  label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string
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

export default function AdminPersonForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: existing } = useAdminPerson(id ?? '')
  const { mutateAsync: update, isPending } = useAdminUpdatePerson()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')

  useEffect(() => {
    if (existing) setForm({
      first_name: existing.first_name ?? '',
      last_name: existing.last_name ?? '',
      email: existing.email ?? '',
      instagram_handle: existing.instagram_handle ?? '',
      telegram_handle: existing.telegram_handle ?? '',
      album_url: existing.album_url ?? '',
      avatar_url: existing.avatar_url ?? '',
      referer_id: existing.referer_id ?? '',
    })
  }, [existing])

  function set(k: FormKey, v: string) { setForm(f => ({ ...f, [k]: v })) }

  async function submit() {
    setError('')
    try {
      const body: Record<string, unknown> = {
        first_name: form.first_name || undefined,
        last_name: form.last_name || undefined,
        email: form.email || undefined,
        instagram_handle: form.instagram_handle || undefined,
        telegram_handle: form.telegram_handle || undefined,
        album_url: form.album_url || undefined,
        avatar_url: form.avatar_url || undefined,
        referer_id: form.referer_id || undefined,
      }
      await update({ id: id!, body })
      navigate(`/admin/people/${id}`)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed')
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 520 }}>
      <Link to={`/admin/people/${id}`} style={{ color: '#555', fontSize: 13, textDecoration: 'none', display: 'inline-block', marginBottom: 20 }}>← Back</Link>
      <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, marginBottom: 24, marginTop: 0 }}>Edit Person</h1>

      <Section title="Name" />
      <Field label="First Name" value={form.first_name} onChange={v => set('first_name', v)} />
      <Field label="Last Name" value={form.last_name} onChange={v => set('last_name', v)} />

      <Section title="Contact" />
      <Field label="Email" value={form.email} onChange={v => set('email', v)} type="email" />
      <Field label="Instagram Handle" value={form.instagram_handle} onChange={v => set('instagram_handle', v)} placeholder="without @" />
      <Field label="Telegram Handle" value={form.telegram_handle} onChange={v => set('telegram_handle', v)} placeholder="optional" />

      <Section title="Links" />
      <Field label="Album URL" value={form.album_url} onChange={v => set('album_url', v)} placeholder="optional" />
      <Field label="Avatar URL" value={form.avatar_url} onChange={v => set('avatar_url', v)} placeholder="optional" />

      <Section title="Referral" />
      <Field label="Referer ID (UUID)" value={form.referer_id} onChange={v => set('referer_id', v)} placeholder="optional" />

      {error && <div style={{ color: '#f44', fontSize: 13, marginBottom: 16 }}>{error}</div>}

      <button onClick={submit} disabled={isPending}
        style={{ width: '100%', height: 48, background: '#fff', color: '#000', border: 'none', borderRadius: 10, fontWeight: 700, fontSize: 15, cursor: isPending ? 'not-allowed' : 'pointer', opacity: isPending ? 0.7 : 1, marginTop: 8 }}>
        {isPending ? 'Saving...' : 'Save Changes'}
      </button>
    </div>
  )
}
