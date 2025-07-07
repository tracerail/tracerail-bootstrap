import asyncio
from tracerail.temporal.activities import LLMProcessingActivity

async def main():
    """Basic example of using TraceRail Temporal activities."""
    activity = LLMProcessingActivity()
    
    result = await activity.process_content("Hello, world!")
    print(f"Processing result: {result.data}")

if __name__ == "__main__":
    asyncio.run(main())
