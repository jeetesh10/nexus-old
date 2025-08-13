const { Pact } = require('@pact-foundation/pact');
const { ConsumerApiClient } = require('./pact-consumer-client');
const path = require('path');

// Configure Pact
const provider = new Pact({
  consumer: 'nexus-platform-consumer',
  provider: 'auth-api-service',
  port: 1234,
  log: path.resolve(process.cwd(), 'logs', 'pact.log'),
  dir: path.resolve(process.cwd(), 'pacts'),
  logLevel: 'INFO',
  spec: 2
});

describe('Auth API Contract Tests', () => {
  const client = new ConsumerApiClient('http://localhost:1234');

  beforeAll(() => provider.setup());
  afterEach(() => provider.verify());
  afterAll(() => provider.finalize());

  describe('POST /api/auth/login', () => {
    it('should return access token for valid credentials', async () => {
      const loginRequest = {
        username: 'admin',
        password: 'AdminPass123'
      };

      const loginResponse = {
        access_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...',
        refresh_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...',
        token_type: 'Bearer',
        expires_in: 3600,
        user: {
          id: '123',
          username: 'admin',
          email: 'admin@nexus.platform',
          roles: ['platform-admin']
        }
      };

      await provider.addInteraction({
        state: 'user exists with valid credentials',
        uponReceiving: 'a login request with valid credentials',
        withRequest: {
          method: 'POST',
          path: '/api/auth/login',
          headers: {
            'Content-Type': 'application/json'
          },
          body: loginRequest
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: loginResponse
        }
      });

      const response = await client.login(loginRequest);
      expect(response.access_token).toBeDefined();
      expect(response.user.username).toBe('admin');
    });

    it('should return 401 for invalid credentials', async () => {
      const loginRequest = {
        username: 'invalid',
        password: 'wrong'
      };

      await provider.addInteraction({
        state: 'user does not exist',
        uponReceiving: 'a login request with invalid credentials',
        withRequest: {
          method: 'POST',
          path: '/api/auth/login',
          headers: {
            'Content-Type': 'application/json'
          },
          body: loginRequest
        },
        willRespondWith: {
          status: 401,
          headers: {
            'Content-Type': 'application/json'
          },
          body: {
            error: 'invalid_credentials',
            message: 'Invalid username or password'
          }
        }
      });

      try {
        await client.login(loginRequest);
        fail('Should have thrown an error');
      } catch (error) {
        expect(error.response.status).toBe(401);
      }
    });
  });

  describe('GET /api/auth/health', () => {
    it('should return health status', async () => {
      await provider.addInteraction({
        state: 'service is healthy',
        uponReceiving: 'a health check request',
        withRequest: {
          method: 'GET',
          path: '/api/auth/health'
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: {
            status: 'healthy',
            timestamp: '2024-01-01T00:00:00Z',
            version: '1.0.0',
            uptime: 3600
          }
        }
      });

      const response = await client.getHealth();
      expect(response.status).toBe('healthy');
    });
  });

  describe('GET /api/auth/user-info', () => {
    it('should return user info with valid token', async () => {
      const userInfo = {
        id: '123',
        username: 'admin',
        email: 'admin@nexus.platform',
        roles: ['platform-admin'],
        groups: ['nexus', 'platform-admin']
      };

      await provider.addInteraction({
        state: 'user is authenticated',
        uponReceiving: 'a user info request with valid token',
        withRequest: {
          method: 'GET',
          path: '/api/auth/user-info',
          headers: {
            'Authorization': 'Bearer valid-token'
          }
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: userInfo
        }
      });

      const response = await client.getUserInfo('valid-token');
      expect(response.username).toBe('admin');
      expect(response.roles).toContain('platform-admin');
    });
  });
});

