// Global Layout and UI utilities
document.addEventListener('DOMContentLoaded', () => {
    // Sidebar toggle for mobile layouts
    const sidebar = document.getElementById('app-sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('open');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
                sidebar.classList.remove('open');
            }
        });
    }

    // Live system clock ticker
    const systemTimeEl = document.getElementById('system-time');
    if (systemTimeEl) {
        const updateTime = () => {
            const now = new Date();
            systemTimeEl.textContent = now.toTimeString().split(' ')[0];
        };
        updateTime();
        setInterval(updateTime, 1000);
    }

    // Initialize page-specific controllers
    initServicesControl();
    initPortsControl();
    initMemoryControl();
    initTerminalControl();
});

// Helper: Format bytes to human readable sizes
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}


// ==========================================
// 2. RUNNING SERVICES CONTROLLER
// ==========================================
function initServicesControl() {
    const servicesList = document.getElementById('services-list');
    if (!servicesList) return; // Not on Services page

    const searchInput = document.getElementById('services-search');
    const refreshBtn = document.getElementById('refresh-services-btn');
    const autoRefreshCb = document.getElementById('auto-refresh-services');
    const countBadge = document.getElementById('running-count');
    const statusMsg = document.getElementById('services-status-msg');
    
    let servicesCache = [];
    const criticalServices = ['ssh', 'sshd', 'dbus', 'systemd-journald', 'NetworkManager', 'systemd-resolved', 'polkit'];

    async function fetchServices() {
        const refreshIcon = refreshBtn ? refreshBtn.querySelector('svg') : null;
        if (refreshIcon) refreshIcon.classList.add('spinning');
        statusMsg.textContent = 'Updating services...';

        try {
            const response = await fetch('/api/services');
            if (!response.ok) throw new Error('Query error');
            servicesCache = await response.json();
            renderServices();
            
            const timestamp = new Date().toTimeString().split(' ')[0];
            statusMsg.textContent = `Synced at ${timestamp}`;
        } catch (error) {
            statusMsg.textContent = `Sync Error: ${error.message}`;
        } finally {
            if (refreshIcon) refreshIcon.classList.remove('spinning');
        }
    }

    function renderServices() {
        const query = searchInput.value.toLowerCase().trim();
        const filtered = servicesCache.filter(s => 
            s.unit.toLowerCase().includes(query) || 
            s.description.toLowerCase().includes(query)
        );

        if (filtered.length === 0) {
            servicesList.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">
                        No services matches the search query.
                    </td>
                </tr>
            `;
            countBadge.textContent = '0 Matches';
            return;
        }

        servicesList.innerHTML = filtered.map(s => {
            const isCritical = criticalServices.includes(s.unit);
            const stopDisabled = isCritical ? 'disabled' : '';
            return `
                <tr>
                    <td style="font-weight: 600; color: #fff;">${s.unit}</td>
                    <td><span class="badge badge-secondary">${s.load}</span></td>
                    <td><span class="badge badge-success">${s.active}</span></td>
                    <td><span class="badge badge-success">${s.sub}</span></td>
                    <td class="desc-col">${s.description}</td>
                    <td style="text-align: right; white-space: nowrap;">
                        <button class="btn-warning" onclick="controlService('${s.unit}', 'restart')" style="margin-right: 4px;">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
                            </svg>
                            <span>Restart</span>
                        </button>
                        <button class="btn-danger" ${stopDisabled} onclick="controlService('${s.unit}', 'stop')">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            </svg>
                            <span>Stop</span>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        countBadge.textContent = `${filtered.length} Active`;
    }

    // Service control action handler
    window.controlService = async function(unit, action) {
        if (!confirm(`Are you sure you want to ${action} the service "${unit}"?`)) {
            return;
        }
        
        statusMsg.textContent = `${action === 'stop' ? 'Stopping' : 'Restarting'} ${unit}...`;
        
        try {
            const response = await fetch('/api/services/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ unit, action })
            });
            const data = await response.json();
            if (response.ok && data.status === 'success') {
                statusMsg.textContent = data.message;
                fetchServices(); // Reload list
            } else {
                alert(`Error: ${data.message || 'Action failed.'}`);
                statusMsg.textContent = `Action failed.`;
            }
        } catch (error) {
            alert(`Network Error: ${error.message}`);
            statusMsg.textContent = `Network error.`;
        }
    };

    // Bind events
    if (searchInput) searchInput.addEventListener('input', renderServices);
    if (refreshBtn) refreshBtn.addEventListener('click', fetchServices);

    // Auto polling
    setInterval(() => {
        if (autoRefreshCb && autoRefreshCb.checked) {
            fetchServices();
        }
    }, 5000);

    // Initial load
    fetchServices();
}

