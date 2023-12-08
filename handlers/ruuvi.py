from influxdb_client import Point
from ruuvi_decoders import Df5Decoder, Df3Decoder
import datetime
import json
from ..handler import Handler

class RuuviHandler(Handler):


    def __init__(self, config) -> None:
        self.SEEN_UUIDS = []


    def getName():
        return "RuuviGateway handler"


    def getConfigSection():
        return "RUUVIGATEWAY"


    def handleMessage(self, msg):
        data_point = None

        payload = json.loads(msg.payload)
        #print(payload)
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

        if not data["mac"] in allowed_ruuvitags:
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
            if uuid not in self.SEEN_UUIDS:
                # track 20 latest unknown uuids to lessen number of log entries
                self.SEEN_UUIDS.append(uuid)
                if len(self.SEEN_UUIDS) > 20:
                    self.SEEN_UUIDS.pop(0)
                print(f"Unknown iBeacon uuid, {uuid}")
                print(f"Data ({len(data)}): {data}")
            return

        # convert from hex strings to integers
        major = int(data[32:36], 16) # temp in fahrenheit
        minor = int(data[36:40], 16) / 1000.0 # gravity
        tx_power = int(data[40], 16)
        rssi = int(data[41], 16)

        #print(f"Data ({len(data)}): {data}")
        #print(f"{data[32:36]} -> {major}, {data[36:40]} -> {minor}, {data[40]} -> {tx_power}, {data[41]} -> {rssi}")
        
        p = Point("tilt")
        p.tag("device", colors[uuid])
        p.field("temperature", (float(major) - 32) * 5/9)
        p.field("gravity", minor)
        #p.field("tx_power", tx_power)
        #p.field("rssi", rssi)

        ts = datetime.datetime.utcfromtimestamp(int(payload.get("ts")))
        p.time(ts.isoformat())

        #print(p)

        return p
