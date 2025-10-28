

BotService: A Production-Ready Microservice Blueprint
Project Name: Nexus BotService Microservice
Document Version: 6.0
1. Introduction
This document provides a comprehensive blueprint for building the BotService, a Python-based microservice for the Nexus project. It is designed to be a highly scalable, multi-model, multi-persona conversational AI API. This blueprint details the business and technical requirements, a robust architecture, and a step-by-step development plan with code guidance. It assumes an enterprise-level infrastructure that includes Keycloak, APISIX, and Linkerd on a Kubernetes platform.

2. Guiding Principles & Best Practices
The development of the BotService will adhere to the following core software engineering principles to ensure a high-quality, production-ready system.
Single Responsibility Principle (SRP): Each class or module should have one, and only one, reason to change. The ModelService classes, for example, will only be responsible for interacting with a specific LLM API and nothing else.
Separation of Concerns (SoC): The codebase will be organized into distinct sections, each addressing a single concern. Business logic, data access, and API interaction are all separate modules.
API-First Approach: The API contract is defined and agreed upon before any code is written. This allows for parallel development and ensures the service is built to be easily consumable.
Don't Repeat Yourself (DRY): Code will be reused through abstractions and helper functions. The BaseModelService is a prime example, ensuring all new model services follow a consistent pattern.
Production-Ready Mindset: From the start, the design will prioritize security, scalability, and reliability by using environment variables for secrets, implementing robust logging, and leveraging a containerized architecture.
Industry Standards: The project will follow industry-standard naming conventions (e.g., PEP 8 for Python), use clear documentation, and implement a CI/CD pipeline.
No Copyrighted Code: All code should be original or from open-source libraries with permissive licenses.

3. Business Requirements
3.1. Business Goals
The core business goals for the BotService are to:
Enable Rapid Development: Provide a reusable microservice that allows other teams to quickly integrate conversational AI.
Support Dynamic Adaptability: Allow for the addition or removal of models and personas without code changes.
Promote Reusability: Create a single, centralized service to power multiple applications.
Enhance Personalization: Implement a subscription-based persona access model.
3.2. Functional Requirements
FR-1: Dynamic Model Configuration: The service will dynamically load and configure LLMs from a database.
FR-2: User-Level Model Assignment: A user-specific primary model can be assigned, overriding the default.
FR-3: Goal-Oriented Workflow: The service will identify a conversation's goal and execute a sequenced workflow of tasks.
FR-4: Multi-Persona Support: The system will support various personas with defined tasks and prompts.
FR-5: Subscription-Based Access: A user's profile will be validated to grant persona access.
FR-6: Sequential Task Execution: Tasks are executed sequentially, with output from one serving as input for the next.
FR-7: Conversation Context: The service will store and retrieve conversation history for context.
FR-8: API Interface: A well-defined RESTful API will be exposed.
FR-9: Authentication & Authorization: Authentication will be offloaded to an API Gateway using Keycloak-issued JWTs.
3.3. Non-Functional Requirements
NFR-1: Performance: Low latency for API responses.
NFR-2: Scalability: Designed for horizontal scaling on Kubernetes.
NFR-3: Security: Secrets managed via environment variables. Authentication and authorization are handled externally. Inter-service communication is secured by a service mesh.
NFR-4: Maintainability: Modular codebase with clear documentation.
NFR-5: Reliability: Robust error handling, logging, and metrics are essential.
NFR-6: Network Security: All inter-service communication will be secured with mTLS via Linkerd.

4. Architecture and Component Breakdown
4.1. Architectural Overview
The BotService is a Python microservice deployed on Kubernetes. All external traffic is routed through APISIX, which acts as an API Gateway and handles Keycloak-based JWT authentication and authorization. The BotService's pod is injected into the Linkerd service mesh for automatic mTLS encryption and observability. This design ensures that the microservice's code focuses solely on its core business logic, as authentication and network security are managed by the surrounding infrastructure.
4.2. Key Components
API Gateway (APISIX): The entry point for all external traffic. It will be configured with a Keycloak plugin to validate JWTs before forwarding requests to the BotService. This offloads authentication from the microservice.
Auth Service (Keycloak): A central Identity and Access Management (IAM) service that issues JWTs upon user authentication.
Service Mesh (Linkerd): Manages all internal traffic within the Kubernetes cluster. It automatically secures all communication between services with mTLS and provides built-in dashboards for metrics and tracing.
Core Microservice (BotService): The Python application itself.
API Layer (FastAPI): Exposes the public API endpoint.
Orchestrator: The central brain that orchestrates the workflow.
Model Service Layer: A collection of model-specific middleware classes.
Data Layer (MongoDB): A document database for dynamic configuration and conversation history.

