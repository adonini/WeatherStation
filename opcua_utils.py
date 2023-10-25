import logging
#import time
#from pathlib import Path
import json
from asyncua import Client
#import asyncio

logger = logging.getLogger('main.asyncua')
#logger.setLevel(logging.DEBUG)


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
        # dps = Path("DPS.json").is_file()
        with open("DPS.json", mode="r") as dpsFile:
            dpsDict = json.load(dpsFile)
            self.dpsList = dpsDict["Elements"]
            opcuaChar = dpsDict["OPCUA"]
            dpsFile.close()
            self.url = "opc.tcp://" + opcuaChar["Host"] + ":" + opcuaChar["Port"]

    async def connectANDread(self):
        #start_time = time.time()
        try:
            async with Client(url=self.url) as client:
                #logger.debug('Connected to ', self.url)
                while True:
                    for element in self.dpsList:
                        node = "ns=" + element["NS"] + ";s=" + element["Name"]
                        var = client.get_node(node)
                        self.listOfWSNode.append(var)

                    logger.debug("Reading all values")
                    #read_start_time = time.time()
                    for nid in self.listOfWSNode:
                        #print("Reading node: ", nid)
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
                            # if date or time value are not readable exit
                    #read_end_time = time.time()
                    #logger.debug(f"Reading values took {read_end_time - read_start_time} seconds")
                    #end_time = time.time()
                    #logger.debug(f"Total elapsed time: {end_time - start_time} seconds")
                    print("Set of WS data: ", self.WSDPValues)
                    return self.WSDPValues
        except KeyboardInterrupt:
            # Handle Ctrl+C (KeyboardInterrupt)
            logger.info("Received Ctrl+C. Exiting gracefully...")
            client.disconnect()
        except Exception as e:
            logger.error(f"Can not connect to OPCUA. Error: {e}")


# async def dict_format(keys, values):
#     return dict(zip(keys, values))


# async def connect_client(url="opc.tcp://localhost:48042/"):
#     try:
#         client = Client(url=url)
#         await client.connect()
#         logger.info("Connected to WS OPC UA server")
#     except Exception:
#         logger.exception('Unable to connect to WS OPC UA server')

# async def get_all_variables(url="opc.tcp://localhost:48042/"):
#     async with Client(url=url) as client:
#         doc = {}  # create a new MongoDB document dict
#         for i in data_variables.items():
#                 # Get the variable node for read / write
#                 myvar = await client.nodes.root.get_child(["0:Objects", "{}:vPLC".format(idx), "{}:{}".format(idx,data_variables[i])])
#                 val = await myvar.get_value()
#                 doc.update({str(i): val})


# async def get_all_values(url="opc.tcp://localhost:48041/"):
#     async with Client(url=url) as client:
#         data_list = []
#         namespace = "mynamespace"
#         idx = await client.get_namespace_index(namespace)
#         for i in range(len(data_variables)):
#             # Get the variable node for read / write
#             myvar = await client.nodes.root.get_child(["0:Objects", "{}:vPLC".format(idx), "{}:{}".format(idx, data_variables[i])])  #vPLC is the Object name
#             val = await myvar.get_value()
#             data_list.append(val)
#         print(await dict_format(data_variables, data_list))
#         await asyncio.sleep(5)
#         #return dict_format(data_variables, data_list)


# async def read_values(self, nodes):

#         Read the value of multiple nodes in one ua call.

#         nodeids = [node.nodeid for node in nodes]
#         results = await self.uaclient.read_attributes(nodeids, ua.AttributeIds.Value)
#         return [result.Value.Value for result in results]
