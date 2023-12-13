from datetime import datetime
from pytz import timezone
import json

from handler import Handler, Database


class BalanceHandler(Handler):
    _name = "Radwag balance message handler"
    _config_section = "BALANCE"


    def __init__(self, config) -> None:
        self._collection = config[BalanceHandler._config_section]["Collection"]
        self.topic = config[BalanceHandler._config_section]["Topic"]
        self.short_topic = self.topic[:-1] if self.topic.endswith("#") else self.topic
        self._tz = timezone("Europe/Helsinki")


    @staticmethod
    def getName():
        return BalanceHandler._name


    @staticmethod
    def getConfigSection():
        return BalanceHandler._config_section


    @staticmethod
    def getDatabase() -> Database:
        return Database.INFLUXDB


    def getCollection(self):
        return self._collection


    def on_message(self, msg):
        payload = json.loads(msg.payload)
        # convert unix ts to datetime object, allows insertion to correct format
        payload["ts"] = datetime.fromtimestamp(payload["ts"], self._tz)

        return payload
