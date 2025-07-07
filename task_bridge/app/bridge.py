"""
TraceRail Task Bridge - FastAPI Application

This service acts as a bridge between human users/external systems and
running Temporal workflows. It provides simple HTTP endpoints to signal
workflows, check their status, and perform other interactions without
needing to use a full Temporal client.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from temporalio.client import Client, WorkflowNotFoundError
from temporalio.exceptions import RPCError

# --- FastAPI Application Setup ---
app = FastAPI(
    title="TraceRail Task Bridge",
    description="A bridge service for sending signals to human-in-the-loop workflows.",
    version="1.0.0",
)

# --- Pydantic Models for API Payloads ---

class Decision(BaseModel):
    """
    Represents the payload for sending a decision to a workflow.
    """
    workflow_id: str = Field(..., description="The ID of the Temporal workflow to signal.")
    status: str = Field(..., description="The decision status (e.g., 'approved', 'rejected').")
    reviewer: str = Field(..., description="The name or ID of the person who made the decision.")
    comments: Optional[str] = Field(None, description="Optional comments from the reviewer.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata.")

class WorkflowSignalInfo(BaseModel):
    """
    Response model after successfully sending a signal.
    """
    workflow_id: str
    signal_name: str
    signal_sent: bool = True
    timestamp: datetime

# --- Temporal Client Helper ---

async def get_temporal_client() -> Client:
    """
    Connects to the Temporal service using settings from environment variables.
    """
    host = os.getenv("TEMPORAL_HOST", "localhost")
    port = int(os.getenv("TEMPORAL_PORT", 7233))
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    target = f"{host}:{port}"
    try:
        client = await Client.connect(target, namespace=namespace)
        return client
    except RPCError as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to Temporal service at {target}") from e


# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse, tags=["General"])
async def root():
    """
    Provides a simple HTML landing page with links to the documentation.
    """
    return """
    <html>
        <head><title>TraceRail Task Bridge</title></head>
        <body style="font-family: sans-serif; padding: 2em;">
            <h1>🌉 TraceRail Task Bridge</h1>
            <p>This service is running and ready to send signals to workflows.</p>
            <ul>
                <li><a href="/docs">API Documentation (Swagger UI)</a></li>
                <li><a href="/redoc">API Documentation (ReDoc)</a></li>
                <li><a href="/health">Health Check</a></li>
            </ul>
        </body>
    </html>
    """

@app.get("/health", tags=["General"])
async def health_check():
    """
    Performs a health check by attempting to connect to the Temporal service.
    """
    client = None
    try:
        client = await get_temporal_client()
        return {
            "status": "healthy",
            "temporal_connected": True,
            "temporal_host": client.target,
            "temporal_namespace": client.namespace,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException as http_exc:
        return {
            "status": "unhealthy",
            "temporal_connected": False,
            "error": http_exc.detail,
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        if client:
            await client.close()


@app.post("/decision", response_model=WorkflowSignalInfo, tags=["Workflows"])
async def post_decision(payload: Decision):
    """
    Receives a decision and signals the corresponding running workflow.
    """
    client = None
    try:
        client = await get_temporal_client()
        signal_name = "decision"

        # Get a handle to the workflow
        handle = client.get_workflow_handle(payload.workflow_id)

        # Send the signal with the decision status
        await handle.signal(signal_name, payload.status)

        return WorkflowSignalInfo(
            workflow_id=payload.workflow_id,
            signal_name=signal_name,
            timestamp=datetime.now()
        )
    except WorkflowNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow with ID '{payload.workflow_id}' not found or has already completed."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send signal: {str(e)}")
    finally:
        if client:
            await client.close()


@app.get("/workflows", tags=["Workflows"])
async def list_workflows(
    query: str = Query("WorkflowType IS NOT NULL", description="Temporal list workflow query string."),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of workflows to return."),
):
    """
    Lists recent workflows from the Temporal service.
    """
    client = None
    try:
        client = await get_temporal_client()
        workflows = []
        async for workflow in client.list_workflows(query=query):
            workflows.append({
                "workflow_id": workflow.id,
                "run_id": workflow.run_id,
                "workflow_type": workflow.workflow_type,
                "status": workflow.status.name,
                "start_time": workflow.start_time,
                "close_time": workflow.close_time,
            })
            if len(workflows) >= limit:
                break
        return {"workflows": workflows, "count": len(workflows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")
    finally:
        if client:
            await client.close()
