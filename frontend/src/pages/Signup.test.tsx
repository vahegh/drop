import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Signup from './Signup'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn(() => ({ data: undefined })) }))
vi.mock('../api/auth', () => ({ signupWithGoogle: vi.fn() }))

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Signup', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('renders blank layout and redirects when no session data', () => {
    wrapper(<Signup />)
    // No pending data → no form shown
    expect(screen.queryByText('Almost there')).not.toBeInTheDocument()
  })

  it('renders form when session data is present', () => {
    sessionStorage.setItem('drop_signup', JSON.stringify({
      credential: 'tok',
      email: 'jane@example.com',
      first_name: 'Jane',
      last_name: 'Doe',
      avatar_url: null,
    }))
    wrapper(<Signup />)
    expect(screen.getByText('Almost there')).toBeInTheDocument()
    expect(screen.getByText('Complete your profile')).toBeInTheDocument()
  })

  it('pre-fills first and last name from session data', () => {
    sessionStorage.setItem('drop_signup', JSON.stringify({
      credential: 'tok',
      email: 'jane@example.com',
      first_name: 'Jane',
      last_name: 'Doe',
      avatar_url: null,
    }))
    wrapper(<Signup />)
    expect((screen.getByPlaceholderText('First name') as HTMLInputElement).value).toBe('Jane')
    expect((screen.getByPlaceholderText('Last name') as HTMLInputElement).value).toBe('Doe')
  })

  it('shows email as section subtitle', () => {
    sessionStorage.setItem('drop_signup', JSON.stringify({
      credential: 'tok',
      email: 'jane@example.com',
      first_name: 'Jane',
      last_name: 'Doe',
      avatar_url: null,
    }))
    wrapper(<Signup />)
    expect(screen.getByText('jane@example.com')).toBeInTheDocument()
  })
})
