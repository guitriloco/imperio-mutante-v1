const DB_NAME = "mutante-local-first";
const DB_VERSION = 1;
const STORE_NAME = "records";
const PERSIST_KEY = "persist:mutante-root";
const LOCAL_STORAGE_KEY = "mutante:state:v1";
const CACHE_PREFIX = "cache:";
const MAX_STATE_BYTES = 2 * 1024 * 1024;
const MAX_CACHE_BYTES = 8 * 1024 * 1024;
const MAX_CACHE_ENTRIES = 256;
const MAX_BACKUP_BYTES = 16 * 1024 * 1024;
const PBKDF2_ITERATIONS = 310_000;

interface DbRecord {
  id: string;
  value: string;
  bytes: number;
  lastAccessed: number;
}

export interface ZustandStateStorage {
  getItem(name: string): Promise<string | null>;
  setItem(name: string, value: string): Promise<void>;
  removeItem(name: string): Promise<void>;
}

export interface CachedValue<T = unknown> {
  value: T;
  expiresAt: number | null;
  lastAccessed: number;
  bytes: number;
}

interface EncryptedBackupV1 {
  format: "mutant-backup";
  version: 1;
  algorithm: "AES-GCM";
  kdf: "PBKDF2-SHA-256";
  iterations: number;
  salt: string;
  iv: string;
  ciphertext: string;
  createdAt: string;
}

function utf8Size(value: string): number {
  return new TextEncoder().encode(value).byteLength;
}

function toBase64(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function fromBase64(value: string): Uint8Array {
  const binary = atob(value);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function getIndexedDb(): IDBFactory | null {
  return typeof window !== "undefined" ? window.indexedDB ?? null : null;
}

function getLocalStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

let databasePromise: Promise<IDBDatabase | null> | null = null;

function openDatabase(): Promise<IDBDatabase | null> {
  const factory = getIndexedDb();
  if (!factory) return Promise.resolve(null);
  if (databasePromise) return databasePromise;

  databasePromise = new Promise((resolve) => {
    try {
      const request = factory.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const database = request.result;
        if (!database.objectStoreNames.contains(STORE_NAME)) {
          database.createObjectStore(STORE_NAME, { keyPath: "id" });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
      request.onblocked = () => resolve(null);
    } catch {
      resolve(null);
    }
  });

  return databasePromise;
}

function idbRequest<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("IndexedDB request failed"));
  });
}

async function readRecord(id: string): Promise<DbRecord | null> {
  const database = await openDatabase();
  if (!database) return null;
  try {
    const transaction = database.transaction(STORE_NAME, "readonly");
    const result = await idbRequest<DbRecord | undefined>(transaction.objectStore(STORE_NAME).get(id));
    return result ?? null;
  } catch {
    return null;
  }
}

async function writeRecord(record: DbRecord): Promise<boolean> {
  const database = await openDatabase();
  if (!database) return false;
  try {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    transaction.objectStore(STORE_NAME).put(record);
    await new Promise<void>((resolve, reject) => {
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error ?? new Error("IndexedDB write failed"));
      transaction.onabort = () => reject(transaction.error ?? new Error("IndexedDB write aborted"));
    });
    return true;
  } catch {
    return false;
  }
}

async function deleteRecord(id: string): Promise<boolean> {
  const database = await openDatabase();
  if (!database) return false;
  try {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    transaction.objectStore(STORE_NAME).delete(id);
    await new Promise<void>((resolve, reject) => {
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error ?? new Error("IndexedDB delete failed"));
      transaction.onabort = () => reject(transaction.error ?? new Error("IndexedDB delete aborted"));
    });
    return true;
  } catch {
    return false;
  }
}

