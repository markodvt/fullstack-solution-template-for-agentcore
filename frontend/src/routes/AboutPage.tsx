/**
 * AboutPage displays information about the FAST project.
 * 
 * This page:
 * - Provides an overview of the Fullstack AgentCore Solution Template
 * - Displays a screenshot of the application
 * - Links to the GitHub repository
 * - Uses responsive layout with Card components
 */

import { NavigationBar } from '@/components/navigation/NavigationBar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Github, ExternalLink } from 'lucide-react'

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background">
      <NavigationBar />
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        <div className="space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold">Fullstack AgentCore Solution Template (FAST)</h1>
          </div>

          {/* Description Card */}
          <Card>
            <CardHeader>
              <CardTitle>About FAST</CardTitle>
              <CardDescription>A starter project for building full stack applications on AgentCore</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground leading-relaxed">
                The Fullstack AgentCore Solution Template (FAST) is a starter project repository that enables users 
                (delivery scientists and engineers) to quickly deploy a secured, web-accessible React frontend 
                connected to an AgentCore backend. Its purpose is to accelerate building full stack applications 
                on AgentCore from weeks to days by handling the undifferentiated heavy lifting of infrastructure 
                setup and to enable vibe-coding style development on top. The only central dependency of FAST is 
                AgentCore. It is agnostic to agent SDK (Strands, LangGraph, etc) and to coding assistant platforms 
                (Q, Kiro, Cline, Claude Code, etc).
              </p>
            </CardContent>
          </Card>

          {/* Architecture Diagram Card */}
          <Card>
            <CardHeader>
              <CardTitle>Architecture</CardTitle>
              <CardDescription>FAST system architecture and components</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg overflow-hidden border">
                <img 
                  src="/architecture-diagram/FAST-architecture-20251201.png" 
                  alt="FAST Architecture Diagram" 
                  className="w-full h-auto"
                />
              </div>
            </CardContent>
          </Card>

          {/* GitHub Link Card */}
          <Card>
            <CardHeader>
              <CardTitle>Source Code</CardTitle>
              <CardDescription>View the project on GitHub</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
                <Button asChild className="gap-2">
                  <a 
                    href="https://github.com/awslabs/fullstack-solution-template-for-agentcore" 
                    target="_blank" 
                    rel="noopener noreferrer"
                  >
                    <Github className="h-4 w-4" />
                    View on GitHub
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </Button>
                <p className="text-sm text-muted-foreground">
                  Contributions and feedback are welcome!
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
