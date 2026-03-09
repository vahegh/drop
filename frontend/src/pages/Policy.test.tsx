import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Policy from './Policy'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn(() => ({ data: undefined })) }))

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Policy', () => {
  it('renders Return Policy heading', () => {
    wrapper(<Policy />)
    expect(screen.getByText('Return Policy')).toBeInTheDocument()
  })

  it('renders refund steps', () => {
    wrapper(<Policy />)
    expect(screen.getByText(/2–3 business days/i)).toBeInTheDocument()
  })

  it('renders home link', () => {
    wrapper(<Policy />)
    expect(screen.getByText('← Home')).toBeInTheDocument()
  })

  it('renders support email link', () => {
    wrapper(<Policy />)
    expect(screen.getByText('email')).toBeInTheDocument()
  })
})
