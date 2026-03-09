import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import About from './About'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn() }))

import { useMe } from '../hooks/useMe'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('About', () => {
  it('renders Verification, Members, What to expect sections', () => {
    vi.mocked(useMe).mockReturnValue({ data: undefined } as any)
    wrapper(<About />)
    expect(screen.getByText('Verification?')).toBeInTheDocument()
    expect(screen.getByText('Who are the Members?')).toBeInTheDocument()
    expect(screen.getByText('What to expect?')).toBeInTheDocument()
  })

  it('shows sign-up Google button when not logged in', () => {
    vi.mocked(useMe).mockReturnValue({ data: undefined } as any)
    wrapper(<About />)
    expect(screen.getByText('Sign up with Google')).toBeInTheDocument()
  })

  it('shows Home link when user is logged in', () => {
    vi.mocked(useMe).mockReturnValue({
      data: { full_name: 'Jane Doe', first_name: 'Jane', last_name: 'Doe', status: 'verified', avatar_url: null },
    } as any)
    wrapper(<About />)
    expect(screen.getByText('← Home')).toBeInTheDocument()
    expect(screen.queryByText('Sign up with Google')).not.toBeInTheDocument()
  })
})
