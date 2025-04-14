// Network visualization script using D3.js

// SVG dimensions
let width = 800;
let height = 600;

// D3 force simulation
let simulation;

// SVG and group elements
let svg, g;

// Node and link data
let nodeData = [];
let linkData = [];

// Initialize visualization
document.addEventListener('DOMContentLoaded', function() {
    // Set initial dimensions based on container
    const container = document.getElementById('network-visualization');
    width = container.clientWidth;
    height = container.clientHeight || 600;
    
    // Create SVG
    svg = d3.select('#network-visualization')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height])
        .attr('style', 'max-width: 100%; height: auto;');
    
    // Add zoom functionality
    const zoom = d3.zoom()
        .scaleExtent([0.1, 3])
        .on('zoom', zoomed);
    
    svg.call(zoom);
    
    // Create a group for the graph
    g = svg.append('g');
    
    // Add legend
    addLegend();
    
    // Initialize simulation
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('x', d3.forceX(width / 2).strength(0.05))
        .force('y', d3.forceY(height / 2).strength(0.05));
    
    // Load initial data
    loadNetworkData();
    
    // Set refresh interval
    setInterval(loadNetworkData, 5000);
    
    // Add resize handler
    window.addEventListener('resize', handleResize);
});

function zoomed(event) {
    g.attr('transform', event.transform);
}

function handleResize() {
    const container = document.getElementById('network-visualization');
    width = container.clientWidth;
    height = container.clientHeight || 600;
    
    svg.attr('width', width)
       .attr('height', height)
       .attr('viewBox', [0, 0, width, height]);
    
    // Update force center
    simulation.force('center', d3.forceCenter(width / 2, height / 2))
              .force('x', d3.forceX(width / 2).strength(0.05))
              .force('y', d3.forceY(height / 2).strength(0.05))
              .alpha(0.3).restart();
}

function addLegend() {
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(20, 20)');
    
    // Node types
    const nodeTypes = [
        { type: 'host', color: '#69b3a2', label: 'Host' },
        { type: 'router', color: '#404080', label: 'Router' },
        { type: 'server', color: '#4C4CFF', label: 'Server' },
        { type: 'attacker', color: '#FF4C4C', label: 'Attacker' },
        { type: 'victim', color: '#FFD700', label: 'Victim' }
    ];
    
    // Add node type legend
    nodeTypes.forEach((type, i) => {
        const group = legend.append('g')
            .attr('transform', `translate(0, ${i * 25})`);
        
        group.append('circle')
            .attr('r', 7)
            .attr('fill', type.color);
        
        group.append('text')
            .attr('x', 15)
            .attr('y', 5)
            .text(type.label)
            .style('font-size', '12px');
    });
    
    // Add link legend
    const linkTypes = [
        { type: 'normal', color: '#999', label: 'Normal Connection' },
        { type: 'attack', color: '#FF0000', label: 'Attack Path' }
    ];
    
    const linkLegend = legend.append('g')
        .attr('transform', `translate(0, ${nodeTypes.length * 25 + 10})`);
    
    linkTypes.forEach((type, i) => {
        const group = linkLegend.append('g')
            .attr('transform', `translate(0, ${i * 25})`);
        
        group.append('line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', 30)
            .attr('y2', 0)
            .attr('stroke', type.color)
            .attr('stroke-width', type.type === 'attack' ? 3 : 1.5);
        
        group.append('text')
            .attr('x', 35)
            .attr('y', 5)
            .text(type.label)
            .style('font-size', '12px');
    });
}

function loadNetworkData() {
    // Fetch network data from API
    fetch('/api/network')
        .then(response => response.json())
        .then(data => {
            // Update global data
            nodeData = data.nodes;
            linkData = data.links;
            
            // Update visualization
            updateVisualization();
            
            // Also fetch attack paths
            fetch('/api/attack_paths')
                .then(response => response.json())
                .then(paths => {
                    updateAttackPaths(paths);
                })
                .catch(error => console.error('Error fetching attack paths:', error));
        })
        .catch(error => console.error('Error fetching network data:', error));
}

