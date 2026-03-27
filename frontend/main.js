// --- Main Application Logic ---

// ============================================================================
// Authentication Management
// ============================================================================

class Auth {
  constructor() {
    this.token = localStorage.getItem('auth_token');
    this.user = JSON.parse(localStorage.getItem('auth_user') || 'null');
    this.isAuthenticated = !!this.token && !!this.user;
  }

  getToken() {
    return this.token;
  }

  isAuthenticated() {
    return !!this.token && !!this.user;
  }

  async signup(email, password) {
    const response = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    const data = await response.json();
    this.setAuth(data.token, data.user);
    return data;
  }

  async login(email, password) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    this.setAuth(data.token, data.user);
    return data;
  }

  async logout() {
    if (this.token) {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
      } catch (e) {
        console.error('Logout API call failed:', e);
      }
    }
    this.clearAuth();
  }

  async checkAuth() {
    if (!this.token) {
      return false;
    }

    try {
      const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (!response.ok) {
        this.clearAuth();
        return false;
      }

      const data = await response.json();
      this.user = data.user;
      localStorage.setItem('auth_user', JSON.stringify(this.user));
      return true;
    } catch (e) {
      this.clearAuth();
      return false;
    }
  }

  setAuth(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem('auth_token', token);
    localStorage.setItem('auth_user', JSON.stringify(user));
    this.isAuthenticated = true;
  }

  clearAuth() {
    this.token = null;
    this.user = null;
    this.isAuthenticated = false;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  }

  // Helper for authenticated fetch requests
  async fetch(url, options = {}) {
    const headers = {
      ...(options.headers || {}),
      'Authorization': `Bearer ${this.token}`
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      this.clearAuth();
      updateAuthUI(false);
      throw new Error('Session expired. Please sign in again.');
    }

    return response;
  }
}

// Initialize auth instance
const auth = new Auth();

// ============================================================================

// DOM Elements
const statusDiv = document.getElementById("status");
const authSection = document.getElementById("auth-section");
const userMenu = document.getElementById("user-menu");
const userEmail = document.getElementById("user-email");
const logoutBtn = document.getElementById("logoutBtn");
const welcomeMessage = document.getElementById("welcome-message");
const appSection = document.getElementById("app-section");
const sessionEndSection = document.getElementById("session-end-section");
const dashboardSection = document.getElementById("dashboard-section");
const restartBtn = document.getElementById("restartBtn");

// Auth form elements
const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");
const loginEmail = document.getElementById("login-email");
const loginPassword = document.getElementById("login-password");
const signupEmail = document.getElementById("signup-email");
const signupPassword = document.getElementById("signup-password");
const loginError = document.getElementById("login-error");
const signupError = document.getElementById("signup-error");
const authTabBtns = document.querySelectorAll(".auth-tab-btn");

// Existing DOM elements
const micBtn = document.getElementById("micBtn");
const cameraBtn = document.getElementById("cameraBtn");
const screenBtn = document.getElementById("screenBtn");
const disconnectBtn = document.getElementById("disconnectBtn");
const textInput = document.getElementById("textInput");
const sendBtn = document.getElementById("sendBtn");
const videoPreview = document.getElementById("video-preview");
const videoPlaceholder = document.getElementById("video-placeholder");
const connectBtn = document.getElementById("connectBtn");
const chatLog = document.getElementById("chat-log");

// Document upload elements
const uploadBtn = document.getElementById("uploadBtn");
const uploadModal = document.getElementById("upload-modal");
const closeModalBtn = document.getElementById("closeModal");
const profileModal = document.getElementById("profile-modal");
const closeProfileModalBtn = document.getElementById("closeProfileModal");
const contextModal = document.getElementById("context-modal");
const closeContextModalBtn = document.getElementById("closeContextModal");
const createContextBtn = document.getElementById("createContextBtn");
const createContextSubmitBtn = document.getElementById("createContextSubmitBtn");

// Tab elements
const tabBtns = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");

