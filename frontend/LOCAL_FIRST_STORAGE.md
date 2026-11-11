# Local-first storage

`src/lib/local-first-storage.ts` provides an async Zustand `StateStorage`-compatible adapter backed by IndexedDB, with a bounded localStorage fallback for persisted application state. It also exposes a bounded IndexedDB LRU cache and encrypted AES-GCM backup/restore utilities.

## Zustand integration

The existing frontend does not currently list Zustand as a dependency. Add it with `npm install zustand` (which updates `package-lock.json`), then configure a store with `persist` and the exported adapter:

```ts
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { localFirstStateStorage } from '@/lib/local-first-storage';

type PersistedAppState = {
  chatSessions: Array<{ id: string; title: string; messages: unknown[]; updatedAt: number }>;
  telemetry: Array<{ timestamp: number; latencyMs: number; healthy: boolean }>;
  license: { apiKey: string | null; tier: string | null };
};

type AppStore = PersistedAppState & {
  replaceState: (state: PersistedAppState) => void;
};

export const useAppStore = create<AppStore>()(persist(
  (set) => ({
    chatSessions: [],
    telemetry: [],
    license: { apiKey: null, tier: null },
    replaceState: (state) => set(state),
  }),
  {
    name: 'mutante-root',
    storage: createJSONStorage(() => localFirstStateStorage),
    partialize: ({ chatSessions, telemetry, license }) => ({ chatSessions, telemetry, license }),
    version: 1,
  },
));
```

Keep telemetry bounded in the state action (for example, retain only the latest 500 samples). License keys are stored locally for convenience; encrypted backups require a user-provided passphrase and never store that passphrase. Browser storage is not a secure vault against XSS or a compromised device.

The current storage implementation has not been run through the repository's TypeScript/build checks in this environment.
