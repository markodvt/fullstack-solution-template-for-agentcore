/**
 * Session List Component
 * 
 * Displays a list of session cards.
 */

import type { Session } from '@/services/observabilityService'
import SessionCard from './SessionCard'

interface SessionListProps {
  sessions: Session[]
}

export default function SessionList({ sessions }: SessionListProps) {
  return (
    <div className="space-y-4">
      {sessions.map((session) => (
        <SessionCard key={session.sessionId} session={session} />
      ))}
    </div>
  )
}
