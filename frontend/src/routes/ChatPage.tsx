"use client"
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import ChatInterface from "@/components/chat/ChatInterface"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/useAuth"
import { GlobalContextProvider } from "@/app/context/GlobalContext"
import { NavigationBar } from "@/components/navigation/NavigationBar"

export default function ChatPage() {
  const { isAuthenticated, signIn } = useAuth()

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-4xl">Please sign in</p>
        <Button onClick={() => signIn()}>Sign In</Button>
      </div>
    )
  }

  return (
    <GlobalContextProvider>
      <div className="flex flex-col h-screen">
        <NavigationBar />
        <div className="flex-1 overflow-hidden">
          <ChatInterface />
        </div>
      </div>
    </GlobalContextProvider>
  )
}
