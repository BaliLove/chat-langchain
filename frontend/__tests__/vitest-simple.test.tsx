import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

describe('Vitest Simple Test', () => {
  it('should pass a basic test', () => {
    expect(1 + 1).toBe(2)
  })

  it('should render a simple component', () => {
    const TestComponent = () => <div>Hello Vitest</div>
    render(<TestComponent />)
    expect(screen.getByText('Hello Vitest')).toBeInTheDocument()
  })
})