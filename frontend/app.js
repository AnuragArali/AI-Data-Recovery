const state = {
  files: [],
  analysis: null,
  chatHistory: [],
};

const elements = {
  fileInput: document.querySelector('#fileInput'),
  dropZone: document.querySelector('#dropZone'),
  browseButton: document.querySelector('#browseButton'),
  fileCount: document.querySelector('#fileCount'),
  emptyQueue: document.querySelector('#emptyQueue'),
  fileQueue: document.querySelector('#fileQueue'),
  clearButton: document.querySelector('#clearButton'),
  analyzeButton: document.querySelector('#analyzeButton'),
  uploadStatus: document.querySelector('#uploadStatus'),
  findings: document.querySelector('#findings'),
  investigator: document.querySelector('#investigator'),
  resultPill: document.querySelector('#resultPill'),
  resultSummary: document.querySelector('#resultSummary'),
  orderConfidence: document.querySelector('#orderConfidence'),
  orderDescription: document.querySelector('#orderDescription'),
  fragmentSequence: document.querySelector('#fragmentSequence'),
  unmatchedFragments: document.querySelector('#unmatchedFragments'),
  integrityBadge: document.querySelector('#integrityBadge'),
  integrityDetails: document.querySelector('#integrityDetails'),
  inventoryCount: document.querySelector('#inventoryCount'),
  inventoryBody: document.querySelector('#inventoryBody'),
  explanationText: document.querySelector('#explanationText'),
  priorityReasons: document.querySelector('#priorityReasons'),
  rawJson: document.querySelector('#rawJson'),
  copyJsonButton: document.querySelector('#copyJsonButton'),
  copyState: document.querySelector('#copyState'),
  questionForm: document.querySelector('#questionForm'),
  questionInput: document.querySelector('#questionInput'),
  askButton: document.querySelector('#askButton'),
  chatMessages: document.querySelector('#chatMessages'),
  assistantMode: document.querySelector('#assistantMode'),
  healthDot: document.querySelector('#healthDot'),
  healthText: document.querySelector('#healthText'),
};

function makeElement(tag, options = {}) {
  const node = document.createElement(tag);

  if (options.className) node.className = options.className;
  if (options.text !== undefined) node.textContent = options.text;
  if (options.title) node.title = options.title;

  return node;
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes < 1) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / (1024 ** index);
  return `${value >= 10 || index === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[index]}`;
}

function formatPercent(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : '—';
}

function normalise(value, fallback = 'UNKNOWN') {
  if (value === undefined || value === null || value === '') return fallback;
  return String(value).replaceAll('_', ' ');
}

function statusClass(value) {
  const upper = String(value || '').toUpperCase();
  if (['VALID', 'SUCCESS', 'RECOVERED', 'LOW', 'ORDERED'].includes(upper)) return 'good';
  if (['PARTIALLY VALID', 'PARTIALLY_VALID', 'MEDIUM', 'PARTIAL ORDER', 'PARTIAL_ORDER'].includes(upper)) return 'warning';
  if (['INVALID', 'FAILED', 'HIGH', 'ERROR'].includes(upper)) return 'bad';
  return '';
}

function setUploadStatus(message = '', type = '') {
  elements.uploadStatus.textContent = message;
  elements.uploadStatus.className = `status-message ${type}`.trim();
}

function updateQueue() {
  const count = state.files.length;
  elements.fileCount.textContent = `${count} ${count === 1 ? 'FILE' : 'FILES'}`;
  elements.emptyQueue.hidden = count > 0;
  elements.fileQueue.replaceChildren();

  for (const file of state.files) {
    const item = makeElement('li', { className: 'file-item' });
    const icon = makeElement('span', { className: 'file-icon', text: 'BIN' });
    const name = makeElement('span', { className: 'file-name', text: file.name, title: file.name });
    const size = makeElement('span', { className: 'file-size', text: formatBytes(file.size) });
    item.append(icon, name, size);
    elements.fileQueue.append(item);
  }

  elements.clearButton.disabled = count === 0;
  elements.analyzeButton.disabled = count === 0;
}

