let currentState = null;
let previousState = null;
let isRunning = false;
let runInterval = null;
let runSpeed = 500;

const API_BASE = '';

function updateSpeed(speed) {
    runSpeed = speed;
    const display = document.getElementById('speed-display');
    if (display) {
        display.textContent = `${speed}ms`;
    }
    if (isRunning) {
        handlePause();
        handleRun();
    }
}

async function fetchState() {
    try {
        const response = await fetch(`${API_BASE}/api/state`);
        if (!response.ok) throw new Error('Failed to fetch state');
        return await response.json();
    } catch (error) {
        console.error('Error fetching state:', error);
        showError('Failed to fetch simulator state');
        return null;
    }
}

async function stepCycle() {
    try {
        const response = await fetch(`${API_BASE}/api/step`, { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Failed to step cycle');
        }
        return await response.json();
    } catch (error) {
        console.error('Error stepping cycle:', error);
        showError('Failed to execute cycle', error.message);
        return null;
    }
}

async function reset() {
    try {
        const response = await fetch(`${API_BASE}/api/reset`, { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Failed to reset');
        }
        return await response.json();
    } catch (error) {
        console.error('Error resetting:', error);
        showError('Failed to reset simulator', error.message);
        return null;
    }
}

async function loadProgram(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE}/api/load`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Failed to load program');
        }
        return await response.json();
    } catch (error) {
        console.error('Error loading program:', error);
        showError('Failed to load program', error.message);
        return null;
    }
}

async function getMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/metrics`);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        return await response.json();
    } catch (error) {
        console.error('Error fetching metrics:', error);
        return null;
    }
}

function updateAll(state) {
    previousState = currentState;
    currentState = state;

    const welcomeMsg = document.getElementById('welcome-message');
    if (state.instructions.length === 0 && welcomeMsg) {
        welcomeMsg.classList.remove('hidden');
    } else if (welcomeMsg) {
        welcomeMsg.classList.add('hidden');
    }

    updateCycleCounter(state);
    updateCurrentActivity(state);
    updateInstructions(state);
    updateReservationStations(state);
    updateROB(state);
    updateRAT(state);
    updateRegisters(state);
    updateMemory(state);
    updateFunctionalUnits(state);
    updateCDB(state);
    updateTimingTable(state);
    updateMetrics(state);

    if (previousState) {
        highlightChanges(previousState, state);
    }
}

function updateCurrentActivity(state) {
    const activityPanel = document.getElementById('current-activity');
    if (!activityPanel) return;

    // Show panel if we have instructions
    if (state.instructions && state.instructions.length > 0) {
        activityPanel.classList.remove('hidden');
    } else {
        activityPanel.classList.add('hidden');
        return;
    }

    // Find what happened this cycle
    const issued = state.last_issued || '—';
    const committed = state.last_committed || '—';
    
    // Find executing and completed instructions
    const executing = state.instructions
        .filter(instr => instr.status === 'executing')
        .map(instr => `#${instr.id}`)
        .join(', ') || '—';
    
    const writeback = state.instructions
        .filter(instr => instr.status === 'write-back')
        .map(instr => `#${instr.id}`)
        .join(', ') || '—';

    // Update activity display
    const issuedEl = document.getElementById('activity-issued');
    const executingEl = document.getElementById('activity-executing');
    const writebackEl = document.getElementById('activity-writeback');
    const committedEl = document.getElementById('activity-committed');
    
    if (issuedEl) issuedEl.textContent = issued;
    if (executingEl) executingEl.textContent = executing;
    if (writebackEl) writebackEl.textContent = writeback;
    if (committedEl) committedEl.textContent = committed;
}

function updateCycleCounter(state) {
    const counter = document.getElementById('cycle-counter');
    if (counter) {
        counter.textContent = state.cycle || 0;
    }
}

