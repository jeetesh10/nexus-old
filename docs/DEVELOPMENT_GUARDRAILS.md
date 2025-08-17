# Development Guardrails & Process

## Mandatory Pre-Development Requirements

### 1. **STRICT ADHERENCE TO RULES**
- **NO hardcoding** - All configuration via environment variables
- **NO mock data** - Production-grade solutions only
- **NO copy-paste code** - Original implementation only
- **NO environment-specific naming** - Generic, environment-agnostic names
- **NO shortcuts** - Follow complete process for every service

### 2. **Architecture Documentation Required BEFORE Development**
For EVERY service, the following MUST be completed and APPROVED:

#### A. Architecture Decision Record (ADR)
- Problem statement
- Considered options
- Decision rationale
- Consequences
- Dev vs Prod differences
- **STATUS: PENDING APPROVAL** ❌

#### B. Sequence Diagram
- Service interactions
- Authentication flow
- Error handling
- **STATUS: PENDING APPROVAL** ❌

#### C. API Contracts
- OpenAPI/Swagger specification
- Request/response schemas
- Error codes
- **STATUS: PENDING APPROVAL** ❌

#### D. Test Strategy
- Unit test coverage requirements (>80%)
- Integration test scenarios
- Load testing requirements
- **STATUS: PENDING APPROVAL** ❌

#### E. Deployment Strategy
- Production-grade configuration
- High availability setup
- Monitoring and alerting
- **STATUS: PENDING APPROVAL** ❌

#### F. Dependencies Analysis
- Third-party libraries justification
- Security scanning results
- License compliance
- **STATUS: PENDING APPROVAL** ❌

### 3. **Approval Process**
- Each document requires explicit user approval
- NO development starts without ALL approvals
- Any deviation requires new RCA document
- Changes to approved documents require re-approval

### 4. **Production-Grade Standards**
- High Availability (3+ replicas minimum)
- TLS encryption everywhere
- Proper secret management (NO dev-mode tools)
- Resource limits and monitoring
- Backup and recovery procedures
- Security scanning and compliance

### 5. **Development Process**
1. **System Context Diagram** - Overall system view
2. **Service-by-Service ADR/Sequence Approval** - Each service individually
3. **Implementation** - Only after ALL approvals
4. **Testing** - Comprehensive testing before deployment
5. **Documentation** - Keep all docs updated

## Current Status Dashboard

### System Level
- [ ] System Context Diagram - **PENDING APPROVAL** ❌
- [ ] Overall Architecture - **PENDING APPROVAL** ❌

### Services Status
- [ ] Keycloak - **PENDING ADR/SEQUENCE APPROVAL** ❌
- [ ] MongoDB - **PENDING ADR/SEQUENCE APPROVAL** ❌
- [ ] Auth API - **PENDING ADR/SEQUENCE APPROVAL** ❌
- [ ] Neo4j - **PENDING ADR/SEQUENCE APPROVAL** ❌
- [ ] API Gateway - **PENDING ADR/SEQUENCE APPROVAL** ❌
- [ ] Admin Dashboard - **PENDING ADR/SEQUENCE APPROVAL** ❌
- [ ] Monitoring - **PENDING ADR/SEQUENCE APPROVAL** ❌

## Enforcement Rules

### **DEVELOPMENT BLOCKER**
- **NO CODE WILL BE WRITTEN** until all approvals are obtained
- **NO SHORTCUTS** - Even if it takes longer
- **NO EXCEPTIONS** - Rules apply to every service
- **NO ASSUMPTIONS** - Explicit approval required for everything

### **Quality Gates**
- Architecture review before implementation
- Security review for all components
- Performance requirements defined upfront
- Monitoring strategy approved
- Backup/recovery procedures documented

This document serves as the CONTRACT between user and AI assistant for all development work.
