/**
 * NavigationBar provides navigation links across the application.
 * 
 * This component:
 * - Displays navigation links to main pages (Chat, Agents)
 * - Highlights the active link based on current route
 * - Includes user authentication controls
 * - Uses responsive design for mobile and desktop
 * 
 * Requirements: 1.1
 */

import { Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { MessageSquare, Users, Brain } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { cn } from '@/lib/utils'

export function NavigationBar() {
  const location = useLocation()
  const { isAuthenticated, signOut } = useAuth()

  const navLinks = [
    {
      to: '/chat',
      label: 'Chat',
      icon: MessageSquare,
    },
    {
      to: '/agents',
      label: 'Agents',
      icon: Users,
    },
    {
      to: '/memory',
      label: 'Memory',
      icon: Brain,
    },
  ]

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Title */}
          <div className="flex items-center gap-6">
            <Link to="/about" className="text-xl font-bold hover:text-primary transition-colors">
              FAST
            </Link>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center gap-2">
              {navLinks.map((link) => {
                const Icon = link.icon
                const isActive = location.pathname === link.to
                
                return (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={cn(
                      'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {link.label}
                  </Link>
                )
              })}
            </div>
          </div>

          {/* User Actions */}
          <div className="flex items-center gap-2">
            {isAuthenticated && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline">Logout</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Confirm Logout</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to log out? You will need to sign in again to access your
                      account.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => signOut()}>Confirm</AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden flex items-center gap-2 pb-3">
          {navLinks.map((link) => {
            const Icon = link.icon
            const isActive = location.pathname === link.to
            
            return (
              <Link
                key={link.to}
                to={link.to}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {link.label}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
