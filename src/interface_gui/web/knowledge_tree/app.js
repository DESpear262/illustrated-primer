// Knowledge Tree JavaScript Application
// Uses Cytoscape.js for graph visualization

let cy;
let bridge;
let hoverPopup;
let currentNodeData = {}; // Store node data for quick lookup

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize QtWebChannel
    new QWebChannel(qt.webChannelTransport, function(channel) {
        bridge = channel.objects.bridge;
        
        // Initialize Cytoscape
        initCytoscape();
        
        // Load initial graph
        refreshGraph('root', 2, 'all');
    });
    
    // Setup hover popup
    hoverPopup = document.getElementById('hover-popup');
    document.getElementById('popup-close').addEventListener('click', function() {
        hoverPopup.classList.add('hidden');
    });
});

function initCytoscape() {
    // Initialize Cytoscape instance
    cy = cytoscape({
        container: document.getElementById('cy'),
        
        // Layout
        layout: {
            name: 'dagre',
            rankDir: 'TB',
            nodeSep: 50,
            edgeSep: 20,
            rankSep: 100,
        },
        
        // Style
        style: [
            {
                selector: 'node[type="topic"]',
                style: {
                    'shape': 'round-rectangle',
                    'width': 120,
                    'height': 60,
                    'background-color': '#4A90E2',
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'color': '#fff',
                    'font-size': '12px',
                    'font-weight': 'bold',
                    'border-width': 2,
                    'border-color': '#2E5C8A',
                }
            },
            {
                selector: 'node[type="skill"]',
                style: {
                    'shape': 'ellipse',
                    'width': 80,
                    'height': 80,
                    'background-color': 'data(masteryColor)',
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'color': '#333',
                    'font-size': '11px',
                    'border-width': 2,
                    'border-color': '#666',
                }
            },
            {
                selector: 'edge[type="parent-child"]',
                style: {
                    'width': 2,
                    'line-color': '#4A90E2',
                    'target-arrow-color': '#4A90E2',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                }
            },
            {
                selector: 'edge[type="topic-skill"]',
                style: {
                    'width': 1,
                    'line-color': '#999',
                    'line-style': 'dashed',
                    'target-arrow-color': '#999',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#FFD700',
                }
            },
            {
                selector: 'node.highlighted',
                style: {
                    'border-width': 4,
                    'border-color': '#FF6B6B',
                    'transition-property': 'border-width, border-color',
                    'transition-duration': '0.3s',
                }
            }
        ],
        
        // User interactions
        userPanningEnabled: true,
        userZoomingEnabled: true,
        boxSelectionEnabled: false,
    });
    
    // Register Dagre layout
    cytoscape.use(cytoscapeDagre);
    
    // Event handlers
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        const nodeId = node.id();
        const nodeType = node.data('type');
        
        // Show hover popup
        showHoverPopup(nodeId, nodeType);
        
        // Notify Python
        if (bridge) {
            bridge.onNodeClicked(nodeId);
        }
    });
    
    cy.on('dbltap', 'node', function(evt) {
        const node = evt.target;
        const nodeId = node.id();
        const nodeType = node.data('type');
        
        // Notify Python
        if (bridge) {
            bridge.onNodeDoubleClicked(nodeId, nodeType);
        }
    });
    
    cy.on('mouseover', 'node', function(evt) {
        const node = evt.target;
        node.addClass('hover');
    });
    
    cy.on('mouseout', 'node', function(evt) {
        const node = evt.target;
        node.removeClass('hover');
    });
}

