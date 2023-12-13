import json
from influxdb_client import Point

from handler import Handler, Database


class ShellyHandler(Handler):
    _name = "Shelly Pro 3EM message handler"
    _config_section = "SHELLY3EM"


    def __init__(self, config) -> None:
        self._bucket = config[ShellyHandler._config_section]["Bucket"]
        self._location = config[ShellyHandler._config_section]["Location"]
        self.topic = config[ShellyHandler._config_section]["Topic"]
        self.short_topic = self.topic[:-1] if self.topic.endswith("#") else self.topic


    @staticmethod
    def getName():
        return ShellyHandler._name


    @staticmethod
    def getConfigSection():
        return ShellyHandler._config_section


    @staticmethod
    def getDatabase() -> Database:
        return Database.INFLUXDB


    def getBucket(self):
        return self._bucket


    def handleMessage(self, msg):
        # The callback for when a PUBLISH message is received from the server.
        payload = json.loads(msg.payload)
        #print(payload)
        data_point = None
        
        if payload.get("total_act_power") is not None:
            try:
                 data_point = self.parseShelly(payload)
            except Exception as e: print(e)

        return data_point


    def parseShelly(self, payload):
        fields = [
            "a_current", "a_voltage", "a_act_power", "a_aprt_power", "a_pf", "a_freq",
            "b_current", "b_voltage", "b_act_power", "b_aprt_power", "b_pf", "b_freq",
            "c_current", "c_voltage", "c_act_power", "c_aprt_power", "c_pf", "c_freq",
            "n_current",
            "total_current", "total_act_power", "total_aprt_power"
        ]
        
        p = Point("shelly")
        p.tag("location", self._location)
        for f in fields:
            p.field(f, payload[f])
        
        return p
