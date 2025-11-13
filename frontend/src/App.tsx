import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Complaints from './pages/Complaints'
import Analytics from './pages/Analytics'
import './styles/globals.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Navigate to="/" replace />} />
            <Route path="/complaints" element={<Complaints />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/maps" element={<div className="p-6"><h1 className="text-2xl font-bold">Maps Page</h1><p className="text-gray-600 mt-2">Interactive maps with real-time locations</p></div>} />
            <Route path="/alerts" element={<div className="p-6"><h1 className="text-2xl font-bold">Alerts Page</h1><p className="text-gray-600 mt-2">Alert management and notifications</p></div>} />
            <Route path="/users" element={<div className="p-6"><h1 className="text-2xl font-bold">Users Page</h1><p className="text-gray-600 mt-2">User administration and management</p></div>} />
            <Route path="/settings" element={<div className="p-6"><h1 className="text-2xl font-bold">Settings Page</h1><p className="text-gray-600 mt-2">System settings and configuration</p></div>} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App