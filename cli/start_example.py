#!/usr/bin/env python3
"""
Example Workflow Starter Script for TraceRail Bootstrap

This script initializes the TraceRail client and starts a new
'ExampleWorkflow' execution with the provided text as input.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path to allow for absolute imports
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables from a .env file in the project root
load_dotenv()

try:
    import tracerail
    # This workflow will be created in the next step
    from workers.workflows import ExampleWorkflow
    from temporalio.client import WorkflowHandle
    from temporalio.service import RPCError
except ImportError as e:
    print(f"⚠️  Import error: {e}. Make sure dependencies are installed with 'poetry install'.")
    sys.exit(1)

async def main(text_input: str):
    """
    Connects to the TraceRail system and starts the example workflow.
    """
    print("🚀 Starting Example Workflow...")
    print("=" * 50)

    try:
        # The client automatically loads configuration from the .env file.
        # Using the async context manager is a clean way to ensure resources are handled.
        print("   - Connecting to TraceRail client...")
        async with await tracerail.create_client_async() as client:
            print(f"   - Client connected to Temporal on '{client.config.temporal.host}:{client.config.temporal.port}'")

            workflow_id = f"example-workflow-{hash(text_input)}"
            task_queue = client.config.temporal.task_queue

            print(f"\n   - Starting workflow with ID: {workflow_id}")
            print(f"   - Task Queue: {task_queue}")
            print(f"   - Input: '{text_input}'")

            # Start the workflow
            handle: WorkflowHandle = await client.start_workflow(
                ExampleWorkflow.run,
                text_input,
                id=workflow_id,
                task_queue=task_queue,
            )

            print("\n✅ Workflow started successfully!")
            print(f"   Workflow ID: {handle.id}")
            print(f"   Run ID: {handle.first_execution_run_id}")

            print("\n⏳ Waiting for workflow to complete...")
            try:
                # Use asyncio.wait_for to handle the timeout correctly
                result = await asyncio.wait_for(handle.result(), timeout=60.0)
                print("\n🎉 Workflow completed!")
                print(f"   Result: {result}")
            except asyncio.TimeoutError:
                print("\n⚠️  Workflow timed out waiting for result.")
                print("   Check the Temporal UI for progress.")
            except Exception as e:
                print(f"\n❌ Error while waiting for result: {e}")

    except RPCError:
        print("\n❌ RPCError: Could not connect to Temporal service.")
        print("   Please ensure Temporal is running and accessible.")
        print("   You can start it with: `make up`")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python cli/start_example.py \"<your text here>\"")
        sys.exit(1)

    input_text = sys.argv[1]
    asyncio.run(main(input_text))