function fallbackRead(key: string): string | null {
  try {
    return getLocalStorage()?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

function fallbackWrite(key: string, value: string): void {
  try {
    getLocalStorage()?.setItem(key, value);
  } catch {
    throw new Error("Local persistence is unavailable or storage quota was exceeded.");
  }
}

export const localFirstStateStorage: ZustandStateStorage = {
  async getItem(name) {
    const record = await readRecord(name === "mutante-root" ? PERSIST_KEY : `persist:${name}`);
    if (record) {
      void writeRecord({ ...record, lastAccessed: Date.now() });
      return record.value;
    }
    return fallbackRead(name === "mutante-root" ? LOCAL_STORAGE_KEY : `mutante:${name}`);
  },

  async setItem(name, value) {
    const bytes = utf8Size(value);
    if (bytes > MAX_STATE_BYTES) {
      throw new Error(`Persisted state exceeds the ${MAX_STATE_BYTES}-byte safety limit.`);
    }
    const id = name === "mutante-root" ? PERSIST_KEY : `persist:${name}`;
    const saved = await writeRecord({ id, value, bytes, lastAccessed: Date.now() });
    if (!saved) fallbackWrite(name === "mutante-root" ? LOCAL_STORAGE_KEY : `mutante:${name}`, value);
  },

  async removeItem(name) {
    const id = name === "mutante-root" ? PERSIST_KEY : `persist:${name}`;
    await deleteRecord(id);
    try {
      getLocalStorage()?.removeItem(name === "mutante-root" ? LOCAL_STORAGE_KEY : `mutante:${name}`);
    } catch {
      // Storage may be disabled by browser policy.
    }
  },
};

async function listRecords(): Promise<DbRecord[]> {
  const database = await openDatabase();
  if (!database) return [];
  try {
    const transaction = database.transaction(STORE_NAME, "readonly");
    return await idbRequest<DbRecord[]>(transaction.objectStore(STORE_NAME).getAll());
  } catch {
    return [];
  }
}

async function evictCacheIfNeeded(): Promise<void> {
  const cache = (await listRecords())
    .filter((record) => record.id.startsWith(CACHE_PREFIX))
    .sort((left, right) => left.lastAccessed - right.lastAccessed);
  let totalBytes = cache.reduce((sum, record) => sum + record.bytes, 0);
  let entries = cache.length;

  for (const record of cache) {
    if (totalBytes <= MAX_CACHE_BYTES && entries <= MAX_CACHE_ENTRIES) break;
    if (await deleteRecord(record.id)) {
      totalBytes -= record.bytes;
      entries -= 1;
    }
  }
}

export async function cacheGet<T>(key: string): Promise<T | null> {
  const id = `${CACHE_PREFIX}${key}`;
  const record = await readRecord(id);
  if (!record) return null;

  try {
    const cached = JSON.parse(record.value) as CachedValue<T>;
    if (cached.expiresAt !== null && cached.expiresAt <= Date.now()) {
      await deleteRecord(id);
      return null;
    }
    cached.lastAccessed = Date.now();
    record.value = JSON.stringify(cached);
    record.bytes = utf8Size(record.value);
    record.lastAccessed = cached.lastAccessed;
    await writeRecord(record);
    return cached.value;
  } catch {
    await deleteRecord(id);
    return null;
  }
}

export async function cacheSet<T>(key: string, value: T, ttlMs: number | null = null): Promise<void> {
  const id = `${CACHE_PREFIX}${key}`;
  const lastAccessed = Date.now();
  const cached: CachedValue<T> = {
    value,
    expiresAt: ttlMs === null ? null : lastAccessed + Math.max(0, ttlMs),
    lastAccessed,
    bytes: 0,
  };
  const serialized = JSON.stringify(cached);
  const bytes = utf8Size(serialized);
  if (bytes > MAX_CACHE_BYTES) throw new Error("Cache item exceeds the configured cache size limit.");

  const saved = await writeRecord({ id, value: serialized, bytes, lastAccessed });
  if (!saved) throw new Error("IndexedDB is required for the bounded LRU cache.");
  await evictCacheIfNeeded();
}

export async function cacheDelete(key: string): Promise<void> {
  await deleteRecord(`${CACHE_PREFIX}${key}`);
}

function deriveAesKey(passphrase: string, salt: Uint8Array): Promise<CryptoKey> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) throw new Error("Web Crypto is unavailable in this browser context.");
  return subtle.importKey("raw", new TextEncoder().encode(passphrase), "PBKDF2", false, ["deriveKey"])
    .then((material) => subtle.deriveKey(
      { name: "PBKDF2", salt: salt as BufferSource, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
      material,
      { name: "AES-GCM", length: 256 },
      false,
      ["encrypt", "decrypt"],
    ));
}

export async function createEncryptedBackup(passphrase: string): Promise<Blob> {
  if (passphrase.length < 12) throw new Error("Use a backup passphrase of at least 12 characters.");
  const rawState = await localFirstStateStorage.getItem("mutante-root");
  if (!rawState) throw new Error("No persisted application state is available to back up.");
  if (utf8Size(rawState) > MAX_BACKUP_BYTES) throw new Error("State exceeds the backup size limit.");

  const salt = globalThis.crypto.getRandomValues(new Uint8Array(16));
  const iv = globalThis.crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveAesKey(passphrase, salt);
  const encrypted = await globalThis.crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    new TextEncoder().encode(rawState),
  );
  const backup: EncryptedBackupV1 = {
    format: "mutant-backup",
    version: 1,
    algorithm: "AES-GCM",
    kdf: "PBKDF2-SHA-256",
    iterations: PBKDF2_ITERATIONS,
    salt: toBase64(salt),
    iv: toBase64(iv),
    ciphertext: toBase64(new Uint8Array(encrypted)),
    createdAt: new Date().toISOString(),
  };
  return new Blob([JSON.stringify(backup)], { type: "application/vnd.mutant-backup+json" });
}

export async function restoreEncryptedBackup(file: File, passphrase: string): Promise<void> {
  if (file.size > MAX_BACKUP_BYTES * 2) throw new Error("Backup file exceeds the accepted size limit.");
  const backup = JSON.parse(await file.text()) as Partial<EncryptedBackupV1>;
  if (
    backup.format !== "mutant-backup" || backup.version !== 1 ||
    backup.algorithm !== "AES-GCM" || backup.kdf !== "PBKDF2-SHA-256" ||
    backup.iterations !== PBKDF2_ITERATIONS || !backup.salt || !backup.iv || !backup.ciphertext
  ) {
    throw new Error("Unsupported or malformed backup file.");
  }

  const plaintext = await globalThis.crypto.subtle.decrypt(
    { name: "AES-GCM", iv: fromBase64(backup.iv) },
    await deriveAesKey(passphrase, fromBase64(backup.salt)),
    fromBase64(backup.ciphertext),
  );
  const state = new TextDecoder().decode(plaintext);
  if (utf8Size(state) > MAX_STATE_BYTES) throw new Error("Restored state exceeds the persistence size limit.");

  const parsed: unknown = JSON.parse(state);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("Backup payload is not a valid application state object.");
  }
  await localFirstStateStorage.setItem("mutante-root", state);
}

export async function downloadEncryptedBackup(passphrase: string): Promise<void> {
  const blob = await createEncryptedBackup(passphrase);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `mutante-${new Date().toISOString().replaceAll(":", "-")}.mutant-backup`;
  anchor.click();
  URL.revokeObjectURL(url);
}
