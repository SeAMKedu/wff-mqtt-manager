from influxdb_client import Point
import json

from handler import Handler, Database


class HomogenizerHandler(Handler):
    _name = "Homogenizer message handler"
    _config_section = "HOMOGENIZER"


    def __init__(self, config) -> None:
        self._bucket = config[HomogenizerHandler._config_section]["Bucket"]
        self.topic = config[HomogenizerHandler._config_section]["Topic"]
        self.short_topic = self.topic[:-1] if self.topic.endswith("#") else self.topic


    @staticmethod
    def getName():
        return HomogenizerHandler._name


    @staticmethod
    def getConfigSection():
        return HomogenizerHandler._config_section
    

    @staticmethod
    def getDatabase() -> Database:
        return Database.INFLUXDB


    def getBucket(self):
        return self._bucket


    def handleMessage(self, msg):
        # {"tst":"2022-10-24T09:25:30.635114Z+0300","topic":"seamk/wff/homogenizer/sensor1","qos":0,"retain":0,"payloadlen":4,"payload":"0.00"}
        # updated payload
        # '{"hall":"81.00","s1raw":"0.00","s2raw":"0.00"}'
        #print(dir(msg))
        
        #field = msg.topic.split("/")[-1]

        data = json.loads(str(msg.payload.decode("utf-8","ignore")))
        
        p = Point("homogenizer")
        p.field("hall", float(data["hall"]))
        p.field("sensor1raw", float(data["s1raw"]))
        p.field("sensor2raw", float(data["s2raw"]))
        
        return p
