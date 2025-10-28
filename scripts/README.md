# scripts/ — Nexus dev scripts

Purpose: keep a small canonical set for daily dev/ops and group other helpers.

Canonical workflow (dev):
1. Build & load images
   ./scripts/build-and-load-images.sh
2. Start cluster (kind)
   ./scripts/start-platform-kind.sh
3. Deploy stack
   ./scripts/deploy-complete-stack.sh
4. Smoke test
   ./scripts/test-current-platform.sh
5. Teardown
   ./scripts/stop-platform.sh

Folders:
- scripts/ops : targeted deploys and infra helpers
- scripts/test : integration/performance/contract tests
- scripts/tools: tooling (postman, generators, env fixes)
- scripts/archive: deprecated / duplicates

Keep scripts idempotent and document args. Use git mv for renames to preserve history.