// Interview session elements
const interviewSessionSection = document.getElementById("interview-session-section");
const sessionStatusDiv = document.getElementById("session-status");
const sessionStatusLabel = sessionStatusDiv?.querySelector(".status-text");
const startInterviewBtn = document.getElementById("startInterviewBtn");
const pauseInterviewBtn = document.getElementById("pauseInterviewBtn");
const resumeInterviewBtn = document.getElementById("resumeInterviewBtn");
const endInterviewBtn = document.getElementById("endInterviewBtn");
const transcriptLog = document.getElementById("transcript-log");
const transcriptCount = document.getElementById("transcript-count");
const sessionEndSummary = document.getElementById("session-end-summary");
const sessionSummaryText = document.getElementById("session-summary-text");
const viewTranscriptBtn = document.getElementById("viewTranscriptBtn");
const closeSessionBtn = document.getElementById("closeSessionBtn");

let currentGeminiMessageDiv = null;
let currentUserMessageDiv = null;
let currentContextId = null;

// Interview session instance
let interviewSession = null;

// ============================================================================
// Authentication UI Functions
// ============================================================================

function updateAuthUI(isAuthenticated) {
  if (isAuthenticated) {
    // Show dashboard, hide auth section
    authSection.classList.add("hidden");
    dashboardSection.classList.remove("hidden");
    userMenu.style.display = "flex";

    // Update welcome message
    if (auth.user && auth.user.email) {
      welcomeMessage.textContent = `Welcome, ${auth.user.email}`;
      userEmail.textContent = auth.user.email;
    }

    // Initialize document uploader
    if (typeof documentUploader !== 'undefined') {
      documentUploader.init();
      documentUploader.fetchContexts();
    }
  } else {
    // Show auth section, hide dashboard
    authSection.classList.remove("hidden");
    dashboardSection.classList.add("hidden");
    userMenu.style.display = "none";
    appSection.classList.add("hidden");
  }
}

function showAuthError(formType, message) {
  const errorEl = formType === 'login' ? loginError : signupError;
  errorEl.textContent = message;
  errorEl.classList.remove("hidden");

  // Clear error after 5 seconds
  setTimeout(() => {
    errorEl.classList.add("hidden");
  }, 5000);
}

function switchAuthTab(tab) {
  authTabBtns.forEach(btn => {
    btn.classList.toggle("active", btn.dataset.authTab === tab);
  });

  loginForm.classList.toggle("hidden", tab !== "login");
  signupForm.classList.toggle("hidden", tab !== "signup");

  // Clear errors
  loginError.classList.add("hidden");
  signupError.classList.add("hidden");
}

// Auth tab switching
authTabBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    switchAuthTab(btn.dataset.authTab);
  });
});

// Login form handler
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = loginEmail.value.trim();
  const password = loginPassword.value;

  try {
    await auth.login(email, password);
    updateAuthUI(true);
    loginForm.reset();
  } catch (error) {
    showAuthError("login", error.message);
  }
});

// Signup form handler
signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = signupEmail.value.trim();
  const password = signupPassword.value;

  try {
    await auth.signup(email, password);
    updateAuthUI(true);
    signupForm.reset();
  } catch (error) {
    showAuthError("signup", error.message);
  }
});

// Logout button handler
if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    await auth.logout();
    updateAuthUI(false);
  });
}

// ============================================================================
// Media and Gemini Client Setup
// ============================================================================

const mediaHandler = new MediaHandler();
const geminiClient = new GeminiClient({
  onOpen: () => {
    statusDiv.textContent = "Connected";
    statusDiv.className = "status connected";
    dashboardSection.classList.add("hidden");
    appSection.classList.remove("hidden");

    // Send context-aware introduction if interview context is active
    const introMessage = currentContextId
      ? `System: You are conducting a job interview. The candidate's profile and job description have been loaded. Begin the interview with a friendly greeting and ask your first question.`
      : `System: Introduce yourself as a demo of the Gemini Live API. Suggest playing with features like the native audio for accents and multilingual support. Keep the intro concise and friendly.`;

    geminiClient.sendText(introMessage);
  },
  onMessage: (event) => {
    if (typeof event.data === "string") {
      try {
        const msg = JSON.parse(event.data);
        handleJsonMessage(msg);
      } catch (e) {
        console.error("Parse error:", e);
      }
    } else {
      mediaHandler.playAudio(event.data);
    }
  },
  onClose: (e) => {
    console.log("WS Closed:", e);
    statusDiv.textContent = "Disconnected";
    statusDiv.className = "status disconnected";
    showSessionEnd();
  },
  onError: (e) => {
    console.error("WS Error:", e);
    statusDiv.textContent = "Connection Error";
    statusDiv.className = "status error";
  },
});

