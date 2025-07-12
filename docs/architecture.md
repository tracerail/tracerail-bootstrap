# TraceRail System Architecture

## 1. Overview

This document describes the architecture of the TraceRail platform. TraceRail is designed as a closed-loop, human-in-the-loop automation system. Its primary purpose is to process complex, semi-structured tasks by intelligently combining deterministic business rules, generative AI agents, and human oversight.

The architecture is built to be asynchronous, observable, and extensible, allowing new automation processes to be defined and deployed without altering the core infrastructure.

## 2. Core Components

The platform is composed of several key services and infrastructure components that work together to execute and monitor workflows.

### Application Services

*   **`tracerail-core`**: The heart of the business logic. This Python library contains the Temporal workflow and activity definitions. It orchestrates the lifecycle of a "Case," from enrichment and rule evaluation to human interaction and final commitment.
*   **`tracerail-task-bridge`**: The API gateway for the system. This FastAPI service exposes a RESTful API to the outside world, receives incoming requests, and translates them into commands for the Temporal service (e.g., starting workflows, sending signals).
*   **`tracerail-action-center`**: The frontend application for human agents. This React-based single-page application provides a user interface for human-in-the-loop review. Agents use the Action Center to view cases that require manual intervention and to submit their decisions.

### Infrastructure Components

*   **Temporal**: The core orchestration engine for the entire platform. Temporal is responsible for the durable execution of our long-running `FlexibleCaseWorkflow`. It guarantees that workflows run to completion, even in the face of process restarts or failures.
*   **DMN Engine (Flowable)**: A containerized decision engine responsible for executing deterministic business rules defined in the Decision Model and Notation (DMN) standard. It acts as a "gate" before and after the AI step to enforce hard policies efficiently.
*   **Observability Stack**: A collection of services that provide deep insight into the system's behavior, based on the "three pillars of observability."
    *   **Prometheus**: Scrapes and stores time-series metrics from the `tracerail-task-bridge` and Temporal server.
    *   **Grafana**: Provides dashboards for visualizing the metrics stored in Prometheus.
    *   **Jaeger**: Collects and visualizes distributed traces, providing an end-to-end view of requests as they travel through the system.

## 3. Architectural Principles

*   **Asynchronous by Default**: The entire system is built around long-running, asynchronous Temporal workflows. This makes the platform resilient and scalable.
*   **Human-in-the-Loop as a Core Feature**: The system is designed with the explicit understanding that not all tasks can be fully automated. The Action Center is a first-class component, not an afterthought.
*   **Observability-First**: The platform is designed to be highly observable. Structured logging, metrics, and distributed tracing are integrated into the core services to provide clear insight into the system's health and behavior.
*   **Decoupled Components**: Each service (`core`, `bridge`, `action-center`) is a separate component with a well-defined responsibility. This separation of concerns allows for independent development, testing, and deployment.

## 4. System Data Flow

The lifecycle of a case follows the steps outlined in the [System Blueprint](./SYSTEM_BLUEPRINT.md).

1.  **Trigger**: A new case is created via a `POST` request to the `tracerail-task-bridge` API. The API starts a new `FlexibleCaseWorkflow` instance in Temporal.
2.  **Pre-Rules Gate**: The workflow first calls an activity that executes a "pre-rules" check against the DMN engine. This can immediately reject cases that are clearly out of policy (e.g., an expense report from a non-employee).
3.  **AI Enrichment**: If the pre-rules check passes, the workflow calls the `enrich_case_data` activity. This activity uses an LLM and other tools to analyze the case and generate summaries, policy checks, and risk scores.
4.  **Guardrails**: (Future) The output of the AI agent is passed through a safety filter to ensure quality and remove sensitive data.
5.  **Post-Rules Gate**: The sanitized output from the agent is then checked against a "post-rules" DMN table. This gate determines if the case can be auto-approved, auto-rejected, or if it requires human review.
6.  **Human Review**: If the post-rules gate flags the case for review, the workflow pauses. The case appears in the `tracerail-action-center`, where a human agent makes a decision. Their decision is sent back to the workflow via a "signal".
7.  **Commit**: Once a final decision is reached (either by automation or a human), the workflow executes a final activity to commit the result (e.g., update a database, call a downstream API).
8.  **Observability**: Throughout this entire process, every API call, workflow step, activity execution, and decision is logged, measured, and traced by the observability stack.

This flow creates a "closed-loop" system where the most expensive and slowest steps (AI processing and human review) are only used when absolutely necessary.