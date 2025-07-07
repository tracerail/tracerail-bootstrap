#!/usr/bin/env python3
"""
Rule-based Decision Engine Test Script for TraceRail Bootstrap

This script tests the rule-based routing decision engine.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Run 'poetry install' first.")
    sys.exit(1)

try:
    from tracerail.config import RoutingConfig, RoutingEngine
    from tracerail.routing import (
        create_routing_engine,
        RoutingContext,
        RoutingDecision,
    )
    from tracerail.llm import LLMResponse
except ImportError:
    print("⚠️  tracerail-core not installed. Run 'poetry install' first.")
    sys.exit(1)


async def test_routing_engine():
    """Tests the TraceRail Core SDK's routing engine with a rules file."""
    print("🧪 Testing TraceRail Core Routing Engine")
    print("=" * 50)

    # --- Setup ---
    # Configure the routing engine directly, pointing to our new YAML file.
    config = RoutingConfig(
        engine_type=RoutingEngine.RULES,
        engine_config={"rules_file": "rules.yaml"}
    )

    # Initialize only the routing engine, not the full client.
    try:
        routing_engine = await create_routing_engine(config)
        print("✅ Rules-Based Routing Engine initialized successfully.")
        print("   - Rules file: rules.yaml")
    except Exception as e:
        print(f"❌ Failed to initialize routing engine: {e}")
        return None  # Can't proceed if engine fails

    # --- Test Cases ---
    # These test cases are designed to trigger the specific rules in `rules.yaml`.
    test_cases = [
        {
            "name": "Urgent Keyword",
            "context": RoutingContext(content="There is a critical outage!"),
            "expected_decision": RoutingDecision.HUMAN,
            "expected_rule": "Urgent Keywords",
        },
        {
            "name": "Complaint Keyword",
            "context": RoutingContext(content="This is unacceptable, I want a refund."),
            "expected_decision": RoutingDecision.HUMAN,
            "expected_rule": "Complaint Keywords",
        },
        {
            "name": "Low LLM Confidence",
            "context": RoutingContext(
                content="I'm not sure what to make of this.",
                llm_response=LLMResponse(content="", metadata={"confidence": 0.5})
            ),
            "expected_decision": RoutingDecision.HUMAN,
            "expected_rule": "Low LLM Confidence",
        },
        {
            "name": "High LLM Confidence (Default)",
            "context": RoutingContext(
                content="This looks fine.",
                llm_response=LLMResponse(content="", metadata={"confidence": 0.9})
            ),
            "expected_decision": RoutingDecision.AUTOMATIC,
            "expected_rule": "Default to Automatic",
        },
        {
            "name": "No matching rule -> Fallback",
            "context": RoutingContext(content="This is a standard inquiry."),
            "expected_decision": RoutingDecision.HUMAN,
            "expected_rule": "No applicable routing rules were matched.", # This is the reason, not a rule name
        },
    ]

    print(f"\nRunning {len(test_cases)} test cases...\n")
    results = []

    # --- Execution Loop ---
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"   Input content: '{test_case['context'].content}'")

        try:
            # Use the standalone routing engine
            result = await routing_engine.route(test_case['context'])

            decision = result.decision
            # If a rule was triggered, take the first one. Otherwise, use the reason.
            rule_name = result.triggered_rules[0] if result.triggered_rules else result.reason

            expected_decision = test_case['expected_decision']
            expected_rule = test_case['expected_rule']
            passed = (decision == expected_decision) and (expected_rule in rule_name)

            print(f"   Result: decision='{decision.value}'")
            print(f"   Triggered Rule/Reason: {rule_name}")

            if passed:
                print(f"   ✅ PASS (expected '{expected_decision.value}')")
            else:
                print(f"   ❌ FAIL (expected '{expected_decision.value}', got '{decision.value}')")
                print(f"   (expected rule '{expected_rule}', got '{rule_name}')")


            results.append({
                'test': test_case['name'],
                'passed': passed,
                'expected': expected_decision.value,
                'actual': decision.value,
                'rule': rule_name
            })

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({
                'test': test_case['name'],
                'passed': False,
                'expected': test_case['expected_decision'].value,
                'actual': 'ERROR',
                'rule': 'error'
            })
        print()

    await routing_engine.close()
    return results


def print_summary(results):
    """Prints a summary of the test results."""
    if results is None:
        return
    print("=" * 50)
    print("📊 Test Summary")
    print("=" * 50)

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['passed'])
    failed_tests = total_tests - passed_tests

    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    if total_tests > 0:
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

    if failed_tests > 0:
        print(f"\n❌ Failed tests:")
        for result in results:
            if not result['passed']:
                print(f"   - {result['test']}: expected '{result['expected']}', got '{result['actual']}'")

    print(f"\n📈 Rule Usage Analysis:")
    rule_counts = {}
    for result in results:
        rule = result['rule']
        rule_counts[rule] = rule_counts.get(rule, 0) + 1

    for rule, count in sorted(rule_counts.items()):
        print(f"   - {rule}: {count} time(s)")


def main():
    """Main test function"""
    print("🚀 TraceRail Core Routing Engine Test")
    print("=" * 50)
    print()

    # Check if we're in the right directory and the rules file exists
    if not Path("rules.yaml").exists():
        print("❌ Could not find 'rules.yaml'.")
        print("   Please run this script from the tracerail-bootstrap root directory.")
        sys.exit(1)

    # Run the async test function
    results = asyncio.run(test_routing_engine())

    # Print summary
    print_summary(results)

    if results:
        passed_tests = sum(1 for r in results if r['passed'])
        total_tests = len(results)
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! The routing engine is working as expected.")
        else:
            print("\n⚠️  Some tests failed. Check the errors above.")
            sys.exit(1)
    else:
        # This happens if the client fails to initialize
        sys.exit(1)


if __name__ == "__main__":
    main()
