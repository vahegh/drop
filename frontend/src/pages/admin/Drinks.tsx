import { useState } from 'react'
import { useAdminDrinks, useAdminCreateDrink, useAdminUpdateDrink, useAdminDeleteDrink } from '../../hooks/useAdmin'

const EMPTY_FORM = { name: '', price: '' }

export default function AdminDrinks() {
  const { data, isLoading, isError, refetch } = useAdminDrinks()
  const createMutation = useAdminCreateDrink()
  const updateMutation = useAdminUpdateDrink()
  const deleteMutation = useAdminDeleteDrink()

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState<string | null>(null)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ name: '', price: '' })
  const [editError, setEditError] = useState<string | null>(null)

  const inputStyle: React.CSSProperties = {
    background: '#0a0a0a', border: '1px solid #2a2a2a', borderRadius: 8,
    color: '#fff', fontSize: 13, padding: '8px 12px', outline: 'none', boxSizing: 'border-box',
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    try {
      await createMutation.mutateAsync({ name: form.name, price: parseInt(form.price) })
      setForm(EMPTY_FORM)
      setShowForm(false)
    } catch (err: any) {
      setFormError(err?.response?.data?.detail ?? 'Failed to create drink')
    }
  }

  function startEdit(drink: any) {
    setEditingId(drink.id)
    setEditForm({ name: drink.name, price: String(drink.price) })
    setEditError(null)
  }

  async function handleUpdate(id: string) {
    setEditError(null)
    try {
      await updateMutation.mutateAsync({ id, body: { name: editForm.name, price: parseInt(editForm.price) } })
      setEditingId(null)
    } catch (err: any) {
      setEditError(err?.response?.data?.detail ?? 'Failed to update drink')
    }
  }

  function fmt(iso: string) {
    return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  return (
    <div className="p-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Drinks</h1>
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
          <div className="flex gap-3">
            <input
              required placeholder="Drink name" value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              style={{ ...inputStyle, flex: 2 }}
            />
            <input
              required type="number" placeholder="Price (AMD)" value={form.price}
              onChange={e => setForm(f => ({ ...f, price: e.target.value }))}
              style={{ ...inputStyle, flex: 1 }}
            />
          </div>
          {formError && <div style={{ color: '#fb2c36', fontSize: 12 }}>{formError}</div>}
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="self-end px-4 py-2 rounded-lg text-sm font-semibold"
            style={{ background: '#fff', color: '#000', opacity: createMutation.isPending ? 0.5 : 1 }}
          >
            {createMutation.isPending ? 'Adding…' : 'Add'}
          </button>
        </form>
      )}

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
            <div className="text-[#555] text-sm text-center py-10">No drinks yet</div>
          ) : (
            (data ?? []).map((drink: any, i: number) => (
              <div
                key={drink.id}
                className="px-4 py-3"
                style={{ borderBottom: i < data.length - 1 ? '1px solid #1a1a1a' : 'none' }}
              >
                {editingId === drink.id ? (
                  <div className="flex flex-col gap-2">
                    <div className="flex gap-3">
                      <input
                        value={editForm.name}
                        onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                        style={{ ...inputStyle, flex: 2, minWidth: 0 }}
                      />
                      <input
                        type="number"
                        value={editForm.price}
                        onChange={e => setEditForm(f => ({ ...f, price: e.target.value }))}
                        style={{ ...inputStyle, width: 120, flexShrink: 0 }}
                      />
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleUpdate(drink.id)}
                        disabled={updateMutation.isPending}
                        className="text-sm px-3 py-1.5 rounded-lg font-semibold"
                        style={{ background: '#fff', color: '#000', opacity: updateMutation.isPending ? 0.5 : 1 }}
                      >
                        {updateMutation.isPending ? 'Saving…' : 'Save'}
                      </button>
                      <button onClick={() => setEditingId(null)} className="text-[#555] text-sm hover:text-white">Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-white text-[15px] font-medium">{drink.name}</span>
                      <span className="text-[#555] text-xs ml-3">{fmt(drink.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-[#888] text-sm">{drink.price.toLocaleString()} AMD</span>
                      <button onClick={() => startEdit(drink)} className="text-[#5b8fff] text-sm hover:text-white">Edit</button>
                      <button
                        onClick={async () => {
                          if (!window.confirm(`Delete "${drink.name}"?`)) return
                          await deleteMutation.mutateAsync(drink.id)
                        }}
                        className="text-[#555] text-sm hover:text-red-400"
                      >Delete</button>
                    </div>
                  </div>
                )}
                {editingId === drink.id && editError && (
                  <div style={{ color: '#fb2c36', fontSize: 12, marginTop: 6 }}>{editError}</div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
