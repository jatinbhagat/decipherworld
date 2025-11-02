/**
 * Robust WebSocket Manager for Design Thinking Sessions
 * Handles connection, reconnection, heartbeat, and error recovery
 */

class DesignThinkingWebSocketManager {
    constructor(sessionCode, options = {}) {
        this.sessionCode = sessionCode;
        this.options = {
            maxReconnectAttempts: 10,
            reconnectInterval: 3000,
            heartbeatInterval: 30000,
            connectionTimeout: 60000,
            debug: false,
            ...options
        };
        
        this.ws = null;
        this.reconnectAttempts = 0;
        this.isConnecting = false;
        this.isManualClose = false;
        this.lastActivity = Date.now();
        this.clientSessionId = this.generateClientSessionId();
        this.messageQueue = [];
        this.heartbeatTimer = null;
        this.connectionStatusTimer = null;
        
        // Event handlers
        this.onOpen = null;
        this.onMessage = null;
        this.onClose = null;
        this.onError = null;
        this.onReconnecting = null;
        this.onReconnected = null;
        
        this.log('WebSocket Manager initialized for session:', sessionCode);
    }
    
    generateClientSessionId() {
        return 'client_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }
        
        this.isConnecting = true;
        this.isManualClose = false;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/design-thinking/${this.sessionCode}/`;
        
        this.log('Connecting to WebSocket:', wsUrl);
        
        try {
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            this.log('Error creating WebSocket connection:', error);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }
    
    setupEventHandlers() {
        this.ws.onopen = (event) => {
            this.log('WebSocket connected successfully');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.lastActivity = Date.now();
            
            // Send any queued messages
            this.flushMessageQueue();
            
            // Start heartbeat
            this.startHeartbeat();
            
            // Start connection monitoring
            this.startConnectionMonitoring();
            
            if (this.onOpen) {
                this.onOpen(event);
            }
            
            // Show connection status
            this.showConnectionStatus('connected', 'Connected to session');
        };
        
        this.ws.onmessage = (event) => {
            this.lastActivity = Date.now();
            
            try {
                const data = JSON.parse(event.data);
                this.handleServerMessage(data);
                
                if (this.onMessage) {
                    this.onMessage(data);
                }
            } catch (error) {
                this.log('Error parsing message:', error, event.data);
            }
        };
        
        this.ws.onclose = (event) => {
            this.log('WebSocket closed:', event.code, event.reason);
            this.isConnecting = false;
            
            // Clear timers
            this.stopHeartbeat();
            this.stopConnectionMonitoring();
            
            if (this.onClose) {
                this.onClose(event);
            }
            
            // Show disconnection status
            this.showConnectionStatus('disconnected', 'Connection lost');
            
            // Attempt reconnection unless manually closed
            if (!this.isManualClose && event.code !== 1000) {
                this.scheduleReconnect();
            }
        };
        
        this.ws.onerror = (event) => {
            this.log('WebSocket error:', event);
            
            if (this.onError) {
                this.onError(event);
            }
            
            this.showConnectionStatus('error', 'Connection error occurred');
        };
    }
    
    handleServerMessage(data) {
        switch (data.type) {
            case 'heartbeat':
                // Respond to server heartbeat
                this.send({\n                    type: 'heartbeat_response',\n                    timestamp: data.timestamp,\n                    client_time: new Date().toISOString()\n                });\n                break;\n                \n            case 'connection_timeout':\n                this.log('Server detected connection timeout');\n                this.showConnectionStatus('timeout', data.message);\n                if (data.should_reconnect) {\n                    this.scheduleReconnect();\n                }\n                break;\n                \n            case 'reconnection_complete':\n                this.log('Reconnection completed successfully');\n                this.showConnectionStatus('connected', data.message);\n                if (this.onReconnected) {\n                    this.onReconnected(data);\n                }\n                break;\n                \n            case 'session_expired':\n                this.log('Session has expired');\n                this.showConnectionStatus('expired', data.message);\n                if (data.should_redirect && data.redirect_url) {\n                    setTimeout(() => {\n                        window.location.href = data.redirect_url;\n                    }, 3000);\n                }\n                break;\n                \n            case 'error':\n                this.log('Server error:', data.message);\n                this.showConnectionStatus('error', data.message);\n                break;\n                \n            case 'pong':\n                // Server responded to our ping\n                this.lastActivity = Date.now();\n                break;\n        }\n    }\n    \n    send(data) {\n        if (this.ws && this.ws.readyState === WebSocket.OPEN) {\n            try {\n                this.ws.send(JSON.stringify(data));\n                this.log('Message sent:', data.type);\n                return true;\n            } catch (error) {\n                this.log('Error sending message:', error);\n                this.messageQueue.push(data);\n                return false;\n            }\n        } else {\n            // Queue message for later\n            this.messageQueue.push(data);\n            this.log('Message queued (connection not ready):', data.type);\n            \n            // Attempt to reconnect if not already connecting\n            if (!this.isConnecting) {\n                this.connect();\n            }\n            \n            return false;\n        }\n    }\n    \n    flushMessageQueue() {\n        while (this.messageQueue.length > 0) {\n            const message = this.messageQueue.shift();\n            this.send(message);\n        }\n    }\n    \n    startHeartbeat() {\n        this.stopHeartbeat();\n        \n        this.heartbeatTimer = setInterval(() => {\n            this.send({\n                type: 'ping',\n                timestamp: new Date().toISOString(),\n                client_session_id: this.clientSessionId\n            });\n        }, this.options.heartbeatInterval);\n    }\n    \n    stopHeartbeat() {\n        if (this.heartbeatTimer) {\n            clearInterval(this.heartbeatTimer);\n            this.heartbeatTimer = null;\n        }\n    }\n    \n    startConnectionMonitoring() {\n        this.stopConnectionMonitoring();\n        \n        this.connectionStatusTimer = setInterval(() => {\n            const timeSinceActivity = Date.now() - this.lastActivity;\n            \n            if (timeSinceActivity > this.options.connectionTimeout) {\n                this.log('Connection timeout detected on client side');\n                this.scheduleReconnect();\n            }\n        }, 10000); // Check every 10 seconds\n    }\n    \n    stopConnectionMonitoring() {\n        if (this.connectionStatusTimer) {\n            clearInterval(this.connectionStatusTimer);\n            this.connectionStatusTimer = null;\n        }\n    }\n    \n    scheduleReconnect() {\n        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {\n            this.log('Maximum reconnection attempts reached');\n            this.showConnectionStatus('failed', 'Unable to reconnect. Please refresh the page.');\n            return;\n        }\n        \n        this.reconnectAttempts++;\n        const delay = Math.min(this.options.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000);\n        \n        this.log(`Reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);\n        \n        if (this.onReconnecting) {\n            this.onReconnecting(this.reconnectAttempts, delay);\n        }\n        \n        this.showConnectionStatus('reconnecting', `Reconnecting... (attempt ${this.reconnectAttempts})`);\n        \n        setTimeout(() => {\n            if (!this.isManualClose) {\n                this.connect();\n            }\n        }, delay);\n    }\n    \n    requestReconnection() {\n        this.send({\n            type: 'reconnect_request',\n            client_session_id: this.clientSessionId,\n            last_known_state: this.getLastKnownState(),\n            timestamp: new Date().toISOString()\n        });\n    }\n    \n    getLastKnownState() {\n        // Override this method to provide application-specific state\n        return {\n            session_code: this.sessionCode,\n            client_session_id: this.clientSessionId,\n            last_activity: this.lastActivity\n        };\n    }\n    \n    showConnectionStatus(status, message) {\n        // Create or update connection status indicator\n        let statusIndicator = document.getElementById('websocket-status');\n        \n        if (!statusIndicator) {\n            statusIndicator = document.createElement('div');\n            statusIndicator.id = 'websocket-status';\n            statusIndicator.style.cssText = `\n                position: fixed;\n                top: 10px;\n                right: 10px;\n                padding: 8px 12px;\n                border-radius: 6px;\n                font-size: 12px;\n                font-weight: bold;\n                z-index: 1000;\n                transition: all 0.3s ease;\n                max-width: 300px;\n                box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n            `;\n            document.body.appendChild(statusIndicator);\n        }\n        \n        const statusStyles = {\n            connected: { bg: '#10b981', color: 'white', icon: '✓' },\n            disconnected: { bg: '#ef4444', color: 'white', icon: '✗' },\n            reconnecting: { bg: '#f59e0b', color: 'white', icon: '↻' },\n            timeout: { bg: '#ef4444', color: 'white', icon: '⏱' },\n            error: { bg: '#ef4444', color: 'white', icon: '⚠' },\n            expired: { bg: '#6b7280', color: 'white', icon: '⌛' },\n            failed: { bg: '#7f1d1d', color: 'white', icon: '✗' }\n        };\n        \n        const style = statusStyles[status] || statusStyles.error;\n        \n        statusIndicator.style.backgroundColor = style.bg;\n        statusIndicator.style.color = style.color;\n        statusIndicator.innerHTML = `${style.icon} ${message}`;\n        \n        // Auto-hide connected status after 3 seconds\n        if (status === 'connected') {\n            setTimeout(() => {\n                if (statusIndicator && statusIndicator.innerHTML.includes('Connected')) {\n                    statusIndicator.style.opacity = '0.7';\n                    setTimeout(() => {\n                        if (statusIndicator) {\n                            statusIndicator.style.display = 'none';\n                        }\n                    }, 3000);\n                }\n            }, 3000);\n        } else {\n            statusIndicator.style.opacity = '1';\n            statusIndicator.style.display = 'block';\n        }\n    }\n    \n    close() {\n        this.log('Manually closing WebSocket connection');\n        this.isManualClose = true;\n        \n        this.stopHeartbeat();\n        this.stopConnectionMonitoring();\n        \n        if (this.ws) {\n            this.ws.close(1000, 'Manual close');\n        }\n    }\n    \n    getConnectionState() {\n        return {\n            readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,\n            reconnectAttempts: this.reconnectAttempts,\n            isConnecting: this.isConnecting,\n            lastActivity: this.lastActivity,\n            clientSessionId: this.clientSessionId,\n            queuedMessages: this.messageQueue.length\n        };\n    }\n    \n    log(...args) {\n        if (this.options.debug) {\n            console.log('[WebSocket Manager]', ...args);\n        }\n    }\n}\n\n// Export for use in templates\nwindow.DesignThinkingWebSocketManager = DesignThinkingWebSocketManager;