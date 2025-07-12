# Technical Debt Task List

This document tracks the known technical debt in the TraceRail platform. It is a living document that should be updated as new debt is incurred or old debt is addressed.

## High Priority / Blocking Issues

- [ ] **Architectural:** The Docker build process is tightly coupled to local file paths (`../tracerail-core`). This needs to be refactored to use a decoupled artifact-based build to ensure reliable and portable container builds.
- [ ] **Frontend:** The UI has zero component-level unit tests, making refactoring risky. We need to add basic rendering and interaction tests for key components like `CaseView` and `ActionButtons`.
- [ ] **Frontend:** The `CaseView` component performs a full-page reload (`window.location.reload()`) after submitting a decision. This should be replaced with a dynamic state update to re-fetch case data.

## `tracerail-core` (Business Logic)

- [ ] **Architecture:** The `FlexibleCaseWorkflow` is not yet flexible. The entire process flow is hardcoded. The system needs to be refactored to use a real, versioned process definition.
- [ ] **Implementation:** The `enrich_case_data` activity is a placeholder and contains no real AI or business logic.
- [ ] **Testing:** The workflow tests only cover the "happy path" of enrichment. There are no tests for the decision-handling logic (Approve/Reject) or for failure modes.

## `tracerail-task-bridge` (API Backend)

- [ ] **Testing:** The API has no fast-running unit tests. All current tests are integration or contract tests that require a live Temporal server. We need unit tests that mock the `CaseService`.
- [ ] **Testing:** There is no contract test for the `POST /api/v1/cases` creation endpoint. (This is lower priority as there is no consumer yet, but it is still a gap).
- [ ] **Error Handling:** The API's error handling is minimal. It needs to be improved to handle invalid request payloads (422 errors) and other downstream failures more gracefully.

## `tracerail-action-center` (Frontend)

- [ ] **State Management:** The frontend relies on basic `useState`. A more robust client-side state management library (like React Query, Zustand, or Redux Toolkit) is needed to handle server state, caching, and background refetching cleanly.
- [ ] **Routing:** The `CaseView` is hardcoded to a single case ID. A routing library (like React Router) should be implemented to handle URLs like `/cases/:caseId`.

## Cross-Cutting Concerns

- [ ] **Configuration:** Configuration values (ports, URLs, etc.) are currently hardcoded in multiple places. These should be consolidated and managed exclusively through environment variables.
- [ ] **Observability:** We have implemented structured logging and metrics, but distributed tracing (the third pillar) is missing.
- [ ] **Security:** The platform has no authentication or authorization whatsoever.