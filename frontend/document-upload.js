/**
 * DocumentUpload: Handles document upload and profile extraction
 */
class DocumentUpload {
  constructor() {
    this.documents = [];
    this.profiles = {};
    this.contexts = [];
    this.currentTab = 'file';
  }

  // Get auth token for API requests
  getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    if (token) {
      return { 'Authorization': `Bearer ${token}` };
    }
    return {};
  }

  // Initialize upload modal
  init() {
    this.setupModalTabs();
    this.setupDropZone();
    this.setupEventListeners();
    this.fetchDocuments();
  }

  setupModalTabs() {
    const tabBtns = document.querySelectorAll('.upload-tab-btn');
    const tabContents = document.querySelectorAll('.upload-tab-content');

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.uploadTab;

        // Update button states
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update content visibility
        tabContents.forEach(content => {
          content.classList.add('hidden');
          if (content.id === `${tab}-upload-tab`) {
            content.classList.remove('hidden');
          }
        });

        this.currentTab = tab;
      });
    });
  }

  setupDropZone() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.handleFileUpload(files[0]);
      }
    });

    // Browse button
    const browseBtn = document.getElementById('browseBtn');
    browseBtn.addEventListener('click', () => {
      fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.handleFileUpload(e.target.files[0]);
      }
    });
  }

  setupEventListeners() {
    // Text submit
    document.getElementById('submitTextBtn').addEventListener('click', () => {
      const text = document.getElementById('jd-textarea').value.trim();
      if (text) {
        this.handleTextSubmit(text);
      } else {
        alert('Please paste some job description text');
      }
    });

    // URL submit
    document.getElementById('submitUrlBtn').addEventListener('click', () => {
      const url = document.getElementById('jd-url').value.trim();
      if (url) {
        this.handleUrlSubmit(url);
      } else {
        alert('Please enter a valid URL');
      }
    });
  }

  async handleFileUpload(file) {
    const allowedTypes = ['.pdf', '.docx'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(fileExt)) {
      alert('Invalid file type. Please upload a PDF or DOCX file.');
      return;
    }

    this.showProcessing(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/documents/resume', {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const result = await response.json();
      this.showProcessing(false);
      this.closeModal();

      // Refresh document list
      await this.fetchDocuments();

      // Ask if user wants to extract profile
      if (confirm('Document uploaded successfully. Extract profile now?')) {
        await this.extractResumeProfile(result.document_id);
      }
    } catch (error) {
      console.error('Upload error:', error);
      this.showProcessing(false);
      alert('Upload failed: ' + error.message);
    }
  }

  async handleTextSubmit(text) {
    this.showProcessing(true);

    try {
      const response = await fetch('/api/documents/job-description', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const result = await response.json();
      this.showProcessing(false);
      this.closeModal();

      // Refresh document list
      await this.fetchDocuments();

      // Ask if user wants to extract profile
      if (confirm('Job description saved. Extract profile now?')) {
        await this.extractJobProfile(result.document_id);
      }
    } catch (error) {
      console.error('Text upload error:', error);
      this.showProcessing(false);
      alert('Upload failed: ' + error.message);
    }
  }

  async handleUrlSubmit(url) {
    this.showProcessing(true);

    try {
      const response = await fetch('/api/documents/job-description', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify({ url })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Import failed');
      }

      const result = await response.json();
      this.showProcessing(false);
      this.closeModal();

      // Refresh document list
      await this.fetchDocuments();

      // Ask if user wants to extract profile
      if (confirm('Job description imported. Extract profile now?')) {
        await this.extractJobProfile(result.document_id);
      }
    } catch (error) {
      console.error('URL import error:', error);
      this.showProcessing(false);
      alert('Import failed: ' + error.message);
    }
  }

  async fetchDocuments() {
    try {
      const response = await fetch('/api/documents', {
        headers: this.getAuthHeaders()
      });
      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }
      this.documents = await response.json();
      this.renderDocumentList();
      this.updateContextSelects();
    } catch (error) {
      console.error('Fetch documents error:', error);
    }
  }

  renderDocumentList() {
    const listEl = document.getElementById('document-list');

    if (this.documents.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state">
          <h3>No documents yet</h3>
          <p>Upload a resume or paste a job description to get started</p>
        </div>
      `;
      return;
    }

    listEl.innerHTML = this.documents.map(doc => `
      <div class="document-card" data-id="${doc.document_id}">
        <div class="document-icon">
          ${doc.file_type === 'PDF' ? '📄' : doc.file_type === 'DOCX' ? '📝' : '📋'}
        </div>
        <div class="document-info">
          <h4>${this.escapeHtml(doc.filename)}</h4>
          <span class="document-type">${doc.type}</span>
          <span class="document-date">${this.formatDate(doc.created_at)}</span>
        </div>
        <div class="document-actions">
          ${doc.type === 'resume' ? `<button class="btn btn-sm" onclick="documentUploader.extractResumeProfile('${doc.document_id}')">Extract Profile</button>` : ''}
          ${doc.type === 'job_description' ? `<button class="btn btn-sm" onclick="documentUploader.extractJobProfile('${doc.document_id}')">Extract Profile</button>` : ''}
          <button class="btn btn-sm danger" onclick="documentUploader.deleteDocument('${doc.document_id}')">Delete</button>
        </div>
      </div>
    `).join('');
  }

  async deleteDocument(id) {
    if (!confirm('Delete this document? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/documents/${id}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Delete failed');
      }

      await this.fetchDocuments();
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete document');
    }
  }

  async extractResumeProfile(documentId) {
    this.showProcessing(true);

    try {
      const response = await fetch('/api/profiles/extract-from-resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify({ document_id: documentId })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Extraction failed');
      }

      const profile = await response.json();
      this.profiles[profile.profile_id] = profile;
      this.showProcessing(false);
      this.showProfileModal(profile, 'resume');
    } catch (error) {
      console.error('Resume extraction error:', error);
      this.showProcessing(false);
      alert('Profile extraction failed: ' + error.message);
    }
  }

  async extractJobProfile(documentId) {
    this.showProcessing(true);

    try {
      const response = await fetch('/api/profiles/extract-from-jd', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify({ document_id: documentId })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Extraction failed');
      }

      const profile = await response.json();
      this.profiles[profile.profile_id] = profile;
      this.showProcessing(false);
      this.showProfileModal(profile, 'job');
    } catch (error) {
      console.error('JD extraction error:', error);
      this.showProcessing(false);
      alert('Profile extraction failed: ' + error.message);
    }
  }

  showProfileModal(profile, type) {
    const modal = document.getElementById('profile-modal');
    const title = document.getElementById('profile-title');
    const content = document.getElementById('profile-content');

    if (type === 'resume') {
      title.textContent = 'Candidate Profile';
      const confidenceColor = profile.confidence_score >= 80 ? '#22c55e' : profile.confidence_score >= 50 ? '#eab308' : '#ef4444';

      content.innerHTML = `
        <div class="profile-header">
          <h3>${this.escapeHtml(profile.name)}</h3>
          <p class="profile-headline">${this.escapeHtml(profile.headline)}</p>
          <span class="confidence-badge" style="background-color: ${confidenceColor}">
            Confidence: ${profile.confidence_score}%
          </span>
        </div>

        <div class="profile-section">
          <h4>Skills</h4>
          <div class="skills-badges">
            ${profile.skills.map(s => `<span class="skill-badge">${this.escapeHtml(s)}</span>`).join('')}
          </div>
        </div>

        <div class="profile-section">
          <h4>Experience</h4>
          ${profile.experience.map(exp => `
            <div class="experience-card">
              <h5>${this.escapeHtml(exp.title)}</h5>
              <p class="company">${this.escapeHtml(exp.company)} | ${this.escapeHtml(exp.duration)}</p>
              <p class="description">${this.escapeHtml(exp.description)}</p>
            </div>
          `).join('')}
        </div>

        <div class="profile-section">
          <h4>Education</h4>
          ${profile.education.map(edu => `
            <div class="education-card">
              <h5>${this.escapeHtml(edu.degree)}</h5>
              <p>${this.escapeHtml(edu.institution)}${edu.year ? ` | ${this.escapeHtml(edu.year)}` : ''}</p>
            </div>
          `).join('')}
        </div>
      `;
    } else {
      title.textContent = 'Job Profile';
      content.innerHTML = `
        <div class="profile-header">
          <h3>${this.escapeHtml(profile.role)}</h3>
          <p class="profile-headline">${this.escapeHtml(profile.company)}</p>
        </div>

        <div class="profile-section">
          <h4>Requirements</h4>
          <ul class="requirements-list">
            ${profile.requirements.map(r => `<li>${this.escapeHtml(r)}</li>`).join('')}
          </ul>
        </div>

        <div class="profile-section">
          <h4>Nice to Have</h4>
          <ul class="requirements-list">
            ${profile.nice_to_have.map(r => `<li>${this.escapeHtml(r)}</li>`).join('')}
          </ul>
        </div>

        <div class="profile-section">
          <h4>Responsibilities</h4>
          <ul class="requirements-list">
            ${profile.responsibilities.map(r => `<li>${this.escapeHtml(r)}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    modal.classList.remove('hidden');
  }

  updateContextSelects() {
    const resumeSelect = document.getElementById('resume-select');
    const jdSelect = document.getElementById('jd-select');

    const resumeDocs = this.documents.filter(d => d.type === 'resume');
    const jdDocs = this.documents.filter(d => d.type === 'job_description');

    resumeSelect.innerHTML = '<option value="">Choose a resume...</option>' +
      resumeDocs.map(d => `<option value="${d.document_id}">${this.escapeHtml(d.filename)}</option>`).join('');

    jdSelect.innerHTML = '<option value="">Choose a job description...</option>' +
      jdDocs.map(d => `<option value="${d.document_id}">${this.escapeHtml(d.filename)}</option>`).join('');
  }

  async fetchContexts() {
    try {
      const response = await fetch('/api/interview-contexts', {
        headers: this.getAuthHeaders()
      });
      if (!response.ok) {
        throw new Error('Failed to fetch contexts');
      }
      this.contexts = await response.json();
      this.renderContextList();
    } catch (error) {
      console.error('Fetch contexts error:', error);
    }
  }

  renderContextList() {
    const listEl = document.getElementById('context-list');

    if (this.contexts.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state">
          <h3>No interview contexts yet</h3>
          <p>Create an interview context by binding a resume with a job description</p>
        </div>
      `;
      return;
    }

    listEl.innerHTML = this.contexts.map(ctx => `
      <div class="context-card" data-id="${ctx.context_id}">
        <div class="context-grid">
          <div class="context-column">
            <span class="context-label">Candidate</span>
            <h4>${this.escapeHtml(ctx.resume_profile_summary.name)}</h4>
            <p>${this.escapeHtml(ctx.resume_profile_summary.headline)}</p>
          </div>
          <div class="context-divider">→</div>
          <div class="context-column">
            <span class="context-label">Position</span>
            <h4>${this.escapeHtml(ctx.job_profile_summary.role)}</h4>
            <p>${this.escapeHtml(ctx.job_profile_summary.company)}</p>
          </div>
        </div>
        <div class="context-actions">
          <span class="context-date">${this.formatDate(ctx.created_at)}</span>
          <button class="btn" onclick="documentUploader.startInterview('${ctx.context_id}')">Start Interview</button>
        </div>
      </div>
    `).join('');
  }

  async createContext(resumeProfileId, jobProfileId) {
    try {
      const response = await fetch('/api/interview-contexts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify({
          resume_profile_id: resumeProfileId,
          job_profile_id: jobProfileId
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create context');
      }

      const context = await response.json();
      this.contexts.push(context);
      return context;
    } catch (error) {
      console.error('Create context error:', error);
      throw error;
    }
  }

  startInterview(contextId) {
    // Use the global interview session handler
    if (typeof window.startInterviewSession === 'function') {
      window.setInterviewContext(contextId);
      window.startInterviewSession(contextId);
    } else {
      // Fallback: set context and show alert
      console.log('Starting interview with context:', contextId);
      window.setInterviewContext?.(contextId);
      alert('Interview starting with context: ' + contextId);
    }
  }

  // Utility methods
  showProcessing(show) {
    const indicator = document.getElementById('processing-indicator');
    const modal = document.getElementById('upload-modal');

    if (show) {
      indicator.classList.remove('hidden');
    } else {
      indicator.classList.add('hidden');
    }
  }

  closeModal() {
    const modal = document.getElementById('upload-modal');
    modal.classList.add('hidden');
    document.getElementById('processing-indicator').classList.add('hidden');
    document.getElementById('jd-textarea').value = '';
    document.getElementById('jd-url').value = '';
    document.getElementById('file-input').value = '';
  }

  closeProfileModal() {
    document.getElementById('profile-modal').classList.add('hidden');
  }

  closeContextModal() {
    document.getElementById('context-modal').classList.add('hidden');
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
  }

  formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }
}

// Initialize singleton
const documentUploader = new DocumentUpload();