function updateInstructions(state) {
    const container = document.getElementById('instructions-list');
    if (!container) return;

    if (state.instructions.length === 0) {
        container.innerHTML = '<div class="empty-state">No instructions loaded</div>';
        return;
    }

    container.innerHTML = '';

    state.instructions.forEach(instr => {
        const item = document.createElement('div');
        item.className = `instruction-item ${instr.status}`;
        item.id = `instr-${instr.id}`;

        const name = instr.name || 'UNKNOWN';
        const details = [];
        if (instr.rA !== null && instr.rA !== undefined) details.push(`R${instr.rA}`);
        if (instr.rB !== null && instr.rB !== undefined) details.push(`R${instr.rB}`);
        if (instr.rC !== null && instr.rC !== undefined) details.push(`R${instr.rC}`);
        if (instr.immediate !== null && instr.immediate !== undefined) details.push(`#${instr.immediate}`);
        if (instr.label) details.push(instr.label);

        const statusText = {
            'pending': 'Pending',
            'issued': 'Issued',
            'executing': 'Executing',
            'write-back': 'Write-back',
            'commit': 'Commit'
        };

        const hasBreakpoint = breakpoints.has(instr.id);
        const breakpointIcon = hasBreakpoint
            ? '<span class="text-red-500 mr-2 cursor-pointer">●</span>'
            : `<span class="text-gray-300 mr-2 cursor-pointer" data-instr-id="${instr.id}">○</span>`;

        // Highlight active instruction (executing or just issued)
        const isActive = instr.status === 'executing' || 
                        (instr.status === 'issued' && currentState?.last_issued === name);

        item.innerHTML = `
            <div class="flex items-center">
                ${breakpointIcon}
                <span class="text-gray-500 font-semibold text-xs mr-2">#${instr.id}</span>
                <span class="font-mono mr-2 font-semibold">${name}</span>
                ${details.length > 0 ? `<span class="text-gray-600 text-xs ml-1">${details.join(', ')}</span>` : ''}
                <span class="ml-auto text-xs px-2.5 py-1 rounded font-semibold ${
                    instr.status === 'executing' ? 'bg-amber-100 text-amber-800' :
                    instr.status === 'issued' ? 'bg-blue-100 text-blue-800' :
                    instr.status === 'write-back' ? 'bg-green-100 text-green-800' :
                    instr.status === 'commit' ? 'bg-emerald-100 text-emerald-800' :
                    'bg-gray-200 text-gray-700'
                }">${statusText[instr.status] || instr.status}</span>
            </div>
        `;

        if (isActive) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }

        const breakpointEl = item.querySelector('[data-instr-id]');
        if (breakpointEl) {
            breakpointEl.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleBreakpoint(parseInt(breakpointEl.getAttribute('data-instr-id')));
            });
        }

        container.appendChild(item);
    });
}

function updateReservationStations(state) {
    const container = document.getElementById('reservation-stations');
    if (!container) return;

    container.innerHTML = '';

    const rsOrder = ['LOAD1', 'LOAD2', 'STORE', 'BEQ1', 'BEQ2', 'CALL/RET',
        'ADD/SUB1', 'ADD/SUB2', 'ADD/SUB3', 'ADD/SUB4', 'NAND', 'MUL'];

    rsOrder.forEach(rsName => {
        const rs = state.reservation_stations[rsName] || { busy: false, name: rsName };
        const card = document.createElement('div');

        if (rs.busy) {
            const stateClass = rs.state ? rs.state.toLowerCase() : 'busy';
            card.className = `rs-card ${stateClass}`;
            card.id = `rs-${rsName}`;

            const instr = rs.instruction || {};
            const details = [];

            if (rs.op) details.push(`<div class="mb-1"><span class="font-semibold">Op:</span> ${rs.op}</div>`);
            if (instr.id) details.push(`<div class="mb-1"><span class="font-semibold">Instr ID:</span> <span class="font-mono">${instr.id}</span></div>`);
            if (rs.dest !== null && rs.dest !== undefined) details.push(`<div class="mb-1"><span class="font-semibold">Dest:</span> <span class="font-mono text-blue-600">ROB[${rs.dest}]</span></div>`);
            if (rs.Vj !== null && rs.Vj !== undefined) details.push(`<div class="mb-1"><span class="font-semibold">Vj:</span> <span class="font-mono">${rs.Vj}</span></div>`);
            if (rs.Vk !== null && rs.Vk !== undefined) details.push(`<div class="mb-1"><span class="font-semibold">Vk:</span> <span class="font-mono">${rs.Vk}</span></div>`);
            if (rs.Qj !== null && rs.Qj !== undefined) details.push(`<div class="mb-1"><span class="font-semibold">Qj:</span> <span class="font-mono text-amber-600">ROB[${rs.Qj}]</span></div>`);
            if (rs.Qk !== null && rs.Qk !== undefined) details.push(`<div class="mb-1"><span class="font-semibold">Qk:</span> <span class="font-mono text-amber-600">ROB[${rs.Qk}]</span></div>`);
            if (rs.A !== null && rs.A !== undefined) details.push(`<div class="mb-1"><span class="font-semibold">A:</span> <span class="font-mono">${rs.A}</span></div>`);

            const statusText = stateClass === 'executing' ? 'EXECUTING' : stateClass === 'write-back' ? 'READY' : 'BUSY';

            card.innerHTML = `
                <div class="font-bold text-xs mb-2 font-mono">${rsName}</div>
                <div class="inline-block px-2 py-1 rounded text-xs font-semibold mb-2 ${stateClass === 'executing' || stateClass === 'busy' ? 'bg-amber-500 text-white' : 'bg-green-500 text-white'}">${statusText}</div>
                <div class="text-xs">${details.join('')}</div>
            `;
        } else {
            card.className = 'rs-card free';
            card.innerHTML = `
                <div class="font-bold text-xs mb-2 font-mono text-gray-400">${rsName}</div>
                <div class="inline-block px-2 py-1 rounded text-xs font-semibold bg-gray-400 text-white">FREE</div>
            `;
        }

        container.appendChild(card);
    });
}