function setFiles(files) {
  state.files = files.filter((file) => file && file.size > 0);
  setUploadStatus(
    state.files.length ? `${state.files.length} file${state.files.length === 1 ? '' : 's'} ready for analysis.` : '',
  );
  updateQueue();
}

function clearSelection() {
  state.files = [];
  elements.fileInput.value = '';
  setUploadStatus('Selection cleared. This does not delete evidence already held by the service.');
  updateQueue();
}

function setAnalysisBusy(isBusy) {
  elements.analyzeButton.disabled = isBusy || state.files.length === 0;
  elements.clearButton.disabled = isBusy || state.files.length === 0;
  elements.analyzeButton.querySelector('span').textContent = isBusy ? 'Analyzing evidence…' : 'Analyze evidence';
}

function showMetric(label, value, note, tone = '') {
  const metric = makeElement('article', { className: 'metric' });
  metric.append(
    makeElement('div', { className: 'metric-label', text: label }),
    makeElement('div', { className: `metric-value ${tone}`.trim(), text: value }),
    makeElement('div', { className: 'metric-note', text: note }),
  );
  return metric;
}

function renderMetrics(data) {
  const investigation = data.investigation || {};
  const reconstruction = data.reconstruction || {};
  const integrity = reconstruction.integrity || {};
  const order = data.fragment_order || reconstruction.order || {};
  const priority = reconstruction.priority || {};
  const status = normalise(investigation.reconstruction_status, reconstruction.success ? 'SUCCESS' : 'FAILED');

  elements.resultSummary.replaceChildren(
    showMetric('RECOVERY STATUS', status, normalise(investigation.status), statusClass(status)),
    showMetric('ARTIFACT TYPE', normalise(investigation.file_type), normalise(investigation.artifact_category)),
    showMetric('ORDERING CONFIDENCE', formatPercent(investigation.ordering_confidence ?? order.confidence), `${investigation.fragments_used ?? 0} fragments used`, 'teal'),
    showMetric('PRIORITY SCORE', `${priority.priority_score ?? investigation.priority_score ?? 0}/100`, normalise(priority.priority ?? investigation.priority), 'amber'),
  );

  elements.resultPill.textContent = status;
  elements.resultPill.className = `result-pill ${status === 'FAILED' ? 'failed' : ''}`.trim();

  return { investigation, reconstruction, integrity, order, priority };
}

function renderOrder(order) {
  const ordered = Array.isArray(order.ordered_fragments) ? order.ordered_fragments : [];
  const remaining = Array.isArray(order.remaining_fragments) ? order.remaining_fragments : [];
  const status = normalise(order.status, 'NO ORDER');

  elements.orderConfidence.textContent = `CONFIDENCE ${formatPercent(order.confidence)}`;
  elements.orderDescription.textContent = ordered.length
    ? `${status}: the engine selected this sequence from the available relationships.`
    : 'No fragment sequence could be determined from the supplied evidence.';
  elements.fragmentSequence.replaceChildren();

  ordered.forEach((filename, index) => {
    const node = makeElement('span', { className: 'fragment-node', text: filename, title: filename });
    elements.fragmentSequence.append(node);
    if (index < ordered.length - 1) elements.fragmentSequence.append(makeElement('span', { className: 'sequence-arrow', text: '→' }));
  });

  elements.unmatchedFragments.hidden = remaining.length === 0;
  elements.unmatchedFragments.textContent = remaining.length
    ? `Not included in sequence: ${remaining.join(', ')}`
    : '';
}

