-- Database schema for service-group mappings
-- This allows dynamic configuration without code changes

-- Services table
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    service_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    url VARCHAR(255),
    status VARCHAR(20) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groups table (Keycloak groups)
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    group_name VARCHAR(100) UNIQUE NOT NULL,
    group_path VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service-Group mappings table
CREATE TABLE IF NOT EXISTS service_group_mappings (
    id SERIAL PRIMARY KEY,
    service_id INTEGER REFERENCES services(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    access_level VARCHAR(20) DEFAULT 'read', -- read, write, admin
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(service_id, group_id)
);

-- Insert default services
INSERT INTO services (service_id, title, description, icon, url, status) VALUES
('admin-dashboard', 'Admin Dashboard', 'Manage your Kubernetes platform, monitor services, and view logs.', '📊', 'http://localhost:8081', 'available'),
('id-service', 'Identity Resolution Service', 'Advanced identity resolution and graph analytics platform.', '🆔', 'http://localhost:8083', 'coming-soon'),
('parking-service', 'Parking Management', 'Smart parking management system with real-time analytics.', '🅿️', 'http://localhost:8084', 'coming-soon'),
('monitoring', 'Platform Monitoring', 'Advanced monitoring and alerting for all platform services.', '📈', 'http://localhost:3000', 'available'),
('logs', 'Centralized Logs', 'View and analyze logs from all platform services.', '📝', 'http://localhost:3100', 'available'),
('metrics', 'Metrics & Analytics', 'Real-time metrics and performance analytics.', '📊', 'http://localhost:9090', 'available')
ON CONFLICT (service_id) DO NOTHING;

-- Insert default groups
INSERT INTO groups (group_name, group_path, description) VALUES
('nexus', 'nexus', 'Internal Nexus platform group'),
('platform-admin', 'nexus/platform-admin', 'Platform administrators'),
('service-admin', 'nexus/service-admin', 'Service administrators'),
('admin-dashboard', 'nexus/admin-dashboard', 'Admin dashboard access'),
('id-service', 'nexus/id-service', 'ID service access'),
('parking-service', 'nexus/parking-service', 'Parking service access'),
('test-client', 'test-client', 'Test client tenant group'),
('test-client-id-service', 'test-client/id-service', 'Test client ID service access'),
('test-client-parking-service', 'test-client/parking-service', 'Test client parking service access')
ON CONFLICT (group_path) DO NOTHING;

-- Insert service-group mappings
INSERT INTO service_group_mappings (service_id, group_id, access_level) 
SELECT s.id, g.id, 'admin'
FROM services s, groups g
WHERE s.service_id = 'admin-dashboard' 
AND g.group_path IN ('nexus', 'nexus/platform-admin', 'nexus/admin-dashboard')
ON CONFLICT (service_id, group_id) DO NOTHING;

INSERT INTO service_group_mappings (service_id, group_id, access_level) 
SELECT s.id, g.id, 'read'
FROM services s, groups g
WHERE s.service_id = 'id-service' 
AND g.group_path IN ('nexus', 'nexus/platform-admin', 'nexus/id-service', 'test-client/id-service')
ON CONFLICT (service_id, group_id) DO NOTHING;

INSERT INTO service_group_mappings (service_id, group_id, access_level) 
SELECT s.id, g.id, 'read'
FROM services s, groups g
WHERE s.service_id = 'parking-service' 
AND g.group_path IN ('nexus', 'nexus/platform-admin', 'nexus/parking-service', 'test-client/parking-service')
ON CONFLICT (service_id, group_id) DO NOTHING;

INSERT INTO service_group_mappings (service_id, group_id, access_level) 
SELECT s.id, g.id, 'admin'
FROM services s, groups g
WHERE s.service_id IN ('monitoring', 'logs', 'metrics') 
AND g.group_path IN ('nexus', 'nexus/platform-admin', 'nexus/service-admin')
ON CONFLICT (service_id, group_id) DO NOTHING;
