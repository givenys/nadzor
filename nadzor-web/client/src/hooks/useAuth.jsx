import { useState, useEffect, useCallback } from 'react';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Проверка сессии при загрузке
  useEffect(() => {
    fetch('/api/users/me', { credentials: 'include' })
      .then(async (res) => {
        if (!res.ok) throw new Error('Not authenticated');
        const data = await res.json();
        setUser(data.user);
      })
      .catch((err) => {
        console.log('Auth check failed:', err.message);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  // Логин
  const login = useCallback(async (login, password) => {
    setError(null);
    const res = await fetch('/api/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ user: login, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Login failed');
    setUser(data.user);
    return data.user;
  }, []);

  // Регистрация
  const register = useCallback(async (login, nickname, password) => {
    setError(null);
    const res = await fetch('/api/users/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ user: login, nickname, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Registration failed');
    setUser(data.user);
    return data.user;
  }, []);

  // Выход
  const logout = useCallback(async () => {
    await fetch('/api/users/logout', {
      method: 'POST',
      credentials: 'include'
    });
    setUser(null);
  }, []);

  // Проверка, админ ли пользователь
  const isAdmin = useCallback(() => {
    return user?.role === 'admin';
  }, [user]);

  return {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAdmin
  };
}
