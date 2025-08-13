const { Verifier } = require('@pact-foundation/pact');
const path = require('path');

// Pact Provider Verification
async function verifyPacts() {
  const opts = {
    provider: 'auth-api-service',
    providerBaseUrl: 'http://localhost:8084',
    pactBrokerUrl: 'http://localhost:9292', // If using Pact Broker
    pactUrls: [
      path.resolve(process.cwd(), 'pacts', 'nexus-platform-consumer-auth-api-service.json')
    ],
    publishVerificationResult: true,
    providerVersion: '1.0.0',
    logLevel: 'INFO'
  };

  try {
    await new Verifier().verifyProvider(opts);
    console.log('✅ Pact verification completed successfully');
  } catch (error) {
    console.error('❌ Pact verification failed:', error);
    process.exit(1);
  }
}

// MongoDB Orchestrator Provider Verification
async function verifyMongoPacts() {
  const opts = {
    provider: 'mongodb-orchestrator-service',
    providerBaseUrl: 'http://localhost:8000',
    pactUrls: [
      path.resolve(process.cwd(), 'pacts', 'nexus-platform-consumer-mongodb-orchestrator-service.json')
    ],
    publishVerificationResult: true,
    providerVersion: '1.0.0',
    logLevel: 'INFO'
  };

  try {
    await new Verifier().verifyProvider(opts);
    console.log('✅ MongoDB Pact verification completed successfully');
  } catch (error) {
    console.error('❌ MongoDB Pact verification failed:', error);
    process.exit(1);
  }
}

// Run verifications
async function runAllVerifications() {
  console.log('🔍 Starting Pact Provider Verifications...');
  
  try {
    await verifyPacts();
    await verifyMongoPacts();
    console.log('🎉 All Pact verifications completed successfully!');
  } catch (error) {
    console.error('💥 Pact verification failed:', error);
    process.exit(1);
  }
}

// Export for use in other scripts
module.exports = {
  verifyPacts,
  verifyMongoPacts,
  runAllVerifications
};

// Run if called directly
if (require.main === module) {
  runAllVerifications();
}
