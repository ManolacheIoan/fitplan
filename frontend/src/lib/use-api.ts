"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

export type QueryState<T> = {
  data: T | undefined;
  error: unknown;
  loading: boolean;
  reload: () => void;
};

type Result<T> = { key: string | null; data?: T; error?: unknown };

/**
 * Minimal GET hook (keeps the bundle small; no data-fetching library needed).
 * Previous data stays visible while reloading.
 */
export function useApi<T>(path: string | null): QueryState<T> {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<Result<T>>({ key: null });
  const key = path === null ? null : `${path}#${version}`;

  useEffect(() => {
    if (path === null || key === null) return;
    let cancelled = false;
    api<T>(path)
      .then((data) => !cancelled && setResult({ key, data }))
      .catch((error: unknown) => !cancelled && setResult((prev) => ({ key, data: prev.data, error })));
    return () => {
      cancelled = true;
    };
  }, [path, key]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  const settled = result.key === key;
  return {
    data: result.data,
    error: settled ? (result.error ?? null) : null,
    loading: key !== null && !settled,
    reload,
  };
}
