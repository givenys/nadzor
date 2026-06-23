import { useEffect, useRef, useState } from 'react';

export const useIncidents = () => {
  const [incidents, setIncidents] = useState([]);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

    const fetchTokenAndConnect = async () => {
      try {
        const response = await fetch('/api/users/token', { credentials: 'include' });
        
        if (!response.ok) {
          console.warn('No token available, incidents WebSocket will not connect');
          return;
        }

        const data = await response.json();
        const token = data.token;

        if (!token) {
          console.warn('No token in response');
          return;
        }

        const wsUrl = `ws://${window.location.hostname}:3001/api/cams/incidents/ws?token=${token}`;
        connectWebSocket(wsUrl);
      } catch (err) {
        console.error('Failed to fetch token:', err);
      }
    };

    const connectWebSocket = (wsUrl) => {
      const connect = () => {
        if (!isMountedRef.current) return;
        if (wsRef.current?.readyState === WebSocket.OPEN || 
            wsRef.current?.readyState === WebSocket.CONNECTING) return;

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (!isMountedRef.current) {
            ws.close();
            return;
          }
          console.log('Incidents WebSocket connected');
          
          fetch('/api/cams/incidents', { credentials: 'include' })
            .then(res => {
              if (!res.ok) throw new Error(`HTTP ${res.status}`);
              return res.json();
            })
            .then(data => {
              if (isMountedRef.current) {
                setIncidents(data);
              }
            })
            .catch(err => console.error('Failed to load incidents:', err));
        };

        ws.onmessage = (event) => {
          if (!isMountedRef.current) return;
          try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'new_incident') {
              setIncidents(prev => [message.incident, ...prev]);
            } 
            else if (message.type === 'incident_resolved') {
              setIncidents(prev => prev.filter(inc => inc.id !== message.incident_id));
            }
          } catch (err) {
            console.error('Failed to parse incident message:', err);
          }
        };

        ws.onclose = () => {
          if (!isMountedRef.current) return;
          console.log('Incidents WebSocket disconnected');
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        };

        ws.onerror = (err) => {
          console.error('Incidents WebSocket error');
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
    };
  }, []);

  const respondToIncident = async (incidentId, action) => {
    try {
      const response = await fetch(`/api/cams/incidents/${incidentId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ action })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      setIncidents(prev => prev.filter(inc => inc.id !== incidentId));
      
      return true;
    } catch (err) {
      console.error('Respond error:', err);
      return false;
    }
  };

  return { incidents, respondToIncident };
};