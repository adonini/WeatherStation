from datetime import time as t
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from mongo_utils import MongoDB
from opcua_utils import OPCUAConnection
import signal
import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the root directory
load_dotenv()
log_path = os.environ.get('OPCUA_LOG_PATH')

#---------------------------------------------------------------------------#
# Initialize the main logger
#---------------------------------------------------------------------------#
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)  # override the default severity of logging
# Create handler: new file every day at 08:00 UTC
utc_time = t(8, 0, 0)
file_handler = TimedRotatingFileHandler(log_path + 'WS.log', when='D', interval=1, atTime=utc_time, backupCount=7, utc=True)
#file_handler = TimedRotatingFileHandler('./logs/WS.log', when='D', interval=1, atTime=utc_time, backupCount=7, utc=True)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


async def main():
    try:
        while True:
            #start_ws = time.perf_counter()
            ws = OPCUAConnection()
            data = await ws.connectANDread()
            #end_ws = time.perf_counter()
            #logger.debug(f"Time taken for OPC UA connection and read: {end_ws - start_ws:.4f} seconds")
            # Connect to MongoDB and insert the data
            if data:
                #start_mongo = time.perf_counter()
                mongo = MongoDB()
                mongo.insert(data)
                mongo.close_connection()
                #end_mongo = time.perf_counter()
                #logger.debug(f"Time taken for MongoDB conect and insert: {end_mongo - start_mongo:.4f} seconds")
            else:
                logger.debug("No data available. Skipping add it to Mongo!")
            # sleep 10s before next pulling
            #time.sleep(10)
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        # Handle Ctrl+C (KeyboardInterrupt)
        logger.info("Received Ctrl+C. Exiting gracefully...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    # Set up a signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal.default_int_handler)
    asyncio.run(main())
