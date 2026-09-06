/* ================================================
   Draft Lifecycle Tracker — Frontend App
   ================================================ */

const API = '';  // Flask serves at same origin

// ====================================================
// UTILITIES
// ====================================================

function $(id) { return document.getElementById(id); }

function toast(msg, type = 'info') {
  const container = $('toastContainer');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  el.textContent = `${icons[type] || ''} ${msg}`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

function formatCountdown(seconds) {
  if (seconds <= 0) return 'Expired';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m left`;
  return `${m}m left`;
}

function statusBadgeHTML(status) {
  const s = (status || 'open').toLowerCase();
  const cls = `badge badge-${s.replace(/_/g, '_')}`;
  const labels = {
    open: 'Open',
    converted: 'Converted',
    converted_edited: 'Converted + Edited',
    expired: 'Expired'
  };
  return `<span class="${cls}">${labels[s] || status}</span>`;
}

function truncate(str, n = 80) {
  if (!str) return '—';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ====================================================
// TAB NAVIGATION
// ====================================================

function switchTab(tabName) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

  const tab = document.querySelector(`[data-tab="${tabName}"]`);
  const view = $(`view-${tabName}`);
  if (tab) tab.classList.add('active');
  if (view) view.classList.add('active');

  if (tabName === 'dashboard') loadDashboard();
  if (tabName === 'analytics') loadAnalytics();
  if (tabName === 'memory') loadMemory();
}

document.querySelectorAll('.nav-tab').forEach(btn => {
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

// ====================================================
// CONFIRM MODAL
// ====================================================

let _modalResolve = null;

function showConfirmModal({ icon = '🗑', title, desc, confirmLabel = 'Confirm', confirmClass = 'btn-danger' }) {
  return new Promise(resolve => {
    _modalResolve = resolve;
    $('modalIcon').textContent = icon;
    $('modalTitle').textContent = title;
    $('modalDesc').textContent = desc;
    $('modalConfirmBtn').textContent = confirmLabel;
    $('modalConfirmBtn').className = confirmClass;
    $('confirmModal').classList.add('open');
  });
}

function closeModal(result) {
  $('confirmModal').classList.remove('open');
  if (_modalResolve) { _modalResolve(result); _modalResolve = null; }
}

$('modalConfirmBtn').addEventListener('click', () => closeModal(true));
$('modalCancelBtn').addEventListener('click', () => closeModal(false));
$('confirmModal').addEventListener('click', e => { if (e.target === $('confirmModal')) closeModal(false); });

// ====================================================
// DASHBOARD
// ====================================================
async function loadDashboard() {
  try {
    const [drafts, report] = await Promise.all([
      apiFetch('/api/drafts'),
      apiFetch('/api/report')
    ]);

    // Stats
    $('statTotal').textContent = report.total_drafts;
    $('statConvRate').textContent = report.conversion_rate + '%';
    $('statConverted').textContent = report.converted;
    $('statEditRate').textContent = report.post_conversion_edit_rate + '%';

    // Draft cards
    const grid = $('draftsGrid');
    if (!drafts.length) {
      grid.innerHTML = `<div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <div class="empty-state-text">No drafts yet. Ask the AI agent to create one!</div>
      </div>`;
      return;
    }

    const now = Date.now();
    grid.innerHTML = drafts.map(d => {
      const proposed = d.proposed || {};
      const isExpired = d.status === 'EXPIRED';
      const isOpen = d.status === 'OPEN';

      // Compute expiry countdown for OPEN drafts
      let expiryHTML = '';
      if (isOpen && d.created_at) {
        const createdAt = new Date(d.created_at).getTime();
        const expiresAt = createdAt + 24 * 3600 * 1000;
        const secondsLeft = Math.max(0, Math.round((expiresAt - now) / 1000));
        const soon = secondsLeft < 3600; // < 1 hour
        expiryHTML = `<span class="expiry-pill ${soon ? 'expiring-soon' : 'expiring-ok'}" data-expires="${expiresAt}">
          ⏱ ${formatCountdown(secondsLeft)}
        </span>`;
      }

      return `
        <div class="draft-card${isExpired ? ' is-expired' : ''}" data-id="${d.id}" role="button" tabindex="0">
          <div class="draft-card-header">
            <div class="draft-card-to">${proposed.to || '—'}</div>
            ${statusBadgeHTML(d.status)}
          </div>
          <div class="draft-card-subject">${proposed.subject || '(no subject)'}</div>
          <div class="draft-card-body">${truncate(proposed.body, 100)}</div>
          <div class="draft-card-footer">
            <div style="display:flex;flex-direction:column;gap:4px;">
              <span class="draft-card-date">${formatDate(d.created_at)}</span>
              ${expiryHTML}
            </div>
            <div style="display:flex;align-items:center;gap:6px;">
              ${!isExpired ? '<span style="font-size:0.75rem;color:var(--text-muted);">→ Edit</span>' : ''}
              <button class="btn-delete-card" data-delete-id="${d.id}" title="Delete draft">🗑</button>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Click handlers for cards (open editor) and delete buttons
    grid.querySelectorAll('.draft-card').forEach(card => {
      card.addEventListener('click', e => {
        if (e.target.closest('.btn-delete-card')) return; // handled separately
        openEditor(card.dataset.id);
      });
    });

    grid.querySelectorAll('.btn-delete-card').forEach(btn => {
      btn.addEventListener('click', async e => {
        e.stopPropagation();
        const draftId = btn.dataset.deleteId;
        const confirmed = await showConfirmModal({
          icon: '🗑',
          title: 'Delete this draft?',
          desc: 'This will permanently remove the draft from the system. This cannot be undone.',
          confirmLabel: 'Yes, Delete'
        });
        if (confirmed) await deleteDraft(draftId);
      });
    });

    // Live countdown tick for all expiry pills
    startCountdownTick();

  } catch (err) {
    toast('Failed to load dashboard: ' + err.message, 'error');
  }
}

