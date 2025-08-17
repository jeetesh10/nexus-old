import http from 'k6/http';
import { check, sleep } from 'k6';

/**
 * k6 Smoke Test
 * 
 * This is a simple smoke test to ensure that the target service is up and running
 * and can handle a minimal amount of traffic. It's not designed to stress the system,
 * but rather to be a quick sanity check that can be run in a CI/CD pipeline.
 * 
 * See https://k6.io/docs/ for more information on k6.
 */

export const options = {
  vus: 1, // 1 virtual user
  duration: '10s', // for 10 seconds
  thresholds: {
    http_req_failed: ['rate<0.01'], // http errors should be less than 1%
    http_req_duration: ['p(95)<200'], // 95% of requests should be below 200ms
  },
};

// This is a placeholder URL. Once the API Gateway and services are deployed,
// this should be updated to a valid endpoint, likely passed in as an environment variable.
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  // Access a sample endpoint
  const res = http.get(`${BASE_URL}/`);

  // Check if the response is successful
  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1); // Wait for 1 second between requests
}
