import time
from datetime import time as t
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from mongo_utils import MongoDB
from opcua_utils import OPCUAConnection
import signal

#---------------------------------------------------------------------------#
# Initialize the main logger
#---------------------------------------------------------------------------#
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)  # override the default severity of logging
# Create handler: new file every day at 12:00 UTC
utc_time = t(12, 0, 0)
file_handler = TimedRotatingFileHandler('/var/log/lst-safetybroker/WS/WS.log', when='D', interval=1, atTime=utc_time, backupCount=7, utc=True)
#file_handler = TimedRotatingFileHandler('./logs/WS.log', when='D', interval=1, atTime=utc_time, backupCount=7, utc=True)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
#print(file_handler.baseFilename)
#print(file_handler.rolloverAt)


async def main():
    try:
        while True:
            # Connect to OPC UA server as client and get the values
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
