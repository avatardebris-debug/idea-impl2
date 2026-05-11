import React, { useState, useEffect } from 'react';
import { api, YouTubeChannelStatus } from '../api';

const YouTubeChannel: React.FC = () => {
  const [status, setStatus] = useState<YouTubeChannelStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.youtube.getChannelStatus();
      setStatus(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleConnect = () => {
    // Redirect to Google OAuth
    window.location.href = `/api/youtube/auth`;
  };

  const handleDisconnect = async () => {
    try {
      await api.youtube.disconnectChannel();
      fetchStatus();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">YouTube Channel</h3>
          <p className="text-sm text-gray-500">Connect your YouTube channel to sync videos</p>
        </div>
        {status?.is_connected ? (
          <button
            onClick={handleDisconnect}
            className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
          >
            Disconnect
          </button>
        ) : (
          <button
            onClick={handleConnect}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
            </svg>
            Connect Channel
          </button>
        )}
      </div>

      {status?.is_connected && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center gap-4 mb-4">
            {status.channel_avatar && (
              <img
                src={status.channel_avatar}
                alt={status.channel_name || 'Channel'}
                className="w-12 h-12 rounded-full"
              />
            )}
            <div>
              <h4 className="font-medium text-gray-900">{status.channel_name}</h4>
              <p className="text-sm text-gray-500">{status.channel_id}</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">
                {status.channel_stats?.subscriberCount || 0}
              </p>
              <p className="text-xs text-gray-500">Subscribers</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">
                {status.channel_stats?.viewCount || 0}
              </p>
              <p className="text-xs text-gray-500">Views</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">
                {status.channel_stats?.videoCount || 0}
              </p>
              <p className="text-xs text-gray-500">Videos</p>
            </div>
          </div>

          {status.last_sync_at && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-500">
                Last synced: {new Date(status.last_sync_at).toLocaleString()}
              </p>
            </div>
          )}

          {status.sync_error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              Sync Error: {status.sync_error}
            </div>
          )}
        </div>
      )}

      {!status?.is_connected && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <svg className="w-12 h-12 mx-auto text-blue-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h4 className="text-lg font-medium text-blue-900 mb-2">Connect Your YouTube Channel</h4>
          <p className="text-sm text-blue-700 mb-4">
            Link your YouTube channel to automatically sync your videos and manage them from this platform.
          </p>
          <button
            onClick={handleConnect}
            className="px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Get Started
          </button>
        </div>
      )}
    </div>
  );
};

export default YouTubeChannel;
