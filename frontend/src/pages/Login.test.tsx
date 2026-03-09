import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Login from './Login'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn() }))
vi.mock('../api/auth', () => ({ googleAuth: vi.fn() }))
vi.mock('@react-oauth/google', () => ({
  GoogleLogin: ({ onSuccess }: { onSuccess: () => void }) => (
    <button onClick={onSuccess}>Google Sign In</button>
  ),
}))

import { useMe } from '../hooks/useMe'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.mocked(useMe).mockReturnValue({ data: undefined, isLoading: false } as any)
})

describe('Login', () => {
  it('renders Drop Dead Disco heading', () => {
    wrapper(<Login />)
    expect(screen.getByText('Drop Dead Disco')).toBeInTheDocument()
  })

  it('renders Sign in section title', () => {
    wrapper(<Login />)
    expect(screen.getAllByText('Sign in').length).toBeGreaterThan(0)
  })

  it('renders Google Login button', () => {
    wrapper(<Login />)
    expect(screen.getByText('Google Sign In')).toBeInTheDocument()
  })

  it('renders subtitle about Google account', () => {
    wrapper(<Login />)
    expect(screen.getByText('Use your Google account to continue')).toBeInTheDocument()
  })
})
