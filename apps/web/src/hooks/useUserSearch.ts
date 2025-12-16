import { useState, useCallback } from "react";
import { searchUsers } from "../api/users";
import type { User } from "../types/user";

export function useUserSearch() {
  const [results, setResults] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const search = useCallback(async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const users = await searchUsers(query);
      setResults(users);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setResults([]);
    setError(null);
  }, []);

  return { results, loading, error, search, clear };
}
