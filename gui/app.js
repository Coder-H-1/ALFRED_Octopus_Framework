const editor = document.getElementById('code-editor');
const filenameDisplay = document.getElementById('current-filename');
const saveBtn = document.getElementById('save-btn');
const compileBtn = document.getElementById('compile-btn');
const functionsList = document.getElementById('functions-list');
const pluginsList = document.getElementById('plugins-list');
const terminal = document.getElementById('terminal-output');
const cliInput = document.getElementById('cli-input');

// Modal Elements
const modalOverlay = document.getElementById('modal-overlay');
const modalTitle = document.getElementById('modal-title');
const modalInput = document.getElementById('modal-input');
const modalConfirm = document.getElementById('modal-confirm');

let currentFilePath = null;

function log(msg, isError = false) {
    const div = document.createElement('div');
    if (isError) div.style.color = 'var(--error)';
    div.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    terminal.appendChild(div);
    terminal.scrollTop = terminal.scrollHeight;
}

function clearTerminal() {
    terminal.innerHTML = 'Terminal cleared.';
}

async function refreshFiles() {
    try {
        const functions = await pywebview.api.list_functions();
        const plugins = await pywebview.api.list_plugins();

        functionsList.innerHTML = functions.map(f => `
            <li class="file-item ${currentFilePath === f.path ? 'active' : ''}" onclick="loadFile('${f.path}', '${f.name}')">
                📄 &nbsp; ${f.name}
            </li>
        `).join('');

        pluginsList.innerHTML = plugins.map(p => `
            <li class="file-item ${currentFilePath === p.path ? 'active' : ''}">
                <span onclick="loadFile('${p.path}', '${p.name}')">🐍 &nbsp; ${p.name}</span>
                <div class="switch ${p.enabled ? 'on' : ''}" onclick="togglePlugin('${p.name}', ${p.enabled})"></div>
            </li>
        `).join('');
        
        // Check ALFRED status
        const statusStr = await pywebview.api.run_cli("status");
        const dot = document.getElementById('main-status');
        if (statusStr.toLowerCase().includes("online")) {
            dot.classList.add('online');
            dot.title = "ALFRED Online";
        } else {
            dot.classList.remove('online');
            dot.title = "ALFRED Offline";
        }
    } catch (e) {
        console.error("Refresh error", e);
    }
}

async function loadFile(path, name) {
    currentFilePath = path;
    filenameDisplay.textContent = name;
    log(`Loading ${name}...`);
    const content = await pywebview.api.read_file(path);
    editor.value = content;
    
    saveBtn.classList.remove('hidden');
    compileBtn.classList.add('hidden');
    refreshFiles();
}

async function togglePlugin(name, currentState) {
    const res = await pywebview.api.toggle_plugin(name, !currentState);
    log(res);
    refreshFiles();
}

// Activity Bar Actions
function promptNewFunction() {
    openModal("New Function", "Enter name (without .oct):", (val) => {
        if (!val) return;
        runCliAndLog(`add ${val}`);
    });
}

function promptDeleteFunction() {
    if (!currentFilePath || !currentFilePath.endsWith(".oct")) {
        log("Select an .oct file to delete first.", true);
        return;
    }
    const name = filenameDisplay.textContent;
    openModal("Delete Function", `Are you sure you want to delete '${name}'?`, () => {
        runCliAndLog(`delete ${name}`);
        currentFilePath = null;
        filenameDisplay.textContent = "Select a file";
        editor.value = "";
    });
}

async function showExample() {
    log("Loading example.oct for reference...");
    const content = await pywebview.api.read_file("example.oct");
    editor.value = content;
    filenameDisplay.textContent = "example.oct (Reference)";
    currentFilePath = "example.oct";
}

// Modal Helpers
function openModal(title, desc, onConfirm) {
    modalTitle.textContent = title;
    document.getElementById('modal-desc').textContent = desc;
    modalOverlay.classList.remove('hidden');
    modalInput.value = "";
    modalInput.focus();
    
    modalConfirm.onclick = () => {
        onConfirm(modalInput.value);
        closeModal();
    };
}

function closeModal() {
    modalOverlay.classList.add('hidden');
}

async function runCliAndLog(cmd) {
    const res = await pywebview.api.run_cli(cmd);
    log(res);
    refreshFiles();
}

// Resizer Logic
const resizer = document.getElementById('sidebar-resizer');
const topBlock = document.getElementById('functions-section');
const bottomBlock = document.getElementById('plugins-section');

let isResizing = false;

resizer.addEventListener('mousedown', (e) => {
    isResizing = true;
});

document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    const sidebarRect = document.getElementById('sidebar').getBoundingClientRect();
    const relativeY = e.clientY - sidebarRect.top;
    const totalHeight = sidebarRect.height;
    
    const topPercent = (relativeY / totalHeight) * 100;
    if (topPercent > 10 && topPercent < 90) {
        topBlock.style.height = `${topPercent}%`;
        bottomBlock.style.height = `${100 - topPercent}%`;
    }
});

document.addEventListener('mouseup', () => {
    isResizing = false;
});

saveBtn.onclick = async () => {
    if (!currentFilePath) return;
    const res = await pywebview.api.save_file(currentFilePath, editor.value);
    log(res);
    saveBtn.classList.add('hidden');
    compileBtn.classList.remove('hidden');
};

compileBtn.onclick = async () => {
    if (!currentFilePath) return;
    log(`Compiling ${filenameDisplay.textContent}...`);
    const res = await pywebview.api.compile_file(currentFilePath);
    log(res);
    refreshFiles();
};

cliInput.onkeydown = async (e) => {
    if (e.key === 'Enter') {
        const cmd = cliInput.value.trim();
        if (cmd) {
            log(`octopus> ${cmd}`);
            const res = await pywebview.api.run_cli(cmd);
            log(res);
            cliInput.value = '';
            refreshFiles();
        }
    }
}

window.addEventListener('pywebviewready', () => {
    refreshFiles();
});