// MongoDB Orchestrator Contract Tests
const mongoProvider = new Pact({
  consumer: 'nexus-platform-consumer',
  provider: 'mongodb-orchestrator-service',
  port: 1235,
  log: path.resolve(process.cwd(), 'logs', 'pact-mongo.log'),
  dir: path.resolve(process.cwd(), 'pacts'),
  logLevel: 'INFO',
  spec: 2
});

describe('MongoDB Orchestrator Contract Tests', () => {
  const mongoClient = new ConsumerApiClient('http://localhost:1235');

  beforeAll(() => mongoProvider.setup());
  afterEach(() => mongoProvider.verify());
  afterAll(() => mongoProvider.finalize());

  describe('POST /api/mongodb/operation', () => {
    it('should insert document successfully', async () => {
      const operationRequest = {
        service_name: 'test-service',
        database_name: 'testdb',
        collection_name: 'users',
        operation: 'insert',
        data: {
          name: 'John Doe',
          email: 'john@example.com',
          created_at: '2024-01-01T00:00:00Z'
        }
      };

      const operationResponse = {
        success: true,
        data: {
          inserted_id: '507f1f77bcf86cd799439011',
          acknowledged: true
        },
        message: 'Document inserted successfully',
        timestamp: '2024-01-01T00:00:00Z'
      };

      await mongoProvider.addInteraction({
        state: 'database and collection exist',
        uponReceiving: 'an insert operation request',
        withRequest: {
          method: 'POST',
          path: '/api/mongodb/operation',
          headers: {
            'Content-Type': 'application/json'
          },
          body: operationRequest
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: operationResponse
        }
      });

      const response = await mongoClient.mongoOperation(operationRequest);
      expect(response.success).toBe(true);
      expect(response.data.inserted_id).toBeDefined();
    });

    it('should find documents successfully', async () => {
      const operationRequest = {
        service_name: 'test-service',
        database_name: 'testdb',
        collection_name: 'users',
        operation: 'find',
        filter: {
          email: 'john@example.com'
        }
      };

      const operationResponse = {
        success: true,
        data: [
          {
            _id: '507f1f77bcf86cd799439011',
            name: 'John Doe',
            email: 'john@example.com',
            created_at: '2024-01-01T00:00:00Z'
          }
        ],
        message: 'Documents found successfully',
        timestamp: '2024-01-01T00:00:00Z'
      };

      await mongoProvider.addInteraction({
        state: 'documents exist in collection',
        uponReceiving: 'a find operation request',
        withRequest: {
          method: 'POST',
          path: '/api/mongodb/operation',
          headers: {
            'Content-Type': 'application/json'
          },
          body: operationRequest
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: operationResponse
        }
      });

      const response = await mongoClient.mongoOperation(operationRequest);
      expect(response.success).toBe(true);
      expect(response.data).toHaveLength(1);
      expect(response.data[0].name).toBe('John Doe');
    });
  });

  describe('GET /api/mongodb/health', () => {
    it('should return health status', async () => {
      await mongoProvider.addInteraction({
        state: 'service is healthy',
        uponReceiving: 'a health check request',
        withRequest: {
          method: 'GET',
          path: '/api/mongodb/health'
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: {
            status: 'healthy',
            mongodb_connected: true,
            timestamp: '2024-01-01T00:00:00Z',
            version: '1.0.0',
            uptime: 3600
          }
        }
      });

      const response = await mongoClient.getHealth();
      expect(response.status).toBe('healthy');
      expect(response.mongodb_connected).toBe(true);
    });
  });
});

// Consumer API Client
class ConsumerApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async login(credentials) {
    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getHealth() {
    const response = await fetch(`${this.baseUrl}/api/auth/health`);
    return response.json();
  }

  async getUserInfo(token) {
    const response = await fetch(`${this.baseUrl}/api/auth/user-info`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.json();
  }

  async mongoOperation(operation) {
    const response = await fetch(`${this.baseUrl}/api/mongodb/operation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(operation)
    });
    return response.json();
  }
}

module.exports = { ConsumerApiClient };