5. API Specification & Object Models
5.1. API Details
Endpoint: /api/v1/bot/chat
Method: POST
Authentication: Requires a valid JWT in the Authorization: Bearer header, validated by APISIX.
Request Body (JSON):
JSON
{
  "user_id": "string",
  "session_id": "string",
  "message": "string",
  "goal_id": "string | null"
}




Response (JSON):
Success (HTTP 200 OK):
JSON
{
  "session_id": "string",
  "response_message": "string"
}




Error (HTTP 400, 401, 500):
JSON
{
  "error": "string",
  "message": "string"
}




5.2. Object Models (Pydantic/MongoDB)
The following models will define the data structures and validation.
UserModel (for users collection):
Python
from pydantic import BaseModel, Field

class UserModel(BaseModel):
    user_id: str = Field(..., description="Unique user identifier from Keycloak.")
    subscription: str = Field(..., description="Subscription tier (e.g., 'bronze', 'silver').")
    model_mapping: dict[str, str] = Field(..., description="Per-user model overrides.")




ModelConfigModel (for models collection):
Python
class ModelConfigModel(BaseModel):
    model_name: str
    provider: str
    model_service_class: str




GoalModel (for goals collection):
Python
class GoalModel(BaseModel):
    goal_id: str
    persona_sequence: list[str]




PersonaModel (for personas collection):
Python
class PersonaModel(BaseModel):
    persona_id: str
    name: str
    access_level: str
    prompts: dict[str, str]




ConversationModel (for conversations collection):
Python
from datetime import datetime

class ConversationModel(BaseModel):
    session_id: str
    user_id: str
    messages: list = []
    created_at: datetime = Field(default_factory=datetime.utcnow)





6. How to Use this Document with GitHub Copilot
A developer or Copilot can use this single document as a comprehensive reference and a clear roadmap. The structure is key, as it provides context, defines requirements, specifies the architecture, and then offers a granular, step-by-step plan.
High-Level Understanding: Begin by reading Sections 1-4 to understand the project's goals, architecture, and technology stack. This establishes the context for all future actions. For example, a developer can prompt, "Based on this document, explain the role of the BotService within the Nexus project's microservices architecture."
Specific Implementations: When starting an activity, refer to its entry in the Development Plan (Section 6). The Code/Guidance column provides a precise prompt for Copilot. For instance, for activity P1.3, the prompt is:
Prompt for Copilot: "Create a .env.example file with MONGO_DB_URL, GEMINI_API_KEY, and GROQ_API_KEY. Now, create a src/app/core/config.py module to load these variables using Pydantic's BaseSettings."
Code Generation & Refinement: Copilot will generate the initial code based on the prompt. The developer's role is to review, refine, and test the generated code against the document's specifications, like the Pydantic models in Section 5.2. If the generated code doesn't match the required structure, the developer can provide more context from the document in the chat.
Connecting Components: For activities that link different modules (like P3.1), the document's API and object model sections become crucial. The developer can prompt Copilot to "write the FastAPI endpoint for /chat that accepts the request body defined in Section 5.1 and calls the orchestrator.process_request function."
This method ensures the developer and Copilot are always working from a single source of truth. The document tells the "what" and "why," and the prompts guide Copilot on the "how," leading to faster development and better code quality that aligns with the project's vision.