// ==========================================
// 3. ACTIVE PORTS CONTROLLER
// ==========================================
function initPortsControl() {
    const portsList = document.getElementById('ports-list');
    if (!portsList) return; // Not on Ports page

    const searchInput = document.getElementById('ports-search');
    const protoFilter = document.getElementById('protocol-filter');
    const refreshBtn = document.getElementById('refresh-ports-btn');
    const autoRefreshCb = document.getElementById('auto-refresh-ports');
    const countBadge = document.getElementById('ports-count');
    const statusMsg = document.getElementById('ports-status-msg');

    let portsCache = [];

    async function fetchPorts() {
        const refreshIcon = refreshBtn ? refreshBtn.querySelector('svg') : null;
        if (refreshIcon) refreshIcon.classList.add('spinning');
        statusMsg.textContent = 'Updating ports...';

        try {
            const response = await fetch('/api/ports');
            if (!response.ok) throw new Error('Query error');
            portsCache = await response.json();
            renderPorts();
            
            const timestamp = new Date().toTimeString().split(' ')[0];
            statusMsg.textContent = `Synced at ${timestamp}`;
        } catch (error) {
            statusMsg.textContent = `Sync Error: ${error.message}`;
        } finally {
            if (refreshIcon) refreshIcon.classList.remove('spinning');
        }
    }

    function renderPorts() {
        const query = searchInput.value.toLowerCase().trim();
        const selectedProto = protoFilter.value;

        const filtered = portsCache.filter(p => {
            const matchesSearch = p.port.toString().includes(query) || 
                                  p.process.toLowerCase().includes(query) ||
                                  p.local_address.includes(query);
            const matchesProto = selectedProto === 'ALL' || p.protocol === selectedProto;
            return matchesSearch && matchesProto;
        });

        if (filtered.length === 0) {
            portsList.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">
                        No open ports matched your criteria.
                    </td>
                </tr>
            `;
            countBadge.textContent = '0 Matches';
            return;
        }

        portsList.innerHTML = filtered.map(p => {
            const protoBadgeClass = p.protocol === 'TCP' ? 'badge-primary' : 'badge-warning';
            const isDisable = p.pid === 'N/A' || p.pid === '';
            const disabledAttr = isDisable ? 'disabled' : '';
            return `
                <tr>
                    <td><span class="badge ${protoBadgeClass}">${p.protocol}</span></td>
                    <td><span class="badge badge-secondary">${p.state}</span></td>
                    <td style="font-family: monospace; font-size: 0.85rem;">${p.local_address}</td>
                    <td style="font-weight: 600; color: var(--accent-cyan); font-family: monospace;">${p.port}</td>
                    <td style="font-weight: 500;">${p.process}</td>
                    <td style="font-family: monospace; color: var(--text-muted); font-size: 0.85rem;">${p.pid}</td>
                    <td style="text-align: right;">
                        <button class="btn-danger" ${disabledAttr} onclick="killPortProcess('${p.pid}', '${p.port}', '${p.process}')">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                            <span>Kill</span>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        countBadge.textContent = `${filtered.length} Open`;
    }

    // Process kill handler
    window.killPortProcess = async function(pid, port, processName) {
        if (!confirm(`Are you sure you want to terminate process "${processName}" (PID ${pid}) listening on port ${port}?`)) {
            return;
        }
        
        try {
            statusMsg.textContent = `Terminating PID ${pid}...`;
            const response = await fetch('/api/ports/kill', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ pid, port })
            });
            const data = await response.json();
            if (response.ok && data.status === 'success') {
                statusMsg.textContent = data.message;
                fetchPorts(); // Refresh table immediately
            } else {
                alert(`Error: ${data.message || 'Failed to terminate process.'}`);
                statusMsg.textContent = `Failed to kill process.`;
            }
        } catch (error) {
            alert(`Network Error: ${error.message}`);
            statusMsg.textContent = `Network error.`;
        }
    };

    // Bind events
    if (searchInput) searchInput.addEventListener('input', renderPorts);
    if (protoFilter) protoFilter.addEventListener('change', renderPorts);
    if (refreshBtn) refreshBtn.addEventListener('click', fetchPorts);

    // Auto polling
    setInterval(() => {
        if (autoRefreshCb && autoRefreshCb.checked) {
            fetchPorts();
        }
    }, 5000);

    // Initial load
    fetchPorts();
}

