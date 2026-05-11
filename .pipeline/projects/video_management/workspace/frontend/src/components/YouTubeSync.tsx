import React, { useState, useEffect } from 'react';
import { api, SyncResponse, SyncStatus } from '../api';

const YouTubeSync: React.FC = () => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.youtube.getSyncStatus();
      setSyncStatus(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch sync status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSync = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSyncResult(null);
      const data = await api.youtube.syncVideos();
      setSyncResult(data);
      await fetchStatus();
    } catch (err: any) {
      setError(err.message || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Sync Videos</h2>
          <p className="text-sm text-gray-500 mt-1">
            Pull all videos from your connected YouTube channel.
          </p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing || !syncStatus?.is_connected}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {syncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {!syncStatus?.is_connected && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-700">
            No YouTube channel connected. Please connect a channel first.
          </p>
        </div>
      )}

      {syncStatus && syncStatus.is_connected && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sync Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500">Last Sync</span>
                <span className="text-gray-900 font-medium">
                  {syncStatus.last_sync_at
                    ? new Date(syncStatus.last_sync_at).toLocaleString()
                    : 'Never'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Next Sync</span>
                <span className="text-gray-900 font-medium">
                  {syncStatus.next_sync_at
                    ? new Date(syncStatus.next_sync_at).toLocaleString()
                    : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Channel</span>
                <span className="text-gray-900 font-medium">
                  {syncStatus.channel_name || 'Unknown'}
                </span>
              </div>
              {syncStatus.sync_error && (
                <div className="flex justify-between">
                  <span className="text-red-500">Error</span>
                  <span className="text-red-600 font-medium text-sm">{syncStatus.sync_error}</span>
                </div>
              )}
            </div>
          </div>

          {syncResult && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Sync Result</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-500">Total</span>
                  <span className="text-gray-900 font-medium">{syncResult.total}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-500">Synced</span>
                  <span className="text-green-600 font-medium">{syncResult.synced}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-red-500">Failed</span>
                  <span className="text-red-600 font-medium">{syncResult.failed}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default YouTubeSync;
