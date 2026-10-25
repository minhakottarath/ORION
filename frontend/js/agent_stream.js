/**
 * ORION Multi-Agent Pipeline & Decision Stream Visualizer
 * Animates Retrieval, Reasoning, and Verification phases and renders verified decision support.
 */

class AgentStreamController {
  constructor() {
    this.badgeStatus = document.getElementById('pipeline-status-badge');
    
    // Agent Timeline Nodes
    this.nodeRetrieval = document.getElementById('node-retrieval');
    this.statusRetrieval = document.getElementById('retrieval-status');
    this.descRetrieval = document.getElementById('retrieval-desc');
    this.meterRetrieval = document.getElementById('meter-retrieval');

    this.nodeReasoning = document.getElementById('node-reasoning');
    this.statusReasoning = document.getElementById('reasoning-status');
    this.descReasoning = document.getElementById('reasoning-desc');
    this.meterReasoning = document.getElementById('meter-reasoning');

    this.nodeVerification = document.getElementById('node-verification');
    this.statusVerification = document.getElementById('verification-status');
    this.descVerification = document.getElementById('verification-desc');
    this.meterVerification = document.getElementById('meter-verification');

    // Results Display
    this.placeholder = document.getElementById('result-placeholder');
    this.resultContainer = document.getElementById('result-content');
    this.answerBody = document.getElementById('answer-markdown');
    this.sourcesList = document.getElementById('sources-list');
    this.citationsCount = document.getElementById('citations-count');
    this.ansTimestamp = document.getElementById('ans-timestamp');

    // Verification Card
    this.vCard = document.getElementById('verification-card');
    this.vCardStatus = document.getElementById('vcard-status');
    this.vCardAudit = document.getElementById('vcard-audit-text');
    this.vCardScoreNum = document.getElementById('vcard-score-num');
  }

  startPipeline() {
    if (this.placeholder) this.placeholder.style.display = 'none';
    if (this.resultContainer) this.resultContainer.style.display = 'none';

    if (this.badgeStatus) {
      this.badgeStatus.textContent = 'ORCHESTRATING';
      this.badgeStatus.className = 'panel-tag live-tag';
    }

    // Reset nodes
    [this.nodeRetrieval, this.nodeReasoning, this.nodeVerification].forEach(n => {
      if (n) {
        n.classList.remove('active', 'completed');
      }
    });

    // Step 1: Retrieval Active
    if (this.nodeRetrieval) {
      this.nodeRetrieval.classList.add('active');
      this.statusRetrieval.textContent = 'SEARCHING...';
      this.meterRetrieval.style.width = '60%';
    }
  }

