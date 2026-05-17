import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import PresetsManager from './components/PresetsManager';
import ExecutionManager from './components/ExecutionManager';
import ConfigPanel from './components/ConfigPanel';

function App() {
  const [activeTab, setActiveTab] = useState<'presets' | 'executions' | 'config'>('presets');
  const [presets, setPresets] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [presetsResult, executionsResult, apiKeyResult] = await Promise.all([
        invoke('list_presets'),
        invoke('get_execution_history'),
        invoke('get_api_key'),
      ]);

      setPresets(presetsResult.data || []);
      setExecutions(executionsResult.data || []);
      setApiKey(apiKeyResult.data || null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    await loadInitialData();
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-blue-400">VAST AI Instance Manager</h1>
          <nav className="flex space-x-4">
            <button
              onClick={() => setActiveTab('presets')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'presets'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Presets
            </button>
            <button
              onClick={() => setActiveTab('executions')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'executions'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Executions
            </button>
            <button
              onClick={() => setActiveTab('config')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'config'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Config
            </button>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
          </div>
        ) : (
          <>
            {activeTab === 'presets' && (
              <PresetsManager
                presets={presets}
                setPresets={setPresets}
                refreshData={refreshData}
              />
            )}
            {activeTab === 'executions' && (
              <ExecutionManager
                executions={executions}
                setExecutions={setExecutions}
                refreshData={refreshData}
              />
            )}
            {activeTab === 'config' && (
              <ConfigPanel
                apiKey={apiKey}
                setApiKey={setApiKey}
                refreshData={refreshData}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