7. Detailed Development Plan and Activity Tracker
This plan provides a detailed, dependency-aware roadmap for building the BotService.
Project: Nexus BotService Microservice
Status: Planning
ID
Activity
Status
Dependencies
Code/Guidance
P1.1
Project Setup
Not Started
None
➡️ Guidance: Create a src/app directory in nexus/services/bot_service.
P1.2
FastAPI & Uvicorn
Not Started
P1.1
➡️ Guidance: In requirements.txt, add fastapi, uvicorn, python-dotenv, and motor. In src/app/main.py, create the FastAPI app and a /health endpoint.
P1.3
MongoDB & Env Vars
Not Started
P1.2
➡️ Guidance: Create a .env.example with MONGO_DB_URL, GEMINI_API_KEY, and GROQ_API_KEY. Implement a src/app/core/config.py module to load these variables using Pydantic's BaseSettings.
P1.4
Database Connection
Not Started
P1.3
➡️ Guidance: In src/app/core/database.py, write a function to establish an async MongoDB connection using motor.MotorClient. This function should be called in FastAPI's lifespan event.
P1.5
Data Models (Pydantic)
Not Started
P1.4
➡️ Guidance: Create a src/app/models directory and define the Pydantic models from Section 5.2.
P1.6
Initial Data Script
Not Started
P1.5
➡️ Guidance: Create scripts/seed_db.py. This script will use pymongo (for synchronous operations) to insert initial data for all collections for development purposes.
P2.1
Model Service Layer (Base)
Not Started
P1.3
➡️ Guidance: In src/app/services, create an abstract class BaseModelService with an abstract invoke method. from abc import ABC, abstractmethod.
P2.2
Implement GeminiService
Not Started
P2.1
➡️ Guidance: In src/app/services/gemini_service.py, create a class that inherits from BaseModelService. Implement the invoke method using the google-generativeai SDK.
P2.3
Implement GroqService
Not Started
P2.1
➡️ Guidance: In src/app/services/groq_service.py, implement the invoke method using the groq SDK.
P2.4
LLM Manager
Not Started
P1.5, P2.2, P2.3
➡️ Guidance: In src/app/core/llm_manager.py, create a class with a method get_model_service(model_name) that dynamically imports and returns the correct ModelService instance.
P2.5
Conversation Manager
Not Started
P1.4, P1.5
➡️ Guidance: In src/app/core/conversation_manager.py, create a class with async methods to retrieve conversation history and save new messages to the conversations collection.
P2.6
Orchestrator Module
Not Started
P2.4, P2.5
➡️ Guidance: In src/app/core/orchestrator.py, create an async function process_request(data) that coordinates the entire workflow using the managers.
P3.1
chat Endpoint
Not Started
P1.2, P2.6
➡️ Guidance: In main.py, define the POST /api/v1/bot/chat endpoint. The function signature will take the Pydantic ChatRequest model. It will call orchestrator.process_request.
P3.2
Implement Workflow
Not Started
P3.1
➡️ Guidance: Inside the orchestrator, implement a loop that iterates over the persona_sequence from the database. Build a prompt for each persona, pass it to the llm_manager, and use the output as input for the next persona.
P3.3
Access Validation
Not Started
P3.2
➡️ Guidance: Within the orchestrator loop, add a check to compare the user's subscription against the persona's access_level from the database.
P3.4
Initial Testing
Not Started
P3.3
➡️ Guidance: Create a tests directory. Use pytest and fastapi.testclient to write unit tests for each module and an integration test for the /chat endpoint. Aim for at least 80% test coverage.
P4.1
Dockerization
Not Started
P3.4
➡️ Guidance: Create a Dockerfile for a multi-stage build. Use a python:3.11-slim base image. Also, create a docker-compose.yml for local development, linking the service to a local MongoDB container.
P4.2
Error Handling & Logging
Not Started
P3.4
➡️ Guidance: Implement centralized logging using Python's logging module. Add FastAPI exception handlers for 400 and 500 errors.
P4.3
Kubernetes Manifests
Not Started
P4.1
➡️ Guidance: Create bot-service-deployment.yaml and bot-service-service.yaml. The Deployment manifest will include annotations for Linkerd injection: linkerd.io/inject: enabled.
P4.4
APISIX Route Config
Not Started
P4.3
➡️ Guidance: Create a bot-service-route.yaml using APISIX's ApisixRoute Custom Resource Definition. It will include a jwt-authz plugin with the Keycloak configuration.
P4.5
RBAC for K8s
Not Started
P4.3
➡️ Guidance: Create a bot-service-rbac.yaml with a ServiceAccount and a Role with restricted permissions.
P4.6
CI/CD Pipeline
Not Started
P4.1, P4.4, P4.5
➡️ Guidance: Set up a GitHub Actions workflow. The CI job will run tests, linting, and build the Docker image. The CD job will apply the Kubernetes manifests to the cluster on a merge to the main branch.