function handleJsonMessage(msg) {
  if (msg.type === "interrupted") {
    mediaHandler.stopAudioPlayback();
    currentGeminiMessageDiv = null;
    currentUserMessageDiv = null;
  } else if (msg.type === "turn_complete") {
    currentGeminiMessageDiv = null;
    currentUserMessageDiv = null;
  } else if (msg.type === "user") {
    if (currentUserMessageDiv) {
      currentUserMessageDiv.textContent += msg.text;
      chatLog.scrollTop = chatLog.scrollHeight;
    } else {
      currentUserMessageDiv = appendMessage("user", msg.text);
    }
  } else if (msg.type === "gemini") {
    if (currentGeminiMessageDiv) {
      currentGeminiMessageDiv.textContent += msg.text;
      chatLog.scrollTop = chatLog.scrollHeight;
    } else {
      currentGeminiMessageDiv = appendMessage("gemini", msg.text);
    }
  }
}

function appendMessage(type, text) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${type}`;
  msgDiv.textContent = text;
  chatLog.appendChild(msgDiv);
  chatLog.scrollTop = chatLog.scrollHeight;
  return msgDiv;
}

// ============================================================================
// Dashboard Navigation
// ============================================================================

function showDashboard() {
  authSection.classList.add("hidden");
  sessionEndSection.classList.add("hidden");
  appSection.classList.add("hidden");
  dashboardSection.classList.remove("hidden");

  // Initialize document uploader if not already done
  if (typeof documentUploader !== 'undefined') {
    documentUploader.init();
    documentUploader.fetchContexts();
  }
}

// Tab switching
tabBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    const tabName = btn.dataset.tab;

    // Update button states
    tabBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    // Update content visibility
    tabContents.forEach(content => {
      content.classList.add("hidden");
      if (content.id === `${tabName}-tab`) {
        content.classList.remove("hidden');
      }
    });

    // Fetch contexts when switching to interviews tab
    if (tabName === 'interviews' && typeof documentUploader !== 'undefined') {
      documentUploader.fetchContexts();
    }
  });
});

// ============================================================================
// Modal Handling
// ============================================================================

// Open upload modal
if (uploadBtn) {
  uploadBtn.addEventListener("click", () => {
    uploadModal.classList.remove("hidden");
  });
}

// Close upload modal
if (closeModalBtn) {
  closeModalBtn.addEventListener("click", () => {
    if (typeof documentUploader !== 'undefined') {
      documentUploader.closeModal();
    } else {
      uploadModal.classList.add("hidden");
    }
  });
}

// Close profile modal
if (closeProfileModalBtn) {
  closeProfileModalBtn.addEventListener("click", () => {
    if (typeof documentUploader !== 'undefined') {
      documentUploader.closeProfileModal();
    } else {
      profileModal.classList.add("hidden");
    }
  });
}

// Close context modal
if (closeContextModalBtn) {
  closeContextModalBtn.addEventListener("click", () => {
    if (typeof documentUploader !== 'undefined') {
      documentUploader.closeContextModal();
    } else {
      contextModal.classList.add("hidden");
    }
  });
}

// Create interview context button
if (createContextBtn) {
  createContextBtn.addEventListener("click", async () => {
    // Open context modal with populated selects
    if (typeof documentUploader !== 'undefined') {
      documentUploader.updateContextSelects();
    }
    contextModal.classList.remove("hidden");
  });
}

// Submit context creation
if (createContextSubmitBtn) {
  createContextSubmitBtn.addEventListener("click", async () => {
    const resumeSelect = document.getElementById("resume-select");
    const jdSelect = document.getElementById("jd-select");

    const resumeId = resumeSelect.value;
    const jdId = jdSelect.value;

    if (!resumeId || !jdId) {
      alert("Please select both a resume and a job description");
      return;
    }

    try {
      // First extract profiles if not already done
      // For now, we'll use the document IDs directly
      // In a real implementation, we'd need to map document IDs to profile IDs
      alert("Creating interview context...\n\nResume: " + resumeId + "\nJob: " + jdId);

      // Close modal and switch to interview tab
      if (typeof documentUploader !== 'undefined') {
        documentUploader.closeContextModal();
      } else {
        contextModal.classList.add("hidden');
      }

      // Trigger the interview tab
      const interviewsTab = document.querySelector('.tab-btn[data-tab="interviews"]');
      if (interviewsTab) interviewsTab.click();

      // Refresh context list
      if (typeof documentUploader !== 'undefined') {
        await documentUploader.fetchContexts();
      }
    } catch (error) {
      console.error("Create context error:", error);
      alert("Failed to create interview context: " + error.message);
    }
  });
}

// Close modals on overlay click
document.querySelectorAll(".modal-overlay").forEach(overlay => {
  overlay.addEventListener("click", () => {
    uploadModal.classList.add("hidden");
    profileModal.classList.add("hidden");
    contextModal.classList.add("hidden");
  });
});

// ============================================================================
// Connect Button Handler
// ============================================================================

connectBtn.onclick = async () => {
  statusDiv.textContent = "Connecting...";
  connectBtn.disabled = true;

  try {
    // Initialize audio context on user gesture
    await mediaHandler.initializeAudio();

    geminiClient.connect();
  } catch (error) {
    console.error("Connection error:", error);
    statusDiv.textContent = "Connection Failed: " + error.message;
    statusDiv.className = "status error";
    connectBtn.disabled = false;
  }
};

// ============================================================================
// UI Controls
// ============================================================================

disconnectBtn.onclick = () => {
  geminiClient.disconnect();
};

micBtn.onclick = async () => {
  if (mediaHandler.isRecording) {
    mediaHandler.stopAudio();
    micBtn.textContent = "Start Mic";
  } else {
    try {
      await mediaHandler.startAudio((data) => {
        if (geminiClient.isConnected()) {
          geminiClient.send(data);
        }
      });
      micBtn.textContent = "Stop Mic";
    } catch (e) {
      alert("Could not start audio capture");
    }
  }
};

cameraBtn.onclick = async () => {
  if (cameraBtn.textContent === "Stop Camera") {
    mediaHandler.stopVideo(videoPreview);
    cameraBtn.textContent = "Start Camera";
    screenBtn.textContent = "Share Screen";
    videoPlaceholder.classList.remove("hidden");
  } else {
    // If another stream is active (e.g. Screen), stop it first
    if (mediaHandler.videoStream) {
      mediaHandler.stopVideo(videoPreview);
      screenBtn.textContent = "Share Screen";
    }

    try {
      await mediaHandler.startVideo(videoPreview, (base64Data) => {
        if (geminiClient.isConnected()) {
          geminiClient.sendImage(base64Data);
        }
      });
      cameraBtn.textContent = "Stop Camera";
      screenBtn.textContent = "Share Screen";
      videoPlaceholder.classList.add("hidden");
    } catch (e) {
      alert("Could not access camera");
    }
  }
};

screenBtn.onclick = async () => {
  if (screenBtn.textContent === "Stop Sharing") {
    mediaHandler.stopVideo(videoPreview);
    screenBtn.textContent = "Share Screen";
    cameraBtn.textContent = "Start Camera";
    videoPlaceholder.classList.remove("hidden");
  } else {
    // If another stream is active (e.g. Camera), stop it first
    if (mediaHandler.videoStream) {
      mediaHandler.stopVideo(videoPreview);
      cameraBtn.textContent = "Start Camera";
    }

    try {
      await mediaHandler.startScreen(
        videoPreview,
        (base64Data) => {
          if (geminiClient.isConnected()) {
            geminiClient.sendImage(base64Data);
          }
        },
        () => {
          // onEnded callback (e.g. user stopped sharing from browser)
          screenBtn.textContent = "Share Screen";
          videoPlaceholder.classList.remove("hidden");
        }
      );
      screenBtn.textContent = "Stop Sharing";
      cameraBtn.textContent = "Start Camera";
      videoPlaceholder.classList.add("hidden");
    } catch (e) {
      alert("Could not share screen");
    }
  }
};

sendBtn.onclick = sendText;
textInput.onkeypress = (e) => {
  if (e.key === "Enter") sendText();
};

function sendText() {
  const text = textInput.value;
  if (text && geminiClient.isConnected()) {
    geminiClient.sendText(text);
    appendMessage("user", text);
    textInput.value = "";
  }
}

function resetUI() {
  authSection.classList.remove("hidden");
  appSection.classList.add("hidden");
  sessionEndSection.classList.add("hidden");

  mediaHandler.stopAudio();
  mediaHandler.stopVideo(videoPreview);
  videoPlaceholder.classList.remove("hidden");

  micBtn.textContent = "Start Mic";
  cameraBtn.textContent = "Start Camera";
  screenBtn.textContent = "Share Screen";
  chatLog.innerHTML = "";
  connectBtn.disabled = false;
  currentContextId = null;
}

function showSessionEnd() {
  appSection.classList.add("hidden");
  sessionEndSection.classList.remove("hidden");
  mediaHandler.stopAudio();
  mediaHandler.stopVideo(videoPreview);
}

restartBtn.onclick = () => {
  resetUI();
  showDashboard();
};

// ============================================================================
// Interview Session Lifecycle
// ============================================================================

/**
 * Update interview session UI state
 * @param {string} state - 'active' | 'paused' | 'ended' | 'connecting'
 */
function updateSessionState(state) {
  if (!sessionStatusDiv || !sessionStatusLabel) return;

  // Update status indicator classes
  sessionStatusDiv.classList.remove('active', 'paused', 'ended', 'connecting');
  sessionStatusDiv.classList.add(state);

  // Update status text
  const statusText = state.charAt(0).toUpperCase() + state.slice(1);
  sessionStatusLabel.textContent = statusText;

  // Update button visibility
  if (startInterviewBtn) startInterviewBtn.classList.toggle('hidden', state !== null);
  if (pauseInterviewBtn) pauseInterviewBtn.classList.toggle('hidden', state !== 'active');
  if (resumeInterviewBtn) resumeInterviewBtn.classList.toggle('hidden', state !== 'paused');
  if (endInterviewBtn) endInterviewBtn.classList.toggle('hidden', state !== 'active' && state !== 'paused');

  console.log('Session state updated:', state);
}

/**
 * Add transcript entry to the log
 * @param {string} speaker - 'user' | 'gemini'
 * @param {string} text
 * @param {string} timestamp
 */
function addTranscriptEntry(speaker, text, timestamp) {
  if (!transcriptLog) return;

  const entry = document.createElement('div');
  entry.className = `transcript-entry ${speaker}`;

  const speakerLabel = speaker === 'user' ? 'You' : 'Interviewer';
  const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();

  entry.innerHTML = `
    <div class="speaker-label">${speakerLabel} <span class="timestamp">${timeStr}</span></div>
    <p class="text">${text}</p>
  `;

  transcriptLog.appendChild(entry);
  transcriptLog.scrollTop = transcriptLog.scrollHeight;

  // Update count
  if (transcriptCount) {
    const count = transcriptLog.querySelectorAll('.transcript-entry').length;
    transcriptCount.textContent = `${count} message${count !== 1 ? 's' : ''}`;
  }
}

/**
 * Show session end summary
 * @param {Array} transcript
 */
function showSessionEndSummary(transcript) {
  if (!sessionEndSummary) return;

  sessionEndSummary.classList.remove('hidden');
  if (sessionSummaryText) {
    const count = transcript ? transcript.length : 0;
    sessionSummaryText.textContent = `You exchanged ${count} message${count !== 1 ? 's' : ''}`;
  }

  // Hide session controls
  if (pauseInterviewBtn) pauseInterviewBtn.classList.add('hidden');
  if (resumeInterviewBtn) resumeInterviewBtn.classList.add('hidden');
  if (endInterviewBtn) endInterviewBtn.classList.add('hidden');
}

/**
 * Start interview session for a context
 * @param {string} contextId
 */
async function startInterviewSession(contextId) {
  try {
    updateSessionState('connecting');

    // Create InterviewSession instance
    interviewSession = new InterviewSession();

    // Set up callbacks
    interviewSession.onStateChange = (state) => {
      updateSessionState(state);
    };

    interviewSession.onTranscriptUpdate = (entries) => {
      entries.forEach(entry => {
        addTranscriptEntry(entry.speaker, entry.text, entry.timestamp);
      });
    };

    interviewSession.onSessionEnd = (transcript) => {
      showSessionEndSummary(transcript);
    };

    // Start session via API
    const result = await interviewSession.startSession(contextId);
    console.log('Interview session started:', result);

    // Connect WebSocket
    interviewSession.connectWebSocket({
      onOpen: () => {
        console.log('Interview WebSocket connected');
        updateSessionState('active');

        // Send initial interviewer introduction
        const introPrompt = `System: You are conducting a job interview. The candidate's profile and job description have been loaded. Begin the interview with a friendly greeting and ask your first question.`;
        interviewSession.sendText(introPrompt);
      },
      onMessage: (msg) => {
        // Handle transcription messages
        if (msg.type === 'user' || msg.type === 'gemini') {
          addTranscriptEntry(msg.type, msg.text, null);
        }
      },
      onAudio: async (blob) => {
        // Play audio through media handler
        const arrayBuffer = await blob.arrayBuffer();
        mediaHandler.playAudio(arrayBuffer);
      },
      onClose: () => {
        console.log('Interview WebSocket closed');
        updateSessionState('ended');
      },
      onError: (error) => {
        console.error('Interview WebSocket error:', error);
      }
    });

    // Show interview session section
    if (interviewSessionSection) {
      interviewSessionSection.classList.remove('hidden');
    }

  } catch (error) {
    console.error('Start interview session error:', error);
    alert('Failed to start interview: ' + error.message);
    updateSessionState(null);
  }
}

