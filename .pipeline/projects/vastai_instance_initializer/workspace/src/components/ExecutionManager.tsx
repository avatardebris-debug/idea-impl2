import { useState } from 'react';

interface ExecutionManagerProps {
  executions: any[];
  setExecutions: (executions: any[]) => void;
  refreshData: () => Promise<void>;
}

function ExecutionManager({ executions, setExecutions, refreshData }: ExecutionManagerProps) {
  const [selectedExecution, setSelectedExecution] = useState<any>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-600';
      case 'running': return 'bg-blue-600';
      case 'failed': return 'bg-red-600';
      case 'partial': return 'bg-yellow-600';
      default: return 'bg-slate-600';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Completed';
      case 'running': return 'Running';
      case 'failed': return 'Failed';
      case 'partial': return 'Partial';
      default: return status;
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Execution History</h2>

      <div className="space-y-4">
        {executions.map(execution => (
          <div
            key={execution.id}
            className="p-6 bg-slate-800 rounded-lg border border-slate-700 cursor-pointer hover:border-slate-600 transition-colors"
            onClick={() => setSelectedExecution(selectedExecution?.id === execution.id ? null : execution)}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-medium text-blue-400">{execution.preset_name}</h3>
                <p className="text-slate-400 text-sm mt-1">
                  Started: {new Date(execution.started_at).toLocaleString()}
                </p>
                {execution.completed_at && (
                  <p className="text-slate-400 text-sm">
                    Completed: {new Date(execution.completed_at).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="flex items-center space-x-3">
                <span className={`px-3 py-1 rounded-full text-sm text-white ${getStatusColor(execution.status)}`}>
                  {getStatusText(execution.status)}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    refreshData();
                  }}
                  className="px-3 py-1 bg-slate-600 hover:bg-slate-500 rounded text-sm"
                >
                  Refresh
                </button>
              </div>
            </div>

            {selectedExecution?.id === execution.id && (
              <div className="mt-4 pt-4 border-t border-slate-700">
                <p className="text-sm text-slate-300">
                  <strong>Execution ID:</strong> {execution.id}
                </p>
                <p className="text-sm text-slate-300">
                  <strong>Preset ID:</strong> {execution.preset_id}
                </p>
                {execution.error_message && (
                  <p className="text-sm text-red-400 mt-2">
                    <strong>Error:</strong> {execution.error_message}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}
        {executions.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            No executions yet. Run a preset to see history here.
          </div>
        )}
      </div>
    </div>
  );
}

export default ExecutionManager;
