from influxdb_client import Point
from ruuvi_decoders import Df5Decoder, Df3Decoder
import datetime
import json
from dfacdecoder import DfAcDecoder
from dfafdecoder import DfAfDecoder
from handler import Handler, Database


class RuuviVibraHandler(Handler):
    _name = "RuuviGateway vibration firmware message handler"
    _config_section = "RUUVIVIBRA"
    _config_allowed_macs = "RUUVIVIBRA.ALLOWED_MACS"


    def __init__(self, config) -> None:
        self.SEEN_MACS = []
        self._bucket = config[RuuviVibraHandler._config_section]["Bucket"]
        self.topic = config[RuuviVibraHandler._config_section]["Topic"]
        self.short_topic = self.topic[:-1] if self.topic.endswith("#") else self.topic
        self.allowed_ruuvitags = []
        for key, value in config.items(RuuviVibraHandler._config_allowed_macs):
            print(value)
            self.allowed_ruuvitags.append(json.loads(value))
        if __debug__: print(f"Allowed tags: {self.allowed_ruuvitags}")


    @staticmethod
    def getName():
        return RuuviVibraHandler._name


    @staticmethod
    def getConfigSection():
        return RuuviVibraHandler._config_section


    @staticmethod
    def getDatabase() -> Database:
        return Database.INFLUXDB
    

    def getBucket(self):
        return self._bucket


    def handleMessage(self, msg):
        data_point = None

        mac = msg.topic.split("/")[-1].replace(":", "").lower()

        # check if mac is on list of allowed devices
        flt = filter(lambda tag: tag["mac"] == mac, self.allowed_ruuvitags)
        tag = next(flt, None)
        if tag is None:
            return None
        
        if tag["seen"] == False:
            print(f"First msg from {tag['name']} ({tag['mac']})")
            tag["seen"] = True

        payload = json.loads(msg.payload)
        
        if payload.get("data") is not None:
            try:
                raw_data = payload.get("data")

                if 'FF9904' in raw_data:
                    data_point = self.parseRuuviTag(payload, mac)
                elif '4C000215' in raw_data:
                    #raise Exception("Ignoring iBeacon")
                    return None
                else:
                    msg = f"Unknown type. mac: {mac} Raw data: {raw_data}"
                    raise Exception(msg)

                if data_point is not None:
                    data_point.tag("name", tag["name"])

                return data_point
            except Exception as e: 
                print(e)
                pass 
    
    def parseRuuviTag(payload, mac):
        clean_data = payload.get("data").split("FF9904")[1]

        format = clean_data[0:2]
        data = {}
        if format == "03":
            decoder = Df3Decoder()
            data = decoder.decode_data(clean_data)
            return None
        elif format == "AF":
            decoder = DfAfDecoder()
            data = decoder.decode_data(clean_data)

            if data is not None:
                p = Point("ruuvi_af")
                p.tag("mac", mac)
                p.tag("format", data.data_format)
                p.tag("type", data.type)
                
                p.field("scale", data.scale)
                p.field("frequency", data.frequency)
                for i in range(len(data.buckets)):
                    p.field(f"bucket_{i + 1:02d}", data.buckets[i])
                p.field("measurementNumber", data.measurementNumber)
                p.field("rssiDB", data.rssiDB)

                ts = datetime.datetime.utcfromtimestamp(int(payload.get("ts")))
                p.time(ts.isoformat())
        
                return p
        elif format == "AC":
            decoder = DfAcDecoder()
            data = decoder.decode_data(clean_data)

            if data is not None:
                p = Point("ruuvi_ac")
                p.tag("mac", mac)
                #p.tag("format", data["data_format"])
                p.field("p2p_x", data.p2px)
                p.field("p2p_y", data.p2py)
                p.field("p2p_z", data.p2pz)

                p.field("rms_x", data.rmsx)
                p.field("rms_y", data.rmsy)
                p.field("rms_z", data.rmsz)

                p.field("sequence", data.seq)

                p.field("temperature", data.temperature)
                p.field("voltage", data.voltage)
                
                ts = datetime.datetime.utcfromtimestamp(int(payload.get("ts")))
                p.time(ts.isoformat())

                return p
        elif format == "05":
            decoder = Df5Decoder()
            data = decoder.decode_data(clean_data)
        
            if data is not None:

                p = Point("ruuvi")
                p.tag("mac", mac)
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
        else:
            print(f"Unknown format: {format}")
            return None