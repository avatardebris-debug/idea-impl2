import { useState, useEffect } from 'react'

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    // In a real app, fetch from /api/dashboard/sentiment-summary
    setStats({
      total: 142,
      positive: 95,
      neutral: 20,
      negative: 27,
      avgRating: 4.2
    })
  }, [])

  if (!stats) return <div className="animate-pulse flex space-x-4"><div className="h-10 bg-slate-200 rounded w-full"></div></div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-gray-800">Overview</h2>
        <a 
          href="/api/dashboard/export?business_id=demo_business"
          className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 font-medium"
        >
          Export CSV
        </a>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p className="text-gray-500 text-sm font-medium">Total Reviews</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{stats.total}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p className="text-gray-500 text-sm font-medium">Avg Rating</p>
          <div className="flex items-center mt-2">
            <p className="text-3xl font-bold text-gray-800">{stats.avgRating}</p>
            <span className="ml-2 text-yellow-400">★</span>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 border-t-4 border-t-green-500">
          <p className="text-gray-500 text-sm font-medium">Positive Sentiment</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{stats.positive}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 border-t-4 border-t-red-500">
          <p className="text-gray-500 text-sm font-medium">Negative Sentiment</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{stats.negative}</p>
        </div>
      </div>

      {/* Charts Placeholder */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-80 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Trend Chart (Recharts Integration Pending)</p>
      </div>
    </div>
  )
}
