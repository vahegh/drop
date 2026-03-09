import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Callback from './Callback'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn(() => ({ data: undefined })) }))
vi.mock('../api/payments', () => ({ confirmPayment: vi.fn() }))

import { confirmPayment } from '../api/payments'

function wrapper(search = '') {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/app/callback${search}`]}>
        <Routes>
          <Route path="/app/callback" element={<Callback />} />
          <Route path="/app/callback/*" element={<Callback />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.mocked(confirmPayment).mockReset()
})

describe('Callback', () => {
  it('shows error when order_id is missing', async () => {
    wrapper()
    expect(await screen.findByText('Missing order ID.')).toBeInTheDocument()
  })

  it('shows confirming payment while waiting', () => {
    vi.mocked(confirmPayment).mockReturnValue(new Promise(() => {}))
    wrapper('?order_id=12345')
    expect(screen.getByText('Confirming payment…')).toBeInTheDocument()
  })

  it('shows payment confirmed on success', async () => {
    vi.mocked(confirmPayment).mockResolvedValue({
      status: 'CONFIRMED',
      num_tickets: 1,
      amount: 5000,
    } as any)
    wrapper('?order_id=12345')
    expect(await screen.findByText('Payment confirmed!')).toBeInTheDocument()
    expect(screen.getByText('1 ticket issued · 5,000 AMD')).toBeInTheDocument()
  })

  it('shows payment failed on non-confirmed status', async () => {
    vi.mocked(confirmPayment).mockResolvedValue({
      status: 'FAILED',
      num_tickets: 0,
      amount: 0,
    } as any)
    wrapper('?order_id=12345')
    expect(await screen.findByText('Payment failed')).toBeInTheDocument()
  })

  it('shows error on API failure', async () => {
    vi.mocked(confirmPayment).mockRejectedValue(new Error('Network error'))
    wrapper('?order_id=12345')
    expect(await screen.findByText('Payment confirmation failed.')).toBeInTheDocument()
  })
})
