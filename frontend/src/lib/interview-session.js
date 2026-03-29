// ============================================================================
// Interview Session Management
// ============================================================================

class InterviewSession {
  constructor() {
    this.sessionId = null;
    this.contextId = null;
    this.state = null;
    this.transcript = [];
    this.websocket = null;
    this.onStateChange = null;
    this.onTranscriptUpdate = null;
    this.onSessionEnd = null;
  }

  // Get auth token for API requests
  getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    if (token) {
      return { 'Authorization': `Bearer ${token}` };
    }
    return {};
  }

  /**
   * Start a new interview session
   * @param {string} contextId - The interview context ID
   * @returns {Promise<{sessionId: string, state: string}>}
   */
  async startSession(contextId) {
    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify({ context_id: contextId })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create session');
      }

      const data = await response.json();
      this.sessionId = data.session_id;
      this.contextId = contextId;
      this.state = data.state;

      return { sessionId: this.sessionId, state: this.state, context: data.context };
    } catch (error) {
      console.error('Start session error:', error);
      throw error;
    }
  }

  /**
   * Connect WebSocket to the session
   * @param {Object} callbacks - WebSocket callbacks
   */
  connectWebSocket(callbacks) {
    const wsUrl = `ws://localhost:8000/ws?session_id=${this.sessionId}`;
    this.websocket = new WebSocket(wsUrl);

    this.websocket.onopen = () => {
      console.log('Interview session WebSocket connected');
      if (callbacks.onOpen) callbacks.onOpen();
    };

    this.websocket.onmessage = (event) => {
      this.handleWebSocketMessage(event, callbacks);
    };

    this.websocket.onclose = (event) => {
      console.log('Interview session WebSocket closed:', event.code, event.reason);
      if (callbacks.onClose) callbacks.onClose(event);
    };

    this.websocket.onerror = (event) => {
      console.error('Interview session WebSocket error:', event);
      if (callbacks.onError) callbacks.onError(event);
    };
  }

  /**
   * Handle WebSocket messages
   * @param {MessageEvent} event
   * @param {Object} callbacks
   */
  handleWebSocketMessage(event, callbacks) {
    if (typeof event.data === 'string') {
      try {
        const msg = JSON.parse(event.data);

        // Handle session control events
        if (msg.type === 'session_paused') {
          this.state = 'paused';
          if (this.onStateChange) this.onStateChange('paused');
          if (callbacks.onMessage) callbacks.onMessage(msg);
        } else if (msg.type === 'session_resumed') {
          this.state = 'active';
          if (this.onStateChange) this.onStateChange('active');
          if (callbacks.onMessage) callbacks.onMessage(msg);
        } else if (msg.type === 'session_ended') {
          this.state = 'ended';
          this.transcript = msg.transcript || [];
          if (this.onStateChange) this.onStateChange('ended');
          if (this.onSessionEnd) this.onSessionEnd(this.transcript);
          if (callbacks.onMessage) callbacks.onMessage(msg);
        } else {
          // Forward regular transcription events
          if (callbacks.onMessage) callbacks.onMessage(msg);
        }
      } catch (e) {
        console.error('Parse error:', e);
      }
    } else if (event.data instanceof Blob) {
      // Audio data - forward to audio callback
      if (callbacks.onAudio) callbacks.onAudio(event.data);
    }
  }

  /**
   * Pause the interview session
   * @returns {Promise<{state: string, previous_state: string}>}
   */
  async pauseSession() {
    return this.sendSessionControl('pause');
  }

  /**
   * Resume the interview session
   * @returns {Promise<{state: string, previous_state: string}>}
   */
  async resumeSession() {
    return this.sendSessionControl('resume');
  }

  /**
   * End the interview session
   * @returns {Promise<{success: boolean}>}
   */
  async endSession() {
    return this.sendSessionControl('end');
  }

  /**
   * Send session control command via WebSocket
   * @param {string} action - 'pause', 'resume', or 'end'
   */
  async sendSessionControl(action) {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const handler = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === `session_${action}ed` || msg.type === 'session_ended') {
            this.websocket.removeEventListener('message', handler);
            resolve(msg);
          }
        } catch (e) {
          reject(e);
        }
      };

      this.websocket.addEventListener('message', handler);
      this.websocket.send(JSON.stringify({ type: 'session_control', action }));

      // Timeout after 5 seconds
      setTimeout(() => {
        this.websocket.removeEventListener('message', handler);
        reject(new Error('Session control timeout'));
      }, 5000);
    });
  }

  /**
   * Send a text message
   * @param {string} text
   */
  sendText(text) {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(text);
    }
  }

  /**
   * Send audio data
   * @param {ArrayBuffer} data
   */
  sendAudio(data) {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(data);
    }
  }

  /**
   * Disconnect the session (without ending it)
   */
  disconnect() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  /**
   * Get current session state
   */
  getState() {
    return this.state;
  }

  /**
   * Get session transcript
   */
  getTranscript() {
    return this.transcript;
  }
}

// Export for use in main.js
window.InterviewSession = InterviewSession;
