import { useAdminPayments } from '../../hooks/useAdmin'

const STATUS_COLOR: Record<string, string> = {
  CREATED: '#555', CONFIRMED: '#1a6e3c', REJECTED: '#7a1010', REFUNDED: '#7a5500', PENDING: '#2a4e8c',
}

export default function AdminPayments() {
  const { data, isLoading, refetch } = useAdminPayments()

  return (
    <div style={{ padding: 24, maxWidth: 700 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, margin: 0 }}>Payments</h1>
        <button onClick={() => refetch()} style={{ color: '#555', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>Refresh</button>
      </div>

      {isLoading ? (
        <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>Loading...</div>
      ) : (
        <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden' }}>
          {(data ?? []).length === 0 ? (
            <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>No payments</div>
          ) : (
            ([...(data ?? [])].sort((a: any, b: any) => b.order_id - a.order_id)).map((p: any, i: number) => (
              <div key={p.order_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', borderBottom: i < data.length - 1 ? '1px solid #1a1a1a' : 'none' }}>
                <div>
                  <div style={{ color: '#fff', fontWeight: 700, fontSize: 15 }}>#{p.order_id}</div>
                  <div style={{ color: '#888', fontSize: 13, marginTop: 2 }}>{p.amount} AMD · {p.provider}</div>
                  <div style={{ color: '#555', fontSize: 12, marginTop: 2 }}>{new Date(p.created_at).toLocaleString()}</div>
                </div>
                <span style={{ background: STATUS_COLOR[p.status] ?? '#333', color: '#fff', fontSize: 11, fontWeight: 600, padding: '4px 10px', borderRadius: 10, marginLeft: 12 }}>
                  {p.status}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
