import { useEffect, useRef, useState } from 'react';

export const useCameraStream = (deviceId) => {
    const [status, setStatus] = useState('disconnected');
    const [frameUrl, setFrameUrl] = useState(null);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    useEffect(() => {
        if (!deviceId) {
            setStatus('disconnected');
            return;
        }

        const wsUrl = `ws://${window.location.hostname}:3001/api/cams/viewer?device_id=${deviceId}`;

        const connect = () => {
            if (wsRef.current?.readyState === WebSocket.OPEN) return;

            setStatus('connecting');
            const ws = new WebSocket(wsUrl);
            ws.binaryType = 'arraybuffer';

            ws.onopen = () => setStatus('connected');

            ws.onmessage = (event) => {
                const blob = new Blob([event.data], { type: 'image/jpeg' });
                const newUrl = URL.createObjectURL(blob);
                
                setFrameUrl(prevUrl => {
                    if (prevUrl) URL.revokeObjectURL(prevUrl);
                    return newUrl;
                });
            };

            ws.onclose = () => {
                setStatus('disconnected');
                reconnectTimeoutRef.current = setTimeout(connect, 3000);
            };

            ws.onerror = () => {
                setStatus('error');
                ws.close();
            };

            wsRef.current = ws;
        };

        connect();

        return () => {
            clearTimeout(reconnectTimeoutRef.current);
            if (wsRef.current) wsRef.current.close();
            setFrameUrl(url => {
                if (url) URL.revokeObjectURL(url);
                return null;
            });
        };
    }, [deviceId]);

    return { status, frameUrl };
};