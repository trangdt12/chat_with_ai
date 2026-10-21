import asyncio
import logging

from app.config import get_settings

log = logging.getLogger("app.worker")


async def run_forever() -> None:
    settings = get_settings()
    log.info("worker started")
    while True:
        await asyncio.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run_forever())
