from pymongo import MongoClient
import logging
import pymongo
from datetime import datetime, timezone
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

logger = logging.getLogger('main.mongo')
#logger.setLevel(logging.DEBUG)

# Load environment variables from the .env file in the root directory
load_dotenv()


class MongoDB:
    """
    Class to take care of storing the data from the WS to mongo database.
    """

    parameters = {}
    client = None
    database = None
    parameters_col = None
    measurements_col = None
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT')
    db_name = os.environ.get('DB_NAME')
    uri = 'mongodb://' + db_host + ':' + db_port

    def __init__(self, uri=uri, dbName=db_name, parameters='Header', measurements='Readings'):
        """
        Constructor; initializes defaults.
        Args:
            dbName: Name of the database.
            uri: Database connection uri.
            parameters: Name of header collection, containing info of each register of the WS
            measurements: Name of the measureament collection, contains the values read from the WS
        """
        try:
            self.client = MongoClient(uri)
            logger.info('### Connected to MongoDB')
        except Exception as err:
            logger.error(f'Could not connect to MongoDB: {err}')

        self.database = self.client[dbName]
        self.parameters_col = self.database[parameters]
        self.measurements_col = self.database[measurements]
        self.get_parameters()

    def get_parameters(self):
        """
        Get name of parameter from parameters collection
        """
        entries = self.parameters_col.find().sort([("name", pymongo.ASCENDING)])
        for entry in entries:
            #entry: {'_id': ObjectId('642494aba6ed43dd2570736c'), 'parameter': 'wind', 'description': 'Wind speed', 'units': 'm/s', 'added': datetime.datetime(2023, 3, 29, 19, 42, 35, 899000)}
            self.parameters[entry['name']] = entry
        #print("parameters: ", self.parameters)
        return self.parameters

    def MongoDB_Connection(self, dbCollection):
        """
        Connect to the mongoDB sever local network
        Args:
            dbCollection: Name of the collection
        """
        try:
            self.client = MongoClient(self.uri)
            #my_db = self.client[self.dbName]
            #col = my_db[dbCollection]
            logger.info('### Connected to MongoDB')
        except Exception as err:
            logger.error(f'Could not connect to MongoDB: {err}')

    def add_parameter(self, parameter, description, units):
        if parameter not in self.parameters:
            data = {
                "name": parameter,
                "description": description,
                "units": units,
                "added": datetime.now(timezone.utc)
            }
            rec = self.parameters_col.insert_one(data)
            self.get_parameters()
            return rec
        else:
            print(f"Parameter {parameter} already exists!")

    def getCollection(self, dbCollection):
        """
        It gets a collection object from the database.
        Args:
            dbCollection: Name of the collection.
        Returns:
            The collection object.
        """
        return self.client[self.dbName][dbCollection]

    def insert(self, dic, added=None):
        """
        It inserts a new document to a collection.
        Args:
            dic: Dictionary containing the pair parameter/measurement of each register.
        """
        data = {}
        for key, value in dic.items():
            if key not in self.parameters:
                logger.error(f'### Parameter {key} cannot be found!')
                return None
            _id = ObjectId(self.parameters[key]['_id'])
            data.update({
                key: {
                    "ref": _id,
                    "value": value,
                }
            })
        if added is None:
            added = datetime.now(timezone.utc)
        data.update({
            "added": added,
        })
        # push to DB
        try:
            self.measurements_col.insert_one(data)
            logger.info("### Values added to MongoDB")
        except Exception:
            logger.error(f'### Failed to add entry to the DB: {data}')

    def close_connection(self):
        """
        Close connection to the mongoDB sever local network
        """
        try:
            self.client.close()
            logger.info('### Connection to MongoDB closed.')
        except Exception as err:
            #print("Could not discconnect from MongoDB: %s" % err)
            logger.error(f'Could not disconnect from MongoDB: {err}')
