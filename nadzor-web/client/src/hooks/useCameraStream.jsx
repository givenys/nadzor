import { useEffect, useRef, useState } from 'react';

export const useCameraStream = (deviceId) => {
  const [status, setStatus] = useState('disconnected');
  const [frameUrl, setFrameUrl] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    if (!deviceId) {
      setStatus('disconnected');
      return;
    }

    isMountedRef.current = true;

    const fetchTokenAndConnect = async () => {
      try {
        const response = await fetch('/api/users/token', { credentials: 'include' });
        
        if (!response.ok) {
          console.warn('No token available for camera stream');
          setStatus('error');
          return;
        }

        const data = await response.json();
        const token = data.token;

        if (!token) {
          setStatus('error');
          return;
        }

        const wsUrl = `ws://${window.location.hostname}:3001/api/cams/viewer?device_id=${deviceId}&token=${token}`;
        connectWebSocket(wsUrl);
      } catch (err) {
        console.error('Failed to fetch token:', err);
        setStatus('error');
      }
    };

    const connectWebSocket = (wsUrl) => {
      const connect = () => {
        if (!isMountedRef.current) return;
        if (wsRef.current?.readyState === WebSocket.OPEN || 
            wsRef.current?.readyState === WebSocket.CONNECTING) return;

        setStatus('connecting');
        const ws = new WebSocket(wsUrl);
        ws.binaryType = 'arraybuffer';

        ws.onopen = () => {
          if (!isMountedRef.current) {
            ws.close();
            return;
          }
          setStatus('connected');
        };

        ws.onmessage = (event) => {
          if (!isMountedRef.current) return;
          const blob = new Blob([event.data], { type: 'image/jpeg' });
          const newUrl = URL.createObjectURL(blob);
          
          setFrameUrl(prevUrl => {
            if (prevUrl) URL.revokeObjectURL(prevUrl);
            return newUrl;
          });
        };

        ws.onclose = () => {
          if (!isMountedRef.current) return;
          setStatus('disconnected');
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          setStatus('error');
        };

        wsRef.current = ws;
      };

      connect();
    };

    fetchTokenAndConnect();

    return () => {
      isMountedRef.current = false;
      clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setFrameUrl(url => {
        if (url) URL.revokeObjectURL(url);
        return null;
      });
    };
  }, [deviceId]);

  return { status, frameUrl };
};