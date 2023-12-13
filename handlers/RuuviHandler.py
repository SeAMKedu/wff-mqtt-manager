from influxdb_client import Point
from ruuvi_decoders import Df5Decoder, Df3Decoder
import datetime
import json
import re
from handler import Handler, Database


class RuuviHandler(Handler):
    _name = "RuuviGateway message handler"
    _config_section = "RUUVIGATEWAY"
    _config_allowed_macs = "RUUVIGATEWAY.ALLOWED_MACS"
    _macs_tracked = 20


    def __init__(self, config) -> None:
        self.SEEN_MACS = []
        self._bucket = config[RuuviHandler._config_section]["Bucket"]
        self.topic = config[RuuviHandler._config_section]["Topic"]
        self.short_topic = self.topic[:-1] if self.topic.endswith("#") else self.topic
        self.allowed_ruuvitags = []
        for key, value in config.items(RuuviHandler._config_allowed_macs):
            self.allowed_ruuvitags.append(re.findall('"([^"]*)"', value)[0])
        if __debug__: print(f"Allowed tags: {self.allowed_ruuvitags}")


    @staticmethod
    def getName():
        return RuuviHandler._name


    @staticmethod
    def getConfigSection():
        return RuuviHandler._config_section


    @staticmethod
    def getDatabase() -> Database:
        return Database.INFLUXDB


    def getBucket(self):
        return self._bucket


    def handleMessage(self, msg):
        data_point = None

        payload = json.loads(msg.payload)

        if payload.get("data") is not None:
            raw_data = payload.get("data")

            if 'FF9904' in raw_data:
                data_point = self.parseRuuviTag(payload)
            elif '4C000215' in raw_data:
                data_point = self.parseiBeacon(payload)

        return data_point

    
    def parseRuuviTag(self, payload):
        clean_data = payload.get("data").split("FF9904")[1]

        format = clean_data[0:2]
        data = {}
        if format == "03":
            decoder = Df3Decoder()
            data = decoder.decode_data(clean_data)
        else:
            decoder = Df5Decoder()
            data = decoder.decode_data(clean_data)


        if not data["mac"] in self.allowed_ruuvitags:
            if __debug__: print("Mac not whitelisted")
            return None

        p = Point("ruuvi")
        p.tag("mac", data["mac"])
        p.tag("format", data["data_format"])
        p.field("humidity", data["humidity"])
        p.field("temperature", data["temperature"])
        p.field("pressure", data["pressure"])
        p.field("acceleration", data["acceleration"])
        p.field("acc_x", data["acceleration_x"])
        p.field("acc_y", data["acceleration_y"])
        p.field("acc_z", data["acceleration_z"])
        p.field("tx_power", data["tx_power"])
        p.field("battery", data["battery"])
        p.field("movement_counter", data["movement_counter"])
        
        ts = datetime.datetime.utcfromtimestamp(int(payload.get("ts")))
        p.time(ts.isoformat())

        return p


    def parseiBeacon(self, payload):
        # adapted from  https://github.com/theBASTI0N/beacondecoder_src/
        # and https://kvurd.com/blog/tilt-hydrometer-ibeacon-data-format/

        colors = {
            'A495BB10C5B14B44B5121370F02D74DE': 'red',
            'A495BB20C5B14B44B5121370F02D74DE': 'green',
            'A495BB30C5B14B44B5121370F02D74DE': 'black',
            'A495BB40C5B14B44B5121370F02D74DE': 'purple',
            'A495BB50C5B14B44B5121370F02D74DE': 'orange',
            'A495BB60C5B14B44B5121370F02D74DE': 'blue',
            'A495BB70C5B14B44B5121370F02D74DE': 'yellow',
            'A495BB80C5B14B44B5121370F02D74DE': 'pink',
        }
        
        data = payload.get("data").split("4C000215")[1]
        uuid = data[0:32]

        if not uuid in colors.keys():
            if uuid not in self.MACS:
                # track n latest unknown uuids to lessen number of log entries
                self.MACS.append(uuid)
                if len(self.SEEN_MACS) > RuuviHandler._macs_tracked:
                    self.SEEN_MACS.pop(0)
                if __debug__: print(f"Unknown iBeacon uuid, {uuid}\nData ({len(data)}): {data}")
            return

        # convert from hex strings to integers
        major = int(data[32:36], 16) # temp in fahrenheit
        minor = int(data[36:40], 16) / 1000.0 # gravity
        tx_power = int(data[40], 16)
        rssi = int(data[41], 16)

        p = Point("tilt")
        p.tag("device", colors[uuid])
        p.field("temperature", (float(major) - 32) * 5/9)
        p.field("gravity", minor)
        #p.field("tx_power", tx_power)
        #p.field("rssi", rssi)

        ts = datetime.datetime.utcfromtimestamp(int(payload.get("ts")))
        p.time(ts.isoformat())

        return p
