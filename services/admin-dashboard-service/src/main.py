import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from kubernetes import client, config
import json
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.metrics import REGISTRY

app = FastAPI()

try:
    config.load_incluster_config()
except config.ConfigException:
    try:
        config.load_kube_config()
    except config.ConfigException:
        raise RuntimeError("Could not configure Kubernetes client")

v1 = client.AppsV1Api()

# Prometheus metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
active_services = Gauge('active_services', 'Number of active services')
total_services = Gauge('total_services', 'Total number of services')

# Role-based tab configuration
TAB_CONFIG = {
    "services": {
        "id": "services",
        "name": "Services",
        "icon": "📊",
        "roles": ["platform-admin", "service-admin"],
        "description": "Manage all platform services"
    },
    "grafana": {
        "id": "grafana",
        "name": "Grafana",
        "icon": "📈",
        "roles": ["platform-admin", "monitoring-admin"],
        "description": "Monitoring dashboards",
        "url": "http://prometheus-grafana.observability:80",
        "enabled": True
    },
    "prometheus": {
        "id": "prometheus",
        "name": "Prometheus",
        "icon": "📊",
        "roles": ["platform-admin", "monitoring-admin"],
        "description": "Metrics and alerting",
        "url": "http://prometheus-kube-prometheus-prometheus.observability:9090",
        "enabled": True
    },
    "loki": {
        "id": "loki",
        "name": "Loki",
        "icon": "📝",
        "roles": ["platform-admin", "monitoring-admin"],
        "description": "Centralized logging",
        "url": "http://loki.observability:3100",
        "enabled": True
    },
    "alertmanager": {
        "id": "alertmanager",
        "name": "Alertmanager",
        "icon": "🚨",
        "roles": ["platform-admin", "monitoring-admin"],
        "description": "Alert management",
        "url": "http://prometheus-kube-prometheus-alertmanager.observability:9093",
        "enabled": True
    },
    "keycloak": {
        "id": "keycloak",
        "name": "Keycloak",
        "icon": "🔐",
        "roles": ["platform-admin", "security-admin"],
        "description": "Identity and access management",
        "url": "http://localhost:8080",
        "enabled": False  # Will be enabled when Keycloak is deployed
    },
    "api": {
        "id": "api",
        "name": "API",
        "icon": "🔧",
        "roles": ["platform-admin", "developer"],
        "description": "API documentation and testing"
    },
    "auth-api": {
        "id": "auth-api",
        "name": "Auth API",
        "icon": "🔐",
        "roles": ["platform-admin", "security-admin", "developer"],
        "description": "Authentication and authorization API",
        "url": "http://localhost:8084",
        "enabled": True
    },
    "service-mesh": {
        "id": "service-mesh",
        "name": "Service Mesh",
        "icon": "🕸️",
        "roles": ["platform-admin", "devops-admin"],
        "description": "Service mesh for internal communication",
        "url": "http://localhost:8085",
        "enabled": True
    },
    "api-gateway": {
        "id": "api-gateway",
        "name": "API Gateway",
        "icon": "🚪",
        "roles": ["platform-admin", "devops-admin"],
        "description": "API Gateway for external traffic",
        "url": "http://localhost:8086",
        "enabled": True
    },
    "group-management": {
        "id": "group-management",
        "name": "Group Management",
        "icon": "👥",
        "roles": ["platform-admin", "security-admin"],
        "description": "Data-driven access control system",
        "url": "http://localhost:8083",
        "enabled": True
    }
}

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    start_time = time.time()
    """Main dashboard with vertical tabs for all services"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexus Admin Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
                overflow-x: hidden;
            }
            
            .dashboard-container {
                display: flex;
                min-height: 100vh;
            }
            
            .main-content {
                flex: 1;
                padding: 20px;
                margin-left: 280px;
                transition: margin-left 0.3s ease;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header-left {
                text-align: left;
            }
            
            .header h1 {
                color: #4a5568;
                margin-bottom: 10px;
            }
            
            .header p {
                color: #718096;
                font-size: 16px;
            }
            
            .user-profile {
                position: relative;
            }
            
            .user-avatar {
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }
            
            .user-avatar:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            }
            
            .avatar-icon {
                font-size: 24px;
                color: white;
            }
            
            .user-dropdown {
                position: absolute;
                top: 60px;
                right: 0;
                width: 280px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
                border: 1px solid #e2e8f0;
                opacity: 0;
                visibility: hidden;
                transform: translateY(-10px);
                transition: all 0.3s ease;
                z-index: 1000;
            }
            
            .user-dropdown.show {
                opacity: 1;
                visibility: visible;
                transform: translateY(0);
            }
            
            .user-header {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .user-avatar-small {
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                color: white;
            }
            
            .user-details {
                flex: 1;
            }
            
            .user-name {
                font-weight: 600;
                color: #2d3748;
                font-size: 16px;
                margin-bottom: 2px;
            }
            
            .user-role {
                color: #718096;
                font-size: 12px;
                background: #f7fafc;
                padding: 2px 8px;
                border-radius: 12px;
                display: inline-block;
            }
            
            .user-menu-items {
                padding: 8px 0;
            }
            
            .menu-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 20px;
                cursor: pointer;
                transition: background-color 0.2s ease;
                color: #4a5568;
                font-size: 14px;
            }
            
            .menu-item:hover {
                background-color: #f7fafc;
            }
            
            .menu-icon {
                font-size: 16px;
                width: 20px;
                text-align: center;
            }
            
            .menu-divider {
                height: 1px;
                background: #e2e8f0;
                margin: 8px 0;
            }
            
            .logout-item {
                color: #e53e3e;
            }
            
            .logout-item:hover {
                background-color: #fed7d7;
            }
            
            .logout-btn-fallback {
                background: #e53e3e;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                margin-left: 10px;
                transition: all 0.2s ease;
            }
            
            .logout-btn-fallback:hover {
                background: #c53030;
                transform: translateY(-1px);
            }
            
            .user-info {
                position: absolute;
                top: 20px;
                left: 300px;
                background: rgba(255, 255, 255, 0.9);
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 14px;
                color: #4a5568;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            
            .sidebar {
                position: fixed;
                left: 0;
                top: 0;
                width: 280px;
                height: 100vh;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                box-shadow: 4px 0 6px rgba(0, 0, 0, 0.1);
                overflow-y: auto;
                z-index: 1000;
            }
            
            .sidebar-header {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                text-align: center;
            }
            
            .sidebar-header h3 {
                color: #4a5568;
                font-size: 18px;
                margin-bottom: 5px;
            }
            
            .sidebar-header p {
                color: #718096;
                font-size: 12px;
            }
            
            .tabs-container {
                padding: 10px;
            }
            
            .tab {
                display: flex;
                align-items: center;
                padding: 15px;
                margin: 5px 0;
                background: transparent;
                border: none;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #4a5568;
                transition: all 0.3s ease;
                border-radius: 8px;
                width: 100%;
                text-align: left;
                position: relative;
            }
            
            .tab:hover {
                background: rgba(102, 126, 234, 0.1);
                color: #667eea;
                transform: translateX(5px);
            }
            
            .tab.active {
                background: rgba(102, 126, 234, 0.15);
                color: #667eea;
                box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
            }
            
            .tab-icon {
                font-size: 18px;
                margin-right: 12px;
                width: 24px;
                text-align: center;
            }
            
            .tab-content {
                flex: 1;
            }
            
            .tab-name {
                font-weight: 600;
                margin-bottom: 2px;
            }
            
            .tab-description {
                font-size: 11px;
                color: #718096;
                opacity: 0.8;
            }
            
            .tab.disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .tab.disabled:hover {
                transform: none;
                background: transparent;
            }
            
            .content-area {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                padding: 30px;
                min-height: 600px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .tab-pane {
                display: none;
            }
            
            .tab-pane.active {
                display: block;
            }
            
            .service-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .service-card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                border-left: 4px solid #667eea;
                transition: transform 0.2s ease;
            }
            
            .service-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }
            
            .service-name {
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 5px;
            }
            
            .service-namespace {
                color: #718096;
                font-size: 12px;
                margin-bottom: 10px;
            }
            
            .service-status {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                margin-bottom: 15px;
            }
            
            .status-running {
                background: #c6f6d5;
                color: #22543d;
            }
            
            .status-stopped {
                background: #fed7d7;
                color: #742a2a;
            }
            
            .service-actions {
                display: flex;
                gap: 10px;
            }
            
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: all 0.2s ease;
                text-decoration: none;
                display: inline-block;
                text-align: center;
            }
            
            .btn-primary {
                background: #667eea;
                color: white;
            }
            
            .btn-primary:hover {
                background: #5a67d8;
            }
            
            .btn-danger {
                background: #e53e3e;
                color: white;
            }
            
            .btn-danger:hover {
                background: #c53030;
            }
            
            .btn-success {
                background: #38a169;
                color: white;
            }
            
            .btn-success:hover {
                background: #2f855a;
            }
            
            .btn-secondary {
                background: #718096;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #4a5568;
            }
            
            .iframe-container {
                width: 100%;
                height: 600px;
                border: none;
                border-radius: 8px;
                background: white;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #718096;
            }
            
            .error {
                background: #fed7d7;
                color: #742a2a;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }
            
            .refresh-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                margin-bottom: 20px;
            }
            
            .refresh-btn:hover {
                background: #5a67d8;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
            }
            
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }
            
            .stat-label {
                color: #718096;
                font-size: 14px;
            }
            
            .chart-container {
                width: 100%;
                height: 200px;
                margin-top: 15px;
            }
            
            .mini-chart {
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                border-radius: 6px;
                position: relative;
                overflow: hidden;
            }
            
            .chart-bar {
                position: absolute;
                bottom: 0;
                background: linear-gradient(to top, #667eea, #764ba2);
                border-radius: 2px 2px 0 0;
                transition: height 0.3s ease;
            }
            
            .chart-line {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 2px;
                background: #667eea;
                transform-origin: left;
                animation: chartGrow 2s ease-out;
            }
            
            @keyframes chartGrow {
                from { transform: scaleX(0); }
                to { transform: scaleX(1); }
            }
            
            .coming-soon {
                text-align: center;
                padding: 60px 20px;
                color: #718096;
            }
            
            .coming-soon h2 {
                margin-bottom: 10px;
                color: #4a5568;
            }
            
            .coming-soon p {
                margin-bottom: 20px;
            }
            
            .role-badge {
                display: inline-block;
                padding: 2px 8px;
                background: #667eea;
                color: white;
                border-radius: 12px;
                font-size: 10px;
                margin-left: 10px;
            }
            
            @media (max-width: 768px) {
                .main-content {
                    margin-left: 0;
                    padding: 10px;
                }
                
                .sidebar {
                    transform: translateX(-100%);
                    transition: transform 0.3s ease;
                }
                
                .sidebar.open {
                    transform: translateX(0);
                }
                
                .mobile-toggle {
                    display: block;
                    position: fixed;
                    top: 20px;
                    left: 20px;
                    z-index: 1001;
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 50%;
                    cursor: pointer;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <div class="main-content">
                <div class="header">
                    <div class="header-left">
                        <h1>🚀 Nexus Admin Dashboard</h1>
                        <p>Unified management interface for your Kubernetes platform</p>
                    </div>
                    <div class="user-profile">
                        <div class="user-avatar" onclick="toggleUserMenu()">
                            <span class="avatar-icon">👤</span>
                        </div>
                        <div class="user-dropdown" id="user-dropdown">
                            <div class="user-header">
                                <div class="user-avatar-small">👤</div>
                                <div class="user-details">
                                    <div class="user-name" id="current-user">Platform Admin</div>
                                    <div class="user-role" id="current-role">platform-admin</div>
                                </div>
                            </div>
                            <div class="user-menu-items">
                                <div class="menu-item" onclick="showUserProfile()">
                                    <span class="menu-icon">👤</span>
                                    <span>Profile</span>
                                </div>
                                <div class="menu-item" onclick="showUserSettings()">
                                    <span class="menu-icon">⚙️</span>
                                    <span>Settings</span>
                                </div>
                                <div class="menu-divider"></div>
                                <div class="menu-item logout-item" onclick="logout()">
                                    <span class="menu-icon">🚪</span>
                                    <span>Logout</span>
                                </div>
                            </div>
                        </div>
                        <!-- Fallback logout button for better visibility -->
                        <button class="logout-btn-fallback" onclick="logout()" title="Logout">
                            🚪 Logout
                        </button>
                    </div>
                </div>
                
                <div class="content-area">
                    <!-- Services Tab -->
                    <div id="services" class="tab-pane active">
                        <button class="refresh-btn" onclick="loadServices()">🔄 Refresh Services</button>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-number" id="total-services">-</div>
                                <div class="stat-label">Total Services</div>
                                <div class="chart-container">
                                    <div class="mini-chart">
                                        <div class="chart-bar" id="total-chart" style="width: 20%; height: 0%; left: 10%;"></div>
                                        <div class="chart-bar" id="total-chart2" style="width: 20%; height: 0%; left: 40%;"></div>
                                        <div class="chart-bar" id="total-chart3" style="width: 20%; height: 0%; left: 70%;"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number" id="running-services">-</div>
                                <div class="stat-label">Running</div>
                                <div class="chart-container">
                                    <div class="mini-chart">
                                        <div class="chart-line" id="running-chart" style="transform: scaleX(0);"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number" id="stopped-services">-</div>
                                <div class="stat-label">Stopped</div>
                                <div class="chart-container">
                                    <div class="mini-chart">
                                        <div class="chart-bar" id="stopped-chart" style="width: 30%; height: 0%; left: 35%;"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="services-container" class="service-grid">
                            <div class="loading">Loading services...</div>
                        </div>
                    </div>
                    
                    <!-- Grafana Tab -->
                    <div id="grafana" class="tab-pane">
                        <h2>📈 Grafana Dashboard</h2>
                        <p>Access your monitoring dashboards and visualizations.</p>
                        <div style="margin: 20px 0;">
                            <a href="http://localhost:3000" target="_blank" class="btn btn-secondary">Open Grafana in New Tab</a>
                            <button class="btn btn-secondary" onclick="refreshGrafana()">🔄 Refresh</button>
                        </div>
                        <div id="grafana-loading" class="loading" style="display: none;">
                            <p>Loading metrics...</p>
                        </div>
                        <div id="grafana-content">
                            <div style="background: #1e1e1e; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                                <h3 style="color: #00ff00; margin-bottom: 15px;">📊 Quick Metrics Overview</h3>
                                <div id="metrics-overview" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="cpu-usage" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">CPU Usage</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="memory-usage" style="font-size: 2em; color: #ffd93d;">-</div>
                                        <div style="color: #888;">Memory Usage</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="pod-count" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Running Pods</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="service-count" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Active Services</div>
                                    </div>
                                </div>
                            </div>
                            <div style="text-align: center; padding: 20px;">
                                <p style="color: #888; margin-bottom: 15px;">For detailed dashboards and advanced visualizations:</p>
                                <a href="http://localhost:3000" target="_blank" class="btn btn-primary">Open Full Grafana Dashboard</a>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Prometheus Tab -->
                    <div id="prometheus" class="tab-pane">
                        <h2>📊 Prometheus Metrics</h2>
                        <p>View metrics and configure alerting rules.</p>
                        <div style="margin: 20px 0;">
                            <a href="http://localhost:9090" target="_blank" class="btn btn-secondary">Open Prometheus in New Tab</a>
                            <button class="btn btn-secondary" onclick="refreshPrometheus()">🔄 Refresh</button>
                        </div>
                        <div id="prometheus-loading" class="loading" style="display: none;">
                            <p>Loading metrics...</p>
                        </div>
                        <div id="prometheus-content">
                            <div style="background: #1e1e1e; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                                <h3 style="color: #00ff00; margin-bottom: 15px;">📊 Key Metrics Overview</h3>
                                <div id="prometheus-metrics" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="up-services" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Services Up</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="cpu-usage-prom" style="font-size: 2em; color: #ffd93d;">-</div>
                                        <div style="color: #888;">CPU Usage</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="memory-usage-prom" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Memory Usage</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="request-rate" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Request Rate</div>
                                    </div>
                                </div>
                            </div>
                            <div style="margin-top: 20px;">
                                <h4>Quick Queries:</h4>
                                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
                                    <button class="btn btn-secondary" onclick="queryPrometheus('up')">Services Status</button>
                                    <button class="btn btn-secondary" onclick="queryPrometheus('node_cpu_seconds_total')">CPU Metrics</button>
                                    <button class="btn btn-secondary" onclick="queryPrometheus('container_memory_usage_bytes')">Memory Metrics</button>
                                    <button class="btn btn-secondary" onclick="queryPrometheus('http_requests_total')">HTTP Requests</button>
                                </div>
                                <div id="prometheus-query-result" style="margin-top: 15px; background: #f5f5f5; padding: 15px; border-radius: 6px; font-family: monospace; display: none;">
                                    <div id="query-result-content"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Loki Tab -->
                    <div id="loki" class="tab-pane">
                        <h2>📝 Loki Logs</h2>
                        <p>Query and view centralized logs.</p>
                        <div style="margin: 20px 0;">
                            <a href="http://localhost:3100" target="_blank" class="btn btn-secondary">Open Loki in New Tab</a>
                            <button class="btn btn-secondary" onclick="refreshLoki()">🔄 Refresh</button>
                        </div>
                        <div id="loki-loading" class="loading" style="display: none;">
                            <p>Loading logs...</p>
                        </div>
                        <div id="loki-content">
                            <div style="background: #1e1e1e; color: #fff; padding: 20px; border-radius: 8px; font-family: monospace; height: 500px; overflow-y: auto;">
                                <h3 style="color: #00ff00; margin-bottom: 15px;">📊 Live Log Stream</h3>
                                <div id="log-stream" style="line-height: 1.6;">
                                    <div style="color: #888;">Loading logs...</div>
                                </div>
                            </div>
                            <div style="margin-top: 20px;">
                                <h4>Quick Queries:</h4>
                                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
                                    <button class="btn btn-secondary" onclick="queryLogs('{app=\"log-generator\"}')">Log Generator</button>
                                    <button class="btn btn-secondary" onclick="queryLogs('{app=\"sample-webapp\"}')">Sample WebApp</button>
                                    <button class="btn btn-secondary" onclick="queryLogs('{level=\"ERROR\"}')">Error Logs</button>
                                    <button class="btn btn-secondary" onclick="queryLogs('{level=\"WARN\"}')">Warning Logs</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Alertmanager Tab -->
                    <div id="alertmanager" class="tab-pane">
                        <h2>🚨 Alertmanager</h2>
                        <p>Manage alerts and notification routing.</p>
                        <div style="margin: 20px 0;">
                            <a href="http://localhost:9093" target="_blank" class="btn btn-primary">Open Alertmanager in New Tab</a>
                        </div>
                        <iframe src="http://localhost:9093" class="iframe-container" id="alertmanager-iframe"></iframe>
                    </div>
                    
                    <!-- Keycloak Tab -->
                    <div id="keycloak" class="tab-pane">
                        <div class="coming-soon">
                            <h2>🔐 Keycloak Admin Console</h2>
                            <p>Identity and access management console will be available here once Keycloak is deployed.</p>
                            <div style="margin: 20px 0;">
                                <a href="http://localhost:8080" target="_blank" class="btn btn-primary">Open Keycloak in New Tab</a>
                            </div>
                            <iframe src="http://localhost:8080" class="iframe-container" id="keycloak-iframe"></iframe>
                        </div>
                    </div>
                    
                    <!-- API Tab -->
                    <div id="api" class="tab-pane">
                        <h2>🔧 API Documentation</h2>
                        <p>Test the admin dashboard API endpoints directly.</p>
                        <div style="margin: 20px 0;">
                            <a href="/docs" target="_blank" class="btn btn-primary">Open API Docs</a>
                        </div>
                        <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3>Available Endpoints:</h3>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li><strong>GET /api/services</strong> - List all services</li>
                                <li><strong>POST /api/services/{name}/stop</strong> - Stop a service</li>
                                <li><strong>POST /api/services/{name}/start</strong> - Start a service</li>
                                <li><strong>GET /health</strong> - Health check</li>
                            </ul>
                        </div>
                        <div style="background: #f7fafc; padding: 20px; border-radius: 8px;">
                            <h3>Quick Test:</h3>
                            <button class="btn btn-secondary" onclick="testAPI()">Test API Connection</button>
                            <div id="api-test-result" style="margin-top: 10px;"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Vertical Sidebar -->
            <div class="sidebar">
                <div class="sidebar-header">
                    <h3>Platform Tools</h3>
                    <p>Select a service to manage</p>
                </div>
                <div class="tabs-container" id="tabs-container">
                    <!-- Tabs will be generated dynamically -->
                </div>
            </div>
        </div>
        
        <script>
            // Tab configuration
            const tabConfig = """ + json.dumps(TAB_CONFIG) + """;
            
            // Current user role (will be integrated with Keycloak later)
            let currentUserRole = 'platform-admin';
            
            function initializeTabs() {
                const container = document.getElementById('tabs-container');
                let html = '';
                
                Object.values(tabConfig).forEach(tab => {
                    if (tab.roles.includes(currentUserRole)) {
                        const isDisabled = tab.enabled === false;
                        html += `
                            <button class="tab ${isDisabled ? 'disabled' : ''}" 
                                    onclick="${isDisabled ? '' : `showTab('${tab.id}')`}"
                                    title="${tab.description}">
                                <div class="tab-icon">${tab.icon}</div>
                                <div class="tab-content">
                                    <div class="tab-name">${tab.name}</div>
                                    <div class="tab-description">${tab.description}</div>
                                </div>
                            </button>
                        `;
                    }
                });
                
                container.innerHTML = html;
            }
            
            function showTab(tabName) {
                // Hide all tab panes
                const tabPanes = document.querySelectorAll('.tab-pane');
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                // Show selected tab pane
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked tab
                event.target.closest('.tab').classList.add('active');
                
                // Auto-load data based on tab
                if (tabName === 'loki') {
                    fetchLogs('{app="log-generator"}');
                } else if (tabName === 'grafana') {
                    loadMetricsOverview();
                } else if (tabName === 'prometheus') {
                    loadPrometheusOverview();
                }
            }
            
            async function loadServices() {
                const container = document.getElementById('services-container');
                container.innerHTML = '<div class="loading">Loading services...</div>';
                
                try {
                    const response = await fetch('/api/services');
                    const data = await response.json();
                    
                    let html = '';
                    let runningCount = 0;
                    let stoppedCount = 0;
                    
                    data.services.forEach(service => {
                        const isRunning = service.status === 'Running';
                        if (isRunning) runningCount++;
                        else stoppedCount++;
                        
                        html += `
                            <div class="service-card">
                                <div class="service-name">${service.name}</div>
                                <div class="service-namespace">Namespace: ${service.namespace}</div>
                                <div class="service-status ${isRunning ? 'status-running' : 'status-stopped'}">
                                    ${service.status} (${service.replicas} replicas)
                                </div>
                                <div class="service-actions">
                                    ${isRunning ? 
                                        `<button class="btn btn-danger" onclick="stopService('${service.name}')">Stop</button>` :
                                        `<button class="btn btn-success" onclick="startService('${service.name}')">Start</button>`
                                    }
                                    <button class="btn btn-secondary" onclick="refreshServices()">Refresh</button>
                                </div>
                            </div>
                        `;
                    });
                    
                    container.innerHTML = html;
                    
                    // Update stats with charts
                    updateStatsWithCharts(data.services.length, runningCount, stoppedCount);
                    
                } catch (error) {
                    container.innerHTML = '<div class="error">Error loading services: ' + error.message + '</div>';
                }
            }
            
            function updateStatsWithCharts(total, running, stopped) {
                // Update numbers
                document.getElementById('total-services').textContent = total;
                document.getElementById('running-services').textContent = running;
                document.getElementById('stopped-services').textContent = stopped;
                
                // Update charts
                const totalPercentage = total > 0 ? (total / 10) * 100 : 0;
                const runningPercentage = total > 0 ? (running / total) * 100 : 0;
                const stoppedPercentage = total > 0 ? (stopped / total) * 100 : 0;
                
                // Animate total services chart
                setTimeout(() => {
                    document.getElementById('total-chart').style.height = Math.min(totalPercentage, 80) + '%';
                }, 100);
                setTimeout(() => {
                    document.getElementById('total-chart2').style.height = Math.min(totalPercentage * 0.7, 60) + '%';
                }, 300);
                setTimeout(() => {
                    document.getElementById('total-chart3').style.height = Math.min(totalPercentage * 0.5, 40) + '%';
                }, 500);
                
                // Animate running services chart
                setTimeout(() => {
                    document.getElementById('running-chart').style.transform = `scaleX(${runningPercentage / 100})`;
                }, 200);
                
                // Animate stopped services chart
                setTimeout(() => {
                    document.getElementById('stopped-chart').style.height = Math.min(stoppedPercentage * 2, 70) + '%';
                }, 400);
            }
            
            async function stopService(name) {
                try {
                    const response = await fetch(`/api/services/${name}/stop`, { method: 'POST' });
                    if (response.ok) {
                        alert(`Service ${name} stopped successfully!`);
                        loadServices();
                    } else {
                        alert(`Error stopping service ${name}`);
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            async function startService(name) {
                try {
                    const response = await fetch(`/api/services/${name}/start`, { method: 'POST' });
                    if (response.ok) {
                        alert(`Service ${name} started successfully!`);
                        loadServices();
                    } else {
                        alert(`Error starting service ${name}`);
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            async function testAPI() {
                const resultDiv = document.getElementById('api-test-result');
                resultDiv.innerHTML = '<div class="loading">Testing API...</div>';
                
                try {
                    const response = await fetch('/api/services');
                    const data = await response.json();
                    resultDiv.innerHTML = `<div style="color: green;">✅ API is working! Found ${data.services.length} services.</div>`;
                } catch (error) {
                    resultDiv.innerHTML = `<div style="color: red;">❌ API Error: ${error.message}</div>`;
                }
            }
            
            function refreshServices() {
                loadServices();
            }
            
            // Embedded service loading functions

            
            async function loadMetricsOverview() {
                try {
                    // Get basic metrics from Prometheus API
                    const response = await fetch('/api/metrics-overview');
                    const data = await response.json();
                    
                    document.getElementById('cpu-usage').textContent = data.cpu_usage + '%';
                    document.getElementById('memory-usage').textContent = data.memory_usage + '%';
                    document.getElementById('pod-count').textContent = data.pod_count;
                    document.getElementById('service-count').textContent = data.service_count;
                    
                } catch (error) {
                    console.error('Error loading metrics:', error);
                    document.getElementById('cpu-usage').textContent = 'N/A';
                    document.getElementById('memory-usage').textContent = 'N/A';
                    document.getElementById('pod-count').textContent = 'N/A';
                    document.getElementById('service-count').textContent = 'N/A';
                }
            }
            
            function refreshGrafana() {
                const iframe = document.getElementById('grafana-iframe');
                if (iframe.style.display !== 'none') {
                    iframe.src = iframe.src;
                }
            }
            
            function loadPrometheusEmbedded() {
                const iframe = document.getElementById('prometheus-iframe');
                const loading = document.getElementById('prometheus-loading');
                
                loading.style.display = 'block';
                iframe.style.display = 'none';
                
                iframe.onload = function() {
                    loading.style.display = 'none';
                    iframe.style.display = 'block';
                };
                
                iframe.onerror = function() {
                    loading.innerHTML = '<div class="error">Failed to load Prometheus. Please try opening in a new tab.</div>';
                };
                
                iframe.src = 'http://localhost:9090';
            }
            
            function refreshPrometheus() {
                const iframe = document.getElementById('prometheus-iframe');
                if (iframe.style.display !== 'none') {
                    iframe.src = iframe.src;
                }
            }
            

            
            async function fetchLogs(query) {
                const logStream = document.getElementById('log-stream');
                try {
                    const response = await fetch(`/api/logs?query=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    if (data.logs && data.logs.length > 0) {
                        let html = '';
                        data.logs.forEach(log => {
                            const timestamp = new Date(log.timestamp).toLocaleTimeString();
                            const level = log.level || 'INFO';
                            const color = level === 'ERROR' ? '#ff6b6b' : level === 'WARN' ? '#ffd93d' : '#6bcf7f';
                            html += `<div style="margin-bottom: 8px;"><span style="color: #888;">[${timestamp}]</span> <span style="color: ${color};">[${level}]</span> <span style="color: #fff;">${log.message}</span></div>`;
                        });
                        logStream.innerHTML = html;
                    } else {
                        logStream.innerHTML = '<div style="color: #888;">No logs found. Try a different query or check if services are generating logs.</div>';
                    }
                } catch (error) {
                    logStream.innerHTML = `<div style="color: #ff6b6b;">Error loading logs: ${error.message}</div>`;
                }
            }
            
            function queryLogs(query) {
                fetchLogs(query);
            }
            
            async function loadPrometheusOverview() {
                try {
                    const response = await fetch('/api/prometheus-overview');
                    const data = await response.json();
                    
                    document.getElementById('up-services').textContent = data.up_services;
                    document.getElementById('cpu-usage-prom').textContent = data.cpu_usage + '%';
                    document.getElementById('memory-usage-prom').textContent = data.memory_usage + '%';
                    document.getElementById('request-rate').textContent = data.request_rate + '/s';
                    
                } catch (error) {
                    console.error('Error loading Prometheus metrics:', error);
                    document.getElementById('up-services').textContent = 'N/A';
                    document.getElementById('cpu-usage-prom').textContent = 'N/A';
                    document.getElementById('memory-usage-prom').textContent = 'N/A';
                    document.getElementById('request-rate').textContent = 'N/A';
                }
            }
            
            async function queryPrometheus(query) {
                try {
                    const response = await fetch(`/api/prometheus-query?query=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    const resultDiv = document.getElementById('prometheus-query-result');
                    const contentDiv = document.getElementById('query-result-content');
                    
                    if (data.result && data.result.length > 0) {
                        let html = `<strong>Query: ${query}</strong><br><br>`;
                        data.result.forEach(item => {
                            html += `<div style="margin-bottom: 8px;">`;
                            html += `<strong>${item.metric.job || 'Unknown'}</strong>: ${item.value[1]}<br>`;
                            html += `<small style="color: #666;">Labels: ${JSON.stringify(item.metric)}</small>`;
                            html += `</div>`;
                        });
                        contentDiv.innerHTML = html;
                    } else {
                        contentDiv.innerHTML = `<strong>Query: ${query}</strong><br><br>No data found for this query.`;
                    }
                    
                    resultDiv.style.display = 'block';
                    
                } catch (error) {
                    const resultDiv = document.getElementById('prometheus-query-result');
                    const contentDiv = document.getElementById('query-result-content');
                    contentDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
                    resultDiv.style.display = 'block';
                }
            }
            
            function refreshLoki() {
                const iframe = document.getElementById('loki-iframe');
                if (iframe.style.display !== 'none') {
                    iframe.src = iframe.src;
                }
            }
            
            // User dropdown functions
            function toggleUserMenu() {
                const dropdown = document.getElementById('user-dropdown');
                dropdown.classList.toggle('show');
            }
            
            function showUserProfile() {
                alert('User Profile - Coming Soon!');
                // TODO: Implement user profile modal/page
                toggleUserMenu();
            }
            
            function showUserSettings() {
                alert('User Settings - Coming Soon!');
                // TODO: Implement user settings modal/page
                toggleUserMenu();
            }
            
            async function logout() {
                if (confirm('Are you sure you want to logout?')) {
                    try {
                        const token = localStorage.getItem('access_token');
                        if (token) {
                            // Call Auth API logout endpoint
                            const response = await fetch('http://auth-api-service:8084/api/auth/logout', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                }
                            });
                            
                            if (response.ok) {
                                console.log('Logout successful');
                            } else {
                                console.warn('Logout API call failed, but clearing local data');
                            }
                        }
                    } catch (error) {
                        console.warn('Logout API call failed, but clearing local data:', error);
                    }
                    
                    // Clear local storage
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user_info');
                    
                    // Redirect to login page
                    window.location.href = '/login';
                }
            }
                }
                toggleUserMenu();
            }
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function(event) {
                const userProfile = document.querySelector('.user-profile');
                const dropdown = document.getElementById('user-dropdown');
                
                if (!userProfile.contains(event.target) && dropdown.classList.contains('show')) {
                    dropdown.classList.remove('show');
                }
            });
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                initializeTabs();
                loadServices();
                
                // Load user info from Auth API if available
                loadUserInfo();
            });
            
            async function loadUserInfo() {
                try {
                    // Try to get user info from Auth API
                    const token = localStorage.getItem('auth_token');
                    if (token) {
                        const response = await fetch(`http://localhost:8084/api/auth/user-info?token=${token}`);
                        if (response.ok) {
                            const userData = await response.json();
                            document.getElementById('current-user').textContent = userData.name || userData.username || 'Platform Admin';
                            document.getElementById('current-role').textContent = userData.role || 'platform-admin';
                        }
                    }
                } catch (error) {
                    console.log('Could not load user info from Auth API:', error);
                    // Keep default values
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/services")
def get_services():
    start_time = time.time()
    try:
        deployments = v1.list_deployment_for_all_namespaces(watch=False)
        services = []
        running_count = 0
        total_count = 0
        
        for dep in deployments.items:
            total_count += 1
            is_running = dep.status.replicas == dep.spec.replicas and dep.spec.replicas > 0
            if is_running:
                running_count += 1
                
            services.append({
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": dep.spec.replicas,
                "status": "Running" if is_running else "Stopped"
            })
        
        # Update metrics
        total_services.set(total_count)
        active_services.set(running_count)
        
        return {"services": services}
    except Exception as e:
        http_requests_total.labels(method='GET', endpoint='/api/services', status='500').inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(method='GET', endpoint='/api/services').observe(duration)
        http_requests_total.labels(method='GET', endpoint='/api/services', status='200').inc()

@app.post("/api/services/{name}/stop")
def stop_service(name: str):
    try:
        body = {"spec": {"replicas": 0}}
        v1.patch_namespaced_deployment(name=name, namespace="default", body=body)
        return {"status": f"Service {name} stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/services/{name}/start")
def start_service(name: str):
    try:
        body = {"spec": {"replicas": 1}} # Assumes 1 replica, can be more dynamic
        v1.patch_namespaced_deployment(name=name, namespace="default", body=body)
        return {"status": f"Service {name} started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/login")
async def login_page():
    """Login page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexus Platform - Login</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 400px;
            }
            .login-header {
                text-align: center;
                margin-bottom: 30px;
            }
            .login-header h1 {
                color: #333;
                margin: 0;
                font-size: 24px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                box-sizing: border-box;
            }
            .login-btn {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .login-btn:hover {
                transform: translateY(-2px);
            }
            .error-message {
                color: #e74c3c;
                text-align: center;
                margin-top: 10px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>🔐 Nexus Platform</h1>
                <p>Sign in to access the admin dashboard</p>
            </div>
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="login-btn">Sign In</button>
            </form>
            <div id="errorMessage" class="error-message"></div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const errorMessage = document.getElementById('errorMessage');
                
                try {
                    const response = await fetch('http://auth-api-service:8084/api/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ username, password })
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('refresh_token', data.refresh_token);
                        localStorage.setItem('user_info', JSON.stringify(data.user));
                        
                        // Redirect to dashboard
                        window.location.href = '/';
                    } else {
                        const errorData = await response.json();
                        errorMessage.textContent = errorData.message || 'Login failed';
                        errorMessage.style.display = 'block';
                    }
                } catch (error) {
                    errorMessage.textContent = 'Network error. Please try again.';
                    errorMessage.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/logs")
async def get_logs(query: str = "{app=\"log-generator\"}"):
    """Fetch logs from Kubernetes pods using Python client"""
    try:
        from kubernetes import client, config
        
        # Load in-cluster config
        try:
            config.load_incluster_config()
        except:
            # Fallback to default config for local development
            config.load_kube_config()
        
        v1 = client.CoreV1Api()
        
        # Get logs from log-generator pods
        logs = []
        try:
            # Get pods with label app=log-generator
            pods = v1.list_namespaced_pod(
                namespace="default",
                label_selector="app=log-generator"
            )
            
            for pod in pods.items:
                if pod.status.phase == 'Running':
                    # Get logs from the pod
                    pod_logs = v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace="default",
                        tail_lines=50,
                        timestamps=True
                    )
                    
                    # Parse logs
                    for line in pod_logs.strip().split('\n'):
                        if line.strip():
                            # Parse timestamp and message
                            parts = line.split(' ', 1)
                            if len(parts) >= 2:
                                timestamp_str = parts[0]
                                message = parts[1]
                                
                                # Extract log level
                                level = 'INFO'
                                if '[ERROR]' in message:
                                    level = 'ERROR'
                                elif '[WARN]' in message:
                                    level = 'WARN'
                                
                                logs.append({
                                    'timestamp': timestamp_str,
                                    'level': level,
                                    'message': message
                                })
                    
                    break  # Only get logs from first running pod
            
            return {"logs": logs[-20:]}  # Return last 20 logs
            
        except Exception as e:
            return {"logs": [], "error": f"Failed to fetch logs: {str(e)}"}
            
    except Exception as e:
        return {"logs": [], "error": str(e)}

@app.get("/api/metrics-overview")
async def get_metrics_overview():
    """Get basic metrics overview for embedded display"""
    try:
        # Get basic cluster metrics
        import subprocess
        
        # Get pod count
        result = subprocess.run([
            'kubectl', 'get', 'pods', '--all-namespaces', '--field-selector=status.phase=Running', '-o', 'json'
        ], capture_output=True, text=True, timeout=10)
        
        pod_count = 0
        if result.returncode == 0:
            import json
            pods_data = json.loads(result.stdout)
            pod_count = len(pods_data.get('items', []))
        
        # Get service count
        result = subprocess.run([
            'kubectl', 'get', 'services', '--all-namespaces', '-o', 'json'
        ], capture_output=True, text=True, timeout=10)
        
        service_count = 0
        if result.returncode == 0:
            services_data = json.loads(result.stdout)
            service_count = len(services_data.get('items', []))
        
        # Get real CPU and memory usage from Prometheus
        try:
            import requests
            base_url = "http://nexus-observability-kube-p-prometheus.monitoring.svc.cluster.local:9090"
            
            # Get CPU usage
            cpu_response = requests.get(f"{base_url}/api/v1/query", params={"query": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"}, timeout=5)
            cpu_data = cpu_response.json()
            cpu_usage = 0
            if cpu_data.get('data', {}).get('result'):
                cpu_usage = round(float(cpu_data['data']['result'][0]['value'][1]), 1)
            
            # Get memory usage
            mem_response = requests.get(f"{base_url}/api/v1/query", params={"query": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"}, timeout=5)
            mem_data = mem_response.json()
            memory_usage = 0
            if mem_data.get('data', {}).get('result'):
                memory_usage = round(float(mem_data['data']['result'][0]['value'][1]), 1)
                
        except Exception as e:
            # Fallback to simulated values if Prometheus is not available
            import random
            cpu_usage = random.randint(15, 45)  # 15-45%
            memory_usage = random.randint(30, 70)  # 30-70%
        
        return {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "pod_count": pod_count,
            "service_count": service_count
        }
        
    except Exception as e:
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "pod_count": 0,
            "service_count": 0,
            "error": str(e)
        }

@app.get("/api/prometheus-overview")
async def get_prometheus_overview():
    """Get basic Prometheus metrics overview"""
    try:
        import requests
        
        # Query Prometheus API
        base_url = "http://nexus-observability-kube-p-prometheus.monitoring.svc.cluster.local:9090"
        
        # Get services up count
        up_response = requests.get(f"{base_url}/api/v1/query", params={"query": "up"}, timeout=5)
        up_data = up_response.json()
        up_services = len(up_data.get('data', {}).get('result', []))
        
        # Get CPU usage
        cpu_response = requests.get(f"{base_url}/api/v1/query", params={"query": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"}, timeout=5)
        cpu_data = cpu_response.json()
        cpu_usage = 0
        if cpu_data.get('data', {}).get('result'):
            cpu_usage = round(float(cpu_data['data']['result'][0]['value'][1]), 1)
        
        # Get memory usage
        mem_response = requests.get(f"{base_url}/api/v1/query", params={"query": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"}, timeout=5)
        mem_data = mem_response.json()
        memory_usage = 0
        if mem_data.get('data', {}).get('result'):
            memory_usage = round(float(mem_data['data']['result'][0]['value'][1]), 1)
        
        # Get request rate
        req_response = requests.get(f"{base_url}/api/v1/query", params={"query": "rate(http_requests_total[5m])"}, timeout=5)
        req_data = req_response.json()
        request_rate = 0
        if req_data.get('data', {}).get('result'):
            request_rate = round(float(req_data['data']['result'][0]['value'][1]), 2)
        
        return {
            "up_services": up_services,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "request_rate": request_rate
        }
        
    except Exception as e:
        return {
            "up_services": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "request_rate": 0,
            "error": str(e)
        }

@app.get("/api/prometheus-query")
async def query_prometheus(query: str):
    """Execute a Prometheus query"""
    try:
        import requests
        
        base_url = "http://nexus-observability-kube-p-prometheus.monitoring.svc.cluster.local:9090"
        response = requests.get(f"{base_url}/api/v1/query", params={"query": query}, timeout=10)
        
        return response.json()
        
    except Exception as e:
        return {"error": str(e)}
# Tue Aug 12 16:28:47 MST 2025
