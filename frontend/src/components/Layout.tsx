import { Link, useLocation } from 'react-router-dom'
import { useMe } from '../hooks/useMe'
import { logout } from '../api/auth'
import { loginUrl } from '../lib/loginUrl'
import { useState } from 'react'

export const STATUS_COLORS: Record<string, string> = {
  verified: '#00c951',
  member: '#ad46ff',
  rejected: '#fb2c36',
  pending: '#ff6900',
}

interface LayoutProps {
  children?: React.ReactNode
  /** Per-page blurred bg override (event pages) - replaces the video */
  heroBg?: string
  showFooter?: boolean
}

export default function Layout({ children, heroBg, showFooter = true }: LayoutProps) {
  const { data: me, isLoading: meLoading } = useMe()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleLogout() {
    setMenuOpen(false)
    setLoggingOut(true)
    const returnTo = window.location.pathname + window.location.search
    await logout()
    // Hard reload so all query cache + React state resets cleanly
    window.location.href = returnTo
  }

  return (
    <>
      {/* Background */}
      {heroBg ? (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundImage: `url('${heroBg}')`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: 'blur(12px) brightness(25%)',
            transform: 'scale(1.05)',
            zIndex: -1,
          }}
        />
      ) : (
        <video autoPlay muted loop playsInline id="bg-video">
          <source src="/static/images/bg_video.mp4" type="video/mp4" />
        </video>
      )}

      {/* Navbar */}
      <nav
        style={{ backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)' }}
        className="fixed top-0 left-0 right-0 h-14 px-4 flex items-center justify-between z-50 bg-black/20"
      >
        {location.pathname === '/' ? (
          <button type="button" onClick={() => document.documentElement.scrollTo({ top: 0, behavior: 'smooth' })} className="flex items-center" aria-label="Scroll to top">
            <img src="/static/images/logo_gray.png" alt="Drop Dead Disco" className="h-12 w-14 object-contain" />
          </button>
        ) : (
          <Link to="/" className="flex items-center">
            <img src="/static/images/logo_gray.png" alt="Drop Dead Disco" className="h-12 w-14 object-contain" />
          </Link>
        )}

        {meLoading ? null : me ? (
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
                    {me.events_attended > 0 && (
                      <p className="text-xs text-white/45">🔥 {me.events_attended}</p>
                    )}
                    {me.referral_count > 0 && (
                      <p className="text-xs text-white/45">👥 {me.referral_count}</p>
                    )}
                  </div>
                  <Link to="/profile" onClick={() => setMenuOpen(false)} className="btn-primary text-sm text-center">
                    Your profile
                  </Link>
                  {me.is_admin && (
                    <Link to="/admin" onClick={() => setMenuOpen(false)} className="text-sm text-center text-white/60 hover:text-white transition-colors">
                      Admin panel
                    </Link>
                  )}
                  <button onClick={handleLogout} disabled={loggingOut} className="text-sm text-white/45 hover:text-white/80 transition-colors disabled:opacity-50">
                    {loggingOut ? 'Logging out…' : 'Log out'}
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <Link to={loginUrl(location.pathname + location.search)} className="btn-outline" style={{ height: '32px', padding: '0 16px', fontSize: '0.8rem', width: 'auto' }}>
            Log in
          </Link>
        )}
      </nav>

      {/* Page content */}
      <div className="flex flex-col items-center gap-4 px-4 pt-14 pb-8 min-h-screen w-full">
        {children}
      </div>

      {/* Footer - mirrors frame.py show_footer */}
      {showFooter && (
        <footer className="w-full border-t border-white/10 py-6 flex flex-col items-center gap-4">
          <button type="button" onClick={() => document.documentElement.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Scroll to top">
            <img src="/static/images/logo_gray.png" alt="Drop Dead Disco" className="h-16 w-24 object-contain opacity-60 hover:opacity-90 transition-opacity" />
          </button>
          <div className="flex gap-1">
            <a href="https://www.instagram.com/dropdeadisco/" rel="noopener noreferrer"
              className="p-2 opacity-50 hover:opacity-90 transition-opacity">
              <img src="/static/images/instagram.svg" alt="Instagram" className="w-5 h-5 invert" />
            </a>
            <a href="https://open.spotify.com/user/4tqtnbljmj15sta3zq3dq6d1v?si=3e5307488a9546c7" rel="noopener noreferrer"
              className="p-2 opacity-50 hover:opacity-90 transition-opacity">
              <img src="/static/images/spotify.svg" alt="Spotify" className="w-5 h-5 invert" />
            </a>
            <a href="https://www.youtube.com/@dropdeadisco" rel="noopener noreferrer"
              className="p-2 opacity-50 hover:opacity-90 transition-opacity">
              <img src="/static/images/youtube.svg" alt="YouTube" className="w-5 h-5 invert" />
            </a>
          </div>
          <a href="mailto:dropdeadisco@gmail.com" className="text-xs text-white/30 hover:text-white/60 transition-colors">
            dropdeadisco@gmail.com
          </a>
        </footer>
      )}
    </>
  )
}
