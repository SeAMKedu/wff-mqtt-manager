from datetime import datetime
from pytz import timezone
from influxdb_client import Point
from handler import Handler, Database


class MQTTStatsHandler(Handler):
    _name = "MQTT statistics handler"
    _config_section = "MQTT_STATS"
    _topics_of_interest = [
        { "tag": "clients_total", "topic": "$SYS/broker/clients/total", "format": int },
        { "tag": "clients_active", "topic": "$SYS/broker/clients/active", "format": int },
        { "tag": "clients_connected", "topic": "$SYS/broker/clients/connected", "format": int },
        { "tag": "messages_received", "topic": "$SYS/broker/load/messages/received/1min", "format": float },
        { "tag": "messages_sent", "topic": "$SYS/broker/load/messages/sent/1min", "format": float },
        { "tag": "bytes_received", "topic": "$SYS/broker/load/bytes/received/1min", "format": float },
        { "tag": "bytes_sent", "topic": "$SYS/broker/load/bytes/sent/1min", "format": float },
        { "tag": "subscription_count", "topic": "$SYS/broker/subscriptions/count", "format": int  }
    ]


    def __init__(self, config) -> None:
        self._bucket = config[MQTTStatsHandler._config_section]["Bucket"]
        self.topic = config[MQTTStatsHandler._config_section]["Topic"]
        self.short_topic = self.topic[:-1] if self.topic.endswith("#") else self.topic
        self._tz = timezone("Europe/Helsinki")


    @staticmethod
    def getName():
        return MQTTStatsHandler._name


    @staticmethod
    def getConfigSection():
        return MQTTStatsHandler._config_section


    @staticmethod
    def getDatabase() -> Database:
        return Database.INFLUXDB

    
    def getBucket(self):
        return self._bucket


    def handleMessage(self, msg):
        data_point = None

        flt = filter(lambda topic: topic["topic"] == msg.topic, self._topics_of_interest)
        topic = next(flt, None)
        if topic is None:
            return None

        value = msg.payload.decode("utf-8")
        value = topic["format"](value)

        data_point = Point("mosquitto")
        data_point.field(topic["tag"], value)

        ts = datetime.now(self._tz)
        data_point.time(ts.isoformat())
        
        return data_point

