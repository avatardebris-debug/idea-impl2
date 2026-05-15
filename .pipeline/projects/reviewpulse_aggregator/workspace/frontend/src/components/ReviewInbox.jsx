import { useState, useEffect } from 'react'

export default function ReviewInbox({ businessId }) {
  const [reviews, setReviews] = useState([])

  useEffect(() => {
    // In a real app, fetch from /api/reviews
    setReviews([
      { id: 1, platform: 'Google', author: 'John Doe', rating: 5, text: 'Great service! Highly recommended.', sentiment_label: 'POSITIVE', published_at: '2026-05-13' },
      { id: 2, platform: 'Yelp', author: 'Jane Smith', rating: 2, text: 'Food was cold and service was slow.', sentiment_label: 'NEGATIVE', published_at: '2026-05-12' },
      { id: 3, platform: 'Facebook', author: 'Bob Wilson', rating: 4, text: 'Good experience overall.', sentiment_label: 'POSITIVE', published_at: '2026-05-11' }
    ])
  }, [])

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Review Inbox</h2>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {reviews.map(review => (
          <div key={review.id} className="p-6 border-b border-gray-100 hover:bg-gray-50 transition-colors">
            <div className="flex justify-between items-start mb-2">
              <div>
                <span className={`inline-block px-2 py-1 rounded text-xs font-bold mr-2 ${review.platform === 'Google' ? 'bg-blue-100 text-blue-700' : review.platform === 'Yelp' ? 'bg-red-100 text-red-700' : 'bg-blue-600 text-white'}`}>
                  {review.platform}
                </span>
                <span className="font-semibold text-gray-800">{review.author}</span>
                <span className="text-gray-400 text-sm ml-2">{review.published_at}</span>
              </div>
              <div className="flex items-center">
                <span className="text-yellow-400 mr-1">{'★'.repeat(review.rating)}{'☆'.repeat(5-review.rating)}</span>
                <span className={`ml-3 px-2 py-1 rounded text-xs font-bold ${review.sentiment_label === 'POSITIVE' ? 'bg-green-100 text-green-700' : review.sentiment_label === 'NEGATIVE' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
                  {review.sentiment_label}
                </span>
              </div>
            </div>
            <p className="text-gray-600 mt-2">{review.text}</p>
            <div className="mt-4 flex space-x-3">
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                Generate Reply Draft
              </button>
              {review.sentiment_label === 'NEGATIVE' && (
                <button className="text-gray-500 hover:text-red-600 px-4 py-2 text-sm font-medium transition-colors">
                  Flag Incorrect Sentiment
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