// ==========================================
// 4. MEMORY UTILIZATION CONTROLLER
// ==========================================
function initMemoryControl() {
    const ramPctEl = document.getElementById('ram-pct');
    if (!ramPctEl) return; // Not on Memory page

    const ramFill = document.getElementById('ram-gauge-fill');
    const ramTotal = document.getElementById('ram-total');
    const ramUsed = document.getElementById('ram-used');
    const ramFree = document.getElementById('ram-free');
    const ramCached = document.getElementById('ram-cached');

    const swapPctEl = document.getElementById('swap-pct');
    const swapFill = document.getElementById('swap-gauge-fill');
    const swapTotal = document.getElementById('swap-total');
    const swapUsed = document.getElementById('swap-used');
    const swapFree = document.getElementById('swap-free');

    const refreshBtn = document.getElementById('refresh-memory-btn');
    const autoRefreshCb = document.getElementById('auto-refresh-memory');

    const serviceList = document.getElementById('service-memory-list');
    const breakdownCount = document.getElementById('memory-breakdown-count');

    // Gauge Circumference (radius is 50)
    // C = 2 * PI * r = 314.159
    const gaugeCircumference = 314.159;

    function setGaugePercentage(element, circle, pct) {
        if (element) element.textContent = `${pct}%`;
        if (circle) {
            const offset = gaugeCircumference - (pct / 100) * gaugeCircumference;
            circle.style.strokeDashoffset = offset;
        }
    }

    async function fetchMemory() {
        const refreshIcon = refreshBtn ? refreshBtn.querySelector('svg') : null;
        if (refreshIcon) refreshIcon.classList.add('spinning');

        try {
            const response = await fetch('/api/memory');
            if (!response.ok) throw new Error('Query error');
            const data = await response.json();

            // RAM Details
            setGaugePercentage(ramPctEl, ramFill, data.ram.used_percent);
            if (ramTotal) ramTotal.textContent = formatBytes(data.ram.total);
            if (ramUsed) ramUsed.textContent = formatBytes(data.ram.used);
            if (ramFree) ramFree.textContent = formatBytes(data.ram.available);
            if (ramCached) ramCached.textContent = formatBytes(data.ram.buffers_cached);

            // Swap Details
            setGaugePercentage(swapPctEl, swapFill, data.swap.used_percent);
            if (swapTotal) swapTotal.textContent = formatBytes(data.swap.total);
            if (swapUsed) swapUsed.textContent = formatBytes(data.swap.used);
            if (swapFree) swapFree.textContent = formatBytes(data.swap.free);

            // Services Memory Breakdown Table
            if (serviceList && data.services) {
                if (breakdownCount) breakdownCount.textContent = `${data.services.length} services tracked`;
                
                if (data.services.length === 0) {
                    serviceList.innerHTML = `
                        <tr>
                            <td colspan="3" style="text-align: center; color: var(--text-muted); padding: 30px;">
                                No active services reporting memory metrics.
                            </td>
                        </tr>
                    `;
                } else {
                    const totalRam = data.ram.total;
                    serviceList.innerHTML = data.services.map(s => {
                        const pctOfTotal = totalRam > 0 ? ((s.memory / totalRam) * 100).toFixed(2) : 0;
                        return `
                            <tr>
                                <td style="font-weight: 600; color: #fff;">${s.name}</td>
                                <td style="font-family: monospace; font-weight: 500; color: var(--accent-cyan);">${formatBytes(s.memory)}</td>
                                <td>
                                    <div class="proportion-bar-container">
                                        <div class="proportion-bar-outer">
                                            <div class="proportion-bar-inner" style="width: ${pctOfTotal}%;"></div>
                                        </div>
                                        <span class="proportion-pct-text">${pctOfTotal}%</span>
                                    </div>
                                </td>
                            </tr>
                        `;
                    }).join('');
                }
            }

            // Process Memory Breakdown Table
            const processList = document.getElementById('process-memory-list');
            const processBreakdownCount = document.getElementById('process-breakdown-count');
            if (processList && data.processes) {
                if (processBreakdownCount) processBreakdownCount.textContent = `${data.processes.length} processes tracked`;
                
                if (data.processes.length === 0) {
                    processList.innerHTML = `
                        <tr>
                            <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 30px;">
                                No active processes reporting memory metrics.
                            </td>
                        </tr>
                    `;
                } else {
                    const totalRam = data.ram.total;
                    processList.innerHTML = data.processes.map(p => {
                        const pctOfTotal = totalRam > 0 ? ((p.memory / totalRam) * 100).toFixed(2) : 0;
                        return `
                            <tr>
                                <td style="font-family: monospace; color: var(--text-muted); font-size: 0.85rem;">${p.pid}</td>
                                <td style="font-weight: 600; color: #fff;">${p.name}</td>
                                <td style="font-family: monospace; font-weight: 500; color: var(--accent-cyan);">${formatBytes(p.memory)}</td>
                                <td>
                                    <div class="proportion-bar-container">
                                        <div class="proportion-bar-outer">
                                            <div class="proportion-bar-inner" style="width: ${pctOfTotal}%;"></div>
                                        </div>
                                        <span class="proportion-pct-text">${pctOfTotal}%</span>
                                    </div>
                                </td>
                            </tr>
                        `;
                    }).join('');
                }
            }

        } catch (error) {
            console.error('Failed to sync memory stats:', error);
        } finally {
            if (refreshIcon) refreshIcon.classList.remove('spinning');
        }
    }

    // Bind events
    if (refreshBtn) refreshBtn.addEventListener('click', fetchMemory);

    // Auto polling (every 5 seconds for memory metrics)
    setInterval(() => {
        if (autoRefreshCb && autoRefreshCb.checked) {
            fetchMemory();
        }
    }, 5000);

    // Initial load
    fetchMemory();
}

