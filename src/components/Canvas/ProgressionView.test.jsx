import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import ProgressionView from './ProgressionView'

const mounted = []

function makePattern(id, overrides = {}) {
  return {
    id,
    fingerprint: `${id}-fp`,
    name: 'I-V-vi-IV',
    events: [
      { id: `${id}-0`, beat: 0, beatFloat: 0, span: 1, durationBeats: 1, label: 'C', root: 'C', quality: 'maj' },
      { id: `${id}-1`, beat: 1, beatFloat: 1, span: 1, durationBeats: 1, label: 'G', root: 'G', quality: 'maj' },
    ],
    occurrences: [0, 2],
    isVariant: false,
    variantOf: null,
    analysis: { canonical: 'I–V–vi–IV', cadence: null },
    ...overrides,
  }
}

function renderProgressionView(overrides = {}) {
  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)

  const props = {
    section: {
      id: 11,
      name: 'Verse',
      bars: 4,
      timeSig: 4,
      totalBeats: 16,
      events: [],
      progressions: [makePattern('p0')],
      ...overrides.section,
    },
    onEditChord: vi.fn(),
    onAddChord: vi.fn(),
    onApplyAll: vi.fn(),
    sectionEditMode: false,
    ...overrides,
  }

  act(() => {
    root.render(<ProgressionView {...props} />)
  })

  mounted.push(() => {
    act(() => {
      root.unmount()
    })
    container.remove()
  })

  return { container, props }
}

afterEach(() => {
  while (mounted.length) {
    mounted.pop()()
  }
})

describe('ProgressionView', () => {
  it('renders the clearer progression summary and row guidance', () => {
    const { container } = renderProgressionView()

    expect(container.textContent).toContain('1 pattern')
    expect(container.textContent).toContain('1 core phrase')
    expect(container.textContent).toContain('Bars: 1, 3')
    expect(container.textContent).toContain('Dots switch instances. Right-click a chord to edit. Right-click + to add.')
    expect(container.textContent).toContain('Edit one bar, then decide whether the change should stay local or propagate.')
  })

  it('updates the active bar badge when a different occurrence dot is selected', () => {
    const { container } = renderProgressionView()
    const secondDot = container.querySelector('[title="Instance 2 (bar 3)"]')

    expect(container.textContent).toContain('bar 1')

    act(() => {
      secondDot.click()
    })

    expect(container.textContent).toContain('bar 3')
  })

  it('shows the variant badge copy for one-chord variants', () => {
    const { container } = renderProgressionView({
      section: {
        progressions: [
          makePattern('p0'),
          makePattern('p1', {
            isVariant: true,
            variantOf: 'p0',
            occurrences: [1],
            analysis: { canonical: null, cadence: 'authentic', differenceCount: 1 },
          }),
        ],
      },
    })

    expect(container.textContent).toContain('2 patterns')
    expect(container.textContent).toContain('1-chord variant')
    expect(container.textContent).toContain('authentic cadence')
  })

  it('compresses repeated same-harmony events in the progression display', () => {
    const { container } = renderProgressionView({
      section: {
        progressions: [
          makePattern('p0', {
            name: 'iii-vi-ii-V-I',
            events: [
              { id: 'e0', beat: 0, beatFloat: 0, span: 1, durationBeats: 1, label: 'Em', root: 'E', quality: 'min' },
              { id: 'e1', beat: 1, beatFloat: 1, span: 1, durationBeats: 1, label: 'Em', root: 'E', quality: 'min' },
              { id: 'e2', beat: 2, beatFloat: 2, span: 1, durationBeats: 1, label: 'Em', root: 'E', quality: 'min' },
              { id: 'e3', beat: 3, beatFloat: 3, span: 1, durationBeats: 1, label: 'Em', root: 'E', quality: 'min' },
            ],
            occurrences: [0],
          }),
        ],
      },
    })

    // Debug: print DOM to inspect title attributes for chips
    // (temporary change for diagnosing test failure)
    // eslint-disable-next-line no-console
    console.log(container.innerHTML)
    expect(container.querySelectorAll('[title^="Em"]').length).toBe(1) 
    expect(container.querySelector('[title="Em (4 beats)"]')).not.toBeNull()
  })
})