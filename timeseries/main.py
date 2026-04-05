import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import time as t
import signal
import os
from dotenv import load_dotenv

from mongo import MongoTS
from opcua_reader import OPCUAReader

# Load env
load_dotenv()
log_path = os.environ.get('OPCUA_LOG_PATH', './')

# Logger setup
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

handler = TimedRotatingFileHandler(
    log_path + 'WS.log',
    when='D',
    interval=1,
    atTime=t(8, 0, 0),
    backupCount=7,
    utc=True
)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


async def main():
    reader = OPCUAReader()
    mongo = MongoTS()

    try:
        while True:
            data = await reader.read_all()

            if data:
                mongo.insert(data)
            else:
                logger.warning("No data read from OPC UA")

            # 6s polling
            await asyncio.sleep(6)

    except KeyboardInterrupt:
        logger.info("Stopping gracefully...")
    finally:
        mongo.close()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.default_int_handler)
    asyncio.run(main())
