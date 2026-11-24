import { DEFAULT_PREFERENCES, type OperatorPreferences } from "../types/preferences";

export const PREFS_STORAGE_KEY = "hima_rakshak_preferences";

/** Loads saved operator preferences from localStorage with safe defaults. */
export function loadStoredPreferences(): OperatorPreferences {
  try {
    const raw = localStorage.getItem(PREFS_STORAGE_KEY);
    return raw
      ? { ...DEFAULT_PREFERENCES, ...(JSON.parse(raw) as Partial<OperatorPreferences>) }
      : DEFAULT_PREFERENCES;
  } catch {
    return DEFAULT_PREFERENCES;
  }
}