function updateVisualization() {
    // Create links
    const link = g.selectAll('.link')
        .data(linkData, d => `${d.source}-${d.target}`);
    
    // Remove old links
    link.exit().remove();
    
    // Add new links
    const linkEnter = link.enter()
        .append('line')
        .attr('class', 'link')
        .attr('stroke', d => d.is_attack_path ? '#FF0000' : '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => d.is_attack_path ? 3 : 1.5);
    
    // Merge links
    const linkMerge = linkEnter.merge(link);
    
    // Create nodes
    const node = g.selectAll('.node')
        .data(nodeData, d => d.id);
    
    // Remove old nodes
    node.exit().remove();
    
    // Add new nodes
    const nodeEnter = node.enter()
        .append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add node circles
    nodeEnter.append('circle')
        .attr('r', 10)
        .attr('fill', getNodeColor)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5);
    
    // Add node labels
    nodeEnter.append('text')
        .attr('dx', 12)
        .attr('dy', '.35em')
        .text(d => {
            if (d.type === 'router') return `Router (${d.ip})`;
            if (d.type === 'server') return `Server (${d.ip})`;
            return `${d.ip}`;
        })
        .style('font-size', '10px');
    
    // Add title for tooltip
    nodeEnter.append('title')
        .text(d => `${d.id}\nIP: ${d.ip}\nType: ${d.type}${d.is_attacker ? '\nATTACKER' : ''}${d.is_victim ? '\nVICTIM' : ''}`);
    
    // Merge nodes
    const nodeMerge = nodeEnter.merge(node);
    
    // Update node colors
    nodeMerge.selectAll('circle')
        .attr('fill', getNodeColor);
    
    // Update node titles
    nodeMerge.selectAll('title')
        .text(d => `${d.id}\nIP: ${d.ip}\nType: ${d.type}${d.is_attacker ? '\nATTACKER' : ''}${d.is_victim ? '\nVICTIM' : ''}`);
    
    // Update simulation
    simulation.nodes(nodeData)
        .on('tick', ticked);
    
    simulation.force('link')
        .links(linkData);
    
    // Restart simulation
    simulation.alpha(0.3).restart();
    
    // Tick function for positioning
    function ticked() {
        linkMerge
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        nodeMerge
            .attr('transform', d => `translate(${d.x},${d.y})`);
    }
}

function updateAttackPaths(paths) {
    // Update links to show attack paths
    const link = g.selectAll('.link');
    
    // Reset all attack paths
    link.attr('stroke', '#999')
        .attr('stroke-width', 1.5)
        .attr('stroke-opacity', 0.6);
    
    // Highlight attack paths
    paths.forEach(path => {
        for (let i = 0; i < path.path.length - 1; i++) {
            const source = path.path[i];
            const target = path.path[i+1];
            
            link.filter(d => 
                (d.source.id === source && d.target.id === target) || 
                (d.source.id === target && d.target.id === source)
            )
            .attr('stroke', '#FF0000')
            .attr('stroke-width', 3)
            .attr('stroke-opacity', 0.8);
        }
    });
    
    // Update attack info
    updateAttackInfo(paths);
}

function updateAttackInfo(paths) {
    const infoContainer = document.getElementById('attack-paths-info');
    
    if (paths.length === 0) {
        infoContainer.innerHTML = '<div class="alert alert-info">No active attack paths detected</div>';
        return;
    }
    
    let html = '<div class="list-group">';
    
    paths.forEach((path, index) => {
        html += `
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">Attack Path ${index + 1}</h5>
                    <small>Path length: ${path.length}</small>
                </div>
                <p class="mb-1">Attacker: ${path.attacker} → Victim: ${path.victim}</p>
                <small>Path: ${path.path.join(' → ')}</small>
            </div>
        `;
    });
    
    html += '</div>';
    infoContainer.innerHTML = html;
}

function getNodeColor(d) {
    // Color nodes based on type and status
    if (d.is_attacker) return '#FF4C4C'; // Attacker
    if (d.is_victim) return '#FFD700';   // Victim
    
    switch (d.type) {
        case 'router':
            return '#404080'; // Dark blue
        case 'server':
            return '#4C4CFF'; // Blue
        case 'host':
        default:
            return '#69b3a2'; // Teal
    }
}

function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}
