from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import httpx
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nexus Platform Landing Page",
    description="Dynamic landing page with service tiles based on user access",
    version="1.0.0"
)

# Configuration
ACCESS_CONTROL_URL = os.getenv("ACCESS_CONTROL_URL", "http://access-control-service:8000")
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://auth-api-service:8084")

@app.get("/")
async def landing_page(request: Request):
    """Dynamic landing page with service tiles"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexus Platform - Landing Page</title>
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
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                color: white;
                margin-bottom: 40px;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.2rem;
                opacity: 0.9;
            }
            
            .user-info {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 30px;
                color: white;
                text-align: center;
            }
            
            .user-info h2 {
                margin-bottom: 10px;
            }
            
            .user-details {
                display: flex;
                justify-content: center;
                gap: 30px;
                flex-wrap: wrap;
            }
            
            .user-detail {
                background: rgba(255, 255, 255, 0.1);
                padding: 10px 20px;
                border-radius: 10px;
                backdrop-filter: blur(5px);
            }
            
            .tiles-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .service-tile {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 25px;
                text-decoration: none;
                color: #333;
                transition: all 0.3s ease;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .service-tile:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
                background: rgba(255, 255, 255, 1);
            }
            
            .tile-header {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .tile-icon {
                font-size: 2rem;
                margin-right: 15px;
            }
            
            .tile-title {
                font-size: 1.3rem;
                font-weight: 600;
                color: #333;
            }
            
            .tile-description {
                color: #666;
                line-height: 1.5;
                margin-bottom: 15px;
            }
            
            .tile-permissions {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-top: 10px;
            }
            
            .permission-tag {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8rem;
                font-weight: 500;
            }
            
            .login-section {
                text-align: center;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 40px;
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            
            .login-section h2 {
                color: #333;
                margin-bottom: 20px;
            }
            
            .login-form {
                display: flex;
                flex-direction: column;
                gap: 15px;
                max-width: 300px;
                margin: 0 auto;
            }
            
            .form-group {
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            
            .form-group label {
                color: #555;
                font-weight: 500;
            }
            
            .form-group input {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
            }
            
            .login-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .login-btn:hover {
                transform: translateY(-2px);
            }
            
            .logout-btn {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                cursor: pointer;
                margin-top: 10px;
                transition: background 0.2s;
            }
            
            .logout-btn:hover {
                background: #c53030;
            }
            
            .error-message {
                color: #e74c3c;
                margin-top: 10px;
                display: none;
            }
            
            .loading {
                text-align: center;
                color: white;
                font-size: 1.2rem;
                margin: 50px 0;
            }
            
            .no-access {
                text-align: center;
                color: white;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 40px;
                margin-top: 30px;
            }
            
            .no-access h2 {
                margin-bottom: 15px;
            }
            
            .no-access p {
                opacity: 0.9;
                line-height: 1.6;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Nexus Platform</h1>
                <p>Your Gateway to Managed Services</p>
            </div>
            
            <!-- Login Section (shown when not authenticated) -->
            <div id="loginSection" class="login-section" style="display: none;">
                <h2>🔐 Sign In to Access Services</h2>
                <form id="loginForm" class="login-form">
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
            
            <!-- User Info Section (shown when authenticated) -->
            <div id="userSection" style="display: none;">
                <div class="user-info">
                    <h2>👋 Welcome, <span id="userName">User</span>!</h2>
                    <div class="user-details">
                        <div class="user-detail">
                            <strong>Service:</strong> <span id="userService">-</span>
                        </div>
                        <div class="user-detail">
                            <strong>Group:</strong> <span id="userGroup">-</span>
                        </div>
                        <div class="user-detail">
                            <strong>Role:</strong> <span id="userRole">-</span>
                        </div>
                    </div>
                    <button class="logout-btn" onclick="logout()">🚪 Logout</button>
                </div>
                
                <!-- Service Tiles -->
                <div id="tilesContainer" class="tiles-container">
                    <!-- Tiles will be populated dynamically -->
                </div>
            </div>
            
            <!-- Loading Section -->
            <div id="loadingSection" class="loading">
                <h2>🔄 Loading your services...</h2>
                <p>Please wait while we fetch your access information.</p>
            </div>
            
            <!-- No Access Section -->
            <div id="noAccessSection" class="no-access" style="display: none;">
                <h2>🔒 Access Restricted</h2>
                <p>You don't have access to any services yet. Please contact your administrator to get access to the services you need.</p>
            </div>
        </div>
        
        <script>
            // Check authentication status on page load
            document.addEventListener('DOMContentLoaded', function() {
                checkAuthStatus();
            });
            
            async function checkAuthStatus() {
                const token = localStorage.getItem('access_token');
                
                if (!token) {
                    showLoginSection();
                    return;
                }
                
                try {
                    // Get landing page data from Access Control Service
                    const response = await fetch('""" + ACCESS_CONTROL_URL + """/api/landing-page', {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        showUserSection(data);
                    } else if (response.status === 401) {
                        // Token expired or invalid
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        localStorage.removeItem('user_info');
                        showLoginSection();
                    } else {
                        showNoAccessSection();
                    }
                } catch (error) {
                    console.error('Error checking auth status:', error);
                    showLoginSection();
                }
            }
            
            function showLoginSection() {
                document.getElementById('loadingSection').style.display = 'none';
                document.getElementById('userSection').style.display = 'none';
                document.getElementById('noAccessSection').style.display = 'none';
                document.getElementById('loginSection').style.display = 'block';
            }
            
            function showUserSection(data) {
                document.getElementById('loadingSection').style.display = 'none';
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('noAccessSection').style.display = 'none';
                document.getElementById('userSection').style.display = 'block';
                
                // Update user info
                const user = data.user;
                document.getElementById('userName').textContent = user.full_name || user.username || 'User';
                document.getElementById('userService').textContent = user.service_name || 'N/A';
                document.getElementById('userGroup').textContent = user.group_name || 'N/A';
                document.getElementById('userRole').textContent = user.role || 'N/A';
                
                // Populate service tiles
                const tilesContainer = document.getElementById('tilesContainer');
                tilesContainer.innerHTML = '';
                
                if (data.tiles && data.tiles.length > 0) {
                    data.tiles.forEach(tile => {
                        const tileElement = createServiceTile(tile);
                        tilesContainer.appendChild(tileElement);
                    });
                } else {
                    tilesContainer.innerHTML = '<div class="no-access"><h3>No services available</h3><p>You don\'t have access to any services yet.</p></div>';
                }
            }
            
            function showNoAccessSection() {
                document.getElementById('loadingSection').style.display = 'none';
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('userSection').style.display = 'none';
                document.getElementById('noAccessSection').style.display = 'block';
            }
            
            function createServiceTile(tile) {
                const tileElement = document.createElement('a');
                tileElement.href = tile.url;
                tileElement.className = 'service-tile';
                tileElement.target = '_blank';
                
                tileElement.innerHTML = `
                    <div class="tile-header">
                        <div class="tile-icon">${tile.icon}</div>
                        <div class="tile-title">${tile.display_name}</div>
                    </div>
                    <div class="tile-description">${tile.description}</div>
                    <div class="tile-permissions">
                        ${tile.permissions.map(perm => `<span class="permission-tag">${perm}</span>`).join('')}
                    </div>
                `;
                
                return tileElement;
            }
            
            // Login form handler
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const errorMessage = document.getElementById('errorMessage');
                
                try {
                    const response = await fetch('""" + AUTH_API_URL + """/api/auth/login', {
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
                        
                        // Reload page data
                        checkAuthStatus();
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
            
            async function logout() {
                if (confirm('Are you sure you want to logout?')) {
                    try {
                        const token = localStorage.getItem('access_token');
                        if (token) {
                            await fetch('""" + AUTH_API_URL + """/api/auth/logout', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                }
                            });
                        }
                    } catch (error) {
                        console.warn('Logout API call failed, but clearing local data');
                    }
                    
                    // Clear local storage
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user_info');
                    
                    // Show login section
                    showLoginSection();
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "landing-page",
        "timestamp": datetime.utcnow()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
