import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Section from './Section'

describe('Section', () => {
  it('renders children', () => {
    render(<Section><p>hello</p></Section>)
    expect(screen.getByText('hello')).toBeInTheDocument()
  })

  it('renders title and subtitle when provided', () => {
    render(<Section title="My Title" subtitle="My Subtitle"><span /></Section>)
    expect(screen.getByText('My Title')).toBeInTheDocument()
    expect(screen.getByText('My Subtitle')).toBeInTheDocument()
  })

  it('renders hr separator when sep={true}', () => {
    const { container } = render(<Section sep><span /></Section>)
    expect(container.querySelector('.bg-white\\/10')).toBeInTheDocument()
  })

  it('omits title element when no title prop', () => {
    render(<Section><span>child</span></Section>)
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })
})
