from modbus.WS_utils import (
    setup_sync_client,
    connect_client,
    #readHoldingRegister,
    readInputRegisters,
    #stop_client,
    inputregister_dict,
    precipitationtype_dict,
)
from mongo_utils import MongoDB
import logging
from logging.handlers import TimedRotatingFileHandler
import time

#---------------------------------------------------------------------------#
# Initialize the main logger
#---------------------------------------------------------------------------#
logger = logging.getLogger('main')
logger.setLevel('DEBUG')  # override the default severity of logging
file_handler = TimedRotatingFileHandler('./logs/WS.log', when="midnight", backupCount=30, utc=True)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def main():
    # Connect to WS
    WS_client = setup_sync_client()
    isClientConnected = connect_client(WS_client)

    # Connect to MongoDB, to a particular db and collection
    mongo = MongoDB()

    # Read and store loop
    while isClientConnected:
        data = readInputRegisters(WS_client, inputregister_dict, precipitationtype_dict)
        # use the insert method to insert a document into the collection
        mongo.insert(data)
        # sleep 1s before next polling
        time.sleep(1)
    #stop_client(WS_client)


if __name__ == "__main__":
    main()
