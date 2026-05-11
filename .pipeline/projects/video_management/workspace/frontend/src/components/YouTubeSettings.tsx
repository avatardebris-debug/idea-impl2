import { useState, useEffect } from 'react';
import { api, type Table } from '../api';

export interface YouTubeConfig {
  id: string;
  channel_id: string;
  api_key: string;
  access_token: string;
  refresh_token: string;
  token_expiry: string | null;
  is_connected: boolean;
  created_at: string;
  updated_at: string;
}

export default function YouTubeSettings() {
  const [config, setConfig] = useState<YouTubeConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [channelId, setChannelId] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [refreshToken, setRefreshToken] = useState('');
  const [showCredentials, setShowCredentials] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/youtube/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
        setApiKey(data.api_key ? '***' + data.api_key.slice(-8) : '');
        setChannelId(data.channel_id || '');
        setAccessToken(data.access_token ? '***' + data.access_token.slice(-8) : '');
        setRefreshToken(data.refresh_token ? '***' + data.refresh_token.slice(-8) : '');
      }
    } catch (err: any) {
      // No config yet
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const body: Partial<YouTubeConfig> = {};
      if (apiKey && !apiKey.startsWith('***')) body.api_key = apiKey;
      if (channelId) body.channel_id = channelId;
      if (accessToken && !accessToken.startsWith('***')) body.access_token = accessToken;
      if (refreshToken && !refreshToken.startsWith('***')) body.refresh_token = refreshToken;

      const response = await fetch('/api/youtube/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save configuration');
      }

      setSuccess(true);
      loadConfig();
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect YouTube? This will remove all YouTube credentials.')) return;

    try {
      await fetch('/api/youtube/config', { method: 'DELETE' });
      setConfig(null);
      setApiKey('');
      setChannelId('');
      setAccessToken('');
      setRefreshToken('');
    } catch (err: any) {
      setError(err.message || 'Failed to disconnect');
    }
  };

  const handleTestConnection = async () => {
    setSaving(true);
    setError(null);

    try {
      const response = await fetch('/api/youtube/test-connection', { method: 'POST' });
      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
      } else {
        setError(data.detail || 'Connection test failed');
      }
    } catch (err: any) {
      setError(err.message || 'Connection test failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '700' }}>YouTube Settings</h1>
        {config?.is_connected && (
          <button className="btn btn-danger" onClick={handleDisconnect}>
            Disconnect
          </button>
        )}
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">Configuration saved successfully!</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Connection Status</h3>
        {loading ? (
          <div className="loading">Loading...</div>
        ) : config?.is_connected ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <span style={{ color: 'var(--success)' }}>✓</span>
              <span>Connected to YouTube</span>
            </div>
            <p><strong>Channel ID:</strong> {config.channel_id}</p>
            <p><strong>API Key:</strong> {config.api_key ? '***' + config.api_key.slice(-8) : 'Not set'}</p>
            <p><strong>Access Token:</strong> {config.access_token ? '***' + config.access_token.slice(-8) : 'Not set'}</p>
            <p><strong>Refresh Token:</strong> {config.refresh_token ? '***' + config.refresh_token.slice(-8) : 'Not set'}</p>
            <p><strong>Last Updated:</strong> {new Date(config.updated_at).toLocaleString()}</p>
            <button className="btn btn-secondary" onClick={handleTestConnection} disabled={saving}>
              Test Connection
            </button>
          </div>
        ) : (
          <div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Not connected. Enter your YouTube API credentials below to connect.
            </p>
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label htmlFor="apiKey">API Key</label>
                <input
                  type="password"
                  id="apiKey"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your YouTube API key"
                />
              </div>

              <div className="form-group">
                <label htmlFor="channelId">Channel ID</label>
                <input
                  type="text"
                  id="channelId"
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  placeholder="Enter your YouTube channel ID"
                />
              </div>

              <div className="form-group">
                <label htmlFor="accessToken">Access Token</label>
                <input
                  type="password"
                  id="accessToken"
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  placeholder="Enter your YouTube access token"
                />
              </div>

              <div className="form-group">
                <label htmlFor="refreshToken">Refresh Token</label>
                <input
                  type="password"
                  id="refreshToken"
                  value={refreshToken}
                  onChange={(e) => setRefreshToken(e.target.value)}
                  placeholder="Enter your YouTube refresh token"
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={handleTestConnection} disabled={saving}>
                  Test Connection
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Setup Instructions</h3>
        <ol style={{ paddingLeft: '1.5rem', color: 'var(--text-secondary)' }}>
          <li style={{ marginBottom: '0.5rem' }}>Go to the <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer">Google Cloud Console</a></li>
          <li style={{ marginBottom: '0.5rem' }}>Create a new project or select an existing one</li>
          <li style={{ marginBottom: '0.5rem' }}>Enable the YouTube Data API v3</li>
          <li style={{ marginBottom: '0.5rem' }}>Create credentials (API key and OAuth 2.0 client ID)</li>
          <li style={{ marginBottom: '0.5rem' }}>Copy your API key and paste it above</li>
          <li style={{ marginBottom: '0.5rem' }}>For full access, complete OAuth 2.0 flow to get access/refresh tokens</li>
          <li>Click "Test Connection" to verify your credentials</li>
        </ol>
      </div>
    </div>
  );
}
