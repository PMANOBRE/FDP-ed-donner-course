import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./api";

export const REFRESH_MS = 2000;

export type Loaded<T> =
  | { state: "loading" }
  | { state: "ready"; data: T }
  | { state: "missing" }
  | { state: "failed"; message: string };

function failure<T>(error: unknown): Loaded<T> {
  if (error instanceof ApiError && error.status === 404) {
    return { state: "missing" };
  }
  return { state: "failed", message: String(error) };
}

/**
 * Load data for a key with a stable loader function. With refresh, load it
 * again every two seconds until it turns out to be missing.
 */
export function useData<K, T>(
  key: K,
  load: (key: K) => Promise<T>,
  refresh = false,
): Loaded<T> & { reload: () => void } {
  const [loaded, setLoaded] = useState<Loaded<T>>({ state: "loading" });
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => {
    setVersion((current) => current + 1);
  }, []);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const tick = () => {
      load(key).then(
        (data) => {
          if (!active) return;
          setLoaded({ state: "ready", data });
          if (refresh) timer = setTimeout(tick, REFRESH_MS);
        },
        (error: unknown) => {
          if (!active) return;
          const next = failure<T>(error);
          setLoaded(next);
          if (refresh && next.state !== "missing") {
            timer = setTimeout(tick, REFRESH_MS);
          }
        },
      );
    };
    tick();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [key, load, refresh, version]);

  return { ...loaded, reload };
}