// ==========================================
// 5. INTERACTIVE TERMINAL CONTROLLER
// ==========================================
function initTerminalControl() {
    const terminalInput = document.getElementById('terminal-input');
    if (!terminalInput) return; // Not on Terminal page

    const terminalOutput = document.getElementById('terminal-output');
    const terminalBody = document.getElementById('terminal-body');
    const clearBtn = document.getElementById('clear-terminal-btn');

    // Click anywhere in the terminal body to focus the input field (only if no text is selected)
    terminalBody.addEventListener('click', () => {
        if (!window.getSelection().toString()) {
            terminalInput.focus();
        }
    });

    // Handle command submission
    terminalInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            const command = terminalInput.value.trim();
            if (!command) return;

            // Clear input field
            terminalInput.value = '';

            // Print the typed command back to the screen
            appendTerminalLine(`radxa@board:~$ ${command}`, 'command');

            // Add visual spinner/loader line
            const loaderId = 'loader-' + Date.now();
            appendTerminalLine('Executing...', 'loader', loaderId);

            const sudoPasswordEl = document.getElementById('sudo-password-input');
            const sudoPassword = sudoPasswordEl ? sudoPasswordEl.value : '';

            try {
                const response = await fetch('/api/terminal/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ command, sudo_password: sudoPassword })
                });
                
                const data = await response.json();
                
                // Remove loader line
                const loaderEl = document.getElementById(loaderId);
                if (loaderEl) loaderEl.remove();

                if (response.ok && data.status === 'success') {
                    if (data.stdout) {
                        appendTerminalLine(data.stdout, 'output');
                    }
                    if (data.stderr) {
                        appendTerminalLine(data.stderr, 'error');
                    }
                    if (!data.stdout && !data.stderr) {
                        appendTerminalLine('[Command completed with no output]', 'system');
                    }
                    appendTerminalLine(`exit status: ${data.exit_code}`, 'system');
                } else {
                    appendTerminalLine(`Error: ${data.message || 'Execution failed.'}`, 'error');
                }
            } catch (error) {
                // Remove loader
                const loaderEl = document.getElementById(loaderId);
                if (loaderEl) loaderEl.remove();

                appendTerminalLine(`Connection Error: ${error.message}`, 'error');
            }
        }
    });

    // Handle clear console
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            terminalOutput.innerHTML = `
                <div class="terminal-line system">Console history cleared.</div>
                <div class="terminal-line system">------------------------------------------------------------------------</div>
            `;
            terminalInput.focus();
        });
    }

    function appendTerminalLine(text, type, id = '') {
        const lineEl = document.createElement('div');
        lineEl.className = `terminal-line ${type}`;
        if (id) lineEl.id = id;
        lineEl.textContent = text;
        terminalOutput.appendChild(lineEl);
        
        // Scroll body to the bottom
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    // Auto-focus input on load
    terminalInput.focus();
}

// ==========================================
// 6. SYSTEM POWER CONTROLS
// ==========================================
let currentPowerAction = null;

