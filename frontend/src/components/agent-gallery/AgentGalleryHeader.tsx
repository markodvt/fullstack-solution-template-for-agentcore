/**
 * AgentGalleryHeader displays the title and description for the Agent Gallery page.
 * 
 * This component provides context to users about what the Agent Gallery is
 * and what they can do with it.
 * 
 * Requirements: 1.1, 1.2
 */

export default function AgentGalleryHeader() {
  return (
    <div className="mb-8">
      <h1 className="text-4xl font-bold mb-2">Agent Gallery</h1>
      <p className="text-muted-foreground text-lg">
        Discover and interact with available agents in your account. Click on any agent to view details and start a conversation.
      </p>
    </div>
  )
}
