/**
 * MemoryExpandContext provides global expand/collapse state for memory sections and cards.
 * 
 * This context:
 * - Manages expand/collapse state for all memory sections
 * - Manages expand/collapse state for all memory cards
 * - Provides expandAll/collapseAll functionality
 * - Persists state in localStorage
 * 
 * Requirements: UX enhancement (task 36.2)
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface MemoryExpandContextType {
  // Section expand state
  sectionsExpanded: Record<string, boolean>
  setSectionExpanded: (sectionType: string, expanded: boolean) => void
  
  // Card expand state
  cardsExpanded: Record<string, boolean>
  setCardExpanded: (cardId: string, expanded: boolean) => void
  
  // Global controls
  expandAll: () => void
  collapseAll: () => void
  
  // Global state for triggering expand/collapse all
  globalExpandState: 'expanded' | 'collapsed' | null
}

const MemoryExpandContext = createContext<MemoryExpandContextType | undefined>(undefined)

const SECTIONS_STORAGE_KEY = 'memory-sections-expanded'
const CARDS_STORAGE_KEY = 'memory-cards-expanded'

interface MemoryExpandProviderProps {
  children: ReactNode
}

export function MemoryExpandProvider({ children }: MemoryExpandProviderProps) {
  // Load initial state from localStorage
  const [sectionsExpanded, setSectionsExpanded] = useState<Record<string, boolean>>(() => {
    try {
      const stored = localStorage.getItem(SECTIONS_STORAGE_KEY)
      return stored ? JSON.parse(stored) : {}
    } catch {
      return {}
    }
  })

  const [cardsExpanded, setCardsExpanded] = useState<Record<string, boolean>>(() => {
    try {
      const stored = localStorage.getItem(CARDS_STORAGE_KEY)
      return stored ? JSON.parse(stored) : {}
    } catch {
      return {}
    }
  })

  const [globalExpandState, setGlobalExpandState] = useState<'expanded' | 'collapsed' | null>(null)

  // Persist sections state to localStorage
  useEffect(() => {
    localStorage.setItem(SECTIONS_STORAGE_KEY, JSON.stringify(sectionsExpanded))
  }, [sectionsExpanded])

  // Persist cards state to localStorage
  useEffect(() => {
    localStorage.setItem(CARDS_STORAGE_KEY, JSON.stringify(cardsExpanded))
  }, [cardsExpanded])

  const setSectionExpanded = (sectionType: string, expanded: boolean) => {
    setSectionsExpanded((prev) => ({
      ...prev,
      [sectionType]: expanded,
    }))
  }

  const setCardExpanded = (cardId: string, expanded: boolean) => {
    setCardsExpanded((prev) => ({
      ...prev,
      [cardId]: expanded,
    }))
  }

  const expandAll = () => {
    setGlobalExpandState('expanded')
    // Clear the global state after a short delay to allow components to react
    setTimeout(() => setGlobalExpandState(null), 100)
  }

  const collapseAll = () => {
    setGlobalExpandState('collapsed')
    // Clear the global state after a short delay to allow components to react
    setTimeout(() => setGlobalExpandState(null), 100)
  }

  return (
    <MemoryExpandContext.Provider
      value={{
        sectionsExpanded,
        setSectionExpanded,
        cardsExpanded,
        setCardExpanded,
        expandAll,
        collapseAll,
        globalExpandState,
      }}
    >
      {children}
    </MemoryExpandContext.Provider>
  )
}

export function useMemoryExpand() {
  const context = useContext(MemoryExpandContext)
  if (context === undefined) {
    throw new Error('useMemoryExpand must be used within a MemoryExpandProvider')
  }
  return context
}
