#!/usr/bin/env python3
"""
Temporal Worker for the TraceRail Bootstrap Application

This script initializes and runs a Temporal worker that listens on a specific
task queue for workflows and activities to execute.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables from a .env file in the project root
load_dotenv()

try:
    from temporalio.client import Client
    from temporalio.worker import Worker

    # Import the activities and workflows the worker will execute
    from workers.activities import llm_activity, routing_activity
    from workers.workflows import ExampleWorkflow

    # Import the core config to get Temporal settings
    from tracerail.config import TraceRailConfig

except ImportError as e:
    print(f"⚠️  Import error: {e}. Please run 'poetry install' to install dependencies.")
    sys.exit(1)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')


async def main():
    """
    Initializes and runs the Temporal worker.
    """
    print("🚀 Starting Temporal Worker...")
    print("=" * 50)

    # Load configuration from .env file using tracerail-core's config model
    config = TraceRailConfig()
    temporal_config = config.temporal
    task_queue = temporal_config.task_queue
    temporal_address = f"{temporal_config.host}:{temporal_config.port}"

    print(f"   - Connecting to Temporal server at: {temporal_address}")
    print(f"   - Listening on task queue: '{task_queue}'")
    print("   - Registered Workflows: [ExampleWorkflow]")
    print("   - Registered Activities: [llm_activity, routing_activity]")
    print("\nLogs will appear below. Press Ctrl+C to stop the worker.")
    print("-" * 50)

    try:
        # Create a client to connect to the Temporal service
        client = await Client.connect(temporal_address, namespace=temporal_config.namespace)

        # Create and run the worker. The worker polls the task queue and executes
        # workflows and activities.
        worker = Worker(
            client,
            task_queue=task_queue,
            workflows=[ExampleWorkflow],
            activities=[llm_activity, routing_activity],
        )
        await worker.run()

    except ConnectionRefusedError:
        logging.error(f"❌ Connection refused. Is the Temporal service running at {temporal_address}?")
        logging.error("   You can start the service with: `make up`")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Worker stopped manually. Goodbye!")
