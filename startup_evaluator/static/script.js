document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('evaluation-form');
    const submitBtn = document.getElementById('submit-btn');
    const spinner = submitBtn.querySelector('.spinner');
    
    const progressSection = document.getElementById('progress-section');
    const terminalOutput = document.getElementById('terminal-output');
    const statusBadge = document.getElementById('status-badge');
    
    const reportSection = document.getElementById('report-section');
    const reportContent = document.getElementById('report-content');
    
    let pollInterval = null;
    let printedLogsCount = 0;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const idea = document.getElementById('startup-idea').value.trim();
        if (!idea) return;

        // Reset UI
        submitBtn.disabled = true;
        spinner.classList.remove('hidden');
        progressSection.classList.remove('hidden');
        reportSection.classList.add('hidden');
        terminalOutput.innerHTML = '';
        printedLogsCount = 0;
        statusBadge.className = 'badge running';
        statusBadge.textContent = 'Running...';
        
        try {
            const response = await fetch('/api/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ idea })
            });
            
            const data = await response.json();
            if (data.run_id) {
                startPolling(data.run_id);
            } else {
                showError("Failed to start evaluation.");
            }
        } catch (err) {
            showError("Network error: " + err.message);
        }
    });

    function startPolling(runId) {
        if (pollInterval) clearInterval(pollInterval);
        
        pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${runId}`);
                const data = await res.json();
                
                // Print new logs
                if (data.logs && data.logs.length > printedLogsCount) {
                    const newLogs = data.logs.slice(printedLogsCount);
                    newLogs.forEach(log => {
                        const p = document.createElement('p');
                        p.textContent = log;
                        if (log.includes('| ERROR')) p.className = 'log-error';
                        else if (log.includes('| INFO')) p.className = 'log-info';
                        else p.className = 'log-debug';
                        terminalOutput.appendChild(p);
                    });
                    printedLogsCount = data.logs.length;
                    terminalOutput.scrollTop = terminalOutput.scrollHeight;
                }
                
                // Check status
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);
                    submitBtn.disabled = false;
                    spinner.classList.add('hidden');
                    
                    if (data.status === 'completed') {
                        statusBadge.className = 'badge completed';
                        statusBadge.textContent = 'Completed';
                        if (data.report) {
                            reportSection.classList.remove('hidden');
                            reportContent.innerHTML = marked.parse(data.report);
                        }
                    } else {
                        statusBadge.className = 'badge failed';
                        statusBadge.textContent = 'Failed';
                        showError(data.error || "Evaluation failed.");
                    }
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 1500);
    }

    function showError(msg) {
        submitBtn.disabled = false;
        spinner.classList.add('hidden');
        const p = document.createElement('p');
        p.className = 'log-error';
        p.textContent = msg;
        terminalOutput.appendChild(p);
    }
});