function updateROB(state) {
    const container = document.getElementById('rob-display');
    if (!container) return;

    container.innerHTML = '';

    if (state.rob.length === 0) {
        container.innerHTML = '<div class="empty-state">ROB is empty</div>';
        return;
    }

    state.rob.forEach(entry => {
        const robEntry = document.createElement('div');
        robEntry.className = `rob-entry ${entry.ready ? 'ready' : 'not-ready'} ${entry.is_head ? 'head' : ''}`;
        robEntry.id = `rob-entry-${entry.index}`;

        // Handle value display - show value if it's a number (including 0) or if it's explicitly set
        let valueStr = '---';
        // Special handling for STORE instructions - they don't produce register values
        if (entry.name === 'STORE' && entry.ready) {
            valueStr = 'Complete';
        } else if (entry.value !== null && entry.value !== undefined) {
            if (typeof entry.value === 'object') {
                // Handle dictionary/object values (e.g., CALL, BEQ results)
                if (entry.value.target !== undefined) {
                    valueStr = `target:${entry.value.target}`;
                    if (entry.value.return_address !== undefined) {
                        valueStr += `, ret:${entry.value.return_address}`;
                    }
                    if (entry.value.taken !== undefined) {
                        valueStr += `, ${entry.value.taken ? 'taken' : 'not taken'}`;
                    }
                } else {
                    // Generic object - show JSON representation
                    valueStr = JSON.stringify(entry.value);
                }
            } else {
                // Primitive value (number, string, etc.)
                valueStr = String(entry.value);
            }
        }
        const destStr = entry.dest !== null && entry.dest !== undefined ? `R${entry.dest}` : '---';
        const readyBadge = entry.ready
            ? '<span class="text-xs text-green-600 font-semibold">Ready</span>'
            : '<span class="text-xs text-amber-600">Waiting</span>';

        robEntry.innerHTML = `
            <div class="font-bold text-blue-600 font-mono text-xs">[${entry.index}]</div>
            <div class="font-semibold text-xs">${entry.name}</div>
            <div class="text-xs">${destStr}</div>
            <div class="text-xs">${readyBadge}</div>
            <div class="font-mono font-bold text-xs">${valueStr}</div>
        `;

        container.appendChild(robEntry);
    });
}

function updateRAT(state) {
    const tbody = document.querySelector('#rat-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    for (let i = 0; i < 8; i++) {
        const row = document.createElement('tr');
        row.id = `rat-r${i}`;

        const robIndex = state.rat[i];
        const robIndexStr = robIndex !== null && robIndex !== undefined
            ? `<span class="font-mono font-bold text-blue-600 text-xs">ROB[${robIndex}]</span>`
            : '<span class="text-gray-400 text-xs">—</span>';

        row.innerHTML = `
            <td class="px-2 py-2 font-semibold text-xs">R${i}</td>
            <td class="px-2 py-2 text-xs">${robIndexStr}</td>
        `;

        tbody.appendChild(row);
    }
}

