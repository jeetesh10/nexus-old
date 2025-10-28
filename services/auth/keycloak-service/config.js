// Configuration for different environments
const config = {
    // Environment detection
    isLocalhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    isCodespaces: /\.github\.dev$/.test(window.location.host),
    isProduction: window.location.protocol === 'https:',

    // Behavior flags
    autoRedirectAfterLogin: false, // default: stay on landing page; set true to auto-route by groups

    // Base URLs
    get keycloakBaseUrl() {
        // Dev defaults
        let base = 'http://localhost:8080';
        if (this.isCodespaces) {
            // Map landing port (e.g., -8082) to Keycloak port (e.g., -11000) in Codespaces subdomain
            // Example: https://<id>-8082.app.github.dev -> https://<id>-11000.app.github.dev
            const host = window.location.host;
            const mapped = host.replace(/-(\d+)\.app\.github\.dev$/, '-11000.app.github.dev');
            // Codespaces uses HTTPS public URLs; ensure we use https here
            const protocol = 'https:';
            base = `${protocol}//${mapped}`;
        } else if (this.isLocalhost) {
            // If using our simple forward for Keycloak on 11000, prefer that
            base = 'http://localhost:11000';
        }
        return base;
    },

    get landingPageUrl() {
        // Use current origin by default so redirects always point back to this page
        return window.location.origin;
    },
    
    // Service URLs
    services: {
        adminDashboard: {
            dev: 'http://localhost:8081',
            prod: 'https://admin.nexus.platform'
        },
        idService: {
            dev: 'http://localhost:8083',
            prod: 'https://id.nexus.platform'
        },
        parkingService: {
            dev: 'http://localhost:8084',
            prod: 'https://parking.nexus.platform'
        },
        customerPortal: {
            dev: 'http://localhost:8084',
            prod: 'https://customer.nexus.platform'
        },
        monitoring: {
            dev: 'http://localhost:3000',
            prod: 'https://monitoring.nexus.platform'
        },
        logs: {
            dev: 'http://localhost:3100',
            prod: 'https://logs.nexus.platform'
        },
        metrics: {
            dev: 'http://localhost:9090',
            prod: 'https://metrics.nexus.platform'
        }
    },
    
    // Get service URL based on environment
    getServiceUrl(serviceName) {
        const service = this.services[serviceName];
        if (!service) {
            console.warn(`Service ${serviceName} not found in config`);
            return '#';
        }
        return this.isDevelopment ? service.dev : service.prod;
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = config;
}