// ====================================================
// COUNTDOWN TICKER
// ====================================================

let _tickInterval = null;

function startCountdownTick() {
  if (_tickInterval) clearInterval(_tickInterval);
  _tickInterval = setInterval(() => {
    document.querySelectorAll('.expiry-pill[data-expires]').forEach(pill => {
      const expiresAt = parseInt(pill.dataset.expires);
      const secondsLeft = Math.max(0, Math.round((expiresAt - Date.now()) / 1000));
      const soon = secondsLeft < 3600;
      pill.textContent = `⏱ ${formatCountdown(secondsLeft)}`;
      pill.className = `expiry-pill ${soon ? 'expiring-soon' : 'expiring-ok'}`;
      pill.dataset.expires = expiresAt; // preserve attribute
      if (secondsLeft === 0) loadDashboard(); // reload when one expires
    });
  }, 30000); // tick every 30s
}

// ====================================================
// DELETE DRAFT
// ====================================================

async function deleteDraft(draftId) {
  try {
    const result = await apiFetch(`/api/drafts/${draftId}`, { method: 'DELETE' });
    if (result.success) {
      toast('🗑 Draft deleted.', 'success');
      loadDashboard();
      // If currently editing this draft, go back
      if (currentDraft && currentDraft.id === draftId) {
        switchTab('dashboard');
        currentDraft = null;
      }
    } else {
      toast('Delete failed: ' + (result.error || 'Unknown'), 'error');
    }
  } catch (err) {
    toast('Error: ' + err.message, 'error');
  }
}

// ====================================================
// EXPIRE ABANDONED
// ====================================================

$('expireNowBtn').addEventListener('click', async () => {
  const btn = $('expireNowBtn');
  btn.textContent = 'Checking…';
  btn.disabled = true;
  try {
    const result = await apiFetch('/api/drafts/expire-abandoned', { method: 'POST' });
    const n = result.expired_count || 0;
    toast(n > 0 ? `⏰ ${n} draft(s) expired.` : 'No drafts to expire yet.', n > 0 ? 'success' : 'info');
    loadDashboard();
  } catch (err) {
    toast('Error: ' + err.message, 'error');
  } finally {
    btn.textContent = '⏰ Expire Abandoned';
    btn.disabled = false;
  }
});

// New draft via prompt
$('newDraftBtn').addEventListener('click', () => {
  openChatPanel();
  appendChatMessage('agent',
    '📝 Tell me the email details and I\'ll create a draft for you!\n\nExample:\n"Draft an email to john@example.com with subject Meeting Tomorrow about our project sync."'
  );
});

// ====================================================
// EDITOR
// ====================================================

let currentDraft = null;
let originalProposed = {};
let originalActual = {};

