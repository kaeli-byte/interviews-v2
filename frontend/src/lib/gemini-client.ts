/**
 * GeminiClient: Handles WebSocket communication
 */

interface GeminiClientConfig {
  onOpen?: () => void;
  onMessage?: (event: MessageEvent) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  wsUrl?: string;
}

export class GeminiClient {
  websocket: WebSocket | null = null;
  private onOpen?: () => void;
  private onMessage?: (event: MessageEvent) => void;
  private onClose?: (event: CloseEvent) => void;
  private onError?: (event: Event) => void;
  private wsUrl: string;

  constructor(config: GeminiClientConfig) {
    this.onOpen = config.onOpen;
    this.onMessage = config.onMessage;
    this.onClose = config.onClose;
    this.onError = config.onError;
    // Default to same host, or use custom wsUrl if provided
    this.wsUrl = config.wsUrl || `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws`;
  }

  connect() {
    this.websocket = new WebSocket(this.wsUrl);
    this.websocket.binaryType = "arraybuffer";

    this.websocket.onopen = () => {
      if (this.onOpen) this.onOpen();
    };

    this.websocket.onmessage = (event: MessageEvent) => {
      if (this.onMessage) this.onMessage(event);
    };

    this.websocket.onclose = (event: CloseEvent) => {
      if (this.onClose) this.onClose(event);
    };

    this.websocket.onerror = (event: Event) => {
      if (this.onError) this.onError(event);
    };
  }

  send(data: string | ArrayBuffer) {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(data);
    }
  }

  sendText(text: string) {
    this.send(JSON.stringify({ type: "text", content: text }));
  }

  sendImage(base64Data: string, mimeType = "image/jpeg") {
    this.send(
      JSON.stringify({
        type: "image",
        mime_type: mimeType,
        data: base64Data,
      })
    );
  }

  disconnect() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  isConnected() {
    return this.websocket && this.websocket.readyState === WebSocket.OPEN;
  }
}