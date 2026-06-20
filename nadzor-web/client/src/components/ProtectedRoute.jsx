import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (loading) return; // Ждём окончания проверки сессии
    
    if (!user) {
      // Сохраняем текущий путь, чтобы вернуться после логина
      navigate('/auth', { state: { from: location.pathname }, replace: true });
    } else if (adminOnly && !isAdmin()) {
      navigate('/auth', { state: { from: location.pathname, error: 'admin_required' }, replace: true });
    }
  }, [user, loading, isAdmin, adminOnly, navigate, location]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-gray-400">
        Проверка сессии...
      </div>
    );
  }

  if (!user || (adminOnly && !isAdmin())) {
    return null; // Редирект уже сработал в useEffect
  }

  return children;
}
