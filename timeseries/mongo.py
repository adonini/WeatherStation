from pymongo import MongoClient
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

logger = logging.getLogger('main.mongo')
load_dotenv()


class MongoTS:
    """
    MongoDB Time Series storage for weather station.
    """

    def __init__(self):
        self.db_host = os.environ.get('DB_HOST', 'localhost')
        self.db_port = os.environ.get('DB_PORT', '27017')
        self.db_name = os.environ.get('DB_NAME', 'WeatherDB')
        self.collection_name = "weather"

        #self.uri = f"mongodb://{self.db_host}:{self.db_port}"
        self.uri = "mongodb://localhost:27017"

        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]

            # Create TS collection if not exists
            if self.collection_name not in self.db.list_collection_names():
                self.db.create_collection(
                    self.collection_name,
                    timeseries={
                        "timeField": "timestamp",
                        "granularity": "seconds"
                    }
                )

            self.col = self.db[self.collection_name]
            logger.info("Connected to MongoDB Time Series")

        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def _build_timestamp(self, ws_date, ws_time):
        """
        Convert WS date + time to UTC datetime
        """
        try:
            ws_time = ws_time.strip().zfill(6)
            dt_str = ws_date + ws_time[:6]
            return datetime.strptime(dt_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.warning(f"Timestamp parsing failed: {e}")
            return datetime.now(timezone.utc)

    def insert(self, data: dict):
        """
        Insert one snapshot into TS collection
        """

        ws_date = str(data.pop("Date", None))
        ws_time = str(data.pop("Time", None))

        if not ws_date or not ws_time:
            logger.warning("Missing Date or Time -> skipping insert")
            return

        timestamp = self._build_timestamp(ws_date, ws_time)

        doc = {
            "timestamp": timestamp,
            **data
        }

        try:
            self.col.insert_one(doc)
            logger.debug(f"Inserted TS doc at {timestamp}")
        except Exception as e:
            logger.error(f"Insert failed: {e}")

    def close(self):
        self.client.close()
