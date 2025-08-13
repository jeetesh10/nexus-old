// Configuration for different environments
const config = {
    // Environment detection
    isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    isProduction: window.location.protocol === 'https:',
    
    // Base URLs
    get keycloakBaseUrl() {
        return this.isDevelopment ? 'http://localhost:8080' : 'https://auth.nexus.platform';
    },
    
    get landingPageUrl() {
        return this.isDevelopment ? 'http://localhost:8082' : 'https://platform.nexus.com';
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
