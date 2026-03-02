/**
 * AgentCodeViewer displays the agent's Python source code with syntax highlighting.
 * 
 * This component shows:
 * - Agent Python source code (when available)
 * - Syntax highlighting for Python
 * - Copy-to-clipboard functionality
 * - Graceful handling when source code is not available
 * 
 * Requirements: 3.6
 */

import { Agent } from '@/services/agentDiscoveryService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Copy, Check, Code2, FileCode } from 'lucide-react'
import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface AgentCodeViewerProps {
  agent: Agent
}

export default function AgentCodeViewer({ agent }: AgentCodeViewerProps) {
  const [copied, setCopied] = useState(false)

  const sourceCode = agent.sourceCode

  const handleCopyCode = async () => {
    if (!sourceCode) return

    try {
      await navigator.clipboard.writeText(sourceCode)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy code:', err)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1.5">
            <CardTitle className="flex items-center gap-2">
              <Code2 className="h-5 w-5" />
              Agent Source Code
            </CardTitle>
            <CardDescription>
              Python implementation of this agent
            </CardDescription>
          </div>
          {sourceCode && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyCode}
              className="gap-2"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  Copy Code
                </>
              )}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {sourceCode ? (
          <div className="relative">
            <SyntaxHighlighter
              language="python"
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
              }}
              showLineNumbers
            >
              {sourceCode}
            </SyntaxHighlighter>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileCode className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Source code could not be loaded for this agent.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
