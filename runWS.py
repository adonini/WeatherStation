import time
from datetime import time as t
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from mongo_utils import MongoDB
from opcua_utils import OPCUAConnection

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
    while True:
        # Connect to OPC UA server as client and get the values
        #start_ws = time.perf_counter()
        ws = OPCUAConnection()
        data = await ws.connectANDread()
        #end_ws = time.perf_counter()
        #print(f"Time taken for OPC UA connection and read: {end_ws - start_ws:.4f} seconds")
        #logger.debug(f"Time taken for OPC UA connection and read: {end_ws - start_ws:.4f} seconds")
        #print(data)
        # Connect to MongoDB and insert the data
        if data:
            #start_mongo = time.perf_counter()
            mongo = MongoDB()
            mongo.insert(data)
            #end_mongo = time.perf_counter()
            #print(f"Time taken for MongoDB connect and insert: {end_mongo - start_mongo:.4f} seconds")
            #logger.debug(f"Time taken for MongoDB conect and insert: {end_mongo - start_mongo:.4f} seconds")
        else:
            #print("No data available. Skipping add it to Mongo!")
            logger.debug("No data available. Skipping add it to Mongo!")
        # sleep 2s before next polling
        time.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
