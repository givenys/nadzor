import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function Auth() {
  const { user, login, register, logout, loading, error: authError } = useAuth();
  const [formLogin, setFormLogin] = useState('');
  const [formNickname, setFormNickname] = useState('');
  const [formPassword, setFormPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [localError, setLocalError] = useState('');
  
  const navigate = useNavigate();
  const location = useLocation();

  // Если пользователь уже авторизован — показываем приветствие
  if (user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="bg-gray-800 p-8 rounded-lg text-center max-w-md w-full">
          <h1 className="text-2xl font-bold text-green-400 mb-4">
            ✅ Привет, {user.nickname}!
          </h1>
          <p className="text-gray-400 mb-6">
            Вы уже авторизованы{user.privilege === 1 ? ' как администратор' : ''}.
          </p>
          
          <div className="space-y-3">
            <button
              onClick={() => {
                const { from } = location.state || { from: '/nadzor' };
                navigate(from, { replace: true });
              }}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded font-semibold transition"
            >
              📷 Перейти к камере
            </button>
            
            <button
              onClick={async () => {
                await logout();
                setFormLogin('');
                setFormPassword('');
              }}
              className="w-full py-3 bg-red-600 hover:bg-red-700 rounded font-semibold transition"
            >
              🚪 Выйти из аккаунта
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Форма входа / регистрации
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    
    try {
      if (isRegister) {
        if (!formNickname) throw new Error('Никнейм обязателен');
        await register(formLogin, formNickname, formPassword);
      } else {
        await login(formLogin, formPassword);
      }
      // Редирект туда, откуда пользователя перекинуло на логин
      const { from } = location.state || { from: '/nadzor' };
      navigate(from, { replace: true });
    } catch (err) {
      setLocalError(err.message || 'Ошибка авторизации');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        Загрузка...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <form onSubmit={handleSubmit} className="bg-gray-800 p-6 rounded-lg w-full max-w-md space-y-4">
        <h2 className="text-xl font-bold text-center">
          {isRegister ? '📝 Регистрация' : '🔐 Вход'}
        </h2>
        
        {(localError || authError) && (
          <p className="text-red-400 text-sm text-center bg-red-900/30 p-2 rounded">
            {localError || authError}
          </p>
        )}
        
        <input
          type="text"
          placeholder="Логин"
          value={formLogin}
          onChange={(e) => setFormLogin(e.target.value)}
          className="w-full p-3 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 outline-none"
          required
          disabled={loading}
        />
        
        {isRegister && (
          <input
            type="text"
            placeholder="Никнейм (отображаемое имя)"
            value={formNickname}
            onChange={(e) => setFormNickname(e.target.value)}
            className="w-full p-3 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 outline-none"
            required
            disabled={loading}
          />
        )}
        
        <input
          type="password"
          placeholder="Пароль"
          value={formPassword}
          onChange={(e) => setFormPassword(e.target.value)}
          className="w-full p-3 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 outline-none"
          required
          disabled={loading}
        />
        
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded font-semibold transition disabled:opacity-50"
        >
          {loading ? 'Обработка...' : (isRegister ? 'Зарегистрироваться' : 'Войти')}
        </button>
        
        <p className="text-center text-sm text-gray-400">
          {isRegister ? 'Уже есть аккаунт?' : 'Нет аккаунта?'}{' '}
          <button
            type="button"
            onClick={() => { 
              setIsRegister(!isRegister); 
              setLocalError(''); 
              setFormNickname('');
            }}
            className="text-blue-400 hover:underline"
            disabled={loading}
          >
            {isRegister ? 'Войти' : 'Зарегистрироваться'}
          </button>
        </p>
      </form>
    </div>
  );
}
