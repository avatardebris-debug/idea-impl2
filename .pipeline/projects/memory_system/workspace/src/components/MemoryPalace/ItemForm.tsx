import React, { useState, useEffect } from 'react';
import {
  MemoryPalaceItemUnion,
  MemoryPalaceItemType,
  WordItem,
  PhraseItem,
  ImageItem,
  DateItem,
  CardItem,
  NumberItem,
} from '../../types/memoryPalace';

interface ItemFormProps {
  onSubmit: (item: Omit<MemoryPalaceItemUnion, 'id'>) => void;
  onCancel: () => void;
  initialData?: MemoryPalaceItemUnion;
}

const getEmptyItem = (type: MemoryPalaceItemType): Omit<MemoryPalaceItemUnion, 'id'> => {
  const base = {
    type,
    value: '',
    metadata: {
      description: '',
      tags: [],
      location: null,
    },
  };

  switch (type) {
    case 'word':
      return {
        ...base,
        metadata: {
          ...base.metadata,
          definition: '',
          partOfSpeech: '',
          tags: [],
        },
      } as Omit<WordItem, 'id'>;
    case 'phrase':
      return {
        ...base,
        metadata: {
          ...base.metadata,
          author: '',
          source: '',
          tags: [],
        },
      } as Omit<PhraseItem, 'id'>;
    case 'image':
      return {
        ...base,
        metadata: {
          ...base.metadata,
          altText: '',
          tags: [],
        },
      } as Omit<ImageItem, 'id'>;
    case 'date':
      return {
        ...base,
        metadata: {
          ...base.metadata,
          dateLabel: '',
          isEvent: false,
          recurring: false,
          category: '',
          tags: [],
        },
      } as Omit<DateItem, 'id'>;
    case 'card':
      return {
        ...base,
        metadata: {
          ...base.metadata,
          front: '',
          back: '',
          tags: [],
        },
      } as Omit<CardItem, 'id'>;
    case 'number':
      return {
        ...base,
        metadata: {
          ...base.metadata,
          context: '',
          tags: [],
        },
      } as Omit<NumberItem, 'id'>;
    default:
      return base;
  }
};

