#!/usr/bin/env python3
"""
Task Bridge Test Script for TraceRail Bootstrap

This script tests the Task Bridge FastAPI service endpoints.
"""

import asyncio
import httpx
import json
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Run 'poetry install' first.")
    sys.exit(1)


async def test_task_bridge_endpoints():
    """Test all Task Bridge endpoints"""
    base_url = "http://localhost:7070"

    print("🌉 Testing TraceRail Task Bridge")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=10.0) as client:

        # Test 1: Root endpoint
        print("\n1. Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                print("   ✅ Root endpoint accessible")
                print(f"   Status: {response.status_code}")
                if "TraceRail Task Bridge" in response.text:
                    print("   ✅ Content looks correct")
                else:
                    print("   ⚠️  Content might be unexpected")
            else:
                print(f"   ❌ Root endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Root endpoint error: {str(e)}")

        # Test 2: Health endpoint
        print("\n2. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print("   ✅ Health endpoint accessible")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Temporal connected: {health_data.get('temporal_connected', False)}")
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Health endpoint error: {str(e)}")

        # Test 3: API docs
        print("\n3. Testing API documentation...")
        try:
            response = await client.get(f"{base_url}/docs")
            if response.status_code == 200:
                print("   ✅ API docs accessible")
                if "FastAPI" in response.text:
                    print("   ✅ Swagger UI loaded correctly")
            else:
                print(f"   ❌ API docs failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ API docs error: {str(e)}")

        # Test 4: Workflows list endpoint
        print("\n4. Testing workflows list...")
        try:
            response = await client.get(f"{base_url}/workflows?limit=5")
            if response.status_code == 200:
                workflows_data = response.json()
                print("   ✅ Workflows endpoint accessible")
                print(f"   Found {workflows_data.get('count', 0)} workflows")
            else:
                print(f"   ❌ Workflows endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Workflows endpoint error: {str(e)}")

        # Test 5: Invalid workflow info (should return 404)
        print("\n5. Testing workflow info (non-existent workflow)...")
        try:
            response = await client.get(f"{base_url}/workflow/non-existent-workflow-id")
            if response.status_code == 404:
                print("   ✅ Correctly returns 404 for non-existent workflow")
            else:
                print(f"   ⚠️  Unexpected status code: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Workflow info error: {str(e)}")

        # Test 6: Decision endpoint (with invalid workflow)
        print("\n6. Testing decision endpoint...")
        decision_payload = {
            "workflow_id": "test-workflow-123",
            "status": "approved",
            "reviewer": "test-reviewer",
            "comments": "This is a test decision",
            "priority": "normal"
        }

        try:
            response = await client.post(
                f"{base_url}/decision",
                json=decision_payload,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 404:
                print("   ✅ Correctly returns 404 for non-existent workflow")
                print("   (This is expected since the workflow doesn't exist)")
            elif response.status_code == 200:
                print("   ✅ Decision endpoint works!")
                result = response.json()
                print(f"   Signal sent to workflow: {result.get('workflow_id')}")
            else:
                print(f"   ❌ Decision endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Decision endpoint error: {str(e)}")


async def test_with_real_workflow():
    """Test Task Bridge with a real running workflow"""
    print("\n" + "=" * 60)
    print("🔄 Testing with Real Workflow")
    print("=" * 60)

    base_url = "http://localhost:7070"

    print("\nℹ️  This test requires a running workflow that routes to 'human'")
    print("   You can start one with: make test-worker")
    print("   Or: poetry run python cli/start_example.py 'complex analysis task'")

    # Wait a moment for user to potentially start a workflow
    print("\n⏱️  Waiting 3 seconds for any workflows to be started...")
    await asyncio.sleep(3)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Get list of workflows
        try:
            response = await client.get(f"{base_url}/workflows?limit=10")
            if response.status_code == 200:
                workflows_data = response.json()
                workflows = workflows_data.get('workflows', [])

                if not workflows:
                    print("   ℹ️  No workflows found. Start a workflow to test signals.")
                    return

                print(f"   Found {len(workflows)} workflow(s):")
                for i, wf in enumerate(workflows, 1):
                    print(f"     {i}. {wf['workflow_id']} - {wf['status']} ({wf['workflow_type']})")

                # Test with the first running workflow
                running_workflows = [wf for wf in workflows if wf['status'] == 'RUNNING']
                if running_workflows:
                    test_workflow = running_workflows[0]
                    workflow_id = test_workflow['workflow_id']

                    print(f"\n🧪 Testing signal with workflow: {workflow_id}")

                    # Send a test decision
                    decision_payload = {
                        "workflow_id": workflow_id,
                        "status": "approved",
                        "reviewer": "test-bridge-script",
                        "comments": "Automated test decision from bridge test script",
                        "priority": "normal",
                        "metadata": {"test": True, "source": "bridge-test"}
                    }

                    response = await client.post(
                        f"{base_url}/decision",
                        json=decision_payload,
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        print("   ✅ Signal sent successfully!")
                        print(f"   Workflow ID: {result['workflow_id']}")
                        print(f"   Signal status: {result['status']}")
                        print(f"   Timestamp: {result['timestamp']}")
                    else:
                        print(f"   ❌ Signal failed: {response.status_code}")
                        print(f"   Response: {response.text}")
                else:
                    print("   ℹ️  No running workflows found to test signals with.")

        except Exception as e:
            print(f"   ❌ Real workflow test error: {str(e)}")


def main():
    """Main test function"""
    print("🚀 TraceRail Task Bridge Test Suite")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path(".env.example").exists():
        print("❌ Please run this script from the tracerail-bootstrap root directory")
        sys.exit(1)

    # Run tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Test basic endpoints
        loop.run_until_complete(test_task_bridge_endpoints())

        # Test with real workflow
        loop.run_until_complete(test_with_real_workflow())

        print("\n" + "=" * 60)
        print("📋 Test Summary")
        print("=" * 60)
        print("✅ Task Bridge endpoint tests completed")
        print("\nNext steps:")
        print("1. Start a worker: make worker")
        print("2. Run a workflow that routes to human: make test-worker")
        print("3. Use the Task Bridge to send decisions back to the workflow")
        print("4. Check the Temporal UI to see the workflow progression")
        print("\nTask Bridge URLs:")
        print("• Main interface: http://localhost:7070/")
        print("• API docs: http://localhost:7070/docs")
        print("• Health check: http://localhost:7070/health")

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {str(e)}")
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
