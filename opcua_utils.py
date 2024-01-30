import logging
import json
from asyncua import Client
from dotenv import load_dotenv
import os

logger = logging.getLogger('main.asyncua')
#logger.setLevel(logging.DEBUG)

# Load environment variables from the .env file in the root directory
load_dotenv()
dps_path = os.environ.get('DPS_PATH', './')


class SubHandler(object):
    def datachange_notification(self, node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        logger.info(f"New data change notification {node} {val}")

    def event_notification(self, event):
        print("New event", event)


class OPCUAConnection():
    def __init__(self):
        self.listOfWSNode = []
        self.WSDPValues = {}
        host = os.environ.get('OPCUA_HOST', 'localhost')
        port = os.environ.get('OPCUA_PORT')
        self.url = "opc.tcp://" + host + ":" + port
        with open(dps_path + "DPS.json", mode="r") as dpsFile:
            dpsDict = json.load(dpsFile)
            self.dpsList = dpsDict["Elements"]
            dpsFile.close()

    async def connectANDread(self):
        #start_time = time.time()
        try:
            async with Client(url=self.url) as client:
                logger.debug('Connected to ', self.url)
                while True:
                    for element in self.dpsList:
                        node = "ns=" + element["NS"] + ";s=" + element["Name"]
                        var = client.get_node(node)
                        self.listOfWSNode.append(var)

                    logger.debug("Reading all values")
                    #read_start_time = time.time()
                    for nid in self.listOfWSNode:
                        try:
                            var = await nid.read_value()
                            # create more readable name
                            node_name = nid.nodeid.to_string().rpartition('.')[2][:-2].replace("_", " ")
                            if node_name == "Time":
                                var = var.strip()  # remove any leading/trailing spaces
                                if len(var) < 6:
                                    var = var.zfill(6)  # pad with leading zeros if necessary
                            self.WSDPValues[node_name] = var
                        except Exception:
                            logger.debug(f"Couldn't read node {nid}")
                            logger.debug(f"Trying reading node {nid} a second time.")
                            try:
                                var = await nid.read_value()
                                # create more readable name
                                node_name = nid.nodeid.to_string().rpartition('.')[2][:-2].replace("_", " ")
                                if node_name == "Time":
                                    var = var.strip()  # remove any leading/trailing spaces
                                    if len(var) < 6:
                                        var = var.zfill(6)  # pad with leading zeros if necessary
                                self.WSDPValues[node_name] = var
                            except Exception:
                                logger.error(f"Second attempt failed for node {nid}")
                                if nid == "ns=2;s=Unit_WS.WS.Monitoring.Time.Time_v" or nid == "ns=2;s=Unit_WS.WS.Monitoring.Date.Date_v":
                                    logger.error(f"Couldn't read node {nid}. Not possible to have timestamp, so avoid entering it to the DB.")
                                    return {}
                                self.WSDPValues[nid.nodeid.to_string().rpartition('.')[2][:-2].replace("_", " ")] = None
                    #read_end_time = time.time()
                    #logger.debug(f"Reading values took {read_end_time - read_start_time} seconds")
                    #end_time = time.time()
                    #logger.debug(f"Total elapsed time: {end_time - start_time} seconds")
                    #logger.debug("Set of WS data: ", self.WSDPValues)
                    return self.WSDPValues
        except KeyboardInterrupt:
            # Handle Ctrl+C (KeyboardInterrupt)
            logger.info("Received Ctrl+C. Exiting gracefully...")
            client.disconnect()
        except Exception as e:
            logger.error(f"Can not connect to OPCUA. Error: {e}")
