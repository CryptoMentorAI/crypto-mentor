type EventCallback = (data: unknown) => void;

class WSClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, EventCallback[]> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private url: string;

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log("WebSocket connected");
        // Start ping interval
        this.ping();
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const callbacks = this.listeners.get(msg.event) || [];
          callbacks.forEach((cb) => cb(msg.data));
        } catch {
          // ignore parse errors
        }
      };

      this.ws.onclose = () => {
        console.log("WebSocket disconnected, reconnecting...");
        this.reconnect();
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      this.reconnect();
    }
  }

  private reconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 3000);
  }

  private ping() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "ping" }));
      setTimeout(() => this.ping(), 30000);
    }
  }

  on(event: string, callback: EventCallback) {
    const existing = this.listeners.get(event) || [];
    existing.push(callback);
    this.listeners.set(event, existing);
  }

  off(event: string, callback: EventCallback) {
    const existing = this.listeners.get(event) || [];
    this.listeners.set(
      event,
      existing.filter((cb) => cb !== callback)
    );
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
export const wsClient = new WSClient(WS_URL);
export default wsClient;
