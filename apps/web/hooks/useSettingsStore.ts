import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'ats' | 'modern' | 'creative' | 'portfolio';
export type Provider = 'anthropic' | 'openai' | 'gemini' | 'ollama';

interface SettingsState {
  defaultTheme: Theme;
  provider: Provider;
  setDefaultTheme: (theme: Theme) => void;
  setProvider: (provider: Provider) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      defaultTheme: 'ats',
      provider: 'anthropic',
      setDefaultTheme: (defaultTheme) => set({ defaultTheme }),
      setProvider: (provider) => set({ provider }),
    }),
    {
      name: 'cvyne-settings',
    }
  )
);