async function openEditor(draftId) {
  switchTab('editor');

  try {
    const draft = await apiFetch(`/api/drafts/${draftId}`);
    currentDraft = draft;

    const proposed = draft.proposed || {};
    const actual = draft.actual || proposed;  // fallback to proposed if not converted

    originalProposed = { ...proposed };
    originalActual = { ...actual };

    // Header info
    $('editorDraftId').textContent = `ID: ${draft.id}`;
    $('editorStatusBadge').innerHTML = statusBadgeHTML(draft.status);

    // Show expiry info for OPEN drafts in editor
    if (draft.status === 'OPEN' && draft.created_at) {
      const expiresAt = new Date(draft.created_at).getTime() + 24 * 3600 * 1000;
      const secondsLeft = Math.max(0, Math.round((expiresAt - Date.now()) / 1000));
      $('editorFeedback').textContent = secondsLeft > 0
        ? `⏱ Expires in ${formatCountdown(secondsLeft)} — convert to save it`
        : '⚠️ This draft has expired';
      $('editorFeedback').style.color = secondsLeft < 3600 ? 'var(--accent-amber)' : 'var(--text-muted)';
    } else {
      $('editorFeedback').textContent = '';
      $('editorFeedback').style.color = '';
    }

    // Original (proposed) panel
    $('orig-to').textContent = proposed.to || '—';
    $('orig-cc').textContent = proposed.cc || '—';
    $('orig-subject').textContent = proposed.subject || '—';
    $('orig-body').textContent = proposed.body || '—';

    // Editable panel — fill with actual if converted, else proposed
    $('edit-to').value = actual.to || proposed.to || '';
    $('edit-cc').value = actual.cc || proposed.cc || '';
    $('edit-subject').value = actual.subject || proposed.subject || '';
    $('edit-body').value = actual.body || proposed.body || '';

    // Show convert button only for OPEN drafts
    $('convertDraftBtn').style.display =
      draft.status === 'OPEN' ? 'inline-flex' : 'none';

    $('editorFeedback').style.cssText = '';
    updateLiveDiff();

  } catch (err) {
    toast('Failed to load draft: ' + err.message, 'error');
  }
}

// Live diff engine — runs on every keystroke
function updateLiveDiff() {
  if (!currentDraft) return;

  const proposed = originalProposed;
  const fields = ['to', 'cc', 'subject', 'body'];
  let changedCount = 0;
  const diffs = [];

  fields.forEach(field => {
    const inputEl = $(`edit-${field}`);
    const origRowEl = $(`orig-${field}-row`);
    const editRowEl = $(`edit-${field}-row`);
    const currentVal = inputEl.value;
    const proposedVal = proposed[field] || '';

    const changed = currentVal !== proposedVal;
    if (changed) {
      changedCount++;
      diffs.push({ field, proposed: proposedVal, actual: currentVal });
      origRowEl.classList.add('field-changed');
      editRowEl.classList.add('field-changed');
    } else {
      origRowEl.classList.remove('field-changed');
      editRowEl.classList.remove('field-changed');
    }
  });

  // Update counter badge
  const indicator = $('editChangedCount');
  if (changedCount > 0) {
    indicator.style.display = 'flex';
    $('changedCount').textContent = changedCount;
  } else {
    indicator.style.display = 'none';
  }

  // Update diff table
  const summaryEl = $('diffSummary');
  const tbody = $('diffTableBody');
  if (diffs.length > 0) {
    summaryEl.style.display = 'block';
    tbody.innerHTML = diffs.map(d => `
      <tr>
        <td>${d.field}</td>
        <td class="diff-old">${truncate(d.proposed, 60) || '(empty)'}</td>
        <td class="diff-new">${truncate(d.actual, 60) || '(empty)'}</td>
      </tr>
    `).join('');
  } else {
    summaryEl.style.display = 'none';
  }
}

// Wire up live diff on all edit inputs
['to', 'cc', 'subject', 'body'].forEach(field => {
  const el = $(`edit-${field}`);
  if (el) el.addEventListener('input', updateLiveDiff);
});

// Reset editor to original
$('resetEditBtn').addEventListener('click', () => {
  if (!currentDraft) return;
  const actual = currentDraft.actual || currentDraft.proposed || {};
  const proposed = currentDraft.proposed || {};
  $('edit-to').value = actual.to || proposed.to || '';
  $('edit-cc').value = actual.cc || proposed.cc || '';
  $('edit-subject').value = actual.subject || proposed.subject || '';
  $('edit-body').value = actual.body || proposed.body || '';
  updateLiveDiff();
  toast('Reset to original values', 'info');
});

