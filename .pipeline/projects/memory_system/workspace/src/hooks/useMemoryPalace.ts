import { useState, useCallback, useMemo } from 'react';
import { Palace, Room, Item } from '../types/palace';

interface UseMemoryPalaceState {
  palace: Palace;
  editingRoomId: string | null;
  searchTerm: string;
}

interface UseMemoryPalaceActions {
  updatePalaceName: (name: string) => void;
  updatePalaceDescription: (description: string) => void;
  addRoom: (room: Room) => void;
  updateRoom: (roomId: string, updates: Partial<Room>) => void;
  deleteRoom: (roomId: string) => void;
  setEditingRoomId: (roomId: string | null) => void;
  addItemToRoom: (roomId: string, item: Item) => void;
  updateItemInRoom: (roomId: string, itemId: string, updates: Partial<Item>) => void;
  deleteItemFromRoom: (roomId: string, itemId: string) => void;
  setSearchTerm: (term: string) => void;
  clearFilters: () => void;
}

export function useMemoryPalace(initialPalace: Palace) {
  const [state, setState] = useState<UseMemoryPalaceState>({
    palace: initialPalace,
    editingRoomId: null,
    searchTerm: '',
  });

  const updatePalaceName = useCallback((name: string) => {
    setState((prev) => ({
      ...prev,
      palace: { ...prev.palace, name },
    }));
  }, []);

  const updatePalaceDescription = useCallback((description: string) => {
    setState((prev) => ({
      ...prev,
      palace: { ...prev.palace, description },
    }));
  }, []);

  const addRoom = useCallback((room: Room) => {
    setState((prev) => ({
      ...prev,
      palace: {
        ...prev.palace,
        rooms: [...prev.palace.rooms, room],
      },
    }));
  }, []);

  const updateRoom = useCallback((roomId: string, updates: Partial<Room>) => {
    setState((prev) => ({
      ...prev,
      palace: {
        ...prev.palace,
        rooms: prev.palace.rooms.map((room) =>
          room.id === roomId ? { ...room, ...updates } : room
        ),
      },
    }));
  }, []);

  const deleteRoom = useCallback((roomId: string) => {
    setState((prev) => ({
      ...prev,
      palace: {
        ...prev.palace,
        rooms: prev.palace.rooms.filter((room) => room.id !== roomId),
      },
      editingRoomId: prev.editingRoomId === roomId ? null : prev.editingRoomId,
    }));
  }, []);

  const setEditingRoomId = useCallback((roomId: string | null) => {
    setState((prev) => ({
      ...prev,
      editingRoomId: roomId,
    }));
  }, []);

  const addItemToRoom = useCallback((roomId: string, item: Item) => {
    setState((prev) => ({
      ...prev,
      palace: {
        ...prev.palace,
        rooms: prev.palace.rooms.map((room) =>
          room.id === roomId
            ? { ...room, items: [...room.items, item] }
            : room
        ),
      },
    }));
  }, []);

  const updateItemInRoom = useCallback((roomId: string, itemId: string, updates: Partial<Item>) => {
    setState((prev) => ({
      ...prev,
      palace: {
        ...prev.palace,
        rooms: prev.palace.rooms.map((room) =>
          room.id === roomId
            ? {
                ...room,
                items: room.items.map((item) =>
                  item.id === itemId ? { ...item, ...updates } : item
                ),
              }
            : room
        ),
      },
    }));
  }, []);

  const deleteItemFromRoom = useCallback((roomId: string, itemId: string) => {
    setState((prev) => ({
      ...prev,
      palace: {
        ...prev.palace,
        rooms: prev.palace.rooms.map((room) =>
          room.id === roomId
            ? { ...room, items: room.items.filter((item) => item.id !== itemId) }
            : room
        ),
      },
    }));
  }, []);

  const setSearchTerm = useCallback((term: string) => {
    setState((prev) => ({
      ...prev,
      searchTerm: term,
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setState((prev) => ({
      ...prev,
      searchTerm: '',
    }));
  }, []);

  const filteredRooms = useMemo(() => {
    if (!state.searchTerm) return state.palace.rooms;
    
    const searchLower = state.searchTerm.toLowerCase();
    return state.palace.rooms.filter((room) =>
      room.name.toLowerCase().includes(searchLower) ||
      room.description.toLowerCase().includes(searchLower)
    );
  }, [state.palace.rooms, state.searchTerm]);

  const totalItems = useMemo(() => {
    return state.palace.rooms.reduce((sum, room) => sum + room.items.length, 0);
  }, [state.palace.rooms]);

  return {
    state: {
      palace: state.palace,
      editingRoomId: state.editingRoomId,
      searchTerm: state.searchTerm,
    },
    actions: {
      updatePalaceName,
      updatePalaceDescription,
      addRoom,
      updateRoom,
      deleteRoom,
      setEditingRoomId,
      addItemToRoom,
      updateItemInRoom,
      deleteItemFromRoom,
      setSearchTerm,
      clearFilters,
    },
    filteredRooms,
    totalItems,
  };
}

export default useMemoryPalace;