export const ItemForm: React.FC<ItemFormProps> = ({ onSubmit, onCancel, initialData }) => {
  const [type, setType] = useState<MemoryPalaceItemType>(
    initialData?.type || 'word'
  );
  const [value, setValue] = useState(initialData?.value || '');
  const [description, setDescription] = useState(initialData?.metadata.description || '');
  const [tags, setTags] = useState<string[]>(initialData?.metadata.tags || []);
  const [tagInput, setTagInput] = useState('');

  // Type-specific fields
  const [definition, setDefinition] = useState(initialData?.metadata.definition || '');
  const [partOfSpeech, setPartOfSpeech] = useState(initialData?.metadata.partOfSpeech || '');
  const [author, setAuthor] = useState(initialData?.metadata.author || '');
  const [source, setSource] = useState(initialData?.metadata.source || '');
  const [altText, setAltText] = useState(initialData?.metadata.altText || '');
  const [dateLabel, setDateLabel] = useState(initialData?.metadata.dateLabel || '');
  const [isEvent, setIsEvent] = useState(initialData?.metadata.isEvent || false);
  const [recurring, setRecurring] = useState(initialData?.metadata.recurring || false);
  const [category, setCategory] = useState(initialData?.metadata.category || '');
  const [front, setFront] = useState(initialData?.metadata.front || '');
  const [back, setBack] = useState(initialData?.metadata.back || '');
  const [context, setContext] = useState(initialData?.metadata.context || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!value.trim()) return;

    const itemData: Omit<MemoryPalaceItemUnion, 'id'> = {
      type,
      value: value.trim(),
      metadata: {
        description: description.trim(),
        tags,
        location: null,
      },
    };

    // Add type-specific metadata
    switch (type) {
      case 'word':
        (itemData.metadata as WordItem['metadata']) = {
          ...itemData.metadata,
          definition: definition.trim(),
          partOfSpeech: partOfSpeech.trim(),
        };
        break;
      case 'phrase':
        (itemData.metadata as PhraseItem['metadata']) = {
          ...itemData.metadata,
          author: author.trim(),
          source: source.trim(),
        };
        break;
      case 'image':
        (itemData.metadata as ImageItem['metadata']) = {
          ...itemData.metadata,
          altText: altText.trim(),
        };
        break;
      case 'date':
        (itemData.metadata as DateItem['metadata']) = {
          ...itemData.metadata,
          dateLabel: dateLabel.trim(),
          isEvent,
          recurring,
          category: category.trim(),
        };
        break;
      case 'card':
        (itemData.metadata as CardItem['metadata']) = {
          ...itemData.metadata,
          front: front.trim(),
          back: back.trim(),
        };
        break;
      case 'number':
        (itemData.metadata as NumberItem['metadata']) = {
          ...itemData.metadata,
          context: context.trim(),
        };
        break;
    }

    onSubmit(itemData);
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  const renderTypeSpecificFields = () => {
    switch (type) {
      case 'word':
        return (
          <div className="item-form-field">
            <label>Definition</label>
            <input
              type="text"
              value={definition}
              onChange={(e) => setDefinition(e.target.value)}
              placeholder="Define the word"
            />
            <label>Part of Speech</label>
            <input
              type="text"
              value={partOfSpeech}
              onChange={(e) => setPartOfSpeech(e.target.value)}
              placeholder="e.g., noun, verb, adjective"
            />
          </div>
        );
      case 'phrase':
        return (
          <div className="item-form-field">
            <label>Author</label>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Author name"
            />
            <label>Source</label>
            <input
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="Source of the phrase"
            />
          </div>
        );
      case 'image':
        return (
          <div className="item-form-field">
            <label>Alt Text</label>
            <textarea
              value={altText}
              onChange={(e) => setAltText(e.target.value)}
              placeholder="Describe the image"
              rows={3}
            />
          </div>
        );
      case 'date':
        return (
          <div className="item-form-field">
            <label>Date Label</label>
            <input
              type="text"
              value={dateLabel}
              onChange={(e) => setDateLabel(e.target.value)}
              placeholder="e.g., 'July 4, 1776'"
            />
            <label>Category</label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g., historical, personal, holiday"
            />
            <div className="item-form-checkboxes">
              <label>
                <input
                  type="checkbox"
                  checked={isEvent}
                  onChange={(e) => setIsEvent(e.target.checked)}
                />
                Is Event
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={recurring}
                  onChange={(e) => setRecurring(e.target.checked)}
                />
                Recurring
              </label>
            </div>
          </div>
        );
      case 'card':
        return (
          <div className="item-form-field">
            <label>Front of Card</label>
            <textarea
              value={front}
              onChange={(e) => setFront(e.target.value)}
              placeholder="Question or term"
              rows={3}
            />
            <label>Back of Card</label>
            <textarea
              value={back}
              onChange={(e) => setBack(e.target.value)}
              placeholder="Answer or definition"
              rows={3}
            />
          </div>
        );
      case 'number':
        return (
          <div className="item-form-field">
            <label>Context</label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="What does this number represent?"
              rows={3}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <form className="item-form" onSubmit={handleSubmit}>
      <h3>{initialData ? 'Edit Item' : 'Add New Item'}</h3>

      <div className="item-form-field">
        <label>Type</label>
        <select value={type} onChange={(e) => setType(e.target.value as MemoryPalaceItemType)}>
          <option value="word">Word</option>
          <option value="phrase">Phrase</option>
          <option value="image">Image</option>
          <option value="date">Date</option>
          <option value="card">Flashcard</option>
          <option value="number">Number</option>
        </select>
      </div>

      <div className="item-form-field">
        <label>Value *</label>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={`Enter ${type} value`}
          required
        />
      </div>

      <div className="item-form-field">
        <label>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Additional description or mnemonic"
          rows={3}
        />
      </div>

      {renderTypeSpecificFields()}

      <div className="item-form-field">
        <label>Tags</label>
        <div className="tag-input">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddTag();
              }
            }}
            placeholder="Add a tag and press Enter"
          />
          <button type="button" onClick={handleAddTag}>Add</button>
        </div>
        <div className="tags-list">
          {tags.map((tag) => (
            <span key={tag} className="tag">
              {tag}
              <button
                type="button"
                onClick={() => handleRemoveTag(tag)}
                aria-label={`Remove tag ${tag}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="item-form-actions">
        <button type="submit" className="btn-primary">
          {initialData ? 'Update Item' : 'Add Item'}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
      </div>
    </form>
  );
};

export default ItemForm;
