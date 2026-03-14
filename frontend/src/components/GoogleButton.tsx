import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGoogleLogin } from '@react-oauth/google'
import { googleAuth } from '../api/auth'

interface Props {
  text: string
  variant: 'primary' | 'outline'
  redirectUrl?: string
  loginHint?: string
  style?: React.CSSProperties
  className?: string
  wrapperStyle?: React.CSSProperties
}

export default function GoogleButton({ text, variant, redirectUrl = '/', loginHint, style, className, wrapperStyle }: Props) {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const login = useGoogleLogin({
    hint: loginHint,
    onSuccess: async (tokenResponse) => {
      setError(null)
      setLoading(true)
      try {
        const result = await googleAuth(tokenResponse.access_token)
        if (result.status === 'ok') {
          window.location.href = redirectUrl
        } else {
          const params = new URLSearchParams({
            token: result.token,
            email: result.email,
            first_name: result.first_name,
            last_name: result.last_name,
          })
          navigate(`/signup?${params}`)
        }
      } catch (err: any) {
        if (err?.response?.status === 403) {
          setError('Your account has been rejected.')
        } else {
          setError('Sign in failed. Please try again.')
        }
        setLoading(false)
      }
    },
    onError: () => { setError('Google sign in failed.'); setLoading(false) },
  })

  const btnClass = variant === 'primary' ? 'btn-primary' : 'btn-outline'
  return (
    <div className={`flex flex-col gap-2 w-full items-center${className ? ` ${className}` : ''}`} style={wrapperStyle}>
      <button className={btnClass} style={{ gap: '8px', ...style }} onClick={() => login()} disabled={loading}>
        <img src="/static/images/google.svg" alt="" style={{ width: '18px', height: '18px' }} />
        {loading ? 'Signing in…' : text}
      </button>
      {error && <p className="text-xs text-center" style={{ color: 'var(--drop-negative)' }}>{error}</p>}
    </div>
  )
}