function updateRegisters(state) {
    const tbody = document.querySelector('#registers-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    for (let i = 0; i < 8; i++) {
        const row = document.createElement('tr');
        row.id = `reg-r${i}`;

        const value = state.registers[i] || 0;
        const valueClass = value !== 0 ? 'font-bold text-blue-600' : 'text-gray-600';

        row.innerHTML = `
            <td class="px-2 py-2 font-semibold text-xs">R${i}</td>
            <td class="px-2 py-2 font-mono text-xs ${valueClass}">${value}</td>
        `;

        tbody.appendChild(row);
    }
}

function updateMemory(state) {
    const tbody = document.querySelector('#memory-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    const memoryEntries = Object.entries(state.memory || {})
        .sort((a, b) => parseInt(a[0]) - parseInt(b[0]));

    if (memoryEntries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" class="empty-state">No memory writes yet</td></tr>';
        return;
    }

    memoryEntries.forEach(([addr, value]) => {
        const row = document.createElement('tr');
        row.id = `mem-${addr}`;

        row.innerHTML = `
            <td class="px-2 py-2 font-mono font-semibold text-xs">${addr}</td>
            <td class="px-2 py-2 font-mono font-bold text-blue-600 text-xs">${value}</td>
        `;

        tbody.appendChild(row);
    });
}

function updateFunctionalUnits(state) {
    const container = document.getElementById('functional-units');
    if (!container) return;

    container.innerHTML = '';

    const fuTypes = Object.keys(state.functional_units || {});

    if (fuTypes.length === 0) {
        container.innerHTML = '<div class="empty-state">No functional units available</div>';
        return;
    }

    fuTypes.forEach(fuType => {
        const fuList = state.functional_units[fuType];

        fuList.forEach((fu, index) => {
            const fuItem = document.createElement('div');
            fuItem.className = `fu-item ${fu.busy ? 'busy' : 'idle'}`;

            const statusText = fu.busy
                ? `<span class="text-amber-600 font-semibold">Busy</span> - Cycles remaining: <span class="font-mono font-bold">${fu.cycles_remaining}</span>`
                : '<span class="text-gray-400">Idle</span>';

            fuItem.innerHTML = `
                <div class="font-bold mb-1 font-mono text-xs">${fuType} #${index}</div>
                <div class="text-xs">${statusText}</div>
            `;

            container.appendChild(fuItem);
        });
    });
}

function updateCDB(state) {
    const container = document.getElementById('cdb-display');
    if (!container) return;

    const cdb = state.cdb || {};

    if (cdb.busy) {
        container.className = 'cdb-container cdb-busy';
        
        // Format the value properly - handle objects (like STORE results)
        let valueDisplay = '—';
        if (cdb.value !== null && cdb.value !== undefined) {
            if (typeof cdb.value === 'object') {
                // Handle STORE results which have address and value
                if (cdb.value.address !== undefined && cdb.value.value !== undefined) {
                    valueDisplay = `Addr: ${cdb.value.address}, Val: ${cdb.value.value}`;
                } else {
                    // For other objects, stringify them
                    valueDisplay = JSON.stringify(cdb.value);
                }
            } else {
                valueDisplay = String(cdb.value);
            }
        }
        
        container.innerHTML = `
            <div class="font-bold mb-2 text-sm text-green-700">Broadcasting</div>
            <div class="mb-1 text-sm"><strong>ROB Index:</strong> <span class="font-mono font-semibold text-blue-600">${cdb.rob_index !== null && cdb.rob_index !== undefined ? cdb.rob_index : '—'}</span></div>
            <div class="mb-1 text-sm"><strong>Value:</strong> <span class="font-mono font-bold">${valueDisplay}</span></div>
            <div class="mb-1 text-sm"><strong>Type:</strong> <span class="font-semibold">${cdb.instruction_type || '—'}</span></div>
            ${cdb.pending_count > 0 ? `<div class="mt-2 pt-2 border-t text-red-600 font-semibold text-sm">Pending: ${cdb.pending_count}</div>` : ''}
        `;
    } else {
        container.className = 'cdb-container cdb-idle';
        container.innerHTML = '<span>CDB is idle</span>';
    }
}

function updateTimingTable(state) {
    const tbody = document.querySelector('#timing-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (state.instructions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Load a program to see timing data</td></tr>';
        return;
    }

    state.instructions.forEach(instr => {
        const row = document.createElement('tr');
        row.id = `timing-${instr.id}`;

        const timing = instr.timing || {};

        const formatCycle = (cycle) => {
            if (cycle !== null && cycle !== undefined) {
                return `<span class="font-mono font-bold text-blue-600 text-xs">${cycle}</span>`;
            }
            return '<span class="text-gray-400 text-xs">—</span>';
        };

        row.innerHTML = `
            <td class="px-2 py-2 font-bold text-xs">${instr.id}</td>
            <td class="px-2 py-2 font-semibold font-mono text-xs">${instr.name}</td>
            <td class="px-2 py-2 text-center">${formatCycle(timing.issue)}</td>
            <td class="px-2 py-2 text-center">${formatCycle(timing.start_exec)}</td>
            <td class="px-2 py-2 text-center">${formatCycle(timing.finish_exec)}</td>
            <td class="px-2 py-2 text-center">${formatCycle(timing.write)}</td>
            <td class="px-2 py-2 text-center">${formatCycle(timing.commit)}</td>
        `;

        tbody.appendChild(row);
    });
}

async function updateMetrics(state) {
    const container = document.getElementById('metrics-display');
    if (!container) return;

    const metrics = await getMetrics();
    if (!metrics) {
        container.innerHTML = '<div class="empty-state col-span-2">Load a program to see metrics</div>';
        return;
    }

    container.innerHTML = `
        <div class="metric-item">
            <div class="metric-label">Total Cycles</div>
            <div class="metric-value">${metrics.total_cycles || 0}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Instructions</div>
            <div class="metric-value">${metrics.total_instructions || 0}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">IPC</div>
            <div class="metric-value">${(metrics.instructions_per_cycle || 0).toFixed(2)}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">CPI</div>
            <div class="metric-value">${(metrics.cycles_per_instruction || 0).toFixed(2)}</div>
        </div>
    `;
}

function highlightChanges(oldState, newState) {
    if (!oldState) return;

    if (oldState.registers) {
        for (let i = 0; i < 8; i++) {
            if (oldState.registers[i] !== newState.registers[i]) {
                const el = document.getElementById(`reg-r${i}`);
                if (el) {
                    el.classList.add('changed');
                    setTimeout(() => el.classList.remove('changed'), 1000);
                }
            }
        }
    }

    if (oldState.rat) {
        for (let i = 0; i < 8; i++) {
            if (oldState.rat[i] !== newState.rat[i]) {
                const el = document.getElementById(`rat-r${i}`);
                if (el) {
                    el.classList.add('changed');
                    setTimeout(() => el.classList.remove('changed'), 1000);
                }
            }
        }
    }
}

async function handleLoad(file) {
    showLoading(true);
    const state = await loadProgram(file);
    showLoading(false);

    if (state) {
        updateAll(state);
        showSuccess(`Program "${file.name}" loaded`);
    }
}

async function handleStep() {
    showLoading(true);
    const state = await stepCycle();
    showLoading(false);

    if (state) {
        updateAll(state);
        updateUndoRedoButtons();
        
        // Disable step button if simulation is complete
        const stepBtn = document.getElementById('step-btn');
        if (state.is_complete) {
            if (stepBtn) {
                stepBtn.disabled = true;
                stepBtn.title = 'Simulation complete - reset to run again';
            }
            showSuccess('Simulation completed! All instructions have been executed.');
        } else {
            if (stepBtn) {
                stepBtn.disabled = false;
                stepBtn.title = 'Step Cycle (Space)';
            }
        }

        if (state.hit_breakpoint) {
            showSuccess('Breakpoint hit');
            handlePause();
        }
    }
}

function handleRun() {
    if (isRunning) return;

    isRunning = true;
    document.getElementById('run-btn').classList.add('hidden');
    document.getElementById('pause-btn').classList.remove('hidden');

    runInterval = setInterval(async () => {
        const state = await stepCycle();
        if (state) {
            updateAll(state);

            if (state.is_complete) {
                handlePause();
                showSuccess('Simulation completed');
                // Disable step button when complete
                const stepBtn = document.getElementById('step-btn');
                if (stepBtn) {
                    stepBtn.disabled = true;
                    stepBtn.title = 'Simulation complete - reset to run again';
                }
            }
        }
    }, runSpeed);
}

function handlePause() {
    if (!isRunning) return;

    isRunning = false;
    if (runInterval) {
        clearInterval(runInterval);
        runInterval = null;
    }

    document.getElementById('run-btn').classList.remove('hidden');
    document.getElementById('pause-btn').classList.add('hidden');
}

async function handleReset() {
    // Re-enable step button on reset
    const stepBtn = document.getElementById('step-btn');
    if (stepBtn) {
        stepBtn.disabled = false;
        stepBtn.title = 'Step Cycle (Space)';
    }
    if (isRunning) {
        handlePause();
    }

    showLoading(true);
    const state = await reset();
    showLoading(false);

    if (state) {
        updateAll(state);
        showSuccess('Simulator reset');
    }
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.toggle('hidden', !show);
    }
}

