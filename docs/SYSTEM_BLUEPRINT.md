# System Blueprint

This document outlines the target architecture for the TraceRail platform. It describes a closed-loop system that combines deterministic rule-based processing with generative AI and human-in-the-loop review to create an efficient, safe, and continuously learning automation platform.

## High-Level Diagram

```text
┌──────────────────────────┐
│ 1. Trigger               │
│    (API / Webhook)       │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│ 2. Pre-Rules Gate (DMN)  │  ← blocks anything
│   • policy, limits       │     out of scope BEFORE
└──────────────┬───────────┘     it hits the LLM
               │  pass
               ▼
┌──────────────────────────┐
│ 3. Agent Step (LangGraph │
│    + LLM + tools)        │
└──────────────┬───────────┘
               │  raw output
               ▼
┌──────────────────────────┐
│ 4. Guardrails Filter     │
│   • schema / PII /       │
│     toxicity, etc.       │
└──────────────┬───────────┘
               │  clean output
               ▼
┌──────────────────────────┐
│ 5. Post-Rules Gate (DMN) │  ← final business
│   • amount ≤ $500?       │     validation
└──────┬─────────┬─────────┘
       │pass     │needs-review
       │         ▼
       │   ┌──────────────────┐
       │   │ 6. Human Review  │
       │   │   (Action Center)      │
       │   └─────────┬────────┘
       │             │ approve / fix
       ▼             ▼
┌──────────────────┐ ┌───────────────────────┐
│ 7. Commit / Next │ │ 8. Logs & Traces      │
│    Step (API/DB) │ │    (OpenTelemetry)    │
└────────┬─────────┘ └──────────┬────────────┘
         │                       │
         ▼                       ▼
                    ┌──────────────────────────┐
                    │ 9. ML Pattern Mining     │
                    │    + Rule Suggestion     │
                    └──────────┬───────────────┘
                               │  approved rule
                               ▼
                    ┌──────────────────────────┐
                    │ DMN Repo (Git + PR)      │
                    │ → promotes to Pre/Post   │
                    │   Rules after shadow test│
                    └──────────────────────────┘
```

---

## Component Legend

1.  **Trigger** – Any external event starts a Temporal workflow (e.g., an API call).
2.  **Pre-Rules DMN** – A cheap, deterministic policy gate using a Decision Model and Notation (DMN) engine. It blocks out-of-scope requests *before* incurring any LLM-related costs.
3.  **Agent** – A LangGraph node running an LLM (e.g., GPT-4o) and a set of tools to perform complex analysis and data enrichment.
4.  **Guardrails** – A safety filter (e.g., using Guardrails AI or NeMo Guardrails) to validate the schema of the LLM's output and check for PII, toxicity, or other quality issues.
5.  **Post-Rules DMN** – A second deterministic gate that re-validates the cleaned output from the agent against hard business rules (e.g., checking expense limits).
6.  **Human Review** – The human-in-the-loop step. A case is routed to a human agent in the Action Center only if the guardrails or DMN gates flag the task for review.
7.  **Commit / Next Step** – The final action taken for the case, such as writing to a database, calling a downstream API, or triggering the next workflow.
8.  **Logs & Traces** – A comprehensive observability pipeline using OpenTelemetry to record the inputs, outputs, decisions, and reviewer actions for every step in the process.
9.  **ML Pattern Mining** – A feedback loop where a nightly batch process mines failure cases and human interventions to propose new, high-precision IF-THEN rules. An SME can approve these rules via a Git pull request, which updates the DMN rules and continuously improves the pre-filter gate.

---

## Core Principle: The Closed Loop

This architecture creates a **closed loop**:

*   **Cost-Saving:** Deterministic gates save money by filtering requests before they reach the expensive LLM.
*   **Safety:** Guardrails sanitize language and data, ensuring quality and safety.
*   **Scalability:** Humans are reserved for true edge cases, closing unknown gaps without being overwhelmed.
*   **Learning:** Machine learning continuously promotes the solutions to repeatable mistakes into new deterministic rules, shrinking risk and human workload over time.