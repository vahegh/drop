import { NavLink, Outlet, Link } from 'react-router-dom'
import { useAdminMe } from '../../hooks/useAdmin'
import { useMe } from '../../hooks/useMe'
import { logout } from '../../api/auth'
import { useState } from 'react'
import { STATUS_COLORS } from '../../components/Layout'

const NAV = [
  { to: '/admin/people', label: 'People' },
  { to: '/admin/events', label: 'Events' },
  { to: '/admin/venues', label: 'Venues' },
  { to: '/admin/drinks', label: 'Drinks' },
  { to: '/admin/stats', label: 'Stats' },
]

export default function AdminLayout() {
  const { data: adminData, isLoading, isError, error } = useAdminMe()
  const { data: me } = useMe()
  const [menuOpen, setMenuOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleLogout() {
    setMenuOpen(false)
    setLoggingOut(true)
    const returnTo = window.location.pathname + window.location.search
    await logout()
    window.location.href = returnTo
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="text-[#555] text-sm">Loading...</div>
      </div>
    )
  }

  if (isError) {
    const status = (error as any)?.response?.status
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-black">
        <div className="text-white text-xl font-bold mb-2">
          {status === 403 ? 'Unauthorized' : status === 401 ? 'Not logged in' : 'Error'}
        </div>
        <div className="text-[#555] text-sm">
          {status === 403 ? "You don't have admin access." : status === 401 ? 'Please log in first.' : 'Could not verify access.'}
        </div>
        {status === 401 && (
          <a href="/login" className="mt-4 text-[#5b8fff] text-sm">Go to login</a>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-black text-white">
      {/* Top navbar - same as regular pages */}
      <nav
        style={{ backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)' }}
        className="fixed top-0 left-0 right-0 h-14 px-4 flex items-center justify-between z-50 bg-black/80 border-b border-[#1a1a1a]"
      >
        <Link to="/" className="flex items-center">
          <img src="/static/images/logo_gray.png" alt="Drop Dead Disco" className="h-12 w-14 object-contain" />
        </Link>

        {me ? (
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="w-8 h-8 rounded-full overflow-hidden border border-white/20 hover:border-white/50 transition-colors flex items-center justify-center"
            >
              {me.avatar_url ? (
                <img src={me.avatar_url} alt={me.full_name} className="w-full h-full object-cover" />
              ) : (
                <span className="text-sm font-semibold" style={{ color: STATUS_COLORS[me.status] }}>
                  {me.first_name[0]}
                </span>
              )}
            </button>

            {menuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
                <div
                  className="absolute right-0 top-10 z-50 w-56 rounded-xl p-4 flex flex-col gap-3"
                  style={{ background: 'var(--drop-card)', boxShadow: '0 8px 32px rgba(0,0,0,0.6)' }}
                >
                  <div className="flex flex-col items-center gap-2 pb-3 border-b border-white/10">
                    {me.avatar_url ? (
                      <img src={me.avatar_url} alt={me.full_name} className="w-16 h-16 rounded-full object-cover" />
                    ) : (
                      <div className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold bg-white/10">
                        {me.first_name[0]}
                      </div>
                    )}
                    <p className="font-semibold text-sm text-center">{me.full_name}</p>
                    <p className="text-xs" style={{ color: STATUS_COLORS[me.status] }}>{me.status}</p>
                  </div>
                  <Link to="/profile" onClick={() => setMenuOpen(false)} className="btn-primary text-sm text-center">
                    Your profile
                  </Link>
                  <button onClick={handleLogout} disabled={loggingOut} className="text-sm text-white/45 hover:text-white/80 transition-colors disabled:opacity-50">
                    {loggingOut ? 'Logging out…' : 'Log out'}
                  </button>
                </div>
              </>
            )}
          </div>
        ) : null}
      </nav>

      <div className="flex flex-1 pt-14">
        {/* Sidebar desktop */}
        <aside className="hidden md:flex flex-col w-44 border-r border-[#1a1a1a] fixed top-14 bottom-0 pb-4 px-3 pt-6" style={{ boxSizing: 'border-box' }}>
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#333] mb-6 px-2">Admin</div>
          <nav className="flex flex-col gap-1">
            {NAV.map(({ to, label }) => (
              <NavLink key={to} to={to} className={({ isActive }) =>
                `px-3 py-2 rounded-lg text-sm font-medium no-underline transition-colors ${isActive ? 'bg-white text-black' : 'text-[#888] hover:text-white hover:bg-[#111]'}`
              }>{label}</NavLink>
            ))}
          </nav>
          <div className="mt-auto px-2 text-[11px] text-[#333] truncate">{adminData?.email}</div>
        </aside>

        {/* Mobile section nav */}
        <div className="md:hidden fixed top-14 left-0 right-0 z-40 bg-black border-b border-[#1a1a1a] flex overflow-x-auto gap-1.5 px-3 py-2">
          {NAV.map(({ to, label }) => (
            <NavLink key={to} to={to} className={({ isActive }) =>
              `px-3 py-1.5 rounded-full text-[13px] font-medium no-underline whitespace-nowrap ${isActive ? 'bg-white text-black' : 'bg-[#111] text-[#888]'}`
            }>{label}</NavLink>
          ))}
        </div>

        <main className="flex-1 md:ml-44 pt-10 md:pt-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