// Submit Edit
$('submitEditBtn').addEventListener('click', async () => {
  if (!currentDraft) return;

  const status = currentDraft.status;

  if (status === 'OPEN') {
    toast('This draft is OPEN — click \"⚡ Convert Draft\" below first, then save your edits.', 'error');
    $('convertDraftBtn').style.animation = 'none';
    setTimeout(() => { $('convertDraftBtn').style.animation = ''; }, 100);
    $('convertDraftBtn').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  const proposed = originalProposed;
  const changes = {};
  ['to', 'cc', 'subject', 'body'].forEach(field => {
    const val = $(`edit-${field}`).value;
    if (val !== (proposed[field] || '')) {
      changes[field] = val;
    }
  });

  if (Object.keys(changes).length === 0) {
    toast('No changes detected.', 'info');
    return;
  }

  const btn = $('submitEditBtn');
  btn.innerHTML = '<span class="spinner"></span> Saving…';
  btn.disabled = true;

  try {
    const result = await apiFetch(`/api/drafts/${currentDraft.id}/edit`, {
      method: 'POST',
      body: JSON.stringify({ changes })
    });

    if (result.success) {
      toast('✅ Edit saved! Agent is learning from your changes.', 'success');
      // Update currentDraft fully so next save works without reload
      currentDraft.status = result.status;
      currentDraft.actual = result.actual;
      currentDraft.diff = result.diff;
      $('editorStatusBadge').innerHTML = statusBadgeHTML(result.status);
      // Keep convert button hidden since draft is now converted
      $('convertDraftBtn').style.display = 'none';
      originalActual = { ...(result.actual || {}) };
      updateLiveDiff();
    } else {
      toast('❌ Edit failed: ' + (result.error || 'Unknown error'), 'error');
    }
  } catch (err) {
    toast('Error: ' + err.message, 'error');
  } finally {
    btn.innerHTML = '💾 Save Edit + Learn';
    btn.disabled = false;
  }
});

// Convert Draft
$('convertDraftBtn').addEventListener('click', async () => {
  if (!currentDraft) return;

  const btn = $('convertDraftBtn');
  btn.innerHTML = '<span class="spinner"></span> Converting…';
  btn.disabled = true;

  try {
    const result = await apiFetch(`/api/drafts/${currentDraft.id}/convert`, {
      method: 'POST',
      body: JSON.stringify({})
    });

    if (result.success) {
      toast('✅ Draft converted! You can now edit and save.', 'success');
      // Re-fetch and refresh editor so status check reflects CONVERTED
      const draftId = currentDraft.id;
      await openEditor(draftId);
    } else {
      toast('❌ Conversion failed: ' + (result.error || 'Unknown'), 'error');
    }
  } catch (err) {
    toast('Error: ' + err.message, 'error');
  } finally {
    btn.innerHTML = '⚡ Convert Draft';
    btn.disabled = false;
  }
});

$('editorBackBtn').addEventListener('click', () => switchTab('dashboard'));

// Delete draft from editor
$('deleteDraftBtn').addEventListener('click', async () => {
  if (!currentDraft) return;
  const confirmed = await showConfirmModal({
    icon: '🗑',
    title: 'Delete this draft?',
    desc: `Draft to: ${currentDraft.proposed?.to || '—'}\nThis cannot be undone.`,
    confirmLabel: 'Yes, Delete'
  });
  if (confirmed) await deleteDraft(currentDraft.id);
});

// ====================================================
// ANALYTICS
// ====================================================

async function loadAnalytics() {
  try {
    const [report, drafts] = await Promise.all([
      apiFetch('/api/report'),
      apiFetch('/api/drafts')
    ]);

    $('aStatTotal').textContent = report.total_drafts;
    $('aStatConv').textContent = report.conversion_rate + '%';
    $('aStatEdit').textContent = report.edit_rate + '%';
    const mins = (report.average_time_to_convert_seconds / 60).toFixed(1);
    $('aStatTime').textContent = mins;

    drawStatusChart(drafts);
    drawRateChart(report);

  } catch (err) {
    toast('Failed to load analytics: ' + err.message, 'error');
  }
}

$('refreshAnalyticsBtn').addEventListener('click', loadAnalytics);

function drawStatusChart(drafts) {
  const canvas = $('statusChart');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const counts = { OPEN: 0, CONVERTED: 0, CONVERTED_EDITED: 0, EXPIRED: 0 };
  drafts.forEach(d => { if (d.status in counts) counts[d.status]++; });

  const total = drafts.length || 1;
  const colors = {
    OPEN: '#3b82f6',
    CONVERTED: '#10b981',
    CONVERTED_EDITED: '#f59e0b',
    EXPIRED: '#ef4444'
  };
  const labels = {
    OPEN: 'Open',
    CONVERTED: 'Converted',
    CONVERTED_EDITED: 'Conv+Edit',
    EXPIRED: 'Expired'
  };

  // Donut chart
  const cx = 140, cy = H / 2, r = 95, inner = 50;
  let startAngle = -Math.PI / 2;

  Object.entries(counts).forEach(([key, val]) => {
    const slice = (val / total) * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, startAngle, startAngle + slice);
    ctx.closePath();
    ctx.fillStyle = colors[key];
    ctx.fill();
    startAngle += slice;
  });

  // Inner hole
  ctx.beginPath();
  ctx.arc(cx, cy, inner, 0, 2 * Math.PI);
  ctx.fillStyle = '#0d1117';
  ctx.fill();

  // Center text
  ctx.fillStyle = '#f1f5f9';
  ctx.font = 'bold 28px Inter';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(total, cx, cy - 6);
  ctx.font = '11px Inter';
  ctx.fillStyle = '#94a3b8';
  ctx.fillText('drafts', cx, cy + 14);

  // Legend
  let lx = 300, ly = 60;
  Object.entries(counts).forEach(([key, val]) => {
    ctx.fillStyle = colors[key];
    ctx.fillRect(lx, ly, 12, 12);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '12px Inter';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(`${labels[key]}: ${val}`, lx + 18, ly);
    ly += 28;
  });
}

