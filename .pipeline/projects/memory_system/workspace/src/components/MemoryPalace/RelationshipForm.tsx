import React, { useState } from 'react';
import { Relationship, RelationshipType } from '../../types/memoryPalace';

interface RelationshipFormProps {
  onSubmit: (relationship: Omit<Relationship, 'id'>) => void;
  onCancel: () => void;
  sourceItemId: string;
  sourceItemLabel: string;
  availableTargetItems: Array<{ id: string; label: string }>;
  initialData?: Relationship;
}

export const RelationshipForm: React.FC<RelationshipFormProps> = ({
  onSubmit,
  onCancel,
  sourceItemId,
  sourceItemLabel,
  availableTargetItems,
  initialData,
}) => {
  const [targetItemId, setTargetItemId] = useState(
    initialData?.targetItemId || ''
  );
  const [type, setType] = useState<RelationshipType>(
    initialData?.type || 'related'
  );
  const [description, setDescription] = useState(
    initialData?.description || ''
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!targetItemId) return;

    const relationshipData: Omit<Relationship, 'id'> = {
      sourceItemId,
      targetItemId,
      type,
      description: description.trim(),
    };

    onSubmit(relationshipData);
  };

  const getRelationshipTypeLabel = (t: RelationshipType): string => {
    const labels: Record<RelationshipType, string> = {
      related: 'Related',
      linked: 'Linked',
      associated: 'Associated',
    };
    return labels[t] || t;
  };

  return (
    <form className="relationship-form" onSubmit={handleSubmit}>
      <h3>{initialData ? 'Edit Relationship' : 'Add New Relationship'}</h3>

      <div className="relationship-form-field">
        <label>From (Source)</label>
        <input
          type="text"
          value={sourceItemLabel}
          disabled
          className="disabled-input"
        />
      </div>

      <div className="relationship-form-field">
        <label>To (Target) *</label>
        <select
          value={targetItemId}
          onChange={(e) => setTargetItemId(e.target.value)}
          required
        >
          <option value="">Select target item...</option>
          {availableTargetItems.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
        {targetItemId &&
          availableTargetItems.find((i) => i.id === targetItemId) && (
            <small className="form-hint">
              Selected: {
                availableTargetItems.find((i) => i.id === targetItemId)?.label
              }
            </small>
          )}
      </div>

      <div className="relationship-form-field">
        <label>Relationship Type *</label>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as RelationshipType)}
          required
        >
          <option value="related">Related</option>
          <option value="linked">Linked</option>
          <option value="associated">Associated</option>
        </select>
      </div>

      <div className="relationship-form-field">
        <label>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the relationship..."
          rows={3}
        />
      </div>

      <div className="relationship-form-actions">
        <button type="submit" className="btn-primary">
          {initialData ? 'Update Relationship' : 'Add Relationship'}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
      </div>
    </form>
  );
};

export default RelationshipForm;
