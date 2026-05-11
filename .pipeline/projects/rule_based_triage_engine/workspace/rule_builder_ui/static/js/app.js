/** Rule Builder UI — Client-side application logic */

const API_BASE = '/rules';

// State
let rules = [];
let currentRuleId = null;
let dirty = false;

// DOM refs
const ruleListEl = document.getElementById('rule-list');
const editorBody = document.getElementById('editor-body');
const emptyState = document.getElementById('empty-state');
const editorTitle = document.getElementById('editor-title');
const btnSave = document.getElementById('btn-save');
const btnDelete = document.getElementById('btn-delete');
const btnDuplicate = document.getElementById('btn-duplicate');
const ruleNameInput = document.getElementById('rule-name');
const rulePriorityInput = document.getElementById('rule-priority');
const priorityValueEl = document.getElementById('priority-value');
const ruleEnabledInput = document.getElementById('rule-enabled');
const conditionsList = document.getElementById('conditions-list');
const actionsList = document.getElementById('actions-list');
const importModal = document.getElementById('import-modal');
const importTextarea = document.getElementById('import-textarea');

// ── API helpers ──

async function fetchRules() {
    const resp = await fetch(API_BASE);
    if (!resp.ok) throw new Error(`GET ${API_BASE} failed: ${resp.statusText}`);
    return resp.json();
}

async function createRule(data) {
    const resp = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.error || `POST ${API_BASE} failed: ${resp.statusText}`);
    }
    return resp.json();
}

async function updateRule(id, data) {
    const resp = await fetch(`${API_BASE}/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.error || `PUT ${API_BASE}/${id} failed: ${resp.statusText}`);
    }
    return resp.json();
}

async function deleteRule(id) {
    const resp = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' });
    if (!resp.ok && resp.status !== 204) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.error || `DELETE ${API_BASE}/${id} failed: ${resp.statusText}`);
    }
}

async function importRules(data) {
    const resp = await fetch(`${API_BASE}/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.error || 'Import failed');
    }
    return resp.json();
}

// ── Rendering ──

function renderRuleList() {
    ruleListEl.innerHTML = '';
    rules.forEach(rule => {
        const div = document.createElement('div');
        div.className = 'rule-item' + (rule.id === currentRuleId ? ' active' : '');
        div.innerHTML = `
            <div class="rule-item-info" data-id="${rule.id}">
                <div class="rule-item-name">${escapeHtml(rule.name)}</div>
                <div class="rule-item-meta">Priority: ${rule.priority} · ${rule.enabled ? 'Enabled' : 'Disabled'}</div>
            </div>
            <div class="rule-item-actions">
                <button class="dup-btn" data-id="${rule.id}" title="Duplicate">⧉</button>
                <button class="del-btn" data-id="${rule.id}" title="Delete">✕</button>
            </div>
        `;
        ruleListEl.appendChild(div);
    });
}

function renderEditor(rule) {
    if (!rule) {
        editorBody.classList.remove('visible');
        emptyState.style.display = 'flex';
        editorTitle.textContent = 'Rule Editor';
        btnSave.disabled = true;
        btnDelete.disabled = true;
        btnDuplicate.disabled = true;
        return;
    }

    emptyState.style.display = 'none';
    editorBody.classList.add('visible');
    editorTitle.textContent = rule.name || 'New Rule';
    btnSave.disabled = false;
    btnDelete.disabled = false;
    btnDuplicate.disabled = false;

    ruleNameInput.value = rule.name || '';
    rulePriorityInput.value = rule.priority ?? 50;
    priorityValueEl.textContent = rule.priority ?? 50;
    ruleEnabledInput.checked = rule.enabled !== false;

    renderConditions(rule.conditions || []);
    renderActions(rule.actions || []);
    clearValidationErrors();
}

function renderConditions(conditions) {
    conditionsList.innerHTML = '';
    conditions.forEach((cond, i) => {
        conditionsList.appendChild(createConditionRow(cond, i));
    });
}

function renderActions(actions) {
    actionsList.innerHTML = '';
    actions.forEach((action, i) => {
        actionsList.appendChild(createActionRow(action, i));
    });
}