function renderIntegrity(integrity) {
  const integrityStatus = normalise(integrity.integrity_status);
  const dataPoints = [
    ['INTEGRITY', integrityStatus],
    ['CORRUPTION', normalise(integrity.corruption_status)],
    ['FILE READABLE', integrity.file_readable ? 'YES' : 'NO'],
    ['FORMAT VALID', integrity.format_valid ? 'YES' : 'NO'],
  ];

  elements.integrityBadge.textContent = integrityStatus;
  elements.integrityBadge.className = `mini-badge ${statusClass(integrityStatus)}`.trim();
  elements.integrityDetails.replaceChildren();

  dataPoints.forEach(([label, value]) => {
    const item = makeElement('div', { className: 'integrity-item' });
    item.append(
      makeElement('span', { text: label }),
      makeElement('b', { text: value }),
    );
    elements.integrityDetails.append(item);
  });
}

function renderInventory(files) {
  elements.inventoryBody.replaceChildren();
  const records = Array.isArray(files) ? files : [];
  elements.inventoryCount.textContent = `${records.length} ${records.length === 1 ? 'FILE' : 'FILES'}`;

  for (const file of records) {
    const row = document.createElement('tr');
    const details = [
      normalise(file.filename, 'Unnamed file'),
      normalise(file.detected_format),
      normalise(file.fragment_type),
      formatBytes(Number(file.size_bytes)),
    ];
    details.forEach((value, index) => {
      const cell = document.createElement('td');
      cell.textContent = value;
      if (index === 2) cell.className = 'role-tag';
      row.append(cell);
    });
    elements.inventoryBody.append(row);
  }
}

function renderExplanation(investigation, priority) {
  elements.explanationText.textContent = investigation.explanation || 'No investigator summary was returned by the analysis service.';
  elements.priorityReasons.replaceChildren();
  const reasons = Array.isArray(priority.reasons) ? priority.reasons : [];
  reasons.forEach((reason) => elements.priorityReasons.append(makeElement('span', { className: 'reason', text: reason })));
}

function displayAnalysis(data) {
  state.analysis = data;
  state.chatHistory = [];
  resetChatMessages();
  const { investigation, integrity, order, priority } = renderMetrics(data);
  renderOrder(order);
  renderIntegrity(integrity);
  renderInventory(data.files);
  renderExplanation(investigation, priority);
  elements.rawJson.textContent = JSON.stringify(data, null, 2);
  elements.findings.hidden = false;
  elements.investigator.hidden = false;
  elements.assistantMode.textContent = 'CONTEXT READY';
  elements.findings.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return response.json();
  return { detail: await response.text() };
}

async function analyzeEvidence() {
  if (!state.files.length) return;

  const formData = new FormData();
  state.files.forEach((file) => formData.append('files', file));
  setAnalysisBusy(true);
  setUploadStatus('Uploading fragment set and running the recovery workflow…', 'loading');

  try {
    const response = await fetch('/api/evidence/upload', { method: 'POST', body: formData });
    const data = await parseResponse(response);
    if (!response.ok) throw new Error(data.detail || 'The evidence service could not analyze this set.');

    setUploadStatus(data.message || 'Evidence set analyzed successfully.', 'success');
    displayAnalysis(data);
  } catch (error) {
    setUploadStatus(error.message || 'The evidence service could not be reached.', 'error');
  } finally {
    setAnalysisBusy(false);
  }
}

