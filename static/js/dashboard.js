// Dashboard.js - Main dashboard functionality

// Charts objects
let bandwidthChart = null;
let packetDistributionChart = null;
let latencyChart = null;
let trafficSourcesChart = null;

// Data refresh interval (in ms)
const REFRESH_INTERVAL = 2000;

// Initialize charts and data
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initCharts();
    
    // Load initial data
    refreshDashboardData();
    
    // Set up periodic refresh
    setInterval(refreshDashboardData, REFRESH_INTERVAL);
    
    // Initialize any event listeners
    document.getElementById('timeRange').addEventListener('change', function() {
        refreshTrafficData(this.value);
    });
});

function initCharts() {
    // Bandwidth chart
    const bandwidthCtx = document.getElementById('bandwidthChart').getContext('2d');
    bandwidthChart = new Chart(bandwidthCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Bandwidth Usage (Mbps)',
                data: [],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Mbps'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                }
            }
        }
    });
    
    // Packet distribution chart
    const packetCtx = document.getElementById('packetDistributionChart').getContext('2d');
    packetDistributionChart = new Chart(packetCtx, {
        type: 'doughnut',
        data: {
            labels: ['TCP', 'UDP', 'HTTP', 'ICMP', 'Other'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
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
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Latency chart
    const latencyCtx = document.getElementById('latencyChart').getContext('2d');
    latencyChart = new Chart(latencyCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Average Latency (ms)',
                data: [],
                borderColor: 'rgba(255, 159, 64, 1)',
                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'ms'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                }
            }
        }
    });
    
    // Traffic sources chart
    const sourcesCtx = document.getElementById('trafficSourcesChart').getContext('2d');
    trafficSourcesChart = new Chart(sourcesCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Packet Count',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Packets'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Source IP'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function refreshDashboardData() {
    // Fetch network stats
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => updateDashboard(data))
        .catch(error => console.error('Error fetching stats:', error));
    
    // Fetch traffic data (default 10 minutes)
    refreshTrafficData(10);
    
    // Fetch DQN model info
    fetch('/api/model')
        .then(response => response.json())
        .then(data => updateModelInfo(data))
        .catch(error => console.error('Error fetching model info:', error));
}

function refreshTrafficData(minutes) {
    fetch(`/api/traffic?minutes=${minutes}`)
        .then(response => response.json())
        .then(data => updateTrafficData(data))
        .catch(error => console.error('Error fetching traffic data:', error));
}

function updateDashboard(data) {
    // Update latest stats
    const stats = data.latest;
    
    // Update status indicators
    document.getElementById('bandwidthValue').textContent = `${stats.total_bandwidth.toFixed(2)} Mbps`;
    document.getElementById('packetsValue').textContent = `${stats.total_packets} pps`;
    document.getElementById('latencyValue').textContent = `${stats.average_latency.toFixed(2)} ms`;
    document.getElementById('connectionsValue').textContent = stats.connection_count;
    
    // Update attack status
    const attackStatus = document.getElementById('attackStatus');
    if (stats.is_under_attack) {
        attackStatus.textContent = 'UNDER ATTACK';
        attackStatus.className = 'badge bg-danger';
        document.getElementById('suspiciousTraffic').textContent = `${stats.suspicious_traffic_percent.toFixed(2)}%`;
        document.getElementById('attackAlert').style.display = 'block';
    } else {
        attackStatus.textContent = 'Normal';
        attackStatus.className = 'badge bg-success';
        document.getElementById('suspiciousTraffic').textContent = `${stats.suspicious_traffic_percent.toFixed(2)}%`;
        document.getElementById('attackAlert').style.display = 'none';
    }
    
    // Update charts with historical data
    updateCharts(data.historical);
    
    // Update active attacks list
    updateActiveAttacks(data.active_attacks);
}

function updateCharts(historicalData) {
    // Format data for charts
    const timestamps = historicalData.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleTimeString();
    });
    
    const bandwidthData = historicalData.map(item => item.total_bandwidth);
    const latencyData = historicalData.map(item => item.average_latency);
    
    // Update bandwidth chart
    bandwidthChart.data.labels = timestamps;
    bandwidthChart.data.datasets[0].data = bandwidthData;
    
    // Add attack indicators
    bandwidthChart.data.datasets[1] = {
        label: 'Attack Period',
        data: historicalData.map(item => item.is_under_attack ? Math.max(...bandwidthData) * 1.1 : null),
        backgroundColor: 'rgba(255, 99, 132, 0.3)',
        borderColor: 'rgba(255, 99, 132, 0)',
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 0
    };
    
    bandwidthChart.update();
    
    // Update latency chart
    latencyChart.data.labels = timestamps;
    latencyChart.data.datasets[0].data = latencyData;
    latencyChart.update();
}

