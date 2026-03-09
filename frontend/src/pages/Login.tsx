import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import { useMe } from '../hooks/useMe'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { googleAuth } from '../api/auth'

export default function Login() {
  const [searchParams] = useSearchParams()
  const redirectUrl = searchParams.get('redirect_url') ?? '/app'
  const navigate = useNavigate()

  const { data: me, isLoading } = useMe()

  useEffect(() => {
    if (!isLoading && me) {
      window.location.href = redirectUrl
    }
  }, [me, isLoading, redirectUrl])

  async function handleSuccess(credentialResponse: { credential?: string }) {
    if (!credentialResponse.credential) return
    const result = await googleAuth(credentialResponse.credential)
    if (result.status === 'ok') {
      window.location.href = redirectUrl
    } else {
      const pending = {
        credential: credentialResponse.credential,
        email: result.email,
        first_name: result.first_name,
        last_name: result.last_name,
        avatar_url: result.avatar_url,
      }
      sessionStorage.setItem('drop_signup', JSON.stringify(pending))
      navigate(`/app/signup?redirect_url=${encodeURIComponent(redirectUrl)}`)
    }
  }

  return (
    <Layout showFooter>
      <Section className="pt-10">
        <h1 className="text-3xl font-bold text-center">Drop Dead Disco</h1>
      </Section>

      <Section title="Sign in" subtitle="Use your Google account to continue" sep>
        <GoogleLogin
          onSuccess={handleSuccess}
          onError={() => {}}
          theme="filled_black"
          shape="pill"
        />
      </Section>
    </Layout>
  )
}
