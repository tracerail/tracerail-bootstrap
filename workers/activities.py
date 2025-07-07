"""
Temporal Activities for the TraceRail Bootstrap Application

This module defines the Temporal activities that orchestrate calls to the
tracerail-core library. These activities act as the bridge between the
workflow's logic and the core functionalities like LLM processing and routing.
"""

import logging
from temporalio import activity

try:
    import tracerail
    from tracerail.routing import RoutingContext, RoutingResult
    from tracerail.llm import LLMResponse
except ImportError as e:
    # This will cause the worker to fail on startup if dependencies aren't right,
    # which is a good, clear failure mode.
    raise ImportError(f"Could not import tracerail-core. Please run 'poetry install'.") from e

# --- Activity-Specific Logging ---
# This helps differentiate activity logs from the rest of the application.
logger = logging.getLogger(__name__)


@activity.defn
async def llm_activity(text_input: str) -> dict:
    """
    An activity that processes text using the configured LLM provider
    from the tracerail-core library.

    Args:
        text_input: The text to be processed by the LLM.

    Returns:
        A dictionary containing the LLM's response and metadata.
    """
    activity.heartbeat("Initializing client...")
    logger.info(f"Received LLM activity request for input: '{text_input[:30]}...'")

    # The client automatically loads configuration from the environment (.env)
    async with await tracerail.create_client_async() as client:
        provider = client.config.llm.provider.value
        activity.heartbeat(f"Processing with {provider}...")

        # Use the high-level process_content method which handles the full pipeline
        result = await client.process_content(text_input)

        logger.info("LLM processing complete.")

        # Return a simplified dictionary, similar to what might have existed before,
        # for compatibility or ease of use in the workflow.
        return {
            "answer": result.llm_response.content,
            "provider": provider,
            # Pass along the full response and routing decision for the next step
            "llm_response": result.llm_response.to_dict(),
            "routing_decision": result.routing_decision.to_dict(),
        }


@activity.defn
async def routing_activity(llm_response_dict: dict, original_content: str) -> dict:
    """
    An activity that makes a routing decision based on the output of the LLM
    and a set of rules defined in `rules.yaml`.

    Args:
        llm_response_dict: The dictionary representation of the LLMResponse from the previous step.
        original_content: The original text content that was processed.

    Returns:
        A dictionary containing the routing decision.
    """
    activity.heartbeat("Initializing routing engine...")
    logger.info("Received routing activity request...")

    # We don't need to re-run the LLM, just the routing part.
    # The config is loaded from the environment by default.
    async with await tracerail.create_client_async() as client:
        # Re-create the necessary context objects from the input dictionaries
        llm_response = LLMResponse.model_validate(llm_response_dict)
        routing_context = RoutingContext(
            content=original_content,
            llm_response=llm_response,
        )

        activity.heartbeat("Evaluating routing rules...")
        # Route the context using the engine from the initialized client
        routing_result: RoutingResult = await client.routing_engine.route(routing_context)
        logger.info(f"Routing decision: '{routing_result.decision.value}' based on reason: '{routing_result.reason}'")

        # Return the routing result as a dictionary
        return routing_result.to_dict()
