import { useState, useEffect, useCallback } from "react";
import { fetchUsers } from "../api/users";
import type { User } from "../types/user";

const STORAGE_KEY = "currentUserId";

export function useCurrentUser() {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchUsers();
      setUsers(response.users);

      // Restore previously selected user from localStorage
      const savedUserId = localStorage.getItem(STORAGE_KEY);
      if (savedUserId) {
        const savedUser = response.users.find(
          (u) => u.id === parseInt(savedUserId, 10)
        );
        if (savedUser) {
          setCurrentUser(savedUser);
        } else if (response.users.length > 0) {
          // Saved user not found, default to first user
          setCurrentUser(response.users[0]);
          localStorage.setItem(STORAGE_KEY, String(response.users[0].id));
        }
      } else if (response.users.length > 0) {
        // No saved user, default to first user
        setCurrentUser(response.users[0]);
        localStorage.setItem(STORAGE_KEY, String(response.users[0].id));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const selectUser = useCallback(
    (userId: number) => {
      const user = users.find((u) => u.id === userId);
      if (user) {
        setCurrentUser(user);
        localStorage.setItem(STORAGE_KEY, String(userId));
      }
    },
    [users]
  );

  return { currentUser, users, loading, error, selectUser };
}
