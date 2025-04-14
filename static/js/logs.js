// logs.js - Attack logs and packet display functionality

// Chart for attack types
let attackTypesChart = null;

// Initialize functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load attack logs
    loadAttackLogs();
    
    // Load attack statistics
    loadAttackStats();
    
    // Load initial packet logs
    loadPacketLogs(false);
    
    // Set up event listeners
    document.getElementById('filterStatus').addEventListener('change', function() {
        loadAttackLogs(this.value);
    });
    
    document.getElementById('showAttackOnly').addEventListener('change', function() {
        loadPacketLogs(this.checked);
    });
    
    document.getElementById('refreshPackets').addEventListener('click', function() {
        const attackOnly = document.getElementById('showAttackOnly').checked;
        loadPacketLogs(attackOnly);
    });
    
    // Initialize chart
    initAttackTypesChart();
    
    // Set up periodic refresh
    setInterval(function() {
        const filterValue = document.getElementById('filterStatus').value;
        loadAttackLogs(filterValue);
        loadAttackStats();
    }, 10000); // Refresh every 10 seconds
});

function initAttackTypesChart() {
    const ctx = document.getElementById('attackTypesChart').getContext('2d');
    attackTypesChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        fontSize: 10
                    }
                }
            }
        }
    });
}

function loadAttackLogs(filter = 'all') {
    // Fetch attack logs from API
    fetch('/api/attacks')
        .then(response => response.json())
        .then(data => {
            // Filter logs if needed
            let filteredData = data;
            if (filter === 'active') {
                filteredData = data.filter(attack => attack.is_active);
            } else if (filter === 'resolved') {
                filteredData = data.filter(attack => !attack.is_active);
            }
            
            // Update table
            updateAttackLogsTable(filteredData);
        })
        .catch(error => {
            console.error('Error fetching attack logs:', error);
            document.getElementById('attackLogsTable').innerHTML = 
                `<tr><td colspan="8" class="text-center text-danger">Error loading attack logs: ${error.message}</td></tr>`;
        });
}

