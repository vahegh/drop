import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Unsubscribe from './Unsubscribe'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn(() => ({ data: undefined })) }))
vi.mock('../api/client', () => ({
  default: { post: vi.fn(), delete: vi.fn() },
}))

function wrapper(search = '') {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/unsubscribe${search}`]}>
        <Routes>
          <Route path="/unsubscribe" element={<Unsubscribe />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Unsubscribe', () => {
  it('shows no email message when email param is missing', () => {
    wrapper()
    expect(screen.getByText('No email address provided.')).toBeInTheDocument()
  })

  it('shows unsubscribe button when email is provided', () => {
    wrapper('?email=test@example.com')
    expect(screen.getByText('Unsubscribe')).toBeInTheDocument()
  })

  it('shows delete account button when email is provided', () => {
    wrapper('?email=test@example.com')
    expect(screen.getByText('Delete my account instead')).toBeInTheDocument()
  })

  it('shows email in subtitle', () => {
    wrapper('?email=test@example.com')
    expect(screen.getByText(/test@example\.com/)).toBeInTheDocument()
  })
})
