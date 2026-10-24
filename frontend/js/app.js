/**
 * ORION Application Master Controller
 * Connects Multimodal Ingestion, Agent Orchestration, Knowledge Base Sync, and Continuous Feedback.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global Toast Function
  window.showToast = function(msg) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'hud-toast';
    toast.innerHTML = `<span>⚡</span> ${msg}`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  };

  // 1. Initialize Sub-controllers
  const audioHandler = new window.AudioRecorderHandler();
  const visionHandler = new window.VisionHandler();
  const agentStream = new window.AgentStreamController();

  // State Tracking
  let currentLastQuery = "";
  let currentLastAnswer = "";
  let currentEquipmentId = "HPU-SERIES-900";

  // 2. Tab Navigation
  const tabs = document.querySelectorAll('.nav-tab');
  const tabContents = document.querySelectorAll('.tab-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-tab');
      tabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add('active');

      if (targetId === 'tab-kb') {
        loadKnowledgeBaseStats();
      } else if (targetId === 'tab-feedback') {
        loadFeedbackRecords();
      }
    });
  });

  // 3. Telemetry Preset Chips
  const presetChips = document.querySelectorAll('.preset-chip');
  const queryInput = document.getElementById('technician-query');

  presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const query = chip.getAttribute('data-query');
      const eq = chip.getAttribute('data-eq');
      if (queryInput && query) {
        queryInput.value = query;
        currentEquipmentId = eq || "GEN-ASSET";
        window.showToast(`Loaded preset for [${eq}]. Click DISPATCH to run.`);
      }
    });
  });

  // 4. Reset Console Button
  const resetBtn = document.getElementById('btn-clear-all');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (queryInput) queryInput.value = '';
      audioHandler.clearAudio();
      visionHandler.clearImage();
      agentStream.reset();
      window.showToast("Console state reset to nominal.");
    });
  }

  // 5. Query Dispatch & Agent Orchestration
  const queryForm = document.getElementById('query-form');
  if (queryForm) {
    queryForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const textQuery = queryInput.value.trim();
      const audioBlob = audioHandler.getAudioBlob();
      const imageFile = visionHandler.getImageFile();

      if (!textQuery && !audioBlob) {
        alert("Please enter a query or record a voice note.");
        return;
      }

      currentLastQuery = textQuery;
      agentStream.startPipeline();

      try {
        let resultData = null;

        // If audio or image attached, use multimodal multipart endpoint
        if (audioBlob || imageFile) {
          const formData = new FormData();
          formData.append('query', textQuery || "Industrial inspection query");
          if (audioBlob) formData.append('voice_file', audioBlob, 'voice_note.wav');
          if (imageFile) formData.append('image_file', imageFile);
          if (currentEquipmentId) formData.append('equipment_id', currentEquipmentId);

          const resp = await fetch('/api/multimodal/query', {
            method: 'POST',
            body: formData
          });
          if (!resp.ok) throw new Error("Multimodal query failed");
          resultData = await resp.json();
        } else {
          // Standard JSON Chat endpoint
          const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query: textQuery,
              equipment_id: currentEquipmentId
            })
          });
          if (!resp.ok) throw new Error("Chat query failed");
          resultData = await resp.json();
        }

        currentLastAnswer = resultData.verified_answer;
        agentStream.renderResults(resultData);
        window.showToast("Multi-Agent verification complete. Grounded advice generated.");

      } catch (err) {
        console.error("Orchestrator error:", err);
        window.showToast("Query dispatch encountered an error. Check backend connection.");
        agentStream.reset();
      }
    });
  }

  // 6. System Status Polling
  async function fetchSystemStatus() {
    try {
      const resp = await fetch('/api/system/status');
      if (resp.ok) {
        const data = await resp.json();
        const llmElem = document.getElementById('llm-model-name');
        const dbElem = document.getElementById('db-chunk-count');

        if (llmElem) {
          const model = data.llm?.selected_model || "Ollama / Internal";
          llmElem.textContent = model;
        }
        if (dbElem) {
          const chunks = data.vector_store?.total_chunks || 0;
          dbElem.textContent = `${chunks} Chunks (ChromaDB)`;
        }
      }
    } catch (e) {
      console.warn("Offline backend polling...", e);
    }
  }
  fetchSystemStatus();

  // 7. Knowledge Base Tab Functions
  async function loadKnowledgeBaseStats() {
    try {
      const resp = await fetch('/api/documents');
      if (resp.ok) {
        const stats = await resp.json();
        document.getElementById('stat-total-chunks').textContent = stats.total_chunks || 0;
        document.getElementById('stat-total-docs').textContent = stats.total_documents || 0;
        document.getElementById('stat-engine-type').textContent = stats.engine || "ChromaDB + SQLite";
        document.getElementById('nav-doc-count').textContent = stats.total_documents || 0;

        const tbody = document.getElementById('kb-docs-tbody');
        tbody.innerHTML = '';
        (stats.documents || []).forEach(doc => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><span class="doc-badge">${doc.doc_id}</span></td>
            <td><strong>${doc.title}</strong></td>
            <td><code>${doc.file_name}</code></td>
            <td><span class="chip-code">${doc.source_type}</span></td>
            <td>${doc.equipment_type}</td>
            <td>
              <button class="hud-btn small outline" onclick="window.queryDoc('${doc.doc_id}', '${doc.equipment_type}')">RUN DIAGNOSTIC</button>
            </td>
          `;
          tbody.appendChild(tr);
        });
      }
    } catch (e) {
      console.error("Error loading documents:", e);
    }
  }

  window.queryDoc = function(docId, equipmentType) {
    const tabConsole = document.getElementById('tab-btn-console');
    if (tabConsole) tabConsole.click();
    currentEquipmentId = equipmentType || "GEN-ASSET";
    if (queryInput) {
      queryInput.value = `Provide full maintenance troubleshooting steps from [${docId}]`;
      const form = document.getElementById('query-form');
      if (form) {
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      }
    }
  };

  // Knowledge Base Ingestion Upload
  const uploadDocTrigger = document.getElementById('btn-upload-doc-trigger');
  const kbFileInput = document.getElementById('kb-file-input');

  if (uploadDocTrigger && kbFileInput) {
    uploadDocTrigger.addEventListener('click', () => kbFileInput.click());
    kbFileInput.addEventListener('change', async (e) => {
      if (e.target.files && e.target.files[0]) {
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);
        window.showToast(`Ingesting and embedding '${file.name}' into ChromaDB...`);

        try {
          const resp = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
          });
          if (resp.ok) {
            const res = await resp.json();
            window.showToast(res.message);
            loadKnowledgeBaseStats();
            fetchSystemStatus();
          }
        } catch (err) {
          window.showToast("Failed to upload document.");
        }
      }
    });
  }

  // Sync / Re-index KB Button
  const reindexBtn = document.getElementById('btn-reindex-kb');
  if (reindexBtn) {
    reindexBtn.addEventListener('click', async () => {
      window.showToast("Re-indexing local knowledge base in ChromaDB...");
      try {
        const resp = await fetch('/api/documents/reindex', { method: 'POST' });
        if (resp.ok) {
          const data = await resp.json();
          window.showToast(`Re-indexing complete: ${data.total_chunks_indexed} chunks synchronized.`);
          fetchSystemStatus();
        }
      } catch (e) {
        window.showToast("Re-index error.");
      }
    });
  }

  // 8. Technician Feedback & Re-indexing Modal
  const feedbackModal = document.getElementById('feedback-modal');
  const btnConfirm = document.getElementById('btn-feedback-confirm');
  const btnModify = document.getElementById('btn-feedback-modify');
  const modalClose = document.getElementById('modal-close-btn');
  const modalCancel = document.getElementById('modal-cancel-btn');
  const feedbackForm = document.getElementById('feedback-form');

  const modalQueryPreview = document.getElementById('modal-query-preview');
  const modalEquipmentId = document.getElementById('modal-equipment-id');
  const modalVerdict = document.getElementById('modal-verdict');
  const modalNotes = document.getElementById('modal-technician-notes');

  function openFeedbackModal(verdict) {
    if (modalQueryPreview) modalQueryPreview.value = currentLastQuery || "General Industrial Inspection";
    if (modalEquipmentId) modalEquipmentId.value = currentEquipmentId || "HPU-SERIES-900";
    if (modalVerdict) modalVerdict.value = verdict;
    if (modalNotes) {
      if (verdict === 'confirmed') {
        modalNotes.value = "Procedure confirmed operational in the field. Pressure and vibration restored to normal limits.";
      } else {
        modalNotes.value = "";
      }
    }
    if (feedbackModal) feedbackModal.style.display = 'flex';
  }

  if (btnConfirm) btnConfirm.addEventListener('click', () => openFeedbackModal('confirmed'));
  if (btnModify) btnModify.addEventListener('click', () => openFeedbackModal('modified'));

  const closeModal = () => { if (feedbackModal) feedbackModal.style.display = 'none'; };
  if (modalClose) modalClose.addEventListener('click', closeModal);
  if (modalCancel) modalCancel.addEventListener('click', closeModal);

  if (feedbackForm) {
    feedbackForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        query: modalQueryPreview.value,
        answer: currentLastAnswer,
        verdict: modalVerdict.value,
        technician_notes: modalNotes.value,
        equipment_id: modalEquipmentId.value,
        technician_name: document.getElementById('modal-tech-name')?.value || "Field Technician"
      };

      try {
        const resp = await fetch('/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (resp.ok) {
          const res = await resp.json();
          closeModal();
          window.showToast(`Feedback logged! Verified solution added to ChromaDB (${res.reindexed_chunks} new chunk).`);
          fetchSystemStatus();
          loadFeedbackRecords();
        }
      } catch (err) {
        window.showToast("Failed to submit feedback.");
      }
    });
  }

  // 9. Feedback Tab Records Listing
  async function loadFeedbackRecords() {
    try {
      const resp = await fetch('/api/feedback');
      if (resp.ok) {
        const data = await resp.json();
        const list = document.getElementById('feedback-list');
        const countSpan = document.getElementById('nav-feedback-count');
        const records = data.feedback_records || [];

        if (countSpan) countSpan.textContent = records.length;
        if (!list) return;

        list.innerHTML = '';
        if (records.length === 0) {
          list.innerHTML = '<div class="stat-box" style="color:var(--text-muted);">No field resolutions submitted yet. Use the Operator Console to log verified solutions.</div>';
          return;
        }

        records.forEach(r => {
          const card = document.createElement('div');
          card.className = `fb-card ${r.status === 'VALIDATED' ? 'validated' : ''}`;
          card.innerHTML = `
            <div class="fb-top">
              <span class="fb-id">${r.feedback_id} — ${r.equipment_id}</span>
              <span class="fb-badge">${r.status} (${r.verdict.toUpperCase()})</span>
            </div>
            <div class="fb-query"><strong>Symptom:</strong> ${r.original_query}</div>
            <div class="fb-notes"><strong>Verified Corrective Action:</strong> ${r.technician_notes}</div>
            <div style="font-size:0.7rem; color:var(--text-muted); font-family:var(--font-mono);">
              Validated by ${r.technician_name} • ${r.timestamp} • Re-indexed in ChromaDB
            </div>
          `;
          list.appendChild(card);
        });
      }
    } catch (e) {
      console.error("Error loading feedback:", e);
    }
  }

  // Initial load
  loadKnowledgeBaseStats();
  loadFeedbackRecords();
});