function drawRateChart(report) {
  const canvas = $('rateChart');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const metrics = [
    { label: 'Conversion Rate', value: report.conversion_rate, color: '#10b981' },
    { label: 'Edit Rate', value: report.edit_rate, color: '#f59e0b' },
    { label: 'Expiration Rate', value: report.expiration_rate, color: '#ef4444' },
    { label: 'Post-Conv Edit', value: report.post_conversion_edit_rate, color: '#7c3aed' },
  ];

  const barH = 32, gap = 20, startY = 30, labelW = 130;
  const maxVal = 100;
  const barMaxW = W - labelW - 80;

  metrics.forEach((m, i) => {
    const y = startY + i * (barH + gap);
    const barW = (m.value / maxVal) * barMaxW;

    // Label
    ctx.fillStyle = '#94a3b8';
    ctx.font = '12px Inter';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(m.label, labelW, y + barH / 2);

    // Background bar
    ctx.fillStyle = 'rgba(255,255,255,0.05)';
    ctx.beginPath();
    ctx.roundRect(labelW + 10, y, barMaxW, barH, 6);
    ctx.fill();

    // Value bar
    if (barW > 0) {
      const grad = ctx.createLinearGradient(labelW + 10, 0, labelW + 10 + barW, 0);
      grad.addColorStop(0, m.color + 'cc');
      grad.addColorStop(1, m.color);
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.roundRect(labelW + 10, y, barW, barH, 6);
      ctx.fill();
    }

    // Value label
    ctx.fillStyle = '#f1f5f9';
    ctx.font = 'bold 13px Inter';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(m.value + '%', labelW + 10 + barW + 8, y + barH / 2);
  });
}

// ====================================================
// AI MEMORY
// ====================================================

async function loadMemory() {
  try {
    const memory = await apiFetch('/api/memory');
    const edits = memory.edits || [];
    const patterns = memory.patterns || 'No patterns yet.';

    $('patternsBox').textContent = patterns;
    $('patternsEditCount').textContent = `Based on ${edits.length} recorded edit(s).`;

    // Edit log
    const log = $('editLog');
    if (!edits.length) {
      log.innerHTML = `<div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <div class="empty-state-text">No edits recorded yet. Edit a converted draft to see learning in action.</div>
      </div>`;
    } else {
      log.innerHTML = [...edits].reverse().map(e => {
        const changedFields = Object.keys(e.diff || e.changes || {});
        return `
          <div class="edit-log-item">
            <div class="edit-log-meta">
              <span class="edit-log-id">${e.draft_id.slice(0, 16)}…</span>
              <span class="edit-log-time">${formatDate(e.timestamp)}</span>
            </div>
            <div class="edit-log-changes">
              Fields changed: <strong style="color:var(--accent-amber)">${changedFields.join(', ') || 'none'}</strong>
            </div>
          </div>
        `;
      }).join('');
    }

    // Field frequency chart
    const fieldCounts = {};
    edits.forEach(e => {
      Object.keys(e.diff || e.changes || {}).forEach(f => {
        fieldCounts[f] = (fieldCounts[f] || 0) + 1;
      });
    });
    drawFieldsChart(fieldCounts);

  } catch (err) {
    toast('Failed to load memory: ' + err.message, 'error');
  }
}

