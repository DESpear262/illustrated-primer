/**
 * LocalStorage hook for AI Tutor application.
 * 
 * Provides typed localStorage access with JSON serialization.
 */

import { useState, useEffect, useCallback } from 'react';

/**
 * LocalStorage hook.
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      try {
        setStoredValue((prevValue) => {
          const valueToStore = value instanceof Function ? value(prevValue) : value;
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
          return valueToStore;
        });
      } catch (error) {
        console.error(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key]
  );

  return [storedValue, setValue] as const;
}

/**
 * Get item from localStorage.
 */
export function getLocalStorageItem<T>(key: string, defaultValue: T): T {
  try {
    const item = window.localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error(`Error reading localStorage key "${key}":`, error);
    return defaultValue;
  }
}

/**
 * Set item in localStorage.
 */
export function setLocalStorageItem<T>(key: string, value: T): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error setting localStorage key "${key}":`, error);
  }
}

/**
 * Remove item from localStorage.
 */
export function removeLocalStorageItem(key: string): void {
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing localStorage key "${key}":`, error);
  }
}