function createConditionRow(cond, index) {
    const row = document.createElement('div');
    row.className = 'condition-row';
    row.innerHTML = `
        <select class="cond-field">
            <option value="subject" ${cond.field === 'subject' ? 'selected' : ''}>subject</option>
            <option value="from" ${cond.field === 'from' ? 'selected' : ''}>from</option>
            <option value="body" ${cond.field === 'body' ? 'selected' : ''}>body</option>
            <option value="has_attachment" ${cond.field === 'has_attachment' ? 'selected' : ''}>has_attachment</option>
            <option value="priority_header" ${cond.field === 'priority_header' ? 'selected' : ''}>priority_header</option>
        </select>
        <select class="cond-operator">
            <option value="contains" ${cond.operator === 'contains' ? 'selected' : ''}>contains</option>
            <option value="not_contains" ${cond.operator === 'not_contains' ? 'selected' : ''}>not_contains</option>
            <option value="equals" ${cond.operator === 'equals' ? 'selected' : ''}>equals</option>
            <option value="regex" ${cond.operator === 'regex' ? 'selected' : ''}>regex</option>
            <option value="is_empty" ${cond.operator === 'is_empty' ? 'selected' : ''}>is_empty</option>
            <option value="gt" ${cond.operator === 'gt' ? 'selected' : ''}>gt</option>
            <option value="lt" ${cond.operator === 'lt' ? 'selected' : ''}>lt</option>
        </select>
        <input type="text" class="cond-value" placeholder="value" value="${escapeAttr(cond.value ?? '')}">
        <button class="remove-btn" title="Remove">✕</button>
    `;
    row.querySelector('.remove-btn').addEventListener('click', () => {
        row.remove();
        markDirty();
    });
    row.querySelectorAll('select, input').forEach(el => {
        el.addEventListener('input', markDirty);
        el.addEventListener('change', markDirty);
    });
    return row;
}

