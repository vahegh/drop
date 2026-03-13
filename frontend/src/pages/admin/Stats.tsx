import { useState } from 'react'
import { useAdminStats } from '../../hooks/useAdmin'
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

function fmt(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(0) + 'K'
  return String(n)
}

function fmtAMD(n: number) {
  return new Intl.NumberFormat('en-US').format(Math.round(n)) + ' AMD'
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function fmtChartDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

const PROVIDER_COLORS: Record<string, string> = {
  VPOS: '#4f8ef7',
  MYAMERIA: '#f7a84f',
  IDRAM: '#9b59b6',
  APPLEPAY: '#888',
  GOOGLEPAY: '#4caf50',
  BINDING: '#e57373',
}

const EVENT_COLORS = ['#4f8ef7', '#f7a84f', '#4caf50', '#e57373', '#9b59b6', '#f06292', '#26c6da']

function toYerevanDateStr(iso: string): string {
  return new Date(iso).toLocaleDateString('en-CA', { timeZone: 'Asia/Yerevan' })
}

function daysBetween(laterDateStr: string, earlierDateStr: string): number {
  return Math.round((new Date(laterDateStr).getTime() - new Date(earlierDateStr).getTime()) / 86_400_000)
}

function buildMultiChartData(events: any[], selectedIds: Set<string>) {
  const selected = events.filter(e => selectedIds.has(e.id))
  if (selected.length === 0) return { chartData: [], selected: [] }

  const allRelativeDays = new Set<number>()
  const byRelDay: Record<string, Record<number, number>> = {}

  for (const ev of selected) {
    const dailyTickets: any[] = ev.daily_tickets ?? []
    const day0 = dailyTickets.length > 0 ? dailyTickets[0].date : toYerevanDateStr(ev.created_at)
    byRelDay[ev.id] = {}
    for (const d of dailyTickets) {
      const rel = daysBetween(d.date, day0)
      allRelativeDays.add(rel)
      byRelDay[ev.id][rel] = d.cumulative
    }
  }

  const sortedDays = Array.from(allRelativeDays).sort((a, b) => a - b)

  const chartData = sortedDays.map(rel => {
    const row: any = { label: `Day ${rel}` }
    for (const ev of selected) row[ev.id] = byRelDay[ev.id][rel] ?? null
    return row
  })

  return { chartData, selected }
}

export default function AdminStats() {
  const { data, isLoading, isError, refetch } = useAdminStats()
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  if (isLoading) {
    return <div style={{ padding: 24, color: '#555', textAlign: 'center' }}>Loading...</div>
  }
  if (isError) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <div style={{ color: '#555', marginBottom: 12 }}>Failed to load stats</div>
        <button onClick={() => refetch()} style={{ background: '#111', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', cursor: 'pointer' }}>Retry</button>
      </div>
    )
  }

  const events: any[] = data?.events ?? []

  // Default: first event selected
  const effectiveIds = selectedIds.size > 0 ? selectedIds : new Set(events.slice(0, 1).map((e: any) => e.id))
  const { chartData, selected: selectedEvents } = buildMultiChartData(events, effectiveIds)

  const isComparing = effectiveIds.size > 1

  function toggleEvent(id: string) {
    setSelectedIds(prev => {
      const next = new Set(prev.size === 0 ? [events[0]?.id].filter(Boolean) : prev)
      if (next.has(id)) {
        if (next.size === 1) return next // keep at least one
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  // Single event view data
  const singleEvent = !isComparing ? selectedEvents[0] : null
  const singleChartData = singleEvent
    ? (singleEvent.daily_tickets ?? []).map((d: any) => ({ ...d, label: fmtChartDate(d.date) }))
    : []

  return (
    <div style={{ padding: 24, maxWidth: 860 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, margin: 0 }}>Stats</h1>
        <button onClick={() => refetch()} style={{ color: '#555', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>Refresh</button>
      </div>

      {/* KPI cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 32 }}>
        <KpiCard label="Total Revenue" value={fmtAMD(data?.total_revenue ?? 0)} />
        <KpiCard label="Total Tickets" value={fmt(data?.total_tickets ?? 0)} />
        <KpiCard label="Confirmed Payments" value={fmt(data?.total_confirmed_payments ?? 0)} />
      </div>

      {/* Ticket sales trend chart */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ color: '#555', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 10 }}>
          Ticket Sales Trend
        </div>

        {selectedEvents.length > 0 ? (
          <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', padding: '20px 16px 8px' }}>
            {!isComparing && singleEvent && (
              <div style={{ display: 'flex', gap: 24, marginBottom: 16 }}>
                <div>
                  <div style={{ color: '#555', fontSize: 11 }}>Event</div>
                  <div style={{ color: '#fff', fontSize: 14, fontWeight: 600, marginTop: 2 }}>{singleEvent.name}</div>
                </div>
                <div>
                  <div style={{ color: '#555', fontSize: 11 }}>Date</div>
                  <div style={{ color: '#ccc', fontSize: 13, marginTop: 2 }}>{fmtDate(singleEvent.starts_at)}</div>
                </div>
                <div>
                  <div style={{ color: '#555', fontSize: 11 }}>Tickets</div>
                  <div style={{ color: '#ccc', fontSize: 13, marginTop: 2 }}>{singleEvent.ticket_count} / {singleEvent.max_capacity}</div>
                </div>
                <div>
                  <div style={{ color: '#555', fontSize: 11 }}>Revenue</div>
                  <div style={{ color: '#ccc', fontSize: 13, marginTop: 2 }}>{fmtAMD(singleEvent.revenue)}</div>
                </div>
              </div>
            )}

            {isComparing && (
              <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
                {selectedEvents.map((ev, i) => (
                  <div key={ev.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 10, height: 3, background: EVENT_COLORS[i % EVENT_COLORS.length], display: 'inline-block', borderRadius: 2 }} />
                    <span style={{ color: '#ccc', fontSize: 12 }}>{ev.name}</span>
                  </div>
                ))}
              </div>
            )}

            {chartData.length > 0 || singleChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                {isComparing ? (
                  <LineChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                    <XAxis dataKey="label" tick={{ fill: '#555', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#555', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ background: '#0d0d0d', border: '1px solid #222', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: '#888' }}
                      itemStyle={{ color: '#fff' }}
                      formatter={(value: any, name: any) => {
                        const ev = events.find((e: any) => e.id === name)
                        return [value, ev?.name ?? name]
                      }}
                    />
                    {selectedEvents.map((ev, i) => (
                      <Line
                        key={ev.id}
                        type="monotone"
                        dataKey={ev.id}
                        stroke={EVENT_COLORS[i % EVENT_COLORS.length]}
                        strokeWidth={2}
                        dot={false}
                        connectNulls
                      />
                    ))}
                  </LineChart>
                ) : (
                  <AreaChart data={singleChartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="ticketGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4f8ef7" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#4f8ef7" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                    <XAxis dataKey="label" tick={{ fill: '#555', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis
                      tick={{ fill: '#555', fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      domain={[0, singleEvent?.max_capacity ?? 'auto']}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={{ background: '#0d0d0d', border: '1px solid #222', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: '#888' }}
                      itemStyle={{ color: '#fff' }}
                      formatter={(value: any, name: any) => [value, name === 'cumulative' ? 'Total tickets' : 'New tickets']}
                    />
                    <Area type="monotone" dataKey="cumulative" stroke="#4f8ef7" strokeWidth={2} fill="url(#ticketGrad)" dot={false} name="cumulative" />
                    <Area type="monotone" dataKey="count" stroke="#888" strokeWidth={1.5} fill="none" dot={false} strokeDasharray="4 2" name="count" />
                  </AreaChart>
                )}
              </ResponsiveContainer>
            ) : (
              <div style={{ color: '#555', fontSize: 13, textAlign: 'center', padding: '32px 0' }}>No ticket sales recorded yet</div>
            )}

            {/* Capacity fill — single event only */}
            {!isComparing && singleEvent && singleEvent.max_capacity > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ color: '#555', fontSize: 11 }}>Capacity fill</span>
                  <span style={{ color: '#888', fontSize: 11 }}>{Math.round((singleEvent.ticket_count / singleEvent.max_capacity) * 100)}%</span>
                </div>
                <div style={{ height: 4, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.min(100, (singleEvent.ticket_count / singleEvent.max_capacity) * 100)}%`,
                      background: singleEvent.ticket_count / singleEvent.max_capacity > 0.8 ? '#e57373' : '#4f8ef7',
                      borderRadius: 2,
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ color: '#555', fontSize: 13, textAlign: 'center', padding: 40 }}>No events found</div>
        )}
      </div>

      {/* Per-event table with multi-select */}
      {events.length > 1 && (
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <div style={{ color: '#555', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em' }}>All Events</div>
            <div style={{ color: '#555', fontSize: 11 }}>Select to compare</div>
          </div>
          <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden' }}>
            {events.map((ev: any, i: number) => {
              const colorIndex = Array.from(effectiveIds).indexOf(ev.id)
              const isSelected = effectiveIds.has(ev.id)
              const color = isSelected ? EVENT_COLORS[colorIndex % EVENT_COLORS.length] : '#333'
              return (
                <button
                  key={ev.id}
                  onClick={() => toggleEvent(ev.id)}
                  style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '12px 16px', borderBottom: i < events.length - 1 ? '1px solid #1a1a1a' : 'none',
                    width: '100%', background: isSelected ? '#161616' : 'transparent',
                    border: 'none', cursor: 'pointer', textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, display: 'inline-block', flexShrink: 0, transition: 'background 0.2s' }} />
                    <div>
                      <div style={{ color: '#fff', fontSize: 14, fontWeight: 600 }}>{ev.name}</div>
                      <div style={{ color: '#555', fontSize: 12, marginTop: 2 }}>{fmtDate(ev.starts_at)}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ color: '#ccc', fontSize: 13, fontWeight: 600 }}>{ev.ticket_count}<span style={{ color: '#555', fontWeight: 400 }}>/{ev.max_capacity}</span></div>
                      <div style={{ color: '#555', fontSize: 11, marginTop: 1 }}>tickets</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ color: '#ccc', fontSize: 13, fontWeight: 600 }}>{fmt(ev.revenue)}</div>
                      <div style={{ color: '#555', fontSize: 11, marginTop: 1 }}>AMD</div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Revenue by provider — bottom */}
      {(data?.by_provider ?? []).length > 0 && (
        <div>
          <div style={{ color: '#555', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 10 }}>Revenue by Provider</div>
          <div style={{ background: '#111', borderRadius: 12, border: '1px solid #1a1a1a', overflow: 'hidden' }}>
            {(data.by_provider as any[]).map((p: any, i: number) => {
              const maxRev = Math.max(...(data.by_provider as any[]).map((x: any) => x.revenue))
              const pct = maxRev > 0 ? (p.revenue / maxRev) * 100 : 0
              return (
                <div key={p.provider} style={{ padding: '12px 16px', borderBottom: i < data.by_provider.length - 1 ? '1px solid #1a1a1a' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: PROVIDER_COLORS[p.provider] ?? '#555', display: 'inline-block' }} />
                      <span style={{ color: '#ccc', fontSize: 13, fontWeight: 600 }}>{p.provider}</span>
                      <span style={{ color: '#555', fontSize: 12 }}>{p.count} payments</span>
                    </div>
                    <span style={{ color: '#fff', fontSize: 13, fontWeight: 700 }}>{fmtAMD(p.revenue)}</span>
                  </div>
                  <div style={{ height: 3, background: '#1a1a1a', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: PROVIDER_COLORS[p.provider] ?? '#555', borderRadius: 2, transition: 'width 0.4s ease' }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: '#111', border: '1px solid #1a1a1a', borderRadius: 12, padding: '16px 20px' }}>
      <div style={{ color: '#555', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 6 }}>{label}</div>
      <div style={{ color: '#fff', fontSize: 22, fontWeight: 700 }}>{value}</div>
    </div>
  )
}
