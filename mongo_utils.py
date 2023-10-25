from pymongo import MongoClient
import logging
import pymongo
#import time
from datetime import datetime
from bson.objectid import ObjectId

logger = logging.getLogger('main.mongo')
#logger.setLevel(logging.DEBUG)


class MongoDB:
    """
    Class to take care of storing the data from the WS to mongo database.
    """

    parameters = {}
    client = None
    database = None
    parameters_col = None
    measurements_col = None

    #def __init__(self, uri='mongodb://127.0.0.1:27017/', dbName='WeatherStation', parameters='parameters', measurements='measurements'):
    def __init__(self, uri='mongodb://localhost:27010/', dbName='WS', parameters='Header', measurements='Readings'):
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
            #print("Connected to MongoDB")
            logger.info('### Connected to MongoDB')  # {my_db} and collection {col}')
        except Exception as err:
            #print("Could not connect to MongoDB: %s" % err)
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
            #print("Could not connect to MongoDB: %s" % err)
            logger.error(f'Could not connect to MongoDB: {err}')

    def add_parameter(self, parameter, description, units):
        if parameter not in self.parameters:
            data = {
                "name": parameter,
                "description": description,
                "units": units,
                "added": datetime.utcnow()
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
        #print('dic: ', dic)
        data = {}
        for key, value in dic.items():
            #print(key, value)
            if key not in self.parameters:
                #print(f"Parameter {key} cannot be found!")
                logger.error(f'## Parameter {key} cannot be found!')
                return None
            _id = ObjectId(self.parameters[key]['_id'])
            data.update({
                key: {
                    "ref": _id,
                    "value": value,
                }
            })
        if added is None:
            added = datetime.utcnow()
        data.update({
            "added": added,
        })
        # push to DB
        try:
            self.measurements_col.insert_one(data)
        except Exception:
            logger.error(f'## Failed to add entry to the DB: {data}')

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
