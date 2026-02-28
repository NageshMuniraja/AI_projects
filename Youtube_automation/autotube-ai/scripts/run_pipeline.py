#!/usr/bin/env python3
"""Manual pipeline trigger script. Run a full video pipeline for a channel."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


async def main():
    parser = argparse.ArgumentParser(description="Manually trigger the AutoTube AI pipeline")
    parser.add_argument("--channel-id", type=int, required=True, help="Channel ID to generate video for")
    parser.add_argument("--topic", type=str, default=None, help="Specific topic (auto-researched if omitted)")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    args = parser.parse_args()

    print(f"Triggering pipeline for channel {args.channel_id}")
    print(f"Topic: {args.topic or '(auto-research)'}")
    print(f"Count: {args.count}")
    print()

    # Will import and run the actual pipeline in Phase 3
    print("Pipeline implementation pending (Phase 3)")
    print("Use the API endpoint POST /api/pipeline/trigger instead.")


if __name__ == "__main__":
    asyncio.run(main())