function createActionRow(action, index) {
    const row = document.createElement('div');
    row.className = 'action-row';
    row.innerHTML = `
        <select class="act-type">
            <option value="set_priority" ${action.type === 'set_priority' ? 'selected' : ''}>set_priority</option>
            <option value="assign_category" ${action.type === 'assign_category' ? 'selected' : ''}>assign_category</option>
            <option value="notify" ${action.type === 'notify' ? 'selected' : ''}>notify</option>
            <option value="forward" ${action.type === 'forward' ? 'selected' : ''}>forward</option>
            <option value="auto_resolve" ${action.type === 'auto_resolve' ? 'selected' : ''}>auto_resolve</option>
        </select>
        <input type="text" class="act-value" placeholder="value" value="${escapeAttr(action.value ?? '')}">
        <button class="remove-btn" title="Remove">✕</button>
    `;
    row.querySelector('.remove-btn').addEventListener('click', () => {
        row.remove();
        markDirty();
    });
    row.querySelectorAll('select, input').forEach(el => {
        el.addEventListener('input', markDirty);
        el.addEventListener('change', markDirty);
    });
    return row;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function clearValidationErrors() {
    document.getElementById('error-name').textContent = '';
    document.getElementById('error-conditions').textContent = '';
    document.getElementById('error-actions').textContent = '';
}

function markDirty() {
    dirty = true;
    btnSave.disabled = false;
}

// ── Collect form data ──

function collectFormData() {
    const conditions = [];
    conditionsList.querySelectorAll('.condition-row').forEach(row => {
        conditions.push({
            field: row.querySelector('.cond-field').value,
            operator: row.querySelector('.cond-operator').value,
            value: row.querySelector('.cond-value').value
        });
    });

    const actions = [];
    actionsList.querySelectorAll('.action-row').forEach(row => {
        actions.push({
            type: row.querySelector('.act-type').value,
            value: row.querySelector('.act-value').value
        });
    });

    return {
        name: ruleNameInput.value.trim(),
        priority: parseInt(rulePriorityInput.value, 10),
        enabled: ruleEnabledInput.checked,
        conditions,
        actions
    };
}

// ── Event handlers ──

async function loadRules() {
    try {
        rules = await fetchRules();
        renderRuleList();
    } catch (err) {
        alert('Failed to load rules: ' + err.message);
    }
}

async function handleSave() {
    const data = collectFormData();
    const name = ruleNameInput.value.trim();
    if (!name) {
        document.getElementById('error-name').textContent = 'Rule name is required.';
        return;
    }

    try {
        if (currentRuleId) {
            data.id = currentRuleId;
            const updated = await updateRule(currentRuleId, data);
            const idx = rules.findIndex(r => r.id === currentRuleId);
            if (idx !== -1) rules[idx] = updated;
        } else {
            const created = await createRule(data);
            rules.push(created);
            currentRuleId = created.id;
        }
        dirty = false;
        btnSave.disabled = true;
        renderRuleList();
        renderEditor(rules.find(r => r.id === currentRuleId));
    } catch (err) {
        alert('Save failed: ' + err.message);
    }
}

async function handleDelete() {
    if (!currentRuleId) return;
    if (!confirm('Delete this rule?')) return;
    try {
        await deleteRule(currentRuleId);
        rules = rules.filter(r => r.id !== currentRuleId);
        currentRuleId = null;
        renderRuleList();
        renderEditor(null);
    } catch (err) {
        alert('Delete failed: ' + err.message);
    }
}

async function handleDuplicate() {
    const rule = rules.find(r => r.id === currentRuleId);
    if (!rule) return;
    const data = collectFormData();
    data.name = data.name + ' (copy)';
    try {
        const created = await createRule(data);
        rules.push(created);
        currentRuleId = created.id;
        renderRuleList();
        renderEditor(created);
    } catch (err) {
        alert('Duplicate failed: ' + err.message);
    }
}

async function handleImport() {
    try {
        const data = JSON.parse(importTextarea.value);
        const imported = await importRules(data);
        rules = imported;
        currentRuleId = null;
        renderRuleList();
        renderEditor(null);
        closeImportModal();
    } catch (err) {
        alert('Import failed: ' + err.message);
    }
}

function openImportModal() {
    importTextarea.value = JSON.stringify(rules, null, 2);
    importModal.classList.add('visible');
}

function closeImportModal() {
    importModal.classList.remove('visible');
}

// ── Wire up events ──

document.getElementById('btn-new-rule').addEventListener('click', () => {
    currentRuleId = null;
    clearValidationErrors();
    renderEditor({
        name: '',
        priority: 50,
        enabled: true,
        conditions: [],
        actions: []
    });
});

document.getElementById('btn-save').addEventListener('click', handleSave);
document.getElementById('btn-delete').addEventListener('click', handleDelete);
document.getElementById('btn-duplicate').addEventListener('click', handleDuplicate);

document.getElementById('btn-import').addEventListener('click', openImportModal);
document.getElementById('btn-export').addEventListener('click', async () => {
    try {
        const resp = await fetch('/rules/export');
        const data = await resp.json();
        importTextarea.value = JSON.stringify(data, null, 2);
        openImportModal();
    } catch (err) {
        alert('Export failed: ' + err.message);
    }
});

document.getElementById('btn-close-import').addEventListener('click', closeImportModal);
document.getElementById('btn-cancel-import').addEventListener('click', closeImportModal);
document.getElementById('btn-confirm-import').addEventListener('click', handleImport);

ruleNameInput.addEventListener('input', markDirty);
rulePriorityInput.addEventListener('input', () => {
    priorityValueEl.textContent = rulePriorityInput.value;
    markDirty();
});
ruleEnabledInput.addEventListener('change', markDirty);

document.getElementById('btn-add-condition').addEventListener('click', () => {
    conditionsList.appendChild(createConditionRow({ field: 'subject', operator: 'contains', value: '' }, 0));
    markDirty();
});

document.getElementById('btn-add-action').addEventListener('click', () => {
    actionsList.appendChild(createActionRow({ type: 'set_priority', value: '' }, 0));
    markDirty();
});

ruleListEl.addEventListener('click', (e) => {
    // Handle delete/duplicate buttons
    const delBtn = e.target.closest('.del-btn');
    if (delBtn) {
        e.stopPropagation();
        const id = delBtn.dataset.id;
        currentRuleId = id;
        handleDelete();
        return;
    }
    const dupBtn = e.target.closest('.dup-btn');
    if (dupBtn) {
        e.stopPropagation();
        const id = dupBtn.dataset.id;
        currentRuleId = id;
        handleDuplicate();
        return;
    }
    // Handle rule selection
    const info = e.target.closest('.rule-item-info');
    if (info) {
        const id = info.dataset.id;
        const rule = rules.find(r => r.id === id);
        if (rule) {
            currentRuleId = id;
            renderEditor(rule);
            renderRuleList();
        }
    }
});

// ── Init ──

loadRules();
