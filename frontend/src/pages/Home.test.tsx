import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Home from './Home'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn() }))
vi.mock('../hooks/useEvents', () => ({ useNextEvent: vi.fn(), useEvents: vi.fn() }))
vi.mock('../hooks/useTickets', () => ({ useTickets: vi.fn() }))

import { useMe } from '../hooks/useMe'
import { useNextEvent, useEvents } from '../hooks/useEvents'
import { useTickets } from '../hooks/useTickets'

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.mocked(useNextEvent).mockReturnValue({ data: undefined } as any)
  vi.mocked(useEvents).mockReturnValue({ data: [] } as any)
  vi.mocked(useTickets).mockReturnValue({ data: [] } as any)
})

describe('Home', () => {
  it('shows empty layout (no crash) while meLoading=true', () => {
    vi.mocked(useMe).mockReturnValue({ data: undefined, isLoading: true } as any)
    const { container } = wrapper(<Home />)
    expect(container).toBeInTheDocument()
  })

  it('shows guest welcome heading when not logged in', () => {
    vi.mocked(useMe).mockReturnValue({ data: undefined, isLoading: false } as any)
    wrapper(<Home />)
    expect(screen.getByText('Drop Dead Disco')).toBeInTheDocument()
  })

  it('shows user greeting with name when logged in', () => {
    vi.mocked(useMe).mockReturnValue({
      data: { full_name: 'Jane Doe', first_name: 'Jane', status: 'verified', avatar_url: null },
      isLoading: false,
    } as any)
    wrapper(<Home />)
    expect(screen.getByText('Jane Doe')).toBeInTheDocument()
  })
})
