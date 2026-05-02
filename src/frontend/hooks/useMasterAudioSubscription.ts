import { useEffect, useRef, useState, useCallback } from "react";

interface SubscriptionOptions {
  projectId: string;
  enabled: boolean;
  onUpdate: () => void;
  getWsUrl?: () => string;
}

interface SubscriptionState {
  loading: boolean;
}

export function useMasterAudioSubscription(opts: SubscriptionOptions): SubscriptionState {
  const { projectId, enabled, onUpdate, getWsUrl } = opts;
  const [loading, setLoading] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      if (data && data.type === "master_audio.updated") {
        onUpdateRef.current();
        setLoading(false);
      }
    } catch {
      // non-JSON or malformed message, ignore
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const url = getWsUrl ? getWsUrl() : `/ws/projects/${projectId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setLoading(false);
    };

    ws.onmessage = handleMessage;

    ws.onclose = () => {
      setLoading(true);
    };

    ws.onerror = () => {
      setLoading(true);
    };

    return () => {
      ws.close();
    };
  }, [projectId, enabled, getWsUrl, handleMessage]);

  return { loading };
}
