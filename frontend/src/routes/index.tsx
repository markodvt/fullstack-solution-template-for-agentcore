// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Routes, Route, Navigate } from 'react-router-dom'
import ChatPage from './ChatPage'
import AgentGalleryPage from './AgentGalleryPage'
import AgentDetailsPage from './AgentDetailsPage'
import AboutPage from './AboutPage'
import MemoryPage from './MemoryPage'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/about" replace />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/agents" element={<AgentGalleryPage />} />
      <Route path="/agents/:agentName" element={<AgentDetailsPage />} />
      <Route path="/memory" element={<MemoryPage />} />
    </Routes>
  )
}
