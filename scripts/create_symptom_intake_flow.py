"""Create, validate, and publish AYUVAN's first static symptom-intake Flow."""

import asyncio

from app.core.config import Settings
from app.services.meta_flows import MetaFlowClient


async def main() -> None:
    flow_id = await MetaFlowClient(Settings()).create_upload_and_publish_symptom_intake()
    print(flow_id)


if __name__ == "__main__":
    asyncio.run(main())
