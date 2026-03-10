import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAdminPeople, useAdminCreatePerson } from '../../hooks/useAdmin'

const STATUSES = ['all', 'pending', 'verified', 'member', 'rejected']

const STATUS_BG: Record<string, string> = {
  pending: '#555', verified: '#1a6e3c', member: '#4a2fa0', rejected: '#7a1010',
}

const EMPTY_FORM = { first_name: '', last_name: '', email: '', instagram_handle: '', telegram_handle: '' }

export default function AdminPeople() {
  const [filter, setFilter] = useState<string | undefined>(undefined)
  const { data, isLoading, isError, refetch } = useAdminPeople(filter)
  const createMutation = useAdminCreatePerson()

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState<string | null>(null)

  function field(key: keyof typeof EMPTY_FORM) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm(f => ({ ...f, [key]: e.target.value }))
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    try {
      await createMutation.mutateAsync({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        instagram_handle: form.instagram_handle,
        telegram_handle: form.telegram_handle || undefined,
      })
      setForm(EMPTY_FORM)
      setShowForm(false)
    } catch (err: any) {
      setFormError(err?.response?.data?.detail ?? 'Failed to create person')
    }
  }

  const inputStyle: React.CSSProperties = {
    width: '100%', background: '#0a0a0a', border: '1px solid #2a2a2a', borderRadius: 8,
    color: '#fff', fontSize: 13, padding: '8px 12px', outline: 'none', boxSizing: 'border-box',
  }

  return (
    <div className="p-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">People</h1>
        <div className="flex gap-3">
          <button
            onClick={() => { setShowForm(s => !s); setFormError(null) }}
            className="text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
            style={{ background: showForm ? '#333' : '#fff', color: showForm ? '#fff' : '#000' }}
          >
            {showForm ? 'Cancel' : '+ New'}
          </button>
          <button onClick={() => refetch()} className="text-[#555] text-sm hover:text-white">Refresh</button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-[#111] rounded-xl border border-[#1a1a1a] p-4 mb-4 flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3">
            <input required placeholder="First name" value={form.first_name} onChange={field('first_name')} style={inputStyle} />
            <input required placeholder="Last name" value={form.last_name} onChange={field('last_name')} style={inputStyle} />
          </div>
          <input required type="email" placeholder="Email" value={form.email} onChange={field('email')} style={inputStyle} />
          <input required placeholder="Instagram handle" value={form.instagram_handle} onChange={field('instagram_handle')} style={inputStyle} />
          <input placeholder="Telegram handle (optional)" value={form.telegram_handle} onChange={field('telegram_handle')} style={inputStyle} />
          {formError && <div style={{ color: '#fb2c36', fontSize: 12 }}>{formError}</div>}
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="self-end px-4 py-2 rounded-lg text-sm font-semibold"
            style={{ background: '#fff', color: '#000', opacity: createMutation.isPending ? 0.5 : 1 }}
          >
            {createMutation.isPending ? 'Creating…' : 'Create'}
          </button>
        </form>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        {STATUSES.map(st => (
          <button
            key={st}
            onClick={() => setFilter(st === 'all' ? undefined : st)}
            className="px-3 py-1.5 rounded-full text-sm font-medium transition-colors"
            style={{
              background: (filter ?? 'all') === st ? '#fff' : '#111',
              color: (filter ?? 'all') === st ? '#000' : '#888',
              border: 'none', cursor: 'pointer',
            }}
          >
            {st}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-[#555] text-sm mt-8 text-center">Loading...</div>
      ) : isError ? (
        <div className="text-center mt-8">
          <div className="text-[#555] text-sm mb-3">Failed to load</div>
          <button onClick={() => refetch()} className="text-sm text-white bg-[#111] px-4 py-2 rounded-lg">Retry</button>
        </div>
      ) : (
        <div className="bg-[#111] rounded-xl border border-[#1a1a1a] overflow-hidden">
          {(data ?? []).length === 0 ? (
            <div className="text-[#555] text-sm text-center py-10">No people found</div>
          ) : (
            (() => {
              const ORDER: Record<string, number> = { pending: 0, member: 1, verified: 2, rejected: 3 }
              const sorted = [...(data ?? [])].sort((a: any, b: any) =>
                (ORDER[a.status] ?? 9) - (ORDER[b.status] ?? 9)
              )
              return sorted.map((person: any, i: number) => (
              <Link
                key={person.id}
                to={`/admin/people/${person.id}`}
                className="flex items-center justify-between px-4 py-3 no-underline hover:bg-[#161616] transition-colors"
                style={{ borderBottom: i < sorted.length - 1 ? '1px solid #1a1a1a' : 'none' }}
              >
                <span className="text-white text-[15px]">{person.first_name} {person.last_name}</span>
                <span className="px-2.5 py-1 rounded-full text-[11px] font-medium text-white"
                  style={{ background: STATUS_BG[person.status] ?? '#333' }}>
                  {person.status}
                </span>
              </Link>
            ))
            })()
          )}
        </div>
      )}
    </div>
  )
}
