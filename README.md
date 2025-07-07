# TraceRail Bootstrap

This repository provides a runnable application stack that demonstrates how to use the **[tracerail-core](https://github.com/tracerail/tracerail-core)** library. It spins up all the necessary backend services to run a complete, end-to-end AI workflow.

*   **Core Logic**: Uses the **[tracerail-core](https://github.com/tracerail/tracerail-core)** library for all workflow, LLM, and routing orchestration.
*   **Durable Workflows**: **Temporal OSS** for stateful, reliable execution.
*   **Human-in-the-Loop**: A simple **Task Bridge** (FastAPI service) to send human decisions back into a running workflow.
*   **Observability**: A small sidecar stack with **Prometheus** and **Grafana** for monitoring.

> _No images from GHCR; all pullable anonymously from Docker Hub or built locally._

## Prerequisites

- **Python 3.12** (use pyenv for version management)
- **Poetry** for Python dependency management
- **Docker** and **Docker Compose** for services
- **LLM API Key** (DeepSeek recommended: https://platform.deepseek.com/api_keys or OpenAI: https://platform.openai.com/api-keys)

---

## Quick start

```bash
# clone
 git clone https://github.com/tracerail/tracerail-bootstrap.git
 cd tracerail-bootstrap

# automated setup (recommended)
 make setup

# or manual setup:
 # pyenv install 3.12.8 && pyenv local 3.12.8
 # make setup  # Creates .env from .env.example
 # # Edit .env and add your LLM API key
 # poetry install
 # make up

# test that the services are running and the worker can connect
 make start-example

# start the worker (in a new terminal)
 make worker

# launch a sample workflow with a custom message
 poetry run python cli/start_example.py "Your custom message here"
```

*   **Temporal UI**: http://localhost:8233
*   **Task Bridge API**: http://localhost:7070/docs
*   **Grafana Dashboards**: http://localhost:3000 (admin / grafana)

---

## Environment Variables

The system uses environment variables for configuration. Run the setup script to configure automatically:

```bash
make setup
```

Or configure manually:
```bash
cp .env.example .env
# Edit .env and set your LLM API key:
# DEEPSEEK_API_KEY=sk-your-actual-deepseek-api-key-here
# OR
# OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**Getting an LLM API Key:**

**Option 1: DeepSeek (Recommended - More Cost Effective)**
1. Visit https://platform.deepseek.com/api_keys
2. Create a new API key
3. Add it to your `.env` file: `DEEPSEEK_API_KEY=your-key-here`

**Option 2: OpenAI**
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Add it to your `.env` file: `OPENAI_API_KEY=your-key-here`

Without an API key, the system will use mock responses for testing.

**Test your setup:**
```bash
make start-example
# For a full list of commands:
make help
```

---
