// settings.js - Settings functionality for DDoS defense system

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form values from model & simulation settings
    initializeFormValues();
    
    // Setup range input display values
    setupRangeInputs();
    
    // Add event listeners for forms
    document.getElementById('dqnForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveDQNSettings();
    });
    
    document.getElementById('simulationForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSimulationSettings();
    });
    
    document.getElementById('thresholdsForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveThresholdSettings();
    });
    
    // Add event listeners for action buttons
    document.getElementById('resetSimulation').addEventListener('click', resetSimulation);
    document.getElementById('resetDQN').addEventListener('click', resetDQNModel);
    document.getElementById('checkStatus').addEventListener('click', checkSystemStatus);
    
    // Check system status initially
    checkSystemStatus();
});

// Setup display values for range inputs
function setupRangeInputs() {
    // DQN Form
    setupRangeInput('gamma', 'gammaValue');
    setupRangeInput('epsilon', 'epsilonValue');
    setupRangeInput('epsilonDecay', 'epsilonDecayValue');
    setupRangeInput('learningRate', 'learningRateValue');
    
    // Simulation Form
    setupRangeInput('simulationSpeed', 'simulationSpeedValue');
    setupRangeInput('attackProbability', 'attackProbabilityValue');
    
    // Thresholds Form
    setupRangeInput('synRatioThreshold', 'synRatioThresholdValue');
    setupRangeInput('entropyThreshold', 'entropyThresholdValue');
}

function setupRangeInput(inputId, valueId) {
    const input = document.getElementById(inputId);
    const valueDisplay = document.getElementById(valueId);
    
    if (input && valueDisplay) {
        // Update display on input change
        input.addEventListener('input', function() {
            valueDisplay.textContent = input.value;
        });
        
        // Set initial value
        valueDisplay.textContent = input.value;
    }
}

// Initialize form values from backend settings
function initializeFormValues() {
    // Fetch current model settings
    fetch('/api/model')
        .then(response => response.json())
        .then(data => {
            // DQN settings
            if (data.epsilon) {
                document.getElementById('epsilon').value = data.epsilon;
                document.getElementById('epsilonValue').textContent = data.epsilon.toFixed(2);
            }
            
            // Other model parameters could be set here if the API provides them
        })
        .catch(error => console.error('Error fetching model settings:', error));
    
    // In a full implementation, we would also fetch simulation and threshold settings
    // For this demo, we'll use the defaults set in the HTML
}

// Save DQN settings
function saveDQNSettings() {
    const settings = {
        gamma: parseFloat(document.getElementById('gamma').value),
        epsilon: parseFloat(document.getElementById('epsilon').value),
        epsilonDecay: parseFloat(document.getElementById('epsilonDecay').value),
        learningRate: parseFloat(document.getElementById('learningRate').value),
        batchSize: parseInt(document.getElementById('batchSize').value),
        memorySize: parseInt(document.getElementById('memorySize').value),
        targetUpdateFreq: parseInt(document.getElementById('targetUpdateFreq').value)
    };
    
    // In a real implementation, this would send data to the backend
    // For now, we'll just simulate success
    console.log('DQN settings to save:', settings);
    
    // Show success message
    showAlert('DQN settings saved successfully!', 'success');
}

// Save simulation settings
function saveSimulationSettings() {
    const settings = {
        numNodes: parseInt(document.getElementById('numNodes').value),
        numRouters: parseInt(document.getElementById('numRouters').value),
        numServers: parseInt(document.getElementById('numServers').value),
        simulationSpeed: parseFloat(document.getElementById('simulationSpeed').value),
        attackProbability: parseFloat(document.getElementById('attackProbability').value),
        attackDuration: [
            parseInt(document.getElementById('attackDurationMin').value),
            parseInt(document.getElementById('attackDurationMax').value)
        ],
        maxAttackers: parseInt(document.getElementById('maxAttackers').value),
        normalTraffic: [
            parseInt(document.getElementById('normalTrafficMin').value),
            parseInt(document.getElementById('normalTrafficMax').value)
        ],
        attackTraffic: [
            parseInt(document.getElementById('attackTrafficMin').value),
            parseInt(document.getElementById('attackTrafficMax').value)
        ]
    };
    
    // In a real implementation, this would send data to the backend
    // For now, we'll just simulate success
    console.log('Simulation settings to save:', settings);
    
    // Show success message
    showAlert('Simulation settings saved successfully!', 'success');
}

// Save threshold settings
function saveThresholdSettings() {
    const settings = {
        packetRateThreshold: parseInt(document.getElementById('packetRateThreshold').value),
        connectionThreshold: parseInt(document.getElementById('connectionThreshold').value),
        synRatioThreshold: parseFloat(document.getElementById('synRatioThreshold').value),
        entropyThreshold: parseFloat(document.getElementById('entropyThreshold').value)
    };
    
    // In a real implementation, this would send data to the backend
    // For now, we'll just simulate success
    console.log('Threshold settings to save:', settings);
    
    // Show success message
    showAlert('Defense threshold settings saved successfully!', 'success');
}

// Reset simulation
function resetSimulation() {
    if (confirm('Are you sure you want to reset the network simulation? This will clear all current network data.')) {
        // In a real implementation, this would send a reset command to the backend
        // For now, we'll just simulate success
        
        // Show success message
        showAlert('Network simulation has been reset successfully!', 'success');
    }
}

// Reset DQN model
function resetDQNModel() {
    if (confirm('Are you sure you want to reset the DQN model? This will clear all trained parameters and experience memory.')) {
        // In a real implementation, this would send a reset command to the backend
        // For now, we'll just simulate success
        
        // Show success message
        showAlert('DQN model has been reset successfully!', 'warning');
    }
}

// Check system status
function checkSystemStatus() {
    // In a full implementation, this would check actual system status from the backend
    // For demo purposes, we'll randomize some statuses
    
    const statuses = ['normal', 'warning', 'danger'];
    const randomStatus = () => statuses[Math.floor(Math.random() * 3)];
    
    // Update database statuses
    updateStatusIndicator('postgresStatus', 'postgresStatusText', 'normal', 'Connected');
    updateStatusIndicator('mongoStatus', 'mongoStatusText', 'normal', 'Connected');
    updateStatusIndicator('neo4jStatus', 'neo4jStatusText', randomStatus(), 
                         randomStatus() === 'normal' ? 'Connected' : 'Connection issues');
    
    // Update system components
    updateStatusIndicator('simulationStatus', 'simulationStatusText', 'normal', 'Running');
    updateStatusIndicator('detectorStatus', 'detectorStatusText', 'normal', 'Active');
    updateStatusIndicator('dqnStatus', 'dqnStatusText', 'normal', 'Trained');
    
    // Show status check message
    showAlert('System status checked successfully!', 'info');
}

// Helper function to update status indicators
function updateStatusIndicator(indicatorId, textId, status, message) {
    const indicator = document.getElementById(indicatorId);
    const text = document.getElementById(textId);
    
    if (indicator && text) {
        // Remove old classes
        indicator.classList.remove('status-normal', 'status-warning', 'status-danger');
        
        // Add new class and update text
        indicator.classList.add(`status-${status}`);
        text.textContent = message;
    }
}

// Helper function to show alerts
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to document
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 3000);
}