$('refreshPatternsBtn').addEventListener('click', async () => {
  const btn = $('refreshPatternsBtn');
  btn.innerHTML = '<span class="spinner"></span> Analyzing…';
  btn.disabled = true;

  try {
    const result = await apiFetch('/api/memory/refresh', { method: 'POST' });
    $('patternsBox').textContent = result.patterns;
    toast('Patterns re-analyzed by AI!', 'success');
  } catch (err) {
    toast('Failed: ' + err.message, 'error');
  } finally {
    btn.innerHTML = '🔄 Re-analyze Patterns';
    btn.disabled = false;
  }
});

function drawFieldsChart(fieldCounts) {
  const canvas = $('fieldsChart');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const fields = Object.entries(fieldCounts).sort((a, b) => b[1] - a[1]);
  if (!fields.length) {
    ctx.fillStyle = '#475569';
    ctx.font = '13px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('No edit data yet.', W / 2, H / 2);
    return;
  }

  const maxVal = Math.max(...fields.map(f => f[1]));
  const barW = Math.min(80, (W - 40) / fields.length - 16);
  const colors = ['#7c3aed', '#06b6d4', '#10b981', '#f59e0b'];
  const chartH = H - 50;

  fields.forEach(([field, count], i) => {
    const x = 20 + i * (barW + 16);
    const bH = (count / maxVal) * (chartH - 20);
    const y = chartH - bH;

    const grad = ctx.createLinearGradient(0, y, 0, chartH);
    grad.addColorStop(0, colors[i % colors.length]);
    grad.addColorStop(1, colors[i % colors.length] + '44');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.roundRect(x, y, barW, bH, 6);
    ctx.fill();

    ctx.fillStyle = '#f1f5f9';
    ctx.font = 'bold 13px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText(count, x + barW / 2, y - 4);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '12px Inter';
    ctx.textBaseline = 'top';
    ctx.fillText(field, x + barW / 2, chartH + 8);
  });
}

// ====================================================
// CHAT PANEL
// ====================================================

function openChatPanel() {
  $('chatPanel').classList.add('open');
  $('chatOverlay').classList.add('open');
  setTimeout(() => $('chatInput').focus(), 300);
}

function closeChatPanel() {
  $('chatPanel').classList.remove('open');
  $('chatOverlay').classList.remove('open');
}

$('chatToggleBtn').addEventListener('click', openChatPanel);
$('chatCloseBtn').addEventListener('click', closeChatPanel);
$('chatOverlay').addEventListener('click', closeChatPanel);

function appendChatMessage(role, content, isToolCall = false) {
  const messages = $('chatMessages');
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;

  if (isToolCall) {
    div.innerHTML = `<div class="chat-tool-call">⚙️ ${content}</div>`;
  } else {
    div.innerHTML = `
      <div class="chat-msg-role">${role === 'user' ? 'You' : 'Agent'}</div>
      <div class="chat-bubble">${content.replace(/\n/g, '<br>')}</div>
    `;
  }

  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function showTypingIndicator() {
  const messages = $('chatMessages');
  const div = document.createElement('div');
  div.className = 'chat-msg agent';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="chat-msg-role">Agent</div>
    <div class="chat-typing">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function removeTypingIndicator() {
  const el = $('typingIndicator');
  if (el) el.remove();
}

async function sendChatMessage() {
  const input = $('chatInput');
  const msg = input.value.trim();
  if (!msg) return;

  input.value = '';
  input.style.height = 'auto';

  appendChatMessage('user', msg);
  showTypingIndicator();

  try {
    const data = await apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message: msg })
    });
    removeTypingIndicator();
    appendChatMessage('agent', data.reply);

    // Refresh dashboard in background after agent actions
    loadDashboard();

  } catch (err) {
    removeTypingIndicator();
    appendChatMessage('agent', `❌ Error: ${err.message}`);
  }
}

$('chatSendBtn').addEventListener('click', sendChatMessage);
$('chatInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
});

// Auto-resize chat textarea
$('chatInput').addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// ====================================================
// BOOTSTRAP
// ====================================================

loadDashboard();
