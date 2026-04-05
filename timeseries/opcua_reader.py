import logging
import json
from asyncua import Client
from dotenv import load_dotenv
import os
import asyncio

logger = logging.getLogger('main.opcua')
load_dotenv()


class OPCUAReader:
    def __init__(self):
        host = os.environ.get('OPCUA_HOST', 'localhost')
        port = os.environ.get('OPCUA_PORT', '4840')
        self.url = f"opc.tcp://{host}:{port}"

        dps_path = os.environ.get('DPS_PATH', './')
        with open(os.path.join(dps_path, "DPS.json")) as f:
            self.dps = json.load(f)["Elements"]

        # Create a mapping of clean names to node IDs which is static and does not change
        self.node_map = {
            self._clean_name(dp["Name"]): f'ns={dp["NS"]};s={dp["Name"]}'
            for dp in self.dps
        }

    def _clean_name(self, full_name):
        return full_name.split('.')[-1][:-2]

    async def read_all(self):
        """
        Read all nodes concurrently.
        """
        data = {}

        try:
            async with Client(url=self.url) as client:
                logger.debug(f'Connected to {self.url}')
                # create node objects
                nodes = {
                    key: client.get_node(nodeid)
                    for key, nodeid in self.node_map.items()
                }

                # read all values concurrently
                results = await asyncio.gather(
                    *(node.read_value() for node in nodes.values()),
                    return_exceptions=True
                )

                for key, value in zip(nodes.keys(), results):
                    if isinstance(value, Exception):
                        logger.warning(f"Read failed for {key}")
                        data[key] = None
                    else:
                        if key == "Time":
                            value = str(value).strip().zfill(6)
                        data[key] = value

        except Exception as e:
            logger.error(f"OPCUA read failed: {e}")
            return {}

        return data
