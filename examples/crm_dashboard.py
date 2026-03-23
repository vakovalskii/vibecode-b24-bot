"""Example: fetch CRM deals using the low-level VibeCode client."""

import asyncio
import os
from vibecode import VibeCode


async def main():
    async with VibeCode(api_key=os.environ["VIBE_API_KEY"]) as client:
        # Portal info
        me = await client.me()
        print(f"Portal: {me['portal']}")

        # List deals
        deals = await client.list_entity("deals", limit=10)
        print(f"\nDeals ({len(deals)}):")
        for d in deals:
            print(f"  #{d['ID']} {d.get('TITLE', '—')} — {d.get('OPPORTUNITY', 0)} RUB")

        # Batch call
        result = await client.batch([
            {"method": "crm.status.list"},
            {"method": "crm.deal.fields"},
        ])
        print(f"\nBatch: got {len(result)} results")


asyncio.run(main())
