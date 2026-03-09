import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Event from './Event'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn() }))
vi.mock('../hooks/useEvents', () => ({ useEvent: vi.fn() }))
vi.mock('react-markdown', () => ({ default: ({ children }: { children: string }) => <p>{children}</p> }))

import { useMe } from '../hooks/useMe'
import { useEvent } from '../hooks/useEvents'

const mockEvent = {
  id: 'evt-1',
  name: 'Summer Nights',
  image_url: 'https://example.com/img.jpg',
  starts_at: new Date(Date.now() + 86400000).toISOString(),
  ends_at: new Date(Date.now() + 2 * 86400000).toISOString(),
  description: 'A great event',
  track_url: null,
  video_url: null,
  member_ticket_price: 2000,
  early_bird_price: 3000,
  general_admission_price: 5000,
  early_bird_date: null,
}

function wrapper() {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/app/event/evt-1']}>
        <Routes>
          <Route path="/app/event/:id" element={<Event />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.mocked(useMe).mockReturnValue({ data: undefined } as any)
})

describe('Event', () => {
  it('shows loading skeleton when event is loading', () => {
    vi.mocked(useEvent).mockReturnValue({ data: undefined, isLoading: true, error: null } as any)
    const { container } = wrapper()
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('shows event not found when error', () => {
    vi.mocked(useEvent).mockReturnValue({ data: undefined, isLoading: false, error: new Error('not found') } as any)
    wrapper()
    expect(screen.getByText('Event not found.')).toBeInTheDocument()
  })

  it('renders event name', () => {
    vi.mocked(useEvent).mockReturnValue({ data: mockEvent, isLoading: false, error: null } as any)
    wrapper()
    expect(screen.getAllByText('Summer Nights').length).toBeGreaterThan(0)
  })

  it('renders ticket tiers for upcoming event', () => {
    vi.mocked(useEvent).mockReturnValue({ data: mockEvent, isLoading: false, error: null } as any)
    wrapper()
    expect(screen.getByText('Members')).toBeInTheDocument()
    expect(screen.getByText('Standard')).toBeInTheDocument()
  })

  it('renders buy ticket button for upcoming event', () => {
    vi.mocked(useEvent).mockReturnValue({ data: mockEvent, isLoading: false, error: null } as any)
    wrapper()
    expect(screen.getByText('🎟️ Buy your ticket')).toBeInTheDocument()
  })

  it('does not render ticket section for past event', () => {
    const pastEvent = {
      ...mockEvent,
      starts_at: new Date(Date.now() - 2 * 86400000).toISOString(),
      ends_at: new Date(Date.now() - 86400000).toISOString(),
    }
    vi.mocked(useEvent).mockReturnValue({ data: pastEvent, isLoading: false, error: null } as any)
    wrapper()
    expect(screen.queryByText('Tickets')).not.toBeInTheDocument()
  })
})
