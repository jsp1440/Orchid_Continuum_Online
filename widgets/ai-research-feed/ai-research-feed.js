/**
 * AI Research Feed Widget - Live AI-to-AI Collaboration Viewer
 * Shows Julius AI ↔ Replit Agent conversations and research insights
 * Embeddable in Neon One CMS for FCOS members
 */

class AIResearchFeedWidget {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.apiBase = options.apiBase || 'https://orchid-continuum.replit.app';
        this.refreshInterval = options.refreshInterval || 60000; // 1 minute
        this.maxMessages = options.maxMessages || 20;
        this.showInsights = options.showInsights !== false; // default true
        this.showCommunication = options.showCommunication !== false; // default true
        this.adminMode = options.adminMode || false;
        
        this.init();
    }
    
    init() {
        this.render();
        this.fetchData();
        
        // Auto-refresh
        setInterval(() => this.fetchData(), this.refreshInterval);
    }
    
    render() {
        this.container.innerHTML = `
            <div class="ai-research-feed">
                <div class="feed-header">
                    <h2>🤖 Live AI Research Feed</h2>
                    <p class="subtitle">Autonomous orchid research by Julius AI & Replit Agent</p>
                    <div class="status-indicator">
                        <span class="status-dot"></span>
                        <span class="status-text">Monitoring...</span>
                    </div>
                </div>
                
                <div class="feed-tabs">
                    ${this.showCommunication ? '<button class="tab-btn active" data-tab="conversation">💬 AI Conversation</button>' : ''}
                    ${this.showInsights ? '<button class="tab-btn" data-tab="insights">🔬 Research Insights</button>' : ''}
                    <button class="tab-btn" data-tab="stats">📊 Statistics</button>
                </div>
                
                <div class="feed-content">
                    ${this.showCommunication ? '<div class="tab-panel active" id="conversation-panel"></div>' : ''}
                    ${this.showInsights ? '<div class="tab-panel" id="insights-panel"></div>' : ''}
                    <div class="tab-panel" id="stats-panel"></div>
                </div>
                
                <div class="feed-footer">
                    <small>Last updated: <span id="last-update">Never</span></small>
                    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                </div>
            </div>
        `;
        
        this.attachEventListeners();
        this.injectStyles();
    }
    
    attachEventListeners() {
        const tabs = this.container.querySelectorAll('.tab-btn');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const panels = this.container.querySelectorAll('.tab-panel');
                panels.forEach(p => p.classList.remove('active'));
                
                const panelId = tab.dataset.tab + '-panel';
                document.getElementById(panelId).classList.add('active');
            });
        });
    }
    
    async fetchData() {
        try {
            // Fetch AI communication
            const commResponse = await fetch(`${this.apiBase}/api/ai-communication?limit=${this.maxMessages}`);
            const communication = await commResponse.json();
            
            // Fetch research insights
            const insightsResponse = await fetch(`${this.apiBase}/api/research-insights?limit=${this.maxMessages}`);
            const insights = await insightsResponse.json();
            
            // Fetch stats
            const statsResponse = await fetch(`${this.apiBase}/api/ai-stats`);
            const stats = await statsResponse.json();
            
            this.renderCommunication(communication);
            this.renderInsights(insights);
            this.renderStats(stats);
            
            this.updateStatus('active');
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            
        } catch (error) {
            console.error('Error fetching AI research data:', error);
            this.updateStatus('error');
        }
    }
    
    renderCommunication(messages) {
        const panel = document.getElementById('conversation-panel');
        if (!panel) return;
        
        if (!messages || messages.length === 0) {
            panel.innerHTML = '<div class="empty-state">No AI conversations yet. System initializing...</div>';
            return;
        }
        
        const html = messages.map(msg => this.renderMessage(msg)).join('');
        panel.innerHTML = `<div class="conversation-list">${html}</div>`;
    }
    
    renderMessage(msg) {
        const isJulius = msg.from_agent === 'julius_ai';
        const icon = isJulius ? '🧠' : '🤖';
        const agentName = isJulius ? 'Julius AI' : 'Replit Agent';
        const agentClass = isJulius ? 'julius' : 'replit';
        
        const statusBadge = this.getStatusBadge(msg.status);
        const timestamp = new Date(msg.created_at).toLocaleString();
        
        return `
            <div class="message ${agentClass}">
                <div class="message-header">
                    <span class="agent-icon">${icon}</span>
                    <span class="agent-name">${agentName}</span>
                    <span class="task-id">${msg.task_id}</span>
                    ${statusBadge}
                </div>
                <div class="message-content">
                    <div class="message-type">${msg.message_type}</div>
                    ${msg.prompt_text ? `<div class="prompt-text">${this.truncate(msg.prompt_text, 200)}</div>` : ''}
                    ${msg.result_summary ? `<div class="result-summary">✅ ${msg.result_summary}</div>` : ''}
                    ${msg.error_message ? `<div class="error-message">❌ ${msg.error_message}</div>` : ''}
                </div>
                <div class="message-footer">
                    <small>${timestamp}</small>
                    ${msg.file_path ? `<small>📄 ${msg.file_path.split('/').pop()}</small>` : ''}
                </div>
            </div>
        `;
    }
    
    renderInsights(insights) {
        const panel = document.getElementById('insights-panel');
        if (!panel) return;
        
        if (!insights || insights.length === 0) {
            panel.innerHTML = '<div class="empty-state">No research insights yet. Julius AI will discover patterns soon...</div>';
            return;
        }
        
        const html = insights.map(insight => this.renderInsight(insight)).join('');
        panel.innerHTML = `<div class="insights-list">${html}</div>`;
    }
    
    renderInsight(insight) {
        const typeIcon = this.getInsightIcon(insight.insight_type);
        const areaIcon = this.getAreaIcon(insight.research_area);
        const confidenceBadge = this.getConfidenceBadge(insight.confidence_level);
        const impactStars = this.getImpactStars(insight.impact_score);
        
        return `
            <div class="insight-card ${insight.insight_type}">
                <div class="insight-header">
                    <span class="type-icon">${typeIcon}</span>
                    <span class="insight-type">${insight.insight_type}</span>
                    <span class="area-badge">${areaIcon} ${insight.research_area}</span>
                    ${confidenceBadge}
                </div>
                <div class="insight-content">
                    <p class="insight-text">${insight.insight_text}</p>
                    ${insight.proposed_followup ? `
                        <div class="followup">
                            <strong>Next steps:</strong> ${insight.proposed_followup}
                        </div>
                    ` : ''}
                </div>
                <div class="insight-footer">
                    <span class="impact">${impactStars}</span>
                    <small>${new Date(insight.created_at).toLocaleDateString()}</small>
                    ${insight.julius_generated ? '<span class="julius-badge">🧠 Julius AI</span>' : ''}
                </div>
            </div>
        `;
    }
    
    renderStats(stats) {
        const panel = document.getElementById('stats-panel');
        if (!panel) return;
        
        panel.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${stats.total_tasks || 0}</div>
                    <div class="stat-label">Total Tasks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.completed_tasks || 0}</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.pending_tasks || 0}</div>
                    <div class="stat-label">Pending</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.total_insights || 0}</div>
                    <div class="stat-label">Insights Discovered</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.hypotheses_tested || 0}</div>
                    <div class="stat-label">Hypotheses Tested</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.research_proposals || 0}</div>
                    <div class="stat-label">Research Proposals</div>
                </div>
            </div>
            
            <div class="recent-activity">
                <h3>Recent Activity Timeline</h3>
                <div class="timeline">
                    ${this.renderTimeline(stats.recent_activity || [])}
                </div>
            </div>
        `;
    }
    
    renderTimeline(activities) {
        if (!activities || activities.length === 0) {
            return '<p class="empty-state">No recent activity</p>';
        }
        
        return activities.map(activity => `
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-content">
                    <div class="timeline-title">${activity.title}</div>
                    <div class="timeline-time">${this.timeAgo(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');
    }
    
    // Helper methods
    getStatusBadge(status) {
        const badges = {
            'pending': '<span class="status-badge pending">⏳ Pending</span>',
            'in_progress': '<span class="status-badge in-progress">⚙️ In Progress</span>',
            'completed': '<span class="status-badge completed">✅ Completed</span>',
            'error': '<span class="status-badge error">❌ Error</span>'
        };
        return badges[status] || '';
    }
    
    getInsightIcon(type) {
        const icons = {
            'finding': '🔍',
            'hypothesis': '💡',
            'anomaly': '⚠️',
            'correlation': '📊',
            'gap': '🕳️',
            'prediction': '🔮'
        };
        return icons[type] || '📝';
    }
    
    getAreaIcon(area) {
        const icons = {
            'pollination': '🐝',
            'climate': '🌡️',
            'evolution': '🧬',
            'geography': '🌍',
            'traits': '🌸',
            'conservation': '🛡️'
        };
        return icons[area] || '🔬';
    }
    
    getConfidenceBadge(level) {
        const badges = {
            'high': '<span class="confidence-badge high">High Confidence</span>',
            'medium': '<span class="confidence-badge medium">Medium Confidence</span>',
            'low': '<span class="confidence-badge low">Low Confidence</span>'
        };
        return badges[level] || '';
    }
    
    getImpactStars(score) {
        if (!score) return '';
        const stars = '⭐'.repeat(Math.min(Math.floor(score / 2), 5));
        return `<span class="impact-stars">${stars}</span>`;
    }
    
    truncate(text, length) {
        if (!text) return '';
        return text.length > length ? text.substring(0, length) + '...' : text;
    }
    
    timeAgo(timestamp) {
        const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    }
    
    updateStatus(status) {
        const dot = this.container.querySelector('.status-dot');
        const text = this.container.querySelector('.status-text');
        
        if (status === 'active') {
            dot.style.backgroundColor = '#00ff00';
            text.textContent = 'Live';
        } else if (status === 'error') {
            dot.style.backgroundColor = '#ff0000';
            text.textContent = 'Connection Error';
        }
    }
    
    injectStyles() {
        if (document.getElementById('ai-research-feed-styles')) return;
        
        const styles = `
            <style id="ai-research-feed-styles">
                .ai-research-feed {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 16px;
                    padding: 24px;
                    color: #fff;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }
                
                .feed-header {
                    text-align: center;
                    margin-bottom: 24px;
                }
                
                .feed-header h2 {
                    margin: 0 0 8px 0;
                    font-size: 28px;
                }
                
                .subtitle {
                    margin: 0 0 16px 0;
                    opacity: 0.9;
                    font-size: 14px;
                }
                
                .status-indicator {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background: rgba(255,255,255,0.2);
                    padding: 6px 12px;
                    border-radius: 20px;
                }
                
                .status-dot {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: #00ff00;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                
                .feed-tabs {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 16px;
                    flex-wrap: wrap;
                }
                
                .tab-btn {
                    flex: 1;
                    min-width: 120px;
                    padding: 12px 16px;
                    border: none;
                    background: rgba(255,255,255,0.1);
                    color: #fff;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s;
                    font-size: 14px;
                }
                
                .tab-btn:hover {
                    background: rgba(255,255,255,0.2);
                    transform: translateY(-2px);
                }
                
                .tab-btn.active {
                    background: rgba(255,255,255,0.3);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                }
                
                .feed-content {
                    background: rgba(255,255,255,0.95);
                    border-radius: 12px;
                    padding: 20px;
                    min-height: 400px;
                    max-height: 600px;
                    overflow-y: auto;
                    color: #333;
                }
                
                .tab-panel {
                    display: none;
                }
                
                .tab-panel.active {
                    display: block;
                }
                
                .conversation-list, .insights-list {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                
                .message {
                    background: #fff;
                    border-radius: 12px;
                    padding: 16px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border-left: 4px solid #667eea;
                }
                
                .message.julius {
                    border-left-color: #764ba2;
                }
                
                .message-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 12px;
                    flex-wrap: wrap;
                }
                
                .agent-icon {
                    font-size: 24px;
                }
                
                .agent-name {
                    font-weight: 600;
                    color: #667eea;
                }
                
                .message.julius .agent-name {
                    color: #764ba2;
                }
                
                .task-id {
                    font-family: monospace;
                    background: #f0f0f0;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                
                .status-badge {
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                }
                
                .status-badge.completed {
                    background: #d4edda;
                    color: #155724;
                }
                
                .status-badge.in-progress {
                    background: #fff3cd;
                    color: #856404;
                }
                
                .status-badge.pending {
                    background: #d1ecf1;
                    color: #0c5460;
                }
                
                .status-badge.error {
                    background: #f8d7da;
                    color: #721c24;
                }
                
                .message-content {
                    margin: 12px 0;
                }
                
                .message-type {
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                }
                
                .prompt-text {
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    margin: 8px 0;
                    font-size: 14px;
                    line-height: 1.5;
                }
                
                .result-summary {
                    padding: 12px;
                    background: #d4edda;
                    border-radius: 8px;
                    margin: 8px 0;
                    font-size: 14px;
                }
                
                .error-message {
                    padding: 12px;
                    background: #f8d7da;
                    border-radius: 8px;
                    margin: 8px 0;
                    font-size: 14px;
                }
                
                .message-footer {
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    color: #666;
                    margin-top: 8px;
                }
                
                .insight-card {
                    background: #fff;
                    border-radius: 12px;
                    padding: 16px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border-left: 4px solid #00bcd4;
                }
                
                .insight-card.finding {
                    border-left-color: #4caf50;
                }
                
                .insight-card.hypothesis {
                    border-left-color: #ff9800;
                }
                
                .insight-card.anomaly {
                    border-left-color: #f44336;
                }
                
                .insight-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 12px;
                    flex-wrap: wrap;
                }
                
                .type-icon {
                    font-size: 24px;
                }
                
                .insight-type {
                    font-weight: 600;
                    text-transform: capitalize;
                    color: #333;
                }
                
                .area-badge {
                    background: #e3f2fd;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    color: #1976d2;
                }
                
                .confidence-badge {
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                }
                
                .confidence-badge.high {
                    background: #d4edda;
                    color: #155724;
                }
                
                .confidence-badge.medium {
                    background: #fff3cd;
                    color: #856404;
                }
                
                .confidence-badge.low {
                    background: #f8d7da;
                    color: #721c24;
                }
                
                .insight-text {
                    font-size: 16px;
                    line-height: 1.6;
                    margin: 12px 0;
                    color: #333;
                }
                
                .followup {
                    padding: 12px;
                    background: #f0f8ff;
                    border-radius: 8px;
                    margin-top: 12px;
                    font-size: 14px;
                }
                
                .insight-footer {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 12px;
                    font-size: 12px;
                    color: #666;
                }
                
                .julius-badge {
                    background: #764ba2;
                    color: #fff;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 16px;
                    margin-bottom: 24px;
                }
                
                .stat-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #fff;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                }
                
                .stat-value {
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 8px;
                }
                
                .stat-label {
                    font-size: 14px;
                    opacity: 0.9;
                }
                
                .recent-activity h3 {
                    margin: 0 0 16px 0;
                    color: #333;
                }
                
                .timeline {
                    position: relative;
                    padding-left: 32px;
                }
                
                .timeline-item {
                    position: relative;
                    padding-bottom: 24px;
                }
                
                .timeline-dot {
                    position: absolute;
                    left: -32px;
                    top: 0;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: #667eea;
                    border: 3px solid #fff;
                    box-shadow: 0 0 0 2px #667eea;
                }
                
                .timeline-item:before {
                    content: '';
                    position: absolute;
                    left: -26px;
                    top: 12px;
                    bottom: -12px;
                    width: 2px;
                    background: #e0e0e0;
                }
                
                .timeline-item:last-child:before {
                    display: none;
                }
                
                .timeline-title {
                    font-weight: 500;
                    color: #333;
                    margin-bottom: 4px;
                }
                
                .timeline-time {
                    font-size: 12px;
                    color: #666;
                }
                
                .empty-state {
                    text-align: center;
                    padding: 60px 20px;
                    color: #999;
                    font-size: 16px;
                }
                
                .feed-footer {
                    margin-top: 16px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 12px;
                }
                
                .refresh-btn {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: #fff;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                
                .refresh-btn:hover {
                    background: rgba(255,255,255,0.3);
                }
                
                @media (max-width: 768px) {
                    .ai-research-feed {
                        padding: 16px;
                    }
                    
                    .feed-tabs {
                        flex-direction: column;
                    }
                    
                    .tab-btn {
                        width: 100%;
                    }
                    
                    .stats-grid {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }
}

// Auto-initialize if data-auto-init attribute is present
document.addEventListener('DOMContentLoaded', () => {
    const autoInitElements = document.querySelectorAll('[data-widget="ai-research-feed"][data-auto-init="true"]');
    autoInitElements.forEach(el => {
        const options = {
            apiBase: el.dataset.apiBase,
            refreshInterval: parseInt(el.dataset.refreshInterval) || 60000,
            maxMessages: parseInt(el.dataset.maxMessages) || 20,
            showInsights: el.dataset.showInsights !== 'false',
            showCommunication: el.dataset.showCommunication !== 'false',
            adminMode: el.dataset.adminMode === 'true'
        };
        new AIResearchFeedWidget(el.id, options);
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIResearchFeedWidget;
}
