"""
Temporal Workflows for the TraceRail Bootstrap Application

This module defines the example Temporal workflow (`ExampleWorkflow`) that
demonstrates how to orchestrate LLM processing and routing logic using
the activities defined in `activities.py`.
"""

import logging
from datetime import timedelta
from temporalio import workflow

# Import activity stubs.
# `with workflow.unsafe.imports_passed_through():` is used to bypass the
# sandbox restrictions for type hinting, which is a best practice.
with workflow.unsafe.imports_passed_through():
    from .activities import llm_activity, routing_activity

# --- Workflow-Specific Logging ---
# This helps differentiate workflow logs from activity or worker logs.
logger = logging.getLogger(__name__)

@workflow.defn
class ExampleWorkflow:
    """
    A sample workflow demonstrating a common AI processing pipeline.
    """

    def __init__(self):
        # A variable to store the result from a human decision signal.
        self._human_decision_result: str | None = None

    @workflow.run
    async def run(self, text_input: str) -> dict:
        """
        Executes the main logic of the workflow.

        Args:
            text_input: The initial text content to process.

        Returns:
            A dictionary summarizing the final outcome of the workflow.
        """
        workflow.logger.info(f"Workflow started for input: '{text_input[:50]}...'")

        # --- Step 1: Process text with an LLM ---
        # Call the LLM activity with a timeout.
        try:
            llm_result = await workflow.execute_activity(
                llm_activity, text_input, start_to_close_timeout=timedelta(seconds=60)
            )
            workflow.logger.info(f"LLM activity completed. Provider: {llm_result.get('provider')}")
        except Exception as e:
            workflow.logger.error(f"LLM activity failed: {e}")
            return {"status": "FAILED", "reason": "LLM processing failed."}

        # --- Step 2: Make a routing decision ---
        # Use the results from the LLM activity to inform the routing logic.
        try:
            routing_result = await workflow.execute_activity(
                routing_activity,
                args=[llm_result["llm_response"], text_input],
                start_to_close_timeout=timedelta(seconds=20),
            )
            decision = routing_result.get("decision")
            workflow.logger.info(f"Routing activity completed. Decision: {decision}")
        except Exception as e:
            workflow.logger.error(f"Routing activity failed: {e}")
            return {"status": "FAILED", "reason": "Routing decision failed."}

        # --- Step 3: Act on the routing decision ---
        if decision == "human":
            workflow.logger.info("Routing to human. Waiting for 'decision' signal...")
            # This is where a task would be created and the system would wait
            # for a human to interact with it, for example, via the Task Bridge.
            try:
                await workflow.wait_for(lambda: self._human_decision_result is not None, timeout=timedelta(hours=24))
                workflow.logger.info(f"Signal received! Human decision: '{self._human_decision_result}'")
                final_status = f"COMPLETED_BY_HUMAN ({self._human_decision_result})"
            except TimeoutError:
                workflow.logger.warning("Timed out waiting for human decision.")
                final_status = "TIMED_OUT"
        else:
            # For "automatic" or other decisions, the workflow completes right away.
            workflow.logger.info("Routing is automatic. Completing workflow.")
            final_status = "COMPLETED_AUTOMATICALLY"

        # --- Step 4: Return the final result ---
        return {
            "status": final_status,
            "llm_output": llm_result.get("answer"),
            "routing_info": routing_result,
        }

    @workflow.signal
    def decision(self, user_decision: str):
        """
        A signal handler that allows an external system (like the Task Bridge)
        to send a decision into the running workflow.
        """
        workflow.logger.info(f"Received 'decision' signal: {user_decision}")
        self._human_decision_result = user_decision
