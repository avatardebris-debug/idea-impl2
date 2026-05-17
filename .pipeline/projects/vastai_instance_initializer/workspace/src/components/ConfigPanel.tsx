import { useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

interface ConfigPanelProps {
  apiKey: string | null;
  setApiKey: (key: string | null) => void;
  refreshData: () => Promise<void>;
}

function ConfigPanel({ apiKey, setApiKey, refreshData }: ConfigPanelProps) {
  const [inputKey, setInputKey] = useState('');
  const [showKey, setShowKey] = useState(false);

  const handleSave = async () => {
    if (!inputKey.trim()) {
      alert('Please enter an API key');
      return;
    }
    try {
      await invoke('set_api_key', { apiKey: inputKey });
      setApiKey(inputKey);
      await refreshData();
      alert('API key saved successfully');
    } catch (err) {
      alert(err instanceof Error ? err.message : String(err));
    }
  };

  const handleClear = async () => {
    try {
      await invoke('set_api_key', { apiKey: '' });
      setApiKey(null);
      await refreshData();
      alert('API key cleared');
    } catch (err) {
      alert(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Configuration</h2>

      <div className="p-6 bg-slate-800 rounded-lg border border-slate-700">
        <h3 className="text-lg font-medium mb-4">VAST AI API Key</h3>
        <p className="text-slate-400 text-sm mb-4">
          Enter your VAST AI API key to manage instances. You can find your API key in your VAST AI account settings.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">API Key</label>
            <div className="flex space-x-2">
              <input
                type={showKey ? 'text' : 'password'}
                value={inputKey}
                onChange={e => setInputKey(e.target.value)}
                placeholder="Enter your VAST AI API key"
                className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="px-3 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg"
              >
                {showKey ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Save API Key
            </button>
            {apiKey && (
              <button
                onClick={handleClear}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Clear API Key
              </button>
            )}
          </div>

          {apiKey && (
            <div className="mt-4 p-3 bg-green-900/30 border border-green-700 rounded-lg">
              <p className="text-green-400 text-sm">
                ✓ API key is configured and ready to use.
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 p-6 bg-slate-800 rounded-lg border border-slate-700">
        <h3 className="text-lg font-medium mb-4">About</h3>
        <p className="text-slate-400 text-sm">
          This application helps you manage GPU instances on the VAST AI marketplace.
          Create presets with your preferred GPU types and configurations, then run them
          to automatically provision and configure instances.
        </p>
      </div>
    </div>
  );
}

export default ConfigPanel;
