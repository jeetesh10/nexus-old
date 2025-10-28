import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp up to 10 users
    { duration: '5m', target: 10 },  // Stay at 10 users
    { duration: '2m', target: 20 },  // Ramp up to 20 users
    { duration: '5m', target: 20 },  // Stay at 20 users
    { duration: '2m', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
    errors: ['rate<0.1'],              // Custom error rate
  },
};

// Test data
const BASE_URL = __ENV.BASE_URL || 'http://localhost:30080';
const AUTH_URL = `${BASE_URL}/api/auth`;
const ADMIN_URL = `${BASE_URL}/admin-dashboard`;
const MONGODB_URL = `${BASE_URL}/api/mongodb`;
const POSTGRESQL_URL = `${BASE_URL}/api/postgresql`;

// Test scenarios
export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Test 1: Health Checks
  const healthChecks = [
    { name: 'Admin Dashboard Health', url: `${ADMIN_URL}/health` },
    { name: 'Auth API Health', url: `${AUTH_URL}/health` },
    { name: 'MongoDB Orchestrator Health', url: `${MONGODB_URL}/health` },
    { name: 'PostgreSQL Orchestrator Health', url: `${POSTGRESQL_URL}/health` },
  ];

  healthChecks.forEach(({ name, url }) => {
    const response = http.get(url, params);
    const success = check(response, {
      [`${name} - Status 200`]: (r) => r.status === 200,
      [`${name} - Response Time < 1s`]: (r) => r.timings.duration < 1000,
    });
    errorRate.add(!success);
  });

  // Test 2: Auth API Login
  const loginPayload = JSON.stringify({
    username: 'admin',
    password: 'AdminPass123',
  });

  const loginResponse = http.post(`${AUTH_URL}/login`, loginPayload, params);
  const loginSuccess = check(loginResponse, {
    'Auth Login - Status 200': (r) => r.status === 200,
    'Auth Login - Has Token': (r) => r.json('access_token') !== undefined,
    'Auth Login - Response Time < 2s': (r) => r.timings.duration < 2000,
  });
  errorRate.add(!loginSuccess);

  // Test 3: MongoDB Operations
  if (loginResponse.status === 200) {
    const token = loginResponse.json('access_token');
    const authParams = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    };

    // MongoDB Health Check
    const mongoHealthResponse = http.get(`${MONGODB_URL}/health`, authParams);
    check(mongoHealthResponse, {
      'MongoDB Health - Status 200': (r) => r.status === 200,
      'MongoDB Health - Response Time < 1s': (r) => r.timings.duration < 1000,
    });

    // MongoDB Operation
    const mongoPayload = JSON.stringify({
      service_name: 'test-service',
      database_name: 'testdb',
      collection_name: 'users',
      operation: 'insert',
      data: {
        name: 'Test User',
        email: 'test@example.com',
        created_at: new Date().toISOString(),
      },
    });

    const mongoResponse = http.post(`${MONGODB_URL}/operation`, mongoPayload, authParams);
    check(mongoResponse, {
      'MongoDB Operation - Status 200': (r) => r.status === 200,
      'MongoDB Operation - Response Time < 3s': (r) => r.timings.duration < 3000,
    });
  }

  // Test 4: PostgreSQL Operations
  if (loginResponse.status === 200) {
    const token = loginResponse.json('access_token');
    const authParams = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    };

    // PostgreSQL Health Check
    const pgHealthResponse = http.get(`${POSTGRESQL_URL}/health`, authParams);
    check(pgHealthResponse, {
      'PostgreSQL Health - Status 200': (r) => r.status === 200,
      'PostgreSQL Health - Response Time < 1s': (r) => r.timings.duration < 1000,
    });

    // PostgreSQL Database Creation
    const pgDbPayload = JSON.stringify({
      service_name: 'test-service',
      database_name: 'testdb',
      description: 'Test database for performance testing',
    });

    const pgDbResponse = http.post(`${POSTGRESQL_URL}/database`, pgDbPayload, authParams);
    check(pgDbResponse, {
      'PostgreSQL Database Creation - Status 200': (r) => r.status === 200,
      'PostgreSQL Database Creation - Response Time < 5s': (r) => r.timings.duration < 5000,
    });
  }

  // Test 5: Admin Dashboard Access
  const dashboardResponse = http.get(ADMIN_URL, params);
  check(dashboardResponse, {
    'Admin Dashboard - Status 200': (r) => r.status === 200,
    'Admin Dashboard - Response Time < 2s': (r) => r.timings.duration < 2000,
    'Admin Dashboard - Has Content': (r) => r.body.length > 1000,
  });

  // Think time between requests
  sleep(1);
}

// Setup function (runs once before the test)
export function setup() {
  console.log('Starting K6 Performance Test');
  console.log(`Base URL: ${BASE_URL}`);
  console.log('Test will run for 16 minutes with varying load');
}

// Teardown function (runs once after the test)
export function teardown(data) {
  console.log('K6 Performance Test completed');
}
