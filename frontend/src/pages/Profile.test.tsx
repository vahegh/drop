import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Profile from './Profile'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn() }))
vi.mock('../hooks/useTickets', () => ({ useTickets: vi.fn() }))
vi.mock('../hooks/useEvents', () => ({ useEvents: vi.fn() }))
vi.mock('../api/people', () => ({ updateMe: vi.fn(), uploadAvatar: vi.fn() }))
vi.mock('../lib/loginUrl', () => ({ loginUrl: (p: string) => `/app/login?redirect_url=${encodeURIComponent(p)}` }))
vi.mock('react-qr-code', () => ({ default: () => <svg data-testid="qr-code" /> }))

import { useMe } from '../hooks/useMe'
import { useTickets } from '../hooks/useTickets'
import { useEvents } from '../hooks/useEvents'

const mockMe = {
  id: 'p-1',
  full_name: 'Jane Doe',
  first_name: 'Jane',
  last_name: 'Doe',
  email: 'jane@example.com',
  instagram_handle: 'janedoe',
  telegram_handle: null,
  status: 'verified',
  avatar_url: null,
  events_attended: 3,
  event_tickets: [],
  member_pass: null,
  drive_folder_url: null,
}

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.mocked(useTickets).mockReturnValue({ data: [] } as any)
  vi.mocked(useEvents).mockReturnValue({ data: [] } as any)
})

describe('Profile', () => {
  it('shows loading skeleton while loading', () => {
    vi.mocked(useMe).mockReturnValue({ data: undefined, isLoading: true, error: null } as any)
    const { container } = wrapper(<Profile />)
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders user full name', () => {
    vi.mocked(useMe).mockReturnValue({ data: mockMe, isLoading: false, error: null } as any)
    wrapper(<Profile />)
    expect(screen.getByText('Jane Doe')).toBeInTheDocument()
  })

  it('renders user status', () => {
    vi.mocked(useMe).mockReturnValue({ data: mockMe, isLoading: false, error: null } as any)
    wrapper(<Profile />)
    expect(screen.getByText('verified')).toBeInTheDocument()
  })

  it('renders instagram handle', () => {
    vi.mocked(useMe).mockReturnValue({ data: mockMe, isLoading: false, error: null } as any)
    wrapper(<Profile />)
    expect(screen.getAllByText('@janedoe').length).toBeGreaterThan(0)
  })

  it('renders edit profile button', () => {
    vi.mocked(useMe).mockReturnValue({ data: mockMe, isLoading: false, error: null } as any)
    wrapper(<Profile />)
    expect(screen.getByText('Edit profile')).toBeInTheDocument()
  })

  it('renders events attended stat', () => {
    vi.mocked(useMe).mockReturnValue({ data: mockMe, isLoading: false, error: null } as any)
    wrapper(<Profile />)
    expect(screen.getByText('Events attended')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('renders home link', () => {
    vi.mocked(useMe).mockReturnValue({ data: mockMe, isLoading: false, error: null } as any)
    wrapper(<Profile />)
    expect(screen.getByText('← Home')).toBeInTheDocument()
  })
})