  renderResults(data) {
    const isInsufficient = data.status === 'INSUFFICIENT_EVIDENCE' || (data.verification && data.verification.status === 'INSUFFICIENT_EVIDENCE');
    const isError = data.status === 'ERROR' || (data.verification && data.verification.status === 'ERROR');

    // 1. Finalize Retrieval Node
    if (this.nodeRetrieval) {
      this.nodeRetrieval.classList.remove('active');
      this.nodeRetrieval.classList.add('completed');
      if (isInsufficient) {
        this.statusRetrieval.textContent = 'NO MATCH';
        this.meterRetrieval.style.width = '100%';
        this.descRetrieval.textContent = 'No chunks met relevance threshold.';
      } else {
        this.statusRetrieval.textContent = 'DONE';
        this.meterRetrieval.style.width = '100%';
        this.descRetrieval.textContent = `Found ${data.sources.length} matching industrial chunks.`;
      }
    }

    // 2. Finalize Reasoning Node
    if (this.nodeReasoning) {
      this.nodeReasoning.classList.remove('active');
      this.nodeReasoning.classList.add('completed');
      if (isInsufficient) {
        this.statusReasoning.textContent = 'REFUSED';
        this.meterReasoning.style.width = '100%';
        this.descReasoning.textContent = 'Refused to invent missing documentation.';
      } else if (isError) {
        this.statusReasoning.textContent = 'ERROR';
        this.meterReasoning.style.width = '100%';
        this.descReasoning.textContent = 'Reasoning error encountered.';
      } else {
        this.statusReasoning.textContent = 'DONE';
        this.meterReasoning.style.width = '100%';
        this.descReasoning.textContent = `Synthesized grounded response (${data.total_latency_ms} ms).`;
      }
    }

    // 3. Finalize Verification Node
    const verif = data.verification || {};
    if (this.nodeVerification) {
      this.nodeVerification.classList.remove('active');
      this.nodeVerification.classList.add('completed');
      if (isInsufficient) {
        this.statusVerification.textContent = 'AUDITED';
        this.meterVerification.style.width = '100%';
        this.descVerification.textContent = 'Refusal verified: 0 hallucinations.';
      } else {
        this.statusVerification.textContent = verif.status || 'VERIFIED';
        this.meterVerification.style.width = '100%';
        this.descVerification.textContent = `Groundedness: ${verif.groundedness_score || 0}% (Risk: ${verif.hallucination_risk || 'LOW'})`;
      }
    }

    if (this.badgeStatus) {
      if (isInsufficient) {
        this.badgeStatus.textContent = 'INSUFFICIENT EVIDENCE';
        this.badgeStatus.className = 'panel-tag warning-tag';
      } else if (isError) {
        this.badgeStatus.textContent = 'SYSTEM ERROR';
        this.badgeStatus.className = 'panel-tag danger-tag';
      } else if (verif.status === 'FLAGGED_FOR_REVIEW') {
        this.badgeStatus.textContent = 'FLAGGED FOR REVIEW';
        this.badgeStatus.className = 'panel-tag warning-tag';
      } else {
        this.badgeStatus.textContent = 'VERIFIED';
        this.badgeStatus.className = 'panel-tag live-tag';
      }
    }

    // 4. Populate Verification Card
    if (isInsufficient) {
      this.vCardScoreNum.textContent = 'N/A';
      this.vCardStatus.textContent = 'INSUFFICIENT EVIDENCE';
      this.vCardAudit.textContent = 'The knowledge base does not contain sufficient verified evidence to answer this query. Fabrication was refused.';
    } else if (isError) {
      this.vCardScoreNum.textContent = 'ERR';
      this.vCardStatus.textContent = 'EXECUTION FAILURE';
      this.vCardAudit.textContent = verif.audit_checks ? verif.audit_checks.join(' • ') : 'Component error.';
    } else {
      const score = verif.groundedness_score || 0;
      this.vCardScoreNum.textContent = `${score}%`;
      this.vCardStatus.textContent = (score >= 80 && !verif.hallucination_detected) ? 'GROUNDED & AUDITED' : 'FLAGGED FOR REVIEW';
      
      if (verif.audit_checks && verif.audit_checks.length > 0) {
        this.vCardAudit.textContent = verif.audit_checks.join(' • ');
      } else {
        this.vCardAudit.textContent = 'Factual consistency cross-referenced with retrieved OEM excerpts.';
      }
    }

    // 5. Render Formatted Markdown Answer
    this.answerBody.innerHTML = this.formatMarkdown(data.verified_answer);
    this.ansTimestamp.textContent = new Date().toLocaleTimeString();

    // 6. Populate Source Citations
    this.renderSources(data.sources || []);

    // Show Result Container
    if (this.resultContainer) {
      this.resultContainer.style.display = 'block';
      this.resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  renderSources(sources) {
    if (!this.sourcesList) return;
    this.sourcesList.innerHTML = '';
    this.citationsCount.textContent = `${sources.length} OEM SOURCES`;

    if (!sources || sources.length === 0) {
      this.sourcesList.innerHTML = '<div class="source-item" style="color:var(--text-muted);">No direct document citations matched or required for this response.</div>';
      return;
    }

    sources.forEach(src => {
      const card = document.createElement('div');
      card.className = 'source-item';
      
      const scorePct = Math.round((src.similarity_score || 0.8) * 100);
      let provenanceInfo = src.section || 'General';
      if (src.page) {
        provenanceInfo += ` • Page ${src.page}`;
      }
      if (src.file_name && src.file_name !== 'unknown') {
        provenanceInfo += ` (${src.file_name})`;
      }

      card.innerHTML = `
        <div class="source-top">
          <span class="source-id-badge">${src.doc_id || 'OEM-REF'}</span>
          <span class="source-score-badge">MATCH CONFIDENCE: ${scorePct}%</span>
        </div>
        <div class="source-title-text">${src.title || 'Technical Manual'} — <span style="color:var(--accent-amber);">${provenanceInfo}</span></div>
        <div class="source-snippet">${src.snippet || ''}</div>
      `;
      this.sourcesList.appendChild(card);
    });
  }

  formatMarkdown(text) {
    if (!text) return '';

    const lines = text.split('\n');
    let html = '';
    let inUl = false;
    let inOl = false;

    for (let rawLine of lines) {
      const line = rawLine.trim();
      if (!line) {
        if (inUl) { html += '</ul>'; inUl = false; }
        if (inOl) { html += '</ol>'; inOl = false; }
        continue;
      }

      // Headers
      if (line.startsWith('### ')) {
        if (inUl) { html += '</ul>'; inUl = false; }
        if (inOl) { html += '</ol>'; inOl = false; }
        html += `<h3>${this.inlineFormat(line.slice(4))}</h3>`;
      } else if (line.startsWith('## ')) {
        if (inUl) { html += '</ul>'; inUl = false; }
        if (inOl) { html += '</ol>'; inOl = false; }
        html += `<h3 style="color:var(--accent-amber);">${this.inlineFormat(line.slice(3))}</h3>`;
      } else if (line.startsWith('# ')) {
        if (inUl) { html += '</ul>'; inUl = false; }
        if (inOl) { html += '</ol>'; inOl = false; }
        html += `<h2 style="color:var(--accent-cyan);">${this.inlineFormat(line.slice(2))}</h2>`;
      }
      // Bullet list items
      else if (/^[-*]\s+/.test(line)) {
        if (inOl) { html += '</ol>'; inOl = false; }
        if (!inUl) { html += '<ul>'; inUl = true; }
        html += `<li>${this.inlineFormat(line.replace(/^[-*]\s+/, ''))}</li>`;
      }
      // Numbered list items
      else if (/^\d+\.\s+/.test(line)) {
        if (inUl) { html += '</ul>'; inUl = false; }
        if (!inOl) { html += '<ol>'; inOl = true; }
        html += `<li>${this.inlineFormat(line.replace(/^\d+\.\s+/, ''))}</li>`;
      }
      // Standard text paragraphs
      else {
        if (inUl) { html += '</ul>'; inUl = false; }
        if (inOl) { html += '</ol>'; inOl = false; }
        html += `<p>${this.inlineFormat(line)}</p>`;
      }
    }

    if (inUl) html += '</ul>';
    if (inOl) html += '</ol>';
    return html;
  }

  inlineFormat(str) {
    return str
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\[([A-Za-z0-9\-_]+)(?::[^\]]+)?\]/g, '<span class="chip-code" style="cursor:pointer;">[$1]</span>');
  }

  reset() {
    if (this.placeholder) this.placeholder.style.display = 'flex';
    if (this.resultContainer) this.resultContainer.style.display = 'none';
    if (this.badgeStatus) this.badgeStatus.textContent = 'READY';

    [this.nodeRetrieval, this.nodeReasoning, this.nodeVerification].forEach(n => {
      if (n) {
        n.classList.remove('active', 'completed');
      }
    });

    if (this.meterRetrieval) this.meterRetrieval.style.width = '0%';
    if (this.meterReasoning) this.meterReasoning.style.width = '0%';
    if (this.meterVerification) this.meterVerification.style.width = '0%';

    if (this.statusRetrieval) this.statusRetrieval.textContent = 'IDLE';
    if (this.statusReasoning) this.statusReasoning.textContent = 'IDLE';
    if (this.statusVerification) this.statusVerification.textContent = 'IDLE';
  }
}

window.AgentStreamController = AgentStreamController;