function appendChatMessage(text, role = 'assistant') {
  const message = makeElement('div', { className: `chat-message ${role}-message` });
  message.append(
    makeElement('span', { className: 'message-label', text: role === 'user' ? 'YOU' : 'ANALYST' }),
    makeElement('p', { text }),
  );
  elements.chatMessages.append(message);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function resetChatMessages() {
  const message = makeElement('div', { className: 'chat-message assistant-message' });
  message.append(
    makeElement('span', { className: 'message-label', text: 'ANALYST' }),
    makeElement('p', {
      text: 'Ask about the fragment order, markers, integrity, recovery, or priority. I retain the recent conversation and ground every answer in the active evidence set.',
    }),
  );
  elements.chatMessages.replaceChildren(message);
}

function rememberChatMessage(content, role) {
  state.chatHistory.push({ role, content: String(content).slice(0, 600) });
  state.chatHistory = state.chatHistory.slice(-6);
}

async function askInvestigator(event) {
  event.preventDefault();
  const question = elements.questionInput.value.trim();
  if (!question || !state.analysis) return;

  appendChatMessage(question, 'user');
  rememberChatMessage(question, 'user');
  elements.questionInput.value = '';
  elements.askButton.disabled = true;
  elements.askButton.textContent = 'Thinking…';
  elements.assistantMode.textContent = 'ANALYZING CONTEXT';

  try {
    const history = encodeURIComponent(JSON.stringify(state.chatHistory.slice(0, -1)));
    const response = await fetch(`/api/evidence/ask?question=${encodeURIComponent(question)}&history=${history}`, { method: 'POST' });
    const data = await parseResponse(response);
    if (!response.ok) throw new Error(data.detail || 'The investigator could not answer that question.');

    const answer = data.answer || 'No answer was returned for this question.';
    appendChatMessage(answer);
    rememberChatMessage(answer, 'assistant');
    elements.assistantMode.textContent = data.ai_generated ? 'AI-GENERATED RESPONSE' : 'EVIDENCE-GROUNDED RESPONSE';
  } catch (error) {
    appendChatMessage(`Unable to answer: ${error.message}`);
    elements.assistantMode.textContent = 'RESPONSE UNAVAILABLE';
  } finally {
    elements.askButton.disabled = false;
    elements.askButton.innerHTML = 'Ask <span aria-hidden="true">↗</span>';
    elements.questionInput.focus();
  }
}

async function copyRecord() {
  if (!state.analysis) return;
  const record = JSON.stringify(state.analysis, null, 2);

  try {
    await navigator.clipboard.writeText(record);
    elements.copyState.textContent = 'Copied';
  } catch {
    elements.copyState.textContent = 'Copy unavailable';
  }

  window.setTimeout(() => { elements.copyState.textContent = ''; }, 1800);
}

async function checkHealth() {
  try {
    const response = await fetch('/health', { cache: 'no-store' });
    const data = await parseResponse(response);
    if (!response.ok || data.status !== 'healthy') throw new Error();
    elements.healthDot.className = 'status-dot healthy';
    elements.healthText.textContent = 'Analysis service online';
  } catch {
    elements.healthDot.className = 'status-dot unhealthy';
    elements.healthText.textContent = 'Analysis service unavailable';
  }
}

elements.fileInput.addEventListener('change', (event) => setFiles([...event.target.files]));
elements.browseButton.addEventListener('click', (event) => {
  event.stopPropagation();
  elements.fileInput.click();
});
elements.dropZone.addEventListener('click', (event) => {
  if (!event.target.closest('button')) elements.fileInput.click();
});
elements.dropZone.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    elements.fileInput.click();
  }
});
['dragenter', 'dragover'].forEach((eventName) => elements.dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  elements.dropZone.classList.add('dragging');
}));
['dragleave', 'drop'].forEach((eventName) => elements.dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  elements.dropZone.classList.remove('dragging');
}));
elements.dropZone.addEventListener('drop', (event) => setFiles([...event.dataTransfer.files]));
elements.clearButton.addEventListener('click', clearSelection);
elements.analyzeButton.addEventListener('click', analyzeEvidence);
elements.questionForm.addEventListener('submit', askInvestigator);
elements.copyJsonButton.addEventListener('click', copyRecord);

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    document.querySelectorAll('.workflow-step').forEach((link) => link.classList.toggle('active', link.getAttribute('href') === `#${entry.target.id}`));
  });
}, { rootMargin: '-40% 0px -55% 0px' });

['intake', 'findings', 'investigator'].forEach((id) => observer.observe(document.querySelector(`#${id}`)));

updateQueue();
checkHealth();