/**
 * Pause current interview session
 */
async function pauseInterview() {
  if (!interviewSession) return;

  try {
    await interviewSession.pauseSession();
    updateSessionState('paused');
  } catch (error) {
    console.error('Pause interview error:', error);
    alert('Failed to pause interview: ' + error.message);
  }
}

/**
 * Resume paused interview session
 */
async function resumeInterview() {
  if (!interviewSession) return;

  try {
    await interviewSession.resumeSession();
    updateSessionState('active');
  } catch (error) {
    console.error('Resume interview error:', error);
    alert('Failed to resume interview: ' + error.message);
  }
}

/**
 * End current interview session
 */
async function endInterview() {
  if (!interviewSession) return;

  if (!confirm('Are you sure you want to end this interview session?')) {
    return;
  }

  try {
    await interviewSession.endSession();
    // State update and summary handled by onSessionEnd callback
  } catch (error) {
    console.error('End interview error:', error);
    alert('Failed to end interview: ' + error.message);
  }
}

/**
 * Close session and return to dashboard
 */
function closeInterviewSession() {
  if (interviewSession) {
    interviewSession.disconnect();
    interviewSession = null;
  }

  // Hide session section
  if (interviewSessionSection) {
    interviewSessionSection.classList.add('hidden');
  }

  // Hide end summary
  if (sessionEndSummary) {
    sessionEndSummary.classList.add('hidden');
  }

  // Clear transcript
  if (transcriptLog) {
    transcriptLog.innerHTML = '';
  }

  if (transcriptCount) {
    transcriptCount.textContent = '0 messages';
  }

  updateSessionState(null);
}

// Interview session event handlers
if (startInterviewBtn) {
  startInterviewBtn.onclick = () => {
    if (currentContextId) {
      startInterviewSession(currentContextId);
    } else {
      alert('Please create or select an interview context first');
    }
  };
}

if (pauseInterviewBtn) {
  pauseInterviewBtn.onclick = pauseInterview;
}

if (resumeInterviewBtn) {
  resumeInterviewBtn.onclick = resumeInterview;
}

if (endInterviewBtn) {
  endInterviewBtn.onclick = endInterview;
}

if (viewTranscriptBtn) {
  viewTranscriptBtn.onclick = () => {
    if (transcriptLog) {
      transcriptLog.scrollIntoView({ behavior: 'smooth' });
    }
  };
}

if (closeSessionBtn) {
  closeSessionBtn.onclick = closeInterviewSession;
}

// Export function for document-upload.js to trigger interview
window.startInterviewSession = startInterviewSession;
window.setInterviewContext = (contextId) => {
  currentContextId = contextId;
};

// ============================================================================
// Initialize on Load
// ============================================================================

// Check authentication status on page load
document.addEventListener("DOMContentLoaded", async () => {
  const isAuthed = await auth.checkAuth();
  updateAuthUI(isAuthed);
});
