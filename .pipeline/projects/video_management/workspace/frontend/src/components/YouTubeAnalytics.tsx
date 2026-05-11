import { useState, useEffect } from 'react';
import { api, type Video } from '../api';

interface YouTubeVideoStats {
  video_id: string;
  title: string;
  views: number;
  likes: number;
  dislikes: number;
  comments: number;
  shares: number;
  estimated_revenue: number;
  average_view_duration: string;
  audience_retention: number;
  last_updated: string;
}

interface YouTubeAnalytics {
  total_videos: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_revenue: number;
  average_views_per_video: number;
  top_videos: YouTubeVideoStats[];
  daily_stats: { date: string; views: number; likes: number; subscribers: number }[];
  subscriber_count: number;
  subscriber_growth: number;
}

interface YouTubeAnalyticsProps {
  tableId: string;
}

export default function YouTubeAnalytics({ tableId }: YouTubeAnalyticsProps) {
  const [analytics, setAnalytics] = useState<YouTubeAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  useEffect(() => {
    loadAnalytics();
    loadVideos();
  }, [tableId, timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/youtube/analytics?table_id=${tableId}&time_range=${timeRange}`);
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const loadVideos = async () => {
    try {
      const data = await api.videos.list({ page: 1, page_size: 100 });
      setVideos(data.items);
    } catch (err: any) {
      // Non-critical
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatCurrency = (num: number): string => {
    return '$' + num.toFixed(2);
  };

  const statCards = analytics ? [
    { label: 'Total Views', value: formatNumber(analytics.total_views), icon: '👁️', change: '+12.5%' },
    { label: 'Total Likes', value: formatNumber(analytics.total_likes), icon: '👍', change: '+8.3%' },
    { label: 'Subscribers', value: formatNumber(analytics.subscriber_count), icon: '👥', change: analytics.subscriber_growth > 0 ? `+${analytics.subscriber_growth.toFixed(1)}` : `${analytics.subscriber_growth.toFixed(1)}` },
    { label: 'Est. Revenue', value: formatCurrency(analytics.total_revenue), icon: '💰', change: '+5.2%' },
    { label: 'Total Videos', value: analytics.total_videos.toString(), icon: '📹', change: '' },
    { label: 'Avg Views/Video', value: formatNumber(analytics.average_views_per_video), icon: '📊', change: '' },
  ] : [];

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '700' }}>YouTube Analytics</h1>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value as typeof timeRange)}
          className="form-group"
          style={{ width: 'auto' }}
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="all">All time</option>
        </select>
      </div>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <div className="loading">Loading analytics...</div>
      ) : !analytics ? (
        <div className="card">
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
            No YouTube analytics available. Make sure your YouTube account is connected.
          </p>
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="stats-grid">
            {statCards.map((stat, index) => (
              <div key={index} className="stat-card">
                <div className="stat-icon">{stat.icon}</div>
                <div className="stat-content">
                  <div className="stat-value">{stat.value}</div>
                  <div className="stat-label">{stat.label}</div>
                </div>
                {stat.change && (
                  <div className={`stat-change ${stat.change.startsWith('+') ? 'positive' : 'negative'}`}>
                    {stat.change}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Daily Stats Chart */}
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Daily Views</h3>
            <div className="chart-container">
              {analytics.daily_stats.length > 0 ? (
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', height: '200px' }}>
                  {analytics.daily_stats.map((stat, index) => (
                    <div
                      key={index}
                      style={{
                        flex: 1,
                        height: `${Math.max(4, (stat.views / Math.max(...analytics.daily_stats.map(s => s.views))) * 100)}%`,
                        backgroundColor: 'var(--primary)',
                        borderRadius: '2px 2px 0 0',
                        position: 'relative',
                      }}
                      title={`${stat.date}: ${stat.views} views`}
                    >
                      <div style={{
                        position: 'absolute',
                        bottom: '-20px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        fontSize: '0.6rem',
                        color: 'var(--text-secondary)',
                        whiteSpace: 'nowrap',
                      }}>
                        {new Date(stat.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No daily stats available</p>
              )}
            </div>
          </div>

          {/* Top Videos */}
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Top Performing Videos</h3>
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Video</th>
                    <th>Views</th>
                    <th>Likes</th>
                    <th>Comments</th>
                    <th>Revenue</th>
                    <th>Avg. Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.top_videos.map((video) => (
                    <tr key={video.video_id}>
                      <td>
                        <div style={{ fontWeight: '500' }}>{video.title}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          {video.video_id}
                        </div>
                      </td>
                      <td>{formatNumber(video.views)}</td>
                      <td>{formatNumber(video.likes)}</td>
                      <td>{formatNumber(video.comments)}</td>
                      <td>{formatCurrency(video.estimated_revenue)}</td>
                      <td>{video.average_view_duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
