#!/usr/bin/env python3
"""
LLM API Test Script for TraceRail Bootstrap

This script tests the DeepSeek/OpenAI API integration and helps verify your API key is working.
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
    import tracerail
except ImportError:
    print("⚠️  tracerail-core not installed. Run 'poetry install' first.")
    sys.exit(1)


async def test_tracerail_core_llm():
    """Tests the TraceRail Core SDK's LLM functionality."""
    print("🔧 Testing TraceRail Core LLM Integration...")
    print("=" * 50)

    # The TraceRailConfig object automatically loads from .env files
    # No need to manually check for keys here.
    try:
        print("   - Initializing TraceRail client...")
        # Create an async client, which also initializes all configured components.
        client = await tracerail.create_client_async()
        provider_name = client.config.llm.provider.value
        print(f"   - Successfully initialized client with '{provider_name}' provider.")

        test_prompt = "Say 'Hello from TraceRail!' and explain what you are in one sentence."
        print(f"\n🤖 Processing prompt via {provider_name}...")

        # Use the high-level process_content method
        result = await client.process_content(test_prompt)
        llm_response = result.llm_response
        usage = llm_response.usage

        print(f"✅ TraceRail LLM call successful!")
        print(f"\n📝 Response:")
        print(f"   {llm_response.content}")
        print(f"\n📊 Usage:")
        print(f"   Prompt tokens: {usage.prompt_tokens}")
        print(f"   Completion tokens: {usage.completion_tokens}")
        print(f"   Total tokens: {usage.total_tokens}")
        print(f"   Model used: {llm_response.model}")

        print("\n✅ TraceRail Core test passed!")
        return True

    except tracerail.TraceRailError as e:
        print(f"❌ TraceRail test failed: {e}")
        if "API key is required" in str(e):
             print("\n   ACTION: No valid API key found!")
             print("   Set DEEPSEEK_API_KEY or OPENAI_API_KEY in your .env file")
             print("   DeepSeek: https://platform.deepseek.com/api_keys")
             print("   OpenAI: https://platform.openai.com/api-keys")
        elif "authentication" in str(e).lower():
            print("   Check your API key is valid and has sufficient credits.")
        elif "quota" in str(e).lower():
            print(f"   API quota exceeded. Check your provider's billing page.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False
    finally:
        if 'client' in locals() and client._initialized:
            await client.close()


def main():
    """Main test function"""
    print("🚀 TraceRail Core LLM Integration Test")
    print("=" * 50)
    print()

    # Check if we're in the right directory
    if not Path(".env.example").exists():
        print("❌ Please run this script from the tracerail-bootstrap root directory")
        sys.exit(1)

    # Run tests
    test_passed = asyncio.run(test_tracerail_core_llm())

    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   TraceRail Core LLM Test: {'✅ PASS' if test_passed else '❌ FAIL'}")

    if test_passed:
        print("\n🎉 All tests passed! Your LLM integration is working.")
        print("\nNext steps:")
        print("   1. Explore other scripts in the `/bin` directory.")
        print("   2. Run the full application with: `make up`")
    else:
        print("\n⚠️  The test failed. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