function updateAttackLogsTable(attacks) {
    const tableBody = document.getElementById('attackLogsTable');
    
    if (attacks.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="8" class="text-center">No attack events found</td></tr>';
        return;
    }
    
    let tableHtml = '';
    
    attacks.forEach(attack => {
        // Format times
        const startTime = new Date(attack.start_time);
        const endTime = attack.end_time ? new Date(attack.end_time) : null;
        
        const formattedStartTime = startTime.toLocaleString();
        const formattedEndTime = endTime ? endTime.toLocaleString() : '-';
        
        // Calculate duration if attack has ended
        let duration = '';
        if (endTime) {
            const durationMs = endTime - startTime;
            const durationSec = Math.floor(durationMs / 1000);
            duration = `${durationSec} sec`;
        }
        
        // Determine severity class
        const severityClass = attack.severity >= 8 ? 'log-severity-high' : 
                             attack.severity >= 5 ? 'log-severity-medium' : 'log-severity-low';
        
        // Status badge
        const statusBadge = attack.is_active ? 
            '<span class="badge bg-danger">Active</span>' : 
            '<span class="badge bg-success">Resolved</span>';
        
        // Mitigation badge
        const mitigationBadge = attack.mitigation_applied ? 
            `<span class="badge bg-info">${attack.mitigation_action || 'Mitigated'}</span>` : 
            '<span class="badge bg-warning">None</span>';
        
        // Create table row
        tableHtml += `
            <tr class="${severityClass}" data-attack-id="${attack.id}">
                <td>${attack.id}</td>
                <td>${formattedStartTime}</td>
                <td>${formattedEndTime}</td>
                <td>${attack.attack_type}</td>
                <td><span class="badge bg-secondary">${attack.severity}/10</span></td>
                <td>${mitigationBadge}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary view-details" data-attack-id="${attack.id}">
                        Details
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = tableHtml;
    
    // Add event listeners to detail buttons
    document.querySelectorAll('.view-details').forEach(button => {
        button.addEventListener('click', function() {
            const attackId = this.getAttribute('data-attack-id');
            showAttackDetails(attacks.find(a => a.id == attackId));
        });
    });
    
    // Also add click event to rows
    document.querySelectorAll('#attackLogsTable tr').forEach(row => {
        row.addEventListener('click', function() {
            const attackId = this.getAttribute('data-attack-id');
            if (attackId) {
                showAttackDetails(attacks.find(a => a.id == attackId));
            }
        });
    });
}

function showAttackDetails(attack) {
    if (!attack) return;
    
    const detailsContainer = document.getElementById('attackDetails');
    
    // Format times
    const startTime = new Date(attack.start_time);
    const endTime = attack.end_time ? new Date(attack.end_time) : null;
    
    const formattedStartTime = startTime.toLocaleString();
    const formattedEndTime = endTime ? endTime.toLocaleString() : 'Ongoing';
    
    // Calculate duration
    let duration = 'Ongoing';
    if (endTime) {
        const durationMs = endTime - startTime;
        const durationSec = Math.floor(durationMs / 1000);
        if (durationSec < 60) {
            duration = `${durationSec} seconds`;
        } else {
            const minutes = Math.floor(durationSec / 60);
            const seconds = durationSec % 60;
            duration = `${minutes} min ${seconds} sec`;
        }
    }
    
    // Status indicator
    const statusBadge = attack.is_active ? 
        '<span class="badge bg-danger">Active</span>' : 
        '<span class="badge bg-success">Resolved</span>';
    
    // Severity class
    const severityClass = attack.severity >= 8 ? 'bg-danger' : 
                        attack.severity >= 5 ? 'bg-warning' : 'bg-info';
    
    // Source IPs
    const sourceIps = attack.source_ips ? attack.source_ips.split(',') : [];
    let sourceIpsList = '';
    if (sourceIps.length > 0) {
        sourceIpsList = '<ul class="list-group list-group-flush small">';
        sourceIps.forEach(ip => {
            sourceIpsList += `<li class="list-group-item">${ip}</li>`;
        });
        sourceIpsList += '</ul>';
    } else {
        sourceIpsList = '<p class="text-muted">No source IPs identified</p>';
    }
    
    // Generate HTML for details
    const html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h4>${attack.attack_type} Attack</h4>
            ${statusBadge}
        </div>
        
        <div class="row mb-3">
            <div class="col-md-6">
                <h6>Start Time</h6>
                <p>${formattedStartTime}</p>
            </div>
            <div class="col-md-6">
                <h6>End Time</h6>
                <p>${formattedEndTime}</p>
            </div>
        </div>
        
        <div class="row mb-3">
            <div class="col-md-6">
                <h6>Duration</h6>
                <p>${duration}</p>
            </div>
            <div class="col-md-6">
                <h6>Severity</h6>
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar ${severityClass}" role="progressbar" 
                         style="width: ${attack.severity * 10}%" 
                         aria-valuenow="${attack.severity}" 
                         aria-valuemin="0" 
                         aria-valuemax="10">
                        ${attack.severity}/10
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-3">
            <div class="col-md-6">
                <h6>Target IP</h6>
                <p>${attack.target_ip || 'Unknown'}</p>
            </div>
            <div class="col-md-6">
                <h6>Packet Count</h6>
                <p>${attack.packet_count.toLocaleString()}</p>
            </div>
        </div>
        
        <h6>Mitigation</h6>
        <div class="alert ${attack.mitigation_applied ? 'alert-success' : 'alert-warning'} mb-3">
            ${attack.mitigation_applied ? 
                `<i class="fas fa-check-circle me-2"></i> Defense Action Applied: <strong>${attack.mitigation_action}</strong>` : 
                '<i class="fas fa-exclamation-triangle me-2"></i> No mitigation actions were applied'}
        </div>
        
        <h6>Attack Sources</h6>
        ${sourceIpsList}
        
        <div class="mt-3">
            <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#attackDetailModal" data-attack-id="${attack.id}">
                View Full Details
            </button>
        </div>
    `;
    
    detailsContainer.innerHTML = html;
}

function loadAttackStats() {
    // Fetch attack logs for statistics
    fetch('/api/attacks')
        .then(response => response.json())
        .then(data => {
            updateAttackStatistics(data);
        })
        .catch(error => console.error('Error fetching attack stats:', error));
}

function updateAttackStatistics(attacks) {
    // Basic counts
    const totalAttacks = attacks.length;
    const activeAttacks = attacks.filter(a => a.is_active).length;
    
    // Calculate average duration for completed attacks
    const completedAttacks = attacks.filter(a => a.end_time != null);
    let totalDuration = 0;
    
    completedAttacks.forEach(attack => {
        const start = new Date(attack.start_time);
        const end = new Date(attack.end_time);
        const duration = (end - start) / 1000; // in seconds
        totalDuration += duration;
    });
    
    const avgDuration = completedAttacks.length > 0 ? 
        Math.round(totalDuration / completedAttacks.length) : 0;
    
    // Calculate average severity
    const totalSeverity = attacks.reduce((sum, attack) => sum + attack.severity, 0);
    const avgSeverity = totalAttacks > 0 ? (totalSeverity / totalAttacks).toFixed(1) : 0;
    
    // Calculate defense effectiveness
    const mitigatedAttacks = attacks.filter(a => a.mitigation_applied).length;
    const defenseEffectiveness = totalAttacks > 0 ? (mitigatedAttacks / totalAttacks) * 100 : 0;
    
    // Count attack types
    const attackTypes = {};
    attacks.forEach(attack => {
        const type = attack.attack_type || 'Unknown';
        if (attackTypes[type]) {
            attackTypes[type]++;
        } else {
            attackTypes[type] = 1;
        }
    });
    
    // Update UI
    document.getElementById('totalAttacks').textContent = totalAttacks;
    document.getElementById('activeAttacks').textContent = activeAttacks;
    document.getElementById('avgDuration').textContent = `${avgDuration} sec`;
    document.getElementById('avgSeverity').textContent = avgSeverity;
    document.getElementById('defenseEffectiveness').style.width = `${defenseEffectiveness}%`;
    document.getElementById('defensePercentage').textContent = `${defenseEffectiveness.toFixed(1)}%`;
    
    // Update chart
    updateAttackTypesChart(attackTypes);
}

function updateAttackTypesChart(attackTypes) {
    // Update chart data
    const labels = Object.keys(attackTypes);
    const data = Object.values(attackTypes);
    
    attackTypesChart.data.labels = labels;
    attackTypesChart.data.datasets[0].data = data;
    attackTypesChart.update();
}

function loadPacketLogs(attackOnly = false) {
    // Show loading state
    document.getElementById('packetLogsList').innerHTML = `
        <div class="text-center py-3">
            <span class="spinner-border spinner-border-sm" role="status"></span>
            Loading packets...
        </div>
    `;
    
    // Fetch recent packets
    const url = attackOnly ? '/api/packets?limit=50&attack_only=true' : '/api/packets?limit=50';
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            updatePacketLogs(data);
        })
        .catch(error => {
            console.error('Error fetching packet logs:', error);
            document.getElementById('packetLogsList').innerHTML = `
                <div class="alert alert-danger">
                    Error loading packet logs: ${error.message}
                </div>
            `;
        });
}

function updatePacketLogs(packets) {
    const container = document.getElementById('packetLogsList');
    
    if (!packets || packets.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                No packets available
            </div>
        `;
        return;
    }
    
    let html = '';
    
    packets.forEach(packet => {
        const isAttack = packet.is_attack || false;
        const packetClass = isAttack ? 'packet-attack' : 'packet-normal';
        const timestamp = new Date(packet.timestamp).toLocaleTimeString();
        
        // Format packet details
        html += `
            <div class="packet-item ${packetClass}">
                <strong>${timestamp}</strong> 
                ${isAttack ? '<span class="badge bg-danger">Attack</span>' : ''} 
                <span class="badge bg-secondary">${packet.protocol}</span> 
                ${packet.source_ip}:${packet.source_port} → ${packet.destination_ip}:${packet.destination_port} 
                ${packet.flags ? `[${packet.flags}]` : ''} 
                ${packet.length ? `Length: ${packet.length}` : ''}
                ${packet.attack_type ? `<span class="badge bg-warning">${packet.attack_type}</span>` : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
}