function showError(message, details = null) {
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-3 rounded shadow-lg z-50 max-w-md';
    toast.innerHTML = `Error: ${message}${details ? `<br><span class="text-sm opacity-90">${details}</span>` : ''}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-3 rounded shadow-lg z-50';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
}

let codeEditor = null;
let breakpoints = new Set();

function initCodeEditor() {
    const editorBtn = document.getElementById('editor-btn');
    const editorModal = document.getElementById('editor-modal');
    const closeEditorBtn = document.getElementById('close-editor-btn');
    const validateBtn = document.getElementById('validate-btn');
    const loadFromEditorBtn = document.getElementById('load-from-editor-btn');
    const editorTextarea = document.getElementById('code-editor');

    if (!editorBtn || !editorModal) return;

    codeEditor = CodeMirror.fromTextArea(editorTextarea, {
        lineNumbers: true,
        mode: 'text/x-assembly',
        theme: 'monokai',
        indentUnit: 4,
        lineWrapping: true
    });

    editorBtn.addEventListener('click', () => {
        editorModal.classList.remove('hidden');
        codeEditor.refresh();
    });

    closeEditorBtn?.addEventListener('click', () => {
        editorModal.classList.add('hidden');
    });

    validateBtn?.addEventListener('click', async () => {
        const code = codeEditor.getValue();
        const errorsDiv = document.getElementById('editor-errors');
        if (!errorsDiv) return;

        const blob = new Blob([code], { type: 'text/plain' });
        const file = new File([blob], 'validate.s', { type: 'text/plain' });
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/validate', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.valid) {
                errorsDiv.innerHTML = `<div class="text-green-600 font-semibold">Valid (${result.instruction_count} instructions)</div>`;
                codeEditor.clearGutter('errors');
            } else {
                let errorHtml = '<div class="text-red-600 font-semibold mb-2">Errors:</div>';
                result.errors.forEach(err => {
                    errorHtml += `<div class="text-red-600 text-sm">Line ${err.line || '?'}: ${err.message}</div>`;
                    if (err.line) {
                        codeEditor.addLineClass(err.line - 1, 'background', 'bg-red-100');
                    }
                });
                errorsDiv.innerHTML = errorHtml;
            }
        } catch (error) {
            errorsDiv.innerHTML = `<div class="text-red-600">Validation error: ${error.message}</div>`;
        }
    });

    loadFromEditorBtn?.addEventListener('click', async () => {
        const code = codeEditor.getValue();
        const blob = new Blob([code], { type: 'text/plain' });
        const file = new File([blob], 'program.s', { type: 'text/plain' });

        showLoading(true);
        const state = await loadProgram(file);
        showLoading(false);

        if (state) {
            editorModal.classList.add('hidden');
            updateAll(state);
            showSuccess('Program loaded from editor');
        }
    });
}

async function toggleBreakpoint(instrId) {
    if (breakpoints.has(instrId)) {
        breakpoints.delete(instrId);
    } else {
        breakpoints.add(instrId);
    }
    await setBreakpoints(Array.from(breakpoints));
    updateInstructions(currentState);
}

async function setBreakpoints(instructionIds) {
    try {
        const response = await fetch('/api/breakpoints', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(instructionIds)
        });
        const result = await response.json();
        breakpoints = new Set(result.breakpoints);
    } catch (error) {
        console.error('Error setting breakpoints:', error);
    }
}

async function undo() {
    try {
        const response = await fetch('/api/undo', { method: 'POST' });
        if (!response.ok) throw new Error('Cannot undo');
        const state = await response.json();
        updateAll(state);
        updateUndoRedoButtons();
    } catch (error) {
        showError('Cannot undo', error.message);
    }
}

async function redo() {
    try {
        const response = await fetch('/api/redo', { method: 'POST' });
        if (!response.ok) throw new Error('Cannot redo');
        const state = await response.json();
        updateAll(state);
        updateUndoRedoButtons();
    } catch (error) {
        showError('Cannot redo', error.message);
    }
}

async function updateUndoRedoButtons() {
    try {
        const response = await fetch('/api/history');
        const info = await response.json();

        const undoBtn = document.getElementById('undo-btn');
        const redoBtn = document.getElementById('redo-btn');

        if (undoBtn) undoBtn.disabled = !info.can_undo;
        if (redoBtn) redoBtn.disabled = !info.can_redo;
    } catch (error) {
        console.error('Error updating undo/redo buttons:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const loadBtn = document.getElementById('load-btn');
    const fileInput = document.getElementById('file-input');

    loadBtn?.addEventListener('click', () => fileInput?.click());
    fileInput?.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (file) {
            await handleLoad(file);
        }
    });

    document.getElementById('step-btn')?.addEventListener('click', handleStep);
    document.getElementById('run-btn')?.addEventListener('click', handleRun);
    document.getElementById('pause-btn')?.addEventListener('click', handlePause);
    document.getElementById('reset-btn')?.addEventListener('click', handleReset);
    document.getElementById('undo-btn')?.addEventListener('click', undo);
    document.getElementById('redo-btn')?.addEventListener('click', redo);

    const speedSlider = document.getElementById('speed-slider');
    if (speedSlider) {
        speedSlider.addEventListener('input', (e) => {
            updateSpeed(parseInt(e.target.value));
        });
        updateSpeed(parseInt(speedSlider.value));
    }

    document.getElementById('compare-btn')?.addEventListener('click', async () => {
        const response = await fetch('/api/history');
        const info = await response.json();

        if (info.total_states < 2) {
            showError('Need at least 2 states to compare');
            return;
        }

        const compareResponse = await fetch(`/api/compare?index1=${info.current_index - 1}&index2=${info.current_index}`);
        const compareData = await compareResponse.json();

        document.getElementById('compare-cycle-1').textContent = compareData.state1.cycle || 0;
        document.getElementById('compare-cycle-2').textContent = compareData.state2.cycle || 0;
        document.getElementById('compare-state-1').innerHTML = '<div class="text-sm">State 1 data...</div>';
        document.getElementById('compare-state-2').innerHTML = '<div class="text-sm">State 2 data...</div>';

        document.getElementById('compare-modal')?.classList.remove('hidden');
    });

    document.getElementById('close-compare-btn')?.addEventListener('click', () => {
        document.getElementById('compare-modal')?.classList.add('hidden');
    });

    // Memory initialization handlers
    let memoryEntryCount = 0;
    
    function createMemoryEntry() {
        memoryEntryCount++;
        const entryDiv = document.createElement('div');
        entryDiv.className = 'flex items-center gap-2';
        entryDiv.innerHTML = `
            <input type="number" 
                   class="memory-addr-input w-24 px-2 py-1 border border-gray-300 rounded text-sm" 
                   placeholder="Address" 
                   min="0" 
                   step="1">
            <span class="text-gray-600">=</span>
            <input type="number" 
                   class="memory-value-input w-32 px-2 py-1 border border-gray-300 rounded text-sm" 
                   placeholder="Value (0-65535)" 
                   min="0" 
                   max="65535" 
                   step="1">
            <button class="remove-memory-entry-btn px-2 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-xs">×</button>
        `;
        
        const removeBtn = entryDiv.querySelector('.remove-memory-entry-btn');
        removeBtn.addEventListener('click', () => {
            entryDiv.remove();
        });
        
        return entryDiv;
    }
    
    function addMemoryEntry() {
        const container = document.getElementById('memory-init-entries');
        if (container) {
            container.appendChild(createMemoryEntry());
        }
    }
    
    document.getElementById('init-memory-btn')?.addEventListener('click', () => {
        const modal = document.getElementById('memory-init-modal');
        const container = document.getElementById('memory-init-entries');
        if (modal && container) {
            // Clear existing entries and add one default entry
            container.innerHTML = '';
            container.appendChild(createMemoryEntry());
            modal.classList.remove('hidden');
        }
    });
    
    document.getElementById('add-memory-entry-btn')?.addEventListener('click', addMemoryEntry);
    
    document.getElementById('close-memory-init-btn')?.addEventListener('click', () => {
        document.getElementById('memory-init-modal')?.classList.add('hidden');
    });
    
    document.getElementById('cancel-memory-init-btn')?.addEventListener('click', () => {
        document.getElementById('memory-init-modal')?.classList.add('hidden');
    });
    
    document.getElementById('apply-memory-init-btn')?.addEventListener('click', async () => {
        const container = document.getElementById('memory-init-entries');
        if (!container) return;
        
        const memoryData = {};
        let hasError = false;
        
        // Collect all address-value pairs
        const entries = container.querySelectorAll('.flex.items-center.gap-2');
        entries.forEach(entry => {
            const addrInput = entry.querySelector('.memory-addr-input');
            const valueInput = entry.querySelector('.memory-value-input');
            
            if (addrInput && valueInput) {
                const addr = addrInput.value.trim();
                const value = valueInput.value.trim();
                
                if (addr && value) {
                    const addrNum = parseInt(addr);
                    const valueNum = parseInt(value);
                    
                    if (isNaN(addrNum) || addrNum < 0) {
                        showError(`Invalid address: ${addr}`);
                        hasError = true;
                        return;
                    }
                    
                    if (isNaN(valueNum) || valueNum < 0 || valueNum > 65535) {
                        showError(`Invalid value: ${value} (must be 0-65535)`);
                        hasError = true;
                        return;
                    }
                    
                    memoryData[addrNum] = valueNum;
                }
            }
        });
        
        if (hasError) {
            return;
        }
        
        if (Object.keys(memoryData).length === 0) {
            showError('Please enter at least one address-value pair');
            return;
        }
        
        try {
            showLoading(true);
            const response = await fetch('/api/memory/init', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(memoryData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to initialize memory');
            }
            
            const state = await response.json();
            updateAll(state);
            
            // Close modal
            document.getElementById('memory-init-modal')?.classList.add('hidden');
            
            showSuccess(`Memory initialized with ${Object.keys(memoryData).length} value(s)`);
        } catch (error) {
            showError(error.message || 'Failed to initialize memory');
        } finally {
            showLoading(false);
        }
    });

    // Toggle activity panel
    document.getElementById('toggle-activity')?.addEventListener('click', () => {
        const panel = document.getElementById('current-activity');
        const content = document.getElementById('activity-content');
        const toggle = document.getElementById('toggle-activity');
        if (panel && content && toggle) {
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                toggle.textContent = 'Hide';
            } else {
                content.classList.add('hidden');
                toggle.textContent = 'Show';
            }
        }
    });

    initCodeEditor();

    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        if (e.code === 'Space' && !isRunning) {
            e.preventDefault();
            handleStep();
        } else if (e.code === 'KeyR' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            handleReset();
        } else if (e.code === 'KeyP' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            if (isRunning) {
                handlePause();
            } else {
                handleRun();
            }
        } else if (e.code === 'KeyL' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            document.getElementById('file-input')?.click();
        } else if ((e.ctrlKey || e.metaKey) && e.code === 'KeyZ' && !e.shiftKey) {
            e.preventDefault();
            undo();
        } else if ((e.ctrlKey || e.metaKey) && (e.code === 'KeyY' || (e.code === 'KeyZ' && e.shiftKey))) {
            e.preventDefault();
            redo();
        }
    });

    fetchState().then(state => {
        if (state) {
            const welcomeMsg = document.getElementById('welcome-message');
            if (state.instructions.length === 0 && welcomeMsg) {
                welcomeMsg.classList.remove('hidden');
            } else if (welcomeMsg) {
                welcomeMsg.classList.add('hidden');
            }
            updateAll(state);
        }
    });
});