function refreshGraph(scope, depth, relation) {
    if (!bridge) {
        console.error('Bridge not initialized');
        return;
    }
    
    // Show loading indicator
    cy.elements().remove();
    
    // Get graph data from Python
    const graphJson = bridge.getGraph(scope, depth, relation);
    const graphData = JSON.parse(graphJson);
    
    if (graphData.error) {
        console.error('Error loading graph:', graphData.error);
        return;
    }
    
    // Store node data for quick lookup
    currentNodeData = {};
    graphData.nodes.forEach(node => {
        currentNodeData[node.data.id] = node.data;
    });
    
    // Process nodes: add mastery color for skills
    const processedNodes = graphData.nodes.map(node => {
        const data = node.data;
        
        if (data.type === 'skill' && data.p_mastery !== undefined) {
            // Calculate color based on mastery (red → yellow → green)
            const mastery = data.p_mastery;
            let r, g, b;
            
            if (mastery < 0.5) {
                // Red to Yellow
                const t = mastery * 2;
                r = 255;
                g = Math.round(255 * t);
                b = 0;
            } else {
                // Yellow to Green
                const t = (mastery - 0.5) * 2;
                r = Math.round(255 * (1 - t));
                g = 255;
                b = 0;
            }
            
            data.masteryColor = `rgb(${r}, ${g}, ${b})`;
        }
        
        return node;
    });
    
    // Add elements to graph
    cy.add({
        nodes: processedNodes,
        edges: graphData.edges,
    });
    
    // Apply layout
    cy.layout({
        name: 'dagre',
        rankDir: 'TB',
        nodeSep: 50,
        edgeSep: 20,
        rankSep: 100,
    }).run();
    
    // Fit to screen
    cy.fit();
}

function showHoverPopup(nodeId, nodeType) {
    if (!bridge) {
        return;
    }
    
    // Get hover payload from Python
    const hoverJson = bridge.getHoverPayload(nodeId, nodeType);
    const hoverData = JSON.parse(hoverJson);
    
    if (hoverData.error) {
        console.error('Error loading hover data:', hoverData.error);
        return;
    }
    
    // Update popup content
    const titleEl = document.getElementById('popup-title');
    const bodyEl = document.getElementById('popup-body');
    
    if (nodeType === 'topic') {
        titleEl.textContent = `Topic: ${hoverData.title || nodeId}`;
        bodyEl.innerHTML = `
            <p><strong>Summary:</strong> ${hoverData.summary || 'No summary available'}</p>
            <p><strong>Event Count:</strong> ${hoverData.event_count || 0}</p>
            <p><strong>Last Event:</strong> ${hoverData.last_event_at || 'Never'}</p>
            <p><strong>Average Mastery:</strong> ${hoverData.average_mastery ? hoverData.average_mastery.toFixed(2) : 'N/A'}</p>
            <p><strong>Child Skills:</strong> ${hoverData.child_skills_count || 0}</p>
            ${hoverData.open_questions && hoverData.open_questions.length > 0 ? `
                <p><strong>Open Questions:</strong></p>
                <ul>
                    ${hoverData.open_questions.map(q => `<li>${q}</li>`).join('')}
                </ul>
            ` : ''}
        `;
    } else if (nodeType === 'skill') {
        titleEl.textContent = `Skill: ${hoverData.title || nodeId}`;
        bodyEl.innerHTML = `
            <p><strong>Mastery:</strong> ${hoverData.p_mastery ? hoverData.p_mastery.toFixed(2) : 'N/A'}</p>
            <p><strong>Last Evidence:</strong> ${hoverData.last_evidence_at || 'Never'}</p>
            <p><strong>Evidence Count:</strong> ${hoverData.evidence_count || 0}</p>
            ${hoverData.recent_event_snippet ? `
                <p><strong>Recent Event:</strong></p>
                <p>${hoverData.recent_event_snippet}</p>
            ` : ''}
        `;
    }
    
    // Show popup
    hoverPopup.classList.remove('hidden');
}

function focusNode(nodeId) {
    if (!cy) {
        return;
    }
    
    const node = cy.getElementById(nodeId);
    if (node.length === 0) {
        console.warn('Node not found:', nodeId);
        return;
    }
    
    // Center node
    cy.center(node);
    cy.fit(node, 50); // 50px padding
    
    // Highlight node
    node.addClass('highlighted');
    
    // Remove highlight after 2 seconds
    setTimeout(() => {
        node.removeClass('highlighted');
    }, 2000);
    
    // Expand path to node if needed
    // (This would require loading parent nodes if not already loaded)
}

function fitToScreen() {
    if (!cy) {
        return;
    }
    
    cy.fit(50); // 50px padding
}

// Expose functions to Python
window.refreshGraph = refreshGraph;
window.focusNode = focusNode;
window.fitToScreen = fitToScreen;

