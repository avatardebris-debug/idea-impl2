import { useState, useEffect, useCallback } from 'react';
import { AssociationSuggestion, AssociationContext, generateAssociationSuggestions } from '../utils/associationEngine';
import { Card, NumberCard } from '../types/cards';

/**
 * Hook for managing association suggestions
 */
export const useAssociationSuggestions = () => {
  const [suggestions, setSuggestions] = useState<AssociationSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);

  /**
   * Generate suggestions based on item context
   */
  const generateSuggestions = useCallback(async (context: AssociationContext) => {
    setIsLoading(true);
    setError(null);

    try {
      // Simulate async operation (in real app, could be API call or complex computation)
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const newSuggestions = generateAssociationSuggestions(context);
      setSuggestions(newSuggestions);
      setSelectedSuggestion(null);
    } catch (err) {
      setError('Failed to generate association suggestions');
      console.error('Association generation error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Generate suggestions for a card item
   */
  const suggestForCard = useCallback((card: Card) => {
    generateSuggestions({
      item: JSON.stringify(card),
      itemType: 'card',
    });
  }, [generateSuggestions]);

  /**
   * Generate suggestions for a number item
   */
  const suggestForNumber = useCallback((number: number) => {
    generateSuggestions({
      item: number.toString(),
      itemType: 'number',
    });
  }, [generateSuggestions]);

  /**
   * Generate suggestions for a text item
   */
  const suggestForText = useCallback((text: string) => {
    generateSuggestions({
      item: text,
      itemType: 'text',
    });
  }, [generateSuggestions]);

  /**
   * Apply a selected suggestion to an item
   */
  const applySuggestion = useCallback((suggestionId: string, itemText: string): string => {
    const suggestion = suggestions.find(s => s.id === suggestionId);
    if (!suggestion) {
      return itemText;
    }

    setSelectedSuggestion(suggestionId);
    // In a real implementation, this would update the item's memory association
    return itemText;
  }, [suggestions]);

  /**
   * Clear current suggestions
   */
  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setSelectedSuggestion(null);
    setError(null);
  }, []);

  /**
   * Get suggestion by ID
   */
  const getSuggestionById = useCallback((id: string): AssociationSuggestion | undefined => {
    return suggestions.find(s => s.id === id);
  }, [suggestions]);

  return {
    suggestions,
    isLoading,
    error,
    selectedSuggestion,
    generateSuggestions,
    suggestForCard,
    suggestForNumber,
    suggestForText,
    applySuggestion,
    clearSuggestions,
    getSuggestionById,
  };
};

export default useAssociationSuggestions;
