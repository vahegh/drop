import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import NotFound from './NotFound'

vi.mock('../hooks/useMe', () => ({ useMe: vi.fn(() => ({ data: undefined })) }))

function wrapper(ui: React.ReactElement) {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('NotFound', () => {
  it('renders 404 heading', () => {
    wrapper(<NotFound />)
    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('renders page not found message', () => {
    wrapper(<NotFound />)
    expect(screen.getByText('Page not found.')).toBeInTheDocument()
  })

  it('renders Go home link', () => {
    wrapper(<NotFound />)
    expect(screen.getByText('Go home')).toBeInTheDocument()
  })
})
