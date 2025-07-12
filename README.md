# TraceRail Platform Bootstrap

This repository is the central development and bootstrapping environment for the TraceRail platform. It contains the necessary Docker Compose configurations, documentation, and helper scripts to launch and manage the entire suite of TraceRail services for local development.

TraceRail is a closed-loop, human-in-the-loop automation platform designed to process complex tasks by intelligently combining deterministic business rules, generative AI, and human oversight.

## 1. Current State & Architecture

The project has successfully completed its initial "vertical slice" implementation, along with a foundational observability stack. The current state is as follows:

*   **Unified Development Environment:** A single `docker-compose up --build` command launches the entire platform, including:
    *   `tracerail-task-bridge`: The API backend.
    *   `tracerail-core`: The Temporal worker for business logic.
    *   A full observability stack with Prometheus, Grafana, and Jaeger.
*   **End-to-End Workflow:** A case can be created via a `POST` request to the API. It is processed by a (mock) AI agent, and can then be viewed and approved/rejected by a human in the Action Center. The system can handle both active and completed cases.
*   **Three Pillars of Observability:**
    *   **Logging:** All backend services use structured (JSON) logging.
    *   **Metrics:** The API exposes key performance indicators that can be visualized in a pre-configured Grafana dashboard.
    *   **Tracing:** The system is fully instrumented with OpenTelemetry for end-to-end distributed tracing, viewable in Jaeger.

## 2. Quick Start

**Prerequisites:**
- Docker and Docker Compose

**Instructions:**
1. Clone all necessary repositories (`tracerail-bootstrap`, `tracerail-core`, `tracerail-task-bridge`, `tracerail-action-center`) into the same parent directory.
2. Navigate to the `tracerail-bootstrap` directory.
3. Run `docker-compose up --build`. This will build all the container images and start the full application stack.

**Accessing Services:**
*   **Action Center (UI):** http://localhost:3002
*   **Task Bridge API Docs:** http://localhost:8000/docs
*   **Temporal UI:** http://localhost:8233
*   **Grafana Dashboard:** http://localhost:3001 (admin / admin)
*   **Jaeger Traces:** http://localhost:16686

## 3. Next Steps

With the stable and observable foundation now in place, the project is ready to begin implementing the core automation logic as defined in the [System Blueprint](./docs/SYSTEM_BLUEPRINT.md).

The immediate next step is to implement the **Pre-Rules Gate (DMN)**.

## 4. Key Documentation

*   **[System Blueprint](./docs/SYSTEM_BLUEPRINT.md):** The high-level vision and target architecture for the platform.
*   **[System Architecture](./docs/architecture.md):** A detailed description of the components and data flow.
*   **[Technical Debt Task List](./docs/TECH_DEBT.md):** A list of known shortcuts and areas for improvement.