function updateTrafficData(data) {
    // Update packet distribution chart
    const protocolLabels = [];
    const protocolData = [];
    
    data.protocol_distribution.forEach(item => {
        protocolLabels.push(item._id || 'Unknown');
        protocolData.push(item.count);
    });
    
    packetDistributionChart.data.labels = protocolLabels;
    packetDistributionChart.data.datasets[0].data = protocolData;
    packetDistributionChart.update();
    
    // Update traffic sources chart
    const sourceLabels = [];
    const sourceData = [];
    
    data.top_sources.forEach(item => {
        sourceLabels.push(item._id);
        sourceData.push(item.count);
    });
    
    trafficSourcesChart.data.labels = sourceLabels;
    trafficSourcesChart.data.datasets[0].data = sourceData;
    trafficSourcesChart.update();
    
    // Update traffic stats
    document.getElementById('totalPackets').textContent = data.total_packets;
    document.getElementById('attackPackets').textContent = data.attack_packets;
    document.getElementById('attackPercentage').textContent = `${data.attack_percentage.toFixed(2)}%`;
}

function updateActiveAttacks(attacks) {
    const attacksList = document.getElementById('activeAttacksList');
    
    if (attacks.length === 0) {
        attacksList.innerHTML = '<li class="list-group-item">No active attacks</li>';
        return;
    }
    
    attacksList.innerHTML = '';
    attacks.forEach(attack => {
        const startTime = new Date(attack.start_time);
        const formattedTime = startTime.toLocaleString();
        
        let mitigationBadge = '';
        if (attack.mitigation_applied) {
            mitigationBadge = `<span class="badge bg-info">${attack.mitigation_action || 'Mitigated'}</span>`;
        } else {
            mitigationBadge = '<span class="badge bg-warning">No Mitigation</span>';
        }
        
        const severityClass = attack.severity >= 8 ? 'bg-danger' : 
                            attack.severity >= 5 ? 'bg-warning' : 'bg-info';
        
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.innerHTML = `
            <div>
                <strong>${attack.attack_type}</strong>
                <br>
                <small>Started: ${formattedTime}</small>
                <br>
                <div class="progress mt-1" style="height: 5px; width: 100px;">
                    <div class="progress-bar ${severityClass}" role="progressbar" 
                         style="width: ${attack.severity * 10}%" 
                         aria-valuenow="${attack.severity}" 
                         aria-valuemin="0" 
                         aria-valuemax="10"></div>
                </div>
                <small>Severity: ${attack.severity}/10</small>
            </div>
            <div>
                ${mitigationBadge}
            </div>
        `;
        attacksList.appendChild(li);
    });
}

function updateModelInfo(data) {
    document.getElementById('dqnEpsilon').textContent = data.epsilon.toFixed(4);
    document.getElementById('dqnMemorySize').textContent = data.memory_size;
    
    // Update average loss/reward if available
    if (data.average_loss !== null) {
        document.getElementById('dqnLoss').textContent = data.average_loss.toFixed(4);
    } else {
        document.getElementById('dqnLoss').textContent = 'N/A';
    }
    
    if (data.average_reward !== null) {
        document.getElementById('dqnReward').textContent = data.average_reward.toFixed(2);
    } else {
        document.getElementById('dqnReward').textContent = 'N/A';
    }
    
    // Update last training time
    if (data.last_training) {
        const lastTraining = new Date(data.last_training);
        document.getElementById('dqnLastTraining').textContent = lastTraining.toLocaleTimeString();
    } else {
        document.getElementById('dqnLastTraining').textContent = 'Never';
    }
    
    // Update actions list
    const actionsList = document.getElementById('dqnActions');
    actionsList.innerHTML = '';
    data.actions.forEach((action, index) => {
        const li = document.createElement('li');
        li.className = 'list-group-item small';
        li.textContent = `${index}: ${action}`;
        actionsList.appendChild(li);
    });
}
