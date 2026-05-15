import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import ReviewInbox from './components/ReviewInbox'
import './index.css'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const businessId = "demo_business" // Mock ID for MVP

  useEffect(() => {
    // Connect to WebSocket for real-time notifications
    const ws = new WebSocket(`ws://localhost:8000/api/ws/notifications/${businessId}`)
    
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'new_review') {
        alert(`New Review from ${msg.data.platform}: ${msg.data.text.substring(0, 30)}...`)
        // In a real app, we'd update global state here
      }
    }
    
    return () => ws.close()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-md">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-blue-600">ReviewPulse</h1>
          <p className="text-sm text-gray-500 mt-1">Aggregator Dashboard</p>
        </div>
        <nav className="mt-6">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`w-full text-left px-6 py-3 font-medium ${activeTab === 'dashboard' ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            Overview
          </button>
          <button 
            onClick={() => setActiveTab('inbox')}
            className={`w-full text-left px-6 py-3 font-medium ${activeTab === 'inbox' ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            Review Inbox
          </button>
          <button 
            className="w-full text-left px-6 py-3 font-medium text-gray-600 hover:bg-gray-50"
          >
            Settings
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'inbox' && <ReviewInbox businessId={businessId} />}
      </div>
    </div>
  )
}

export default App
