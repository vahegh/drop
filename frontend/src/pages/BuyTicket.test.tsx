import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import BuyTicket from './BuyTicket'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn() }))
vi.mock('../hooks/useEvents', () => ({ useEvent: vi.fn() }))
vi.mock('../api/payments', () => ({ initiatePayment: vi.fn() }))
vi.mock('../lib/loginUrl', () => ({ loginUrl: (p: string) => `/login?redirect_url=${encodeURIComponent(p)}` }))

import { useMe } from '../hooks/useMe'
import { useEvent } from '../hooks/useEvents'

const mockEvent = {
  id: 'evt-1',
  name: 'Summer Nights',
  image_url: 'https://example.com/img.jpg',
  starts_at: new Date(Date.now() + 86400000).toISOString(),
  ends_at: new Date(Date.now() + 2 * 86400000).toISOString(),
  tiers: [
    { id: 't-1', name: 'Member Ticket', price: 2000, required_person_status: 'member', sort_order: 0, is_active: true, available_from: null, available_until: null, capacity: null, ecrm_good_code: null, ecrm_good_name: null, event_id: 'evt-1', created_at: '' },
    { id: 't-2', name: 'General Admission', price: 5000, required_person_status: null, sort_order: 1, is_active: true, available_from: null, available_until: null, capacity: null, ecrm_good_code: null, ecrm_good_name: null, event_id: 'evt-1', created_at: '' },
  ],
}

const mockMe = {
  id: 'p-1',
  full_name: 'Jane Doe',
  first_name: 'Jane',
  status: 'verified',
  avatar_url: null,
}

function wrapper(search = '?event_id=evt-1') {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/buy-ticket${search}`]}>
        <Routes>
          <Route path="/buy-ticket" element={<BuyTicket />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.mocked(useMe).mockReturnValue({ data: undefined } as any)
  vi.mocked(useEvent).mockReturnValue({ data: mockEvent, isLoading: false } as any)
})

describe('BuyTicket', () => {
  it('shows no event selected when no event_id param', () => {
    vi.mocked(useEvent).mockReturnValue({ data: undefined, isLoading: false } as any)
    wrapper('')
    expect(screen.getByText('No event selected.')).toBeInTheDocument()
  })

  it('shows loading skeleton while event loads', () => {
    vi.mocked(useEvent).mockReturnValue({ data: undefined, isLoading: true } as any)
    const { container } = wrapper()
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('shows sign in prompt when user is not logged in', () => {
    wrapper()
    expect(screen.getByText(/Sign in to buy a ticket/)).toBeInTheDocument()
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument()
  })

  it('shows event name and pay button when logged in', () => {
    vi.mocked(useMe).mockReturnValue({ data: mockMe } as any)
    wrapper()
    expect(screen.getByText('Summer Nights')).toBeInTheDocument()
    expect(screen.getByText(/Pay.*AMD/)).toBeInTheDocument()
  })

  it('shows payment method selector when logged in', () => {
    vi.mocked(useMe).mockReturnValue({ data: mockMe } as any)
    wrapper()
    expect(screen.getByText('Payment method')).toBeInTheDocument()
    expect(screen.getByText('Card')).toBeInTheDocument()
  })

  it('shows member ticket price for member user', () => {
    vi.mocked(useMe).mockReturnValue({ data: { ...mockMe, status: 'member' } } as any)
    wrapper()
    expect(screen.getByText(/Member Ticket/)).toBeInTheDocument()
    expect(screen.getAllByText('2,000 AMD').length).toBeGreaterThan(0)
  })
})
