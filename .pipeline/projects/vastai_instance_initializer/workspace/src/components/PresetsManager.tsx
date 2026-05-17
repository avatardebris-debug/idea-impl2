import { useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

interface PresetsManagerProps {
  presets: any[];
  setPresets: (presets: any[]) => void;
  refreshData: () => Promise<void>;
}

function PresetsManager({ presets, setPresets, refreshData }: PresetsManagerProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingPreset, setEditingPreset] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    gpu_type: 'A100',
    max_price: 1.0,
    instance_count: 1,
    inter_instance_delay_seconds: 5,
    commands: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingPreset) {
        const result = await invoke('update_preset', {
          request: {
            id: editingPreset.id,
            ...formData,
          },
        });
        setPresets(presets.map(p => p.id === editingPreset.id ? result.data : p));
      } else {
        const result = await invoke('create_preset', {
          request: formData,
        });
        setPresets([...presets, result.data]);
      }
      setShowForm(false);
      setEditingPreset(null);
      setFormData({
        name: '',
        description: '',
        gpu_type: 'A100',
        max_price: 1.0,
        instance_count: 1,
        inter_instance_delay_seconds: 5,
        commands: '',
      });
    } catch (err) {
      alert(err instanceof Error ? err.message : String(err));
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this preset?')) return;
    try {
      await invoke('delete_preset', { id });
      setPresets(presets.filter(p => p.id !== id));
    } catch (err) {
      alert(err instanceof Error ? err.message : String(err));
    }
  };

  const handleEdit = (preset: any) => {
    setEditingPreset(preset);
    setFormData({
      name: preset.name,
      description: preset.description,
      gpu_type: preset.config.gpu_type,
      max_price: preset.config.max_price,
      instance_count: preset.config.instance_count,
      inter_instance_delay_seconds: preset.config.inter_instance_delay_seconds,
      commands: preset.config.commands,
    });
    setShowForm(true);
  };

  const handleRun = async (preset: any) => {
    try {
      const result = await invoke('run_preset', {
        request: { preset_id: preset.id },
      });
      alert(`Execution started: ${result.data.id}`);
      await refreshData();
    } catch (err) {
      alert(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Presets</h2>
        <button
          onClick={() => {
            setEditingPreset(null);
            setFormData({
              name: '',
              description: '',
              gpu_type: 'A100',
              max_price: 1.0,
              instance_count: 1,
              inter_instance_delay_seconds: 5,
              commands: '',
            });
            setShowForm(true);
          }}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          Create Preset
        </button>
      </div>

      {showForm && (
        <div className="mb-6 p-6 bg-slate-800 rounded-lg border border-slate-700">
          <h3 className="text-lg font-medium mb-4">
            {editingPreset ? 'Edit Preset' : 'Create Preset'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={e => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">GPU Type</label>
                <input
                  type="text"
                  value={formData.gpu_type}
                  onChange={e => setFormData({ ...formData, gpu_type: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Max Price ($/hr)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.max_price}
                  onChange={e => setFormData({ ...formData, max_price: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Instance Count</label>
                <input
                  type="number"
                  value={formData.instance_count}
                  onChange={e => setFormData({ ...formData, instance_count: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Delay Between Instances (sec)</label>
                <input
                  type="number"
                  value={formData.inter_instance_delay_seconds}
                  onChange={e => setFormData({ ...formData, inter_instance_delay_seconds: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Commands (one per line)</label>
              <textarea
                value={formData.commands}
                onChange={e => setFormData({ ...formData, commands: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={4}
                placeholder="pip install torch&#10;python train.py"
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                {editingPreset ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-4">
        {presets.map(preset => (
          <div key={preset.id} className="p-6 bg-slate-800 rounded-lg border border-slate-700">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-medium text-blue-400">{preset.name}</h3>
                <p className="text-slate-400 text-sm mt-1">{preset.description}</p>
                <div className="mt-3 flex flex-wrap gap-2 text-sm">
                  <span className="px-2 py-1 bg-slate-700 rounded">GPU: {preset.config.gpu_type}</span>
                  <span className="px-2 py-1 bg-slate-700 rounded">Max: ${preset.config.max_price}/hr</span>
                  <span className="px-2 py-1 bg-slate-700 rounded">Count: {preset.config.instance_count}</span>
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleEdit(preset)}
                  className="px-3 py-1 bg-slate-600 hover:bg-slate-500 rounded text-sm"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(preset.id)}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                >
                  Delete
                </button>
                <button
                  onClick={() => handleRun(preset)}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm"
                >
                  Run
                </button>
              </div>
            </div>
          </div>
        ))}
        {presets.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            No presets yet. Create one to get started!
          </div>
        )}
      </div>
    </div>
  );
}

export default PresetsManager;