window.showPowerModal = function(action) {
    currentPowerAction = action;
    const modal = document.getElementById('power-modal');
    const card = document.getElementById('power-modal-card');
    const iconContainer = document.getElementById('power-modal-icon');
    const title = document.getElementById('power-modal-title');
    const desc = document.getElementById('power-modal-desc');
    const confirmBtn = document.getElementById('power-confirm-btn');
    const footer = document.getElementById('power-modal-footer');
    const progressContainer = document.getElementById('power-progress-container');
    const progressFill = document.getElementById('power-progress-fill');

    if (!modal || !confirmBtn) return;

    // Reset state
    card.classList.remove('progress-state');
    footer.style.display = 'flex';
    progressContainer.style.display = 'none';
    progressFill.style.width = '0%';
    progressFill.className = 'modal-progress-fill';

    if (action === 'reboot') {
        iconContainer.className = 'modal-icon reboot';
        iconContainer.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
            </svg>
        `;
        title.textContent = 'Confirm Restart';
        desc.textContent = 'Are you sure you want to restart the Radxa board? This will terminate all active processes and disconnect the monitoring panel.';
        confirmBtn.className = 'modal-btn btn-confirm-reboot';
        confirmBtn.textContent = 'Restart Board';
        confirmBtn.onclick = () => executePowerAction('reboot');
    } else if (action === 'shutdown') {
        iconContainer.className = 'modal-icon shutdown';
        iconContainer.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path>
                <line x1="12" y1="2" x2="12" y2="12"></line>
            </svg>
        `;
        title.textContent = 'Confirm Shutdown';
        desc.textContent = 'Are you sure you want to shut down the Radxa board? This will power off the hardware completely. You will not be able to reconnect to this panel until you power it on manually.';
        confirmBtn.className = 'modal-btn btn-confirm-shutdown';
        confirmBtn.textContent = 'Shutdown Board';
        confirmBtn.onclick = () => executePowerAction('shutdown');
    }

    modal.classList.add('open');
};

window.closePowerModal = function() {
    const modal = document.getElementById('power-modal');
    if (modal) {
        modal.classList.remove('open');
    }
    currentPowerAction = null;
};

async function executePowerAction(action) {
    const card = document.getElementById('power-modal-card');
    const title = document.getElementById('power-modal-title');
    const desc = document.getElementById('power-modal-desc');
    const footer = document.getElementById('power-modal-footer');
    const progressContainer = document.getElementById('power-progress-container');
    const progressFill = document.getElementById('power-progress-fill');

    title.textContent = action === 'reboot' ? 'Restarting System...' : 'Shutting Down...';
    desc.textContent = action === 'reboot' 
        ? 'Sending restart instruction. The dashboard will go offline shortly. Please wait.' 
        : 'Sending shutdown instruction. The system is powering off and the dashboard will go offline.';
    
    card.classList.add('progress-state');
    progressContainer.style.display = 'block';
    progressFill.classList.add(action);

    // Dynamic progress bar load animation to show immediate feedback
    let width = 0;
    const interval = setInterval(() => {
        if (width >= 90) {
            clearInterval(interval);
        } else {
            width += 5;
            progressFill.style.width = width + '%';
        }
    }, 100);

    try {
        const response = await fetch('/api/system/power', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action })
        });
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            // Accelerate progress fill to 100%
            clearInterval(interval);
            progressFill.style.width = '100%';
            
            // Wait and update label to show offline
            setTimeout(() => {
                desc.textContent = action === 'reboot'
                    ? 'Board is offline and restarting. You can close this window or wait for it to recover.'
                    : 'Board has shutdown. The dashboard is now offline.';
                
                // Update navigation sidebar status
                const label = document.getElementById('connection-label');
                const dot = document.querySelector('.sidebar-footer .status-dot');
                if (label) label.textContent = 'Offline';
                if (dot) {
                    dot.style.backgroundColor = 'var(--error-color)';
                    dot.style.boxShadow = '0 0 6px var(--error-color)';
                }
            }, 1000);
        } else {
            clearInterval(interval);
            card.classList.remove('progress-state');
            progressContainer.style.display = 'none';
            alert(`Failed: ${data.message || 'Error occurred'}`);
            closePowerModal();
        }
    } catch (error) {
        clearInterval(interval);
        card.classList.remove('progress-state');
        progressContainer.style.display = 'none';
        alert(`Network Error: ${error.message}`);
        closePowerModal();
    }
}

