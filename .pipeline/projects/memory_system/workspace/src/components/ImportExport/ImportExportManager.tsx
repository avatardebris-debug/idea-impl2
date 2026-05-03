import React, { useCallback, useState } from 'react';
import { MemoryPalaceItemUnion, Relationship, Palace, Room } from '../../types/memoryPalace';

interface ImportExportManagerProps {
  items: MemoryPalaceItemUnion[];
  relationships: Relationship[];
  palace?: Palace;
  onImport?: (data: any) => void;
  onExport?: () => void;
}

export const ImportExportManager: React.FC<ImportExportManagerProps> = ({
  items,
  relationships,
  palace,
  onImport,
  onExport,
}) => {
  const [importMode, setImportMode] = useState<'json' | 'csv' | 'text'>('json');
  const [importText, setImportText] = useState('');
  const [exportData, setExportData] = useState<string>('');
  const [isImporting, setIsImporting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [importStatus, setImportStatus] = useState<{ success: boolean; message: string } | null>(null);

  const handleImport = useCallback(() => {
    if (!importText.trim()) {
      setImportStatus({ success: false, message: 'Please enter data to import' });
      return;
    }

    setIsImporting(true);
    setImportStatus(null);

    try {
      const parsedData = JSON.parse(importText);
      
      if (onImport) {
        onImport(parsedData);
        setImportStatus({ success: true, message: 'Import successful!' });
        setImportText('');
      }
    } catch (error) {
      setImportStatus({ success: false, message: 'Invalid JSON format. Please check your input.' });
    } finally {
      setIsImporting(false);
    }
  }, [importText, onImport]);

  const handleExport = useCallback(() => {
    setIsExporting(true);
    
    const exportPayload = {
      version: '1.0',
      timestamp: new Date().toISOString(),
      items,
      relationships,
      palace,
    };

    const exported = JSON.stringify(exportPayload, null, 2);
    setExportData(exported);
    setIsExporting(false);
  }, [items, relationships, palace]);

  const handleCopyToClipboard = useCallback(() => {
    navigator.clipboard.writeText(exportData);
    setImportStatus({ success: true, message: 'Copied to clipboard!' });
  }, [exportData]);

  const handleDownload = useCallback(() => {
    const blob = new Blob([exportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `memory-palace-export-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setImportStatus({ success: true, message: 'Download started!' });
  }, [exportData]);

  const getImportTemplate = useCallback(() => {
    return JSON.stringify({
      version: '1.0',
      items: [
        {
          id: 'item-1',
          type: 'word',
          metadata: {
            title: 'Example Word',
            content: 'This is an example word item',
            location: {
              address: '123 Main St',
              city: 'Springfield',
              latitude: 39.7817,
              longitude: -89.6501,
            },
          },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ],
      relationships: [
        {
          id: 'rel-1',
          type: 'spatial',
          metadata: {
            title: 'Connection',
            description: 'Spatial relationship between items',
          },
          sourceItemId: 'item-1',
          targetItemId: 'item-2',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ],
      palace: {
        id: 'palace-1',
        name: 'My Memory Palace',
        description: 'A sample memory palace',
        rooms: [
          {
            id: 'room-1',
            name: 'Living Room',
            description: 'The main living area',
            items: ['item-1'],
            position: { x: 0, y: 0 },
          },
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    }, null, 2);
  }, []);

  return (
    <div className="import-export-manager">
      <div className="import-export-tabs">
        <button
          className={`tab ${importMode === 'json' ? 'active' : ''}`}
          onClick={() => setImportMode('json')}
        >
          JSON
        </button>
        <button
          className={`tab ${importMode === 'csv' ? 'active' : ''}`}
          onClick={() => setImportMode('csv')}
        >
          CSV
        </button>
        <button
          className={`tab ${importMode === 'text' ? 'active' : ''}`}
          onClick={() => setImportMode('text')}
        >
          Text
        </button>
      </div>

      <div className="import-export-content">
        <div className="import-section">
          <h3>📥 Import Data</h3>
          <textarea
            className="import-textarea"
            placeholder={`Paste ${importMode.toUpperCase()} data here...`}
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            rows={8}
          />
          <div className="import-actions">
            <button
              className="btn btn-secondary"
              onClick={() => setImportText(getImportTemplate())}
              disabled={isImporting}
            >
              Load Template
            </button>
            <button
              className="btn btn-primary"
              onClick={handleImport}
              disabled={isImporting}
            >
              {isImporting ? 'Importing...' : 'Import'}
            </button>
          </div>
          {importStatus && (
            <div className={`import-status ${importStatus.success ? 'success' : 'error'}`}>
              {importStatus.message}
            </div>
          )}
        </div>

        <div className="export-section">
          <h3>📤 Export Data</h3>
          <button
            className="btn btn-primary"
            onClick={handleExport}
            disabled={isExporting}
          >
            {isExporting ? 'Exporting...' : 'Generate Export'}
          </button>
          
          {exportData && (
            <div className="export-content">
              <pre className="export-json">{exportData}</pre>
              <div className="export-actions">
                <button
                  className="btn btn-secondary"
                  onClick={handleCopyToClipboard}
                >
                  📋 Copy to Clipboard
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={handleDownload}
                >
                  💾 Download File
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImportExportManager;
