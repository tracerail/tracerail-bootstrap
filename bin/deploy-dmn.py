#!/usr/bin/env python3
"""
DMN Deployment Script for TraceRail Bootstrap

This script deploys DMN decision tables to the Flowable DMN engine.
"""

import asyncio
import os
import sys
from pathlib import Path
import httpx

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Run 'poetry install' first.")
    sys.exit(1)


async def test_flowable_connection():
    """Test connection to Flowable DMN service"""
    flowable_url = os.getenv("FLOWABLE_BASE_URL", "http://localhost:8082/flowable-rest")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{flowable_url}/service/dmn-repository/deployments",
                auth=(os.getenv("FLOWABLE_USERNAME", "rest-admin"), os.getenv("FLOWABLE_PASSWORD", "test"))
            )

            if response.status_code == 200:
                deployments = response.json()
                print(f"✅ Connected to Flowable DMN service")
                print(f"   Found {len(deployments.get('data', []))} existing deployments")
                return True
            else:
                print(f"❌ Flowable connection failed: HTTP {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Failed to connect to Flowable: {str(e)}")
        print("   Make sure Flowable is running: docker compose up -d")
        return False


async def deploy_dmn_file(dmn_file_path: Path):
    """Deploy a single DMN file to Flowable"""
    flowable_url = os.getenv("FLOWABLE_BASE_URL", "http://localhost:8082/flowable-rest")
    deployment_url = f"{flowable_url}/service/dmn-repository/deployments"

    if not dmn_file_path.exists():
        print(f"❌ DMN file not found: {dmn_file_path}")
        return False

    try:
        # Read the DMN file content
        dmn_content = dmn_file_path.read_text(encoding='utf-8')

        # Prepare multipart form data
        files = {
            'file': (dmn_file_path.name, dmn_content, 'application/xml')
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            username = os.getenv("FLOWABLE_USERNAME", "rest-admin")
            password = os.getenv("FLOWABLE_PASSWORD", "test")
            response = await client.post(
                deployment_url,
                files=files,
                auth=(username, password)
            )

            if response.status_code == 201:
                result = response.json()
                print(f"✅ Successfully deployed: {dmn_file_path.name}")
                print(f"   Deployment ID: {result.get('id', 'unknown')}")
                print(f"   Deployment time: {result.get('deploymentTime', 'unknown')}")
                return True
            else:
                print(f"❌ Deployment failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Error deploying {dmn_file_path.name}: {str(e)}")
        return False


async def test_dmn_execution(decision_key: str = "risk-routing"):
    """Test the deployed DMN decision table"""
    flowable_url = os.getenv("FLOWABLE_BASE_URL", "http://localhost:8082/flowable-rest")
    execute_url = f"{flowable_url}/service/dmn-runtime/execute"

    # Test cases
    test_cases = [
        {
            "name": "Low risk case",
            "variables": {"tokenScore": 50, "textLength": 100, "sentiment": "positive"},
            "expected_route": "auto"
        },
        {
            "name": "High token usage",
            "variables": {"tokenScore": 250, "textLength": 200, "sentiment": "neutral"},
            "expected_route": "human"
        },
        {
            "name": "Negative sentiment",
            "variables": {"tokenScore": 120, "textLength": 300, "sentiment": "negative"},
            "expected_route": "human"
        },
        {
            "name": "Very long text",
            "variables": {"tokenScore": 80, "textLength": 1200, "sentiment": "neutral"},
            "expected_route": "human"
        }
    ]

    print(f"\n🧪 Testing DMN decision execution...")
    print("=" * 50)

    success_count = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")

        payload = {
            "decisionDefinitionKey": decision_key,
            "variables": test_case["variables"]
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                username = os.getenv("FLOWABLE_USERNAME", "rest-admin")
                password = os.getenv("FLOWABLE_PASSWORD", "test")
                response = await client.post(
                    execute_url,
                    json=payload,
                    auth=(username, password),
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()

                    if "resultVariables" in result and result["resultVariables"]:
                        route = result["resultVariables"][0].get("route")
                        confidence = result["resultVariables"][0].get("confidence")

                        print(f"   Variables: {test_case['variables']}")
                        print(f"   Result: route='{route}', confidence={confidence}")

                        if route == test_case["expected_route"]:
                            print(f"   ✅ PASS (expected '{test_case['expected_route']}')")
                            success_count += 1
                        else:
                            print(f"   ❌ FAIL (expected '{test_case['expected_route']}', got '{route}')")
                    else:
                        print(f"   ❌ FAIL: No result variables in response")
                        print(f"   Response: {result}")
                else:
                    print(f"   ❌ FAIL: HTTP {response.status_code}")
                    print(f"   Response: {response.text}")

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")

    print(f"\n📊 Test Results: {success_count}/{len(test_cases)} passed")
    return success_count == len(test_cases)


async def list_deployments():
    """List all current DMN deployments"""
    flowable_url = os.getenv("FLOWABLE_BASE_URL", "http://localhost:8082/flowable-rest")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{flowable_url}/service/dmn-repository/deployments",
                auth=(os.getenv("FLOWABLE_USERNAME", "rest-admin"), os.getenv("FLOWABLE_PASSWORD", "test"))
            )

            if response.status_code == 200:
                deployments = response.json()
                data = deployments.get("data", [])

                print(f"\n📋 Current DMN Deployments ({len(data)}):")
                print("=" * 50)

                if not data:
                    print("   No deployments found")
                else:
                    for deployment in data:
                        print(f"   ID: {deployment.get('id', 'N/A')}")
                        print(f"   Name: {deployment.get('name', 'N/A')}")
                        print(f"   Time: {deployment.get('deploymentTime', 'N/A')}")
                        print(f"   Category: {deployment.get('category', 'N/A')}")
                        print()

                return True
            else:
                print(f"❌ Failed to list deployments: HTTP {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Error listing deployments: {str(e)}")
        return False


def main():
    """Main deployment function"""
    print("🚀 TraceRail DMN Deployment Script")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path(".env.example").exists():
        print("❌ Please run this script from the tracerail-bootstrap root directory")
        sys.exit(1)

    # Find DMN files
    dmn_dir = Path("dmn")
    if not dmn_dir.exists():
        print("❌ DMN directory not found. Creating it...")
        dmn_dir.mkdir()
        print("   Place your .dmn files in the dmn/ directory")
        sys.exit(1)

    dmn_files = list(dmn_dir.glob("*.dmn"))
    if not dmn_files:
        print("❌ No .dmn files found in dmn/ directory")
        sys.exit(1)

    print(f"📁 Found {len(dmn_files)} DMN file(s):")
    for dmn_file in dmn_files:
        print(f"   - {dmn_file.name}")

    # Run deployment
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Test connection
        connected = loop.run_until_complete(test_flowable_connection())
        if not connected:
            sys.exit(1)

        # List existing deployments
        loop.run_until_complete(list_deployments())

        # Deploy each DMN file
        print(f"\n🚀 Deploying DMN files...")
        print("=" * 50)

        success_count = 0
        for dmn_file in dmn_files:
            deployed = loop.run_until_complete(deploy_dmn_file(dmn_file))
            if deployed:
                success_count += 1

        print(f"\n📊 Deployment Summary: {success_count}/{len(dmn_files)} successful")

        if success_count > 0:
            # Test DMN execution
            test_passed = loop.run_until_complete(test_dmn_execution())

            if test_passed:
                print("\n🎉 All tests passed! DMN deployment successful.")
                print("\nNext steps:")
                print("   1. Start the worker: make worker")
                print("   2. Run a workflow: make test-worker")
                print("   3. Check routing decisions in Temporal UI")
            else:
                print("\n⚠️  DMN deployed but tests failed. Check the decision logic.")
        else:
            print("\n❌ No DMN files were successfully deployed.")
            sys.exit(1)

    finally:
        loop.close()


if __name__ == "__main__":
    main()
