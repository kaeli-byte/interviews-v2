// --- Main Application Logic ---

// DOM Elements
const statusDiv = document.getElementById("status");
const authSection = document.getElementById("auth-section");
const appSection = document.getElementById("app-section");
const sessionEndSection = document.getElementById("session-end-section");
const dashboardSection = document.getElementById("dashboard-section");
const restartBtn = document.getElementById("restartBtn");
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

let currentGeminiMessageDiv = null;
let currentUserMessageDiv = null;
let currentContextId = null;

const mediaHandler = new MediaHandler();
const geminiClient = new GeminiClient({
  onOpen: () => {
    statusDiv.textContent = "Connected";
    statusDiv.className = "status connected";
    authSection.classList.add("hidden");
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
// Initialize on Load
// ============================================================================

// Show dashboard by default (for MVP without auth)
document.addEventListener("DOMContentLoaded", () => {
  showDashboard();
});
