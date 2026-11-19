import { useEffect, useState } from "react";
import { ApiError } from "./api";

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

/** Load data for a key with a stable loader function. */
export function useData<K, T>(key: K, load: (key: K) => Promise<T>): Loaded<T> {
  const [loaded, setLoaded] = useState<Loaded<T>>({ state: "loading" });

  useEffect(() => {
    let active = true;
    load(key).then(
      (data) => {
        if (active) setLoaded({ state: "ready", data });
      },
      (error: unknown) => {
        if (active) setLoaded(failure(error));
      },
    );
    return () => {
      active = false;
    };
  }, [key, load]);

  return loaded;
}